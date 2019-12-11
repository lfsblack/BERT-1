import tensorflow as tf
import numpy as np

from utils.bert import bert_utils
from utils.bert import bert_modules, albert_modules

class FlipGradientBuilder(object):
	def __init__(self):
		self.num_calls = 0

	def __call__(self, x, l=1.0):
		grad_name = "FlipGradient%d" % self.num_calls
		@ops.RegisterGradient(grad_name)
		def _flip_gradients(op, grad):
			return [tf.negative(grad) * l]
		
		g = tf.get_default_graph()
		with g.gradient_override_map({"Identity": grad_name}):
			y = tf.identity(x)
			
		self.num_calls += 1
		return y
	
flip_gradient = FlipGradientBuilder()

def sample_gumbel(shape, samples=1, eps=1e-20): 
	"""Sample from Gumbel(0, 1)"""
	if samples > 1:
		sample_shape = shape + [samples]
	else:
		sample_shape = shape
	U = tf.random_uniform(sample_shape, minval=0, maxval=1)
	return -tf.log(-tf.log(U + eps) + eps)

def gumbel_softmax(logits, temperature, samples=1): 
	""" Draw a sample from the Gumbel-Softmax distribution"""
	input_shape_list = bert_utils.get_shape_list(logits, expected_rank=2)
	if samples > 1:
		logits = tf.expand_dims(logits, -1)
	y = logits + sample_gumbel(input_shape_list, samples)
	return tf.exp(tf.nn.log_softmax(y / temperature, axis=1))

def token_generator_gumbel(config, input_tensor,
					output_weights, 
					input_ids, 
					input_ori_ids,
					input_mask, 
					**kargs):
	
	input_shape_list = bert_utils.get_shape_list(input_tensor, expected_rank=3)
	batch_size = input_shape_list[0]
	seq_length = input_shape_list[1]
	hidden_dims = input_shape_list[2]

	embedding_projection = kargs.get('embedding_projection', None)

	scope = kargs.get('scope', None)
	if scope:
		scope = scope + '/' + 'cls/predictions'
	else:
		scope = 'cls/predictions'

	tf.logging.info("**** mlm generator scope **** %s", str(scope))

	# with tf.variable_scope("cls/predictions", reuse=tf.AUTO_REUSE):
	with tf.variable_scope(scope, reuse=tf.AUTO_REUSE):
		if config.get('ln_type', 'postln') == 'preln':
			input_tensor = albert_modules.layer_norm(input_tensor)
		elif config.get('ln_type', 'postln') == 'postln':
			input_tensor = input_tensor
		else:
			input_tensor = input_tensor

		if config.get("embedding", "factorized") == "factorized":
			projection_width = config.hidden_size
		else:
			projection_width = config.embedding_size

		with tf.variable_scope("transform"):
			input_tensor = tf.layers.dense(
					input_tensor,
					units=projection_width,
					activation=albert_modules.get_activation(config.hidden_act),
					kernel_initializer=albert_modules.create_initializer(
							config.initializer_range))

			if config.get('ln_type', 'postln') == 'preln':
				input_tensor = input_tensor
			elif config.get('ln_type', 'postln') == 'postln':
				input_tensor = albert_modules.layer_norm(input_tensor)
			else:
				input_tensor = albert_modules.layer_norm(input_tensor)

		if embedding_projection is not None:
			# batch x seq x hidden, embedding x hidden
			print(input_tensor.get_shape(), embedding_projection.get_shape())
			input_tensor = tf.einsum("abc,dc->abd", input_tensor, embedding_projection)
		else:
			print("==no need for embedding projection==")
			input_tensor = input_tensor

		output_bias = tf.get_variable(
				"output_bias",
				shape=[config.vocab_size],
				initializer=tf.zeros_initializer())
		# batch x seq x embedding
		logits = tf.einsum("abc,dc->abd", input_tensor, output_weights)
		logits = tf.nn.bias_add(logits, output_bias)

		input_shape_list = bert_utils.get_shape_list(logits, expected_rank=3)
		width = input_shape_list[2]

		logits_tempered = logits / config.get("temperature", 1.0)

		# width=config.vocab_size
		flat_logits_tempered = tf.reshape(logits_tempered,
									[batch_size * seq_length, width])

		annealed_temp = tf.train.polynomial_decay(config.get('gumbel_temperature', 2.0),
												tf.train.get_or_create_global_step(),
												kargs.get("num_train_steps", 10000),
												end_learning_rate=0.1,
												power=1.0,
												cycle=False)

		# [batch x seq] x config.vocab_size x config.get('gen_sample', 1)
		sampled_logprob = gumbel_softmax(flat_logits_tempered, 
										temperature=1.0,
										samples=config.get('gen_sample', 1))

		# argmax on config.vocab_size which is always axis=1
		# [batch x seq] x config.vocab_size x config.get('gen_sample', 1)
		sampled_id = tf.one_hot(tf.argmax(sampled_logprob, axis=1), 
								config.vocab_size,
								axis=1) # sampled multiminal id

		# straight-thourth gumbel softmax estimator
		sampled_id = tf.stop_gradient(sampled_id-sampled_logprob) + flip_gradient(sampled_logprob)

		sampled_binary_mask = kargs.get('sampled_binary_mask', None)
		if sampled_binary_mask is not None:
			label_diff_ids =  tf.identity(sampled_binary_mask) # 0 for original and 1 for replace
		else:
			label_diff_ids = tf.not_equal(
							tf.cast(input_ids, tf.int32),
							tf.cast(input_ori_ids, tf.int32) # 0 for original and 1 for replace
						)

		label_diff_ids = tf.cast(label_diff_ids, tf.float32)

		label_diff_ids = tf.expand_dims(label_diff_ids, axis=[-1]) # batch x seq x 1
		input_ori_ids = tf.one_hot(input_ori_ids, config.vocab_size) # batch x seq x vocab
		input_ori_ids = tf.cast(input_ori_ids, tf.float32)

		if config.get('gen_sample', 1) == 1:
			sampled_input_id = tf.reshape(sampled_id, [batch_size, seq_length, config.vocab_size])
			if kargs.get('mask_method', 'only_mask') == 'only_mask':
				tf.logging.info("****** only mask sample *******")
				label_diff_ids = tf.cast(label_diff_ids, tf.float32)
				sampled_input_id = (label_diff_ids) * tf.cast(sampled_input_id, tf.float32) + (1 - label_diff_ids) * tf.cast(input_ori_ids, tf.float32)
		else:
			sampled_input_id = tf.reshape(samples, [batch_size, seq_length, config.vocab_size, config.get('gen_sample', 1)])
			label_diff_ids = tf.expand_dims(label_diff_ids, axis=-1) # batch x seq x 1
			input_ori_ids = tf.expand_dims(input_ori_ids, axis=-1) # batch x seq x vocab x 1

			if kargs.get('mask_method', 'only_mask') == 'only_mask':
				tf.logging.info("****** only mask sample *******")
				sampled_input_id = (label_diff_ids) * tf.cast(sampled_input_id, tf.float32) + (1 - input_ori_ids) * label_diff_ids

		return sampled_input_id









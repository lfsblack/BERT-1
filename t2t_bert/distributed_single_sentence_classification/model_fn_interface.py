try:
	from .model_fn import model_fn_builder
	from .model_distillation_fn import model_fn_builder as model_distillation_builder_fn
	from distributed_pair_sentence_classification.bert_model_fn import model_fn_builder as bert_nli_builder_fn
	from distributed_pair_sentence_classification.interaction_model_fn import model_fn_builder as interaction_builder_fn
	from distributed_pair_sentence_classification.interaction_distillation_model_fn import model_fn_builder as interaction_distillation_builder_fn
	from .embed_model_fn import model_fn_builder as embed_model_fn_builder
	from .model_feature_distillation_fn import model_fn_builder as feature_distillation_fn_builder
except:
	from model_fn import model_fn_builder
	from model_distillation_fn import model_fn_builder as model_distillation_builder_fn
	from distributed_pair_sentence_classification.bert_model_fn import model_fn_builder as bert_nli_builder_fn
	from distributed_pair_sentence_classification.interaction_model_fn import model_fn_builder as interaction_builder_fn
	from distributed_pair_sentence_classification.interaction_distillation_model_fn import model_fn_builder as interaction_distillation_builder_fn
	from embed_model_fn import model_fn_builder as embed_model_fn_builder
	from model_feature_distillation_fn import model_fn_builder as feature_distillation_fn_builder

def model_fn_interface(FLAGS):
	print("==apply {} {} model fn builder==".format(FLAGS.task_type, FLAGS.distillation))
	if FLAGS.task_type in ["single_sentence_classification"]:
		if FLAGS.distillation == "distillation":
			return model_distillation_builder_fn
		elif FLAGS.distillation == "normal":
			return model_fn_builder
		elif FLAGS.distillation == "feature_distillation":
			return feature_distillation_fn_builder
		else:
			return model_fn_builder
	elif FLAGS.task_type in ["pair_sentence_classification"]:
		if FLAGS.distillation == "normal":
			return bert_nli_builder_fn
		else:
			return bert_nli_builder_fn
	elif FLAGS.task_type in ["interaction_pair_sentence_classification"]:
		if FLAGS.distillation == "normal":
			return interaction_builder_fn
		elif FLAGS.distillation == "distillation":
			return interaction_distillation_builder_fn
		else:
			return interaction_builder_fn
	elif FLAGS.task_type in ["embed_sentence_classification"]:
		return embed_model_fn_builder

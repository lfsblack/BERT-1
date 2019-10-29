CUDA_VISIBLE_DEVICES="" python ./t2t_bert/chid_nlpcc2019/export_api.py \
 	--buckets "/data/xuht" \
	--config_file "./data/chinese_L-12_H-768_A-12/bert_config.json" \
	--init_checkpoint "open_data/model/bert_chid_0816_ema/model.ckpt-270830" \
	--vocab_file "./data/chinese_L-12_H-768_A-12/vocab.txt" \
	--label_id "./data/lcqmc/label_dict.json" \
	--max_length 272 \
	--train_file "porn/clean_data/textcnn/distillation/train_tfrecords" \
	--dev_file "porn/clean_data/textcnn/distillation/test_tfrecords" \
	--model_output "open_data/model/bert_chid_0816_ema/" \
	--export_dir "open_data/model/bert_chid_0816_ema/export" \
	--epoch 8 \
	--num_classes 2 \
	--train_size 952213 \
	--eval_size 238054 \
	--batch_size 24 \
	--model_type "bert" \
	--if_shard 2 \
	--is_debug 1 \
	--run_type "sess" \
	--opt_type "all_reduce" \
	--num_gpus 4 \
	--parse_type "parse_batch" \
	--rule_model "normal" \
	--profiler "no" \
	--train_op "adam_weight_decay_exclude" \
	--running_type "eval" \
	--cross_tower_ops_type "paisoar" \
	--distribution_strategy "MirroredStrategy" \
	--load_pretrained "yes" \
	--w2v_path "w2v/tencent_ai_lab/char_w2v.txt" \
	--with_char "no_char" \
	--input_target "" \
	--decay "no" \
	--warmup "no" \
	--distillation "normal" \
    --task_type "bert_chid" \
    --max_predictions_per_seq 5
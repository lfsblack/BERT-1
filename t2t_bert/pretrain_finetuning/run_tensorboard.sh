odpscmd=$1
pai_command="
	pai -name tensorboard
		-DsummaryDir='oss://alg-misc/BERT/bert_pretrain/open_domain/pretrain_single_random_debug_gan/group/corrupted_ce_generator_1_1_embedding_checkpoint_0.2_soft_vqvae_v2/?role_arn=acs:ram::1265628042679515:role/yuefeng2&host=cn-hangzhou.oss-internal.aliyun-inc.com'
"

echo "${pai_command}"
${odpscmd} -e "${pai_command}"
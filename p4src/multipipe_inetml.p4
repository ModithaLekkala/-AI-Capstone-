#include "common/headers.p4"
//#include "tf_pipelines/tf_feature_extr/feature_extractor.p4"
// #include "tf_pipelines/tf_bnn_exec_132-42-2_7nr/tofino_mlp.p4"
// #include "tf_pipelines/tf_bnn_exec_128-32-8-2_4nr/tofino_mlp.p4"
 #include "tf_pipelines/tf_bnn_exec_98-21-2_7nr/tofino_mlp.p4"

// Switch(features_collector, bnn_executor) main;
Switch(bnn_executor) main;
// Switch(features_collector) main;

# 0) env
export SDE=/home/sgeraci/bf-sde-9.13.4
export SDE_INSTALL=/home/sgeraci/bf-sde-9.13.4/install
export REPO_PATH=/home/sgeraci/inet-hynn

# 1) clean previous install + build
bash tools/clean_tofino_program.sh -p multipipe_inetml -b $REPO_PATH/p4src/build/multipipe_inetml -k -y

# 2) build + install (+ optionally run)
bash tools/build_install_p4.sh \
  -p multipipe_inetml \
  -P $REPO_PATH/p4src/multipipe_inetml.p4 \
  -b $REPO_PATH/p4src/build/multipipe_inetml \
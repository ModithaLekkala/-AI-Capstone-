# 0) env
export SDE=/home/sgeraci/p4/open-p4studio
export SDE_INSTALL=/home/sgeraci/p4/open-p4studio/install

# 1) clean previous install + build
bash tools/clean_tofino_program.sh -p multipipe_inetml -b ./build/multipipe_inetml -k -y

# 2) build + install (+ optionally run)
bash tools/build_install_p4.sh \
  -p multipipe_inetml \
  -P /home/sgeraci/slu/inet-hynn/p4src/multipipe_inetml.p4 \
  -b ./build/multipipe_inetml \
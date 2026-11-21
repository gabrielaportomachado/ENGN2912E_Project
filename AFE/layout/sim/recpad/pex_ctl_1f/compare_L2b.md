# compare.py L2b: AFE/layout/sim/recpad/pex_ctl_1f against AFE/layout/baseline

| check | corner | value | baseline | post-layout | change | limit | result |
|---|---|---|---|---|---|---|---|
| amp_pwrup | ff85 | err_1s_mv | 0.09506 | 18.178 | +18.08 | <= 50 | PASS |
| amp_pwrup | ff85 | vout_before_v | 1.1413 | 1.1494 | +0.0081 |  |  |
| amp_pwrup | ss-40 | err_1s_mv | 0.61939 | 19.817 | +19.2 | <= 50 | PASS |
| amp_pwrup | ss-40 | vout_before_v | 1.8006 | 2.4735 | +0.6729 |  |  |
| amp_pwrup | typ | err_1s_mv | 0.23517 | 30.276 | +30.04 | <= 50 | PASS |
| amp_pwrup | typ | vout_before_v | 2.4605 | 2.466 | +0.00554 |  |  |
| amp_reset | ff85 | t_fs_ms_os10m | 1.6282 | 1.6215 | -0.006693 | x / baseline 0.7 .. 1.4 | PASS |
| amp_reset | ff85 | t_1mv_s_os0 | 2.9885 | 5.4726 | +2.484 | <= 6.75 | PASS |
| amp_reset | ff85 | t_1mv_s_os1m | 2.3341 | 5.5065 | +3.172 | <= 6.75 | PASS |
| amp_reset | ff85 | t_1mv_s_os10m | 4.3769 | 8.437 | +4.06 | <= 9.75 | PASS |
| amp_reset | ff85 | t_1mv_s_os100m | 5.4605 | 9.5917 | +4.131 | <= 12 | PASS |
| amp_reset | ff85 | final_v_os100m | 1.6511 | 1.6511 | -3.54e-05 | 1.6 .. 1.7 | PASS |
| amp_reset | ff85 | final_v_os10m | 1.651 | 1.6511 | +0.000153 | 1.6 .. 1.7 | PASS |
| amp_reset | ff85 | peak_mv_os100m | 169.46 | 421.42 | +252 |  |  |
| amp_reset | ff85 | rel_step_mv_os10m | 4.0326 | -319.52 | -323.5 |  |  |
| amp_reset | ff85 | drift_mv_s_os10m | -0.77377 | -7.9031 | -7.129 |  |  |
| amp_reset | ss-40 | t_fs_ms_os10m | 5.7918 | 5.899 | +0.1073 | x / baseline 0.7 .. 1.4 | PASS |
| amp_reset | ss-40 | t_1mv_s_os0 | 0.6545 | 5.461 | +4.807 | <= 6.75 | PASS |
| amp_reset | ss-40 | t_1mv_s_os1m | 0.39849 | 5.4254 | +5.027 | <= 6.75 | PASS |
| amp_reset | ss-40 | t_1mv_s_os10m | 2.7357 | 7.3009 | +4.565 | <= 9.75 | PASS |
| amp_reset | ss-40 | t_1mv_s_os100m | 6.8473 | 7.8371 | +0.9898 | <= 12 | PASS |
| amp_reset | ss-40 | final_v_os100m | 1.6503 | 1.6503 | -1.962e-05 | 1.6 .. 1.7 | PASS |
| amp_reset | ss-40 | final_v_os10m | 1.6502 | 1.6502 | +3.296e-05 | 1.6 .. 1.7 | PASS |
| amp_reset | ss-40 | peak_mv_os100m | 53.334 | 160.35 | +107 |  |  |
| amp_reset | ss-40 | rel_step_mv_os10m | 0.00206 | 0.00943 | +0.00737 |  |  |
| amp_reset | ss-40 | drift_mv_s_os10m | -0.32478 | -6.7301 | -6.405 |  |  |
| amp_reset | typ | t_fs_ms_os10m | 3.0966 | 3.0211 | -0.07547 | x / baseline 0.7 .. 1.4 | PASS |
| amp_reset | typ | t_1mv_s_os0 | 1.7995 | 5.5912 | +3.792 | <= 6.75 | PASS |
| amp_reset | typ | t_1mv_s_os1m | 1.3957 | 5.5625 | +4.167 | <= 6.75 | PASS |
| amp_reset | typ | t_1mv_s_os10m | 3.8016 | 8.5718 | +4.77 | <= 9.75 | PASS |
| amp_reset | typ | t_1mv_s_os100m | 8.4225 | 9.5283 | +1.106 | <= 12 | PASS |
| amp_reset | typ | final_v_os100m | 1.6507 | 1.6507 | +8.085e-07 | 1.6 .. 1.7 | PASS |
| amp_reset | typ | final_v_os10m | 1.6507 | 1.6508 | +0.0001406 | 1.6 .. 1.7 | PASS |
| amp_reset | typ | peak_mv_os100m | 57.939 | 280.16 | +222.2 |  |  |
| amp_reset | typ | rel_step_mv_os10m | -7.8744 | -253.95 | -246.1 |  |  |
| amp_reset | typ | drift_mv_s_os10m | -0.53498 | -7.7304 | -7.195 |  |  |
| amp_reset_host | ff85 | t_1mv_s_os10m | 3.7084 | 7.4247 | +3.716 | <= 9.75 | PASS |
| amp_reset_host | ff85 | t_1mv_s_os100m | 8.0417 | 9.1325 | +1.091 | <= 12 | PASS |
| amp_reset_host | ff85 | final_v_os100m | 1.6511 | 1.6511 | -2.668e-06 | 1.6 .. 1.7 | PASS |
| amp_reset_host | ss-40 | t_1mv_s_os10m | 2.8915 | 6.5185 | +3.627 | <= 9.75 | PASS |
| amp_reset_host | ss-40 | t_1mv_s_os100m | 6.5169 | 7.7269 | +1.21 | <= 12 | PASS |
| amp_reset_host | ss-40 | final_v_os100m | 1.6503 | 1.6503 | -4.193e-06 | 1.6 .. 1.7 | PASS |
| amp_reset_host | typ | t_1mv_s_os10m | 3.8841 | 7.6287 | +3.745 | <= 9.75 | PASS |
| amp_reset_host | typ | t_1mv_s_os100m | 8.0065 | 9.144 | +1.138 | <= 12 | PASS |
| amp_reset_host | typ | final_v_os100m | 1.6507 | 1.6507 | -3.158e-06 | 1.6 .. 1.7 | PASS |

MISSING: amp_ac: AFE/layout/sim/recpad/pex_ctl_1f/amp_ac.json does not exist (run AFE/layout/tb/tb_amp_ac.py --netlist <PEX> --corner all)
MISSING: amp_noise: AFE/layout/sim/recpad/pex_ctl_1f/amp_noise.json does not exist (run AFE/layout/tb/tb_amp_noise.py --netlist <PEX> --corner all)
MISSING: amp_loop: AFE/layout/sim/recpad/pex_ctl_1f/amp_loop.json does not exist (run AFE/layout/tb/tb_amp_loop.py --netlist <PEX> --corner all)
MISSING: amp_psrr: AFE/layout/sim/recpad/pex_ctl_1f/amp_psrr.json does not exist (run AFE/layout/tb/tb_amp_psrr.py --netlist <PEX> --corner all)
MISSING: amp_thd: AFE/layout/sim/recpad/pex_ctl_1f/amp_thd.json does not exist (run AFE/layout/tb/tb_amp_thd.py --netlist <PEX> --corner all)
MISSING: amp_ac_junction: AFE/layout/sim/recpad/pex_ctl_1f/amp_ac_junction.json does not exist (run AFE/layout/tb/tb_amp_ac.py --netlist <PEX> --corner all --junction)
MISSING: amp_pwrup_junction: AFE/layout/sim/recpad/pex_ctl_1f/amp_pwrup_junction.json does not exist (run AFE/layout/tb/tb_amp_pwrup.py --netlist <PEX> --corner all --junction)
MISSING: amp_reset_host_junction: AFE/layout/sim/recpad/pex_ctl_1f/amp_reset_host_junction.json does not exist (run AFE/layout/tb/tb_amp_reset.py --netlist <PEX> --corner all --junction)
RESULT compare L2b: FAIL  (33 PASS, 0 WARN, 0 FAIL, 8 missing)

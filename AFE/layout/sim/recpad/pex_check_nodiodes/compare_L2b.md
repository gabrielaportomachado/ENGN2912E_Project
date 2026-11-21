# compare.py L2b: AFE/layout/sim/recpad/pex_check_nodiodes against AFE/layout/baseline

| check | corner | value | baseline | post-layout | change | limit | result |
|---|---|---|---|---|---|---|---|
| amp_pwrup | ff85 | err_1s_mv | 0.09506 | 18.173 | +18.08 | <= 50 | PASS |
| amp_pwrup | ff85 | vout_before_v | 1.1413 | 1.1494 | +0.00809 |  |  |
| amp_pwrup | ss-40 | err_1s_mv | 0.61939 | 19.894 | +19.27 | <= 50 | PASS |
| amp_pwrup | ss-40 | vout_before_v | 1.8006 | 2.4738 | +0.6732 |  |  |
| amp_pwrup | typ | err_1s_mv | 0.23517 | 30.248 | +30.01 | <= 50 | PASS |
| amp_pwrup | typ | vout_before_v | 2.4605 | 2.3688 | -0.09172 |  |  |
| amp_reset | ff85 | t_fs_ms_os10m | 1.6282 | 1.6905 | +0.06232 | x / baseline 0.7 .. 1.4 | PASS |
| amp_reset | ff85 | t_1mv_s_os0 | 2.9885 | 5.4709 | +2.482 | <= 6.75 | PASS |
| amp_reset | ff85 | t_1mv_s_os1m | 2.3341 | 5.4967 | +3.163 | <= 6.75 | PASS |
| amp_reset | ff85 | t_1mv_s_os10m | 4.3769 | 8.6731 | +4.296 | <= 9.75 | PASS |
| amp_reset | ff85 | t_1mv_s_os100m | 5.4605 | 9.7165 | +4.256 | <= 12 | PASS |
| amp_reset | ff85 | final_v_os100m | 1.6511 | 1.6511 | -3.54e-05 | 1.6 .. 1.7 | PASS |
| amp_reset | ff85 | final_v_os10m | 1.651 | 1.6512 | +0.0001827 | 1.6 .. 1.7 | PASS |
| amp_reset | ff85 | peak_mv_os100m | 169.46 | 329.57 | +160.1 |  |  |
| amp_reset | ff85 | rel_step_mv_os10m | 4.0326 | -303.05 | -307.1 |  |  |
| amp_reset | ff85 | drift_mv_s_os10m | -0.77377 | -9.5937 | -8.82 |  |  |
| amp_reset | ss-40 | t_fs_ms_os10m | 5.7918 | 5.9846 | +0.1928 | x / baseline 0.7 .. 1.4 | PASS |
| amp_reset | ss-40 | t_1mv_s_os0 | 0.6545 | 5.4587 | +4.804 | <= 6.75 | PASS |
| amp_reset | ss-40 | t_1mv_s_os1m | 0.39849 | 5.4585 | +5.06 | <= 6.75 | PASS |
| amp_reset | ss-40 | t_1mv_s_os10m | 2.7357 | 7.1394 | +4.404 | <= 9.75 | PASS |
| amp_reset | ss-40 | t_1mv_s_os100m | 6.8473 | 8.1634 | +1.316 | <= 12 | PASS |
| amp_reset | ss-40 | final_v_os100m | 1.6503 | 1.6503 | -1.958e-05 | 1.6 .. 1.7 | PASS |
| amp_reset | ss-40 | final_v_os10m | 1.6502 | 1.6502 | +2.855e-05 | 1.6 .. 1.7 | PASS |
| amp_reset | ss-40 | peak_mv_os100m | 53.334 | 242.55 | +189.2 |  |  |
| amp_reset | ss-40 | rel_step_mv_os10m | 0.00206 | -11.409 | -11.41 |  |  |
| amp_reset | ss-40 | drift_mv_s_os10m | -0.32478 | -6.1562 | -5.831 |  |  |
| amp_reset | typ | t_fs_ms_os10m | 3.0966 | 3.0291 | -0.06746 | x / baseline 0.7 .. 1.4 | PASS |
| amp_reset | typ | t_1mv_s_os0 | 1.7995 | 5.5909 | +3.791 | <= 6.75 | PASS |
| amp_reset | typ | t_1mv_s_os1m | 1.3957 | 5.6049 | +4.209 | <= 6.75 | PASS |
| amp_reset | typ | t_1mv_s_os10m | 3.8016 | 8.5706 | +4.769 | <= 9.75 | PASS |
| amp_reset | typ | t_1mv_s_os100m | 8.4225 | 12.535 | +4.113 | <= 12 | FAIL |
| amp_reset | typ | final_v_os100m | 1.6507 | 1.6507 | +7.839e-07 | 1.6 .. 1.7 | PASS |
| amp_reset | typ | final_v_os10m | 1.6507 | 1.6508 | +0.0001405 | 1.6 .. 1.7 | PASS |
| amp_reset | typ | peak_mv_os100m | 57.939 | 863.11 | +805.2 |  |  |
| amp_reset | typ | rel_step_mv_os10m | -7.8744 | -255.53 | -247.7 |  |  |
| amp_reset | typ | drift_mv_s_os10m | -0.53498 | -7.7148 | -7.18 |  |  |
| amp_reset_host | ff85 | t_1mv_s_os10m | 3.7084 | 7.4249 | +3.716 | <= 9.75 | PASS |
| amp_reset_host | ff85 | t_1mv_s_os100m | 8.0417 | 9.1324 | +1.091 | <= 12 | PASS |
| amp_reset_host | ff85 | final_v_os100m | 1.6511 | 1.6511 | -2.67e-06 | 1.6 .. 1.7 | PASS |
| amp_reset_host | ss-40 | t_1mv_s_os10m | 2.8915 | 6.4677 | +3.576 | <= 9.75 | PASS |
| amp_reset_host | ss-40 | t_1mv_s_os100m | 6.5169 | 7.6454 | +1.129 | <= 12 | PASS |
| amp_reset_host | ss-40 | final_v_os100m | 1.6503 | 1.6503 | -4.191e-06 | 1.6 .. 1.7 | PASS |
| amp_reset_host | typ | t_1mv_s_os10m | 3.8841 | 7.6291 | +3.745 | <= 9.75 | PASS |
| amp_reset_host | typ | t_1mv_s_os100m | 8.0065 | 9.1439 | +1.137 | <= 12 | PASS |
| amp_reset_host | typ | final_v_os100m | 1.6507 | 1.6507 | -3.157e-06 | 1.6 .. 1.7 | PASS |

MISSING: amp_ac: AFE/layout/sim/recpad/pex_check_nodiodes/amp_ac.json does not exist (run AFE/layout/tb/tb_amp_ac.py --netlist <PEX> --corner all)
MISSING: amp_noise: AFE/layout/sim/recpad/pex_check_nodiodes/amp_noise.json does not exist (run AFE/layout/tb/tb_amp_noise.py --netlist <PEX> --corner all)
MISSING: amp_loop: AFE/layout/sim/recpad/pex_check_nodiodes/amp_loop.json does not exist (run AFE/layout/tb/tb_amp_loop.py --netlist <PEX> --corner all)
MISSING: amp_psrr: AFE/layout/sim/recpad/pex_check_nodiodes/amp_psrr.json does not exist (run AFE/layout/tb/tb_amp_psrr.py --netlist <PEX> --corner all)
MISSING: amp_thd: AFE/layout/sim/recpad/pex_check_nodiodes/amp_thd.json does not exist (run AFE/layout/tb/tb_amp_thd.py --netlist <PEX> --corner all)
MISSING: amp_ac_junction: AFE/layout/sim/recpad/pex_check_nodiodes/amp_ac_junction.json does not exist (run AFE/layout/tb/tb_amp_ac.py --netlist <PEX> --corner all --junction)
MISSING: amp_pwrup_junction: AFE/layout/sim/recpad/pex_check_nodiodes/amp_pwrup_junction.json does not exist (run AFE/layout/tb/tb_amp_pwrup.py --netlist <PEX> --corner all --junction)
MISSING: amp_reset_host_junction: AFE/layout/sim/recpad/pex_check_nodiodes/amp_reset_host_junction.json does not exist (run AFE/layout/tb/tb_amp_reset.py --netlist <PEX> --corner all --junction)
RESULT compare L2b: FAIL  (32 PASS, 0 WARN, 1 FAIL, 8 missing)

# compare.py L2b: AFE/layout/sim/recpad/pex_probe_ac against AFE/layout/baseline

| check | corner | value | baseline | post-layout | change | limit | result |
|---|---|---|---|---|---|---|---|
| amp_ac | ff85 | g_mid_db | 60.057 | 59.811 | -0.2466 | 59 .. 61 | PASS |
| amp_ac | ff85 | g_mid_db | 60.057 | 59.811 | -0.2466 | |change| <= 0.3 | PASS |
| amp_ac | ff85 | f_lo_hz | 0.28137 | 0.27639 | -0.004981 | <= 0.5 | PASS |
| amp_ac | ff85 | f_hi_hz | 997.67 | 973.98 | -23.69 | >= 300 | PASS |
| amp_ac | ff85 | idd_ua | 118.81 | 118.81 | +0 | x / baseline 0.95 .. 1.05 | PASS |
| amp_ac | ff85 | vout_v | 1.651 | 1.6509 | -2e-05 | 1.6 .. 1.7 | PASS |
| amp_ac | ff85 | hf_dev_db | - | 1.07 |  | <= 2 | PASS |
| amp_ac | ff85 | g_300_db | 59.685 | 59.419 | -0.266 |  |  |
| amp_ac | ff85 | g_0p5_db | 58.936 | 58.721 | -0.2144 |  |  |
| amp_ac | ff85 | g1_mid_db | 39.986 | 39.82 | -0.1657 |  |  |
| amp_ac | ss-40 | g_mid_db | 60.038 | 59.833 | -0.2047 | 59 .. 61 | PASS |
| amp_ac | ss-40 | g_mid_db | 60.038 | 59.833 | -0.2047 | |change| <= 0.3 | PASS |
| amp_ac | ss-40 | f_lo_hz | 0.2878 | 0.28342 | -0.004375 | <= 0.5 | PASS |
| amp_ac | ss-40 | f_hi_hz | 422.1 | 409.39 | -12.72 | >= 300 | PASS |
| amp_ac | ss-40 | idd_ua | 47.133 | 47.133 | +0 | x / baseline 0.95 .. 1.05 | PASS |
| amp_ac | ss-40 | vout_v | 1.6502 | 1.6502 | +0 | 1.6 .. 1.7 | PASS |
| amp_ac | ss-40 | hf_dev_db | - | 1.3146 |  | <= 2 | PASS |
| amp_ac | ss-40 | g_300_db | 58.271 | 57.976 | -0.2953 |  |  |
| amp_ac | ss-40 | g_0p5_db | 58.894 | 58.716 | -0.1777 |  |  |
| amp_ac | ss-40 | g1_mid_db | 39.988 | 39.848 | -0.1393 |  |  |
| amp_ac | typ | g_mid_db | 60.053 | 59.83 | -0.2235 | 59 .. 61 | PASS |
| amp_ac | typ | g_mid_db | 60.053 | 59.83 | -0.2235 | |change| <= 0.3 | PASS |
| amp_ac | typ | f_lo_hz | 0.24588 | 0.24193 | -0.003949 | <= 0.5 | PASS |
| amp_ac | typ | f_hi_hz | 653.5 | 635.57 | -17.93 | >= 300 | PASS |
| amp_ac | typ | idd_ua | 74.43 | 74.43 | +0 | x / baseline 0.95 .. 1.05 | PASS |
| amp_ac | typ | vout_v | 1.6506 | 1.6506 | -1e-05 | 1.6 .. 1.7 | PASS |
| amp_ac | typ | hf_dev_db | - | 1.069 |  | <= 2 | PASS |
| amp_ac | typ | g_300_db | 59.228 | 58.961 | -0.2668 |  |  |
| amp_ac | typ | g_0p5_db | 59.198 | 58.995 | -0.203 |  |  |
| amp_ac | typ | g1_mid_db | 39.988 | 39.837 | -0.1512 |  |  |
| amp_noise | ff85 | noise_d8_post_uv | - | 2.1556 |  | <= 2.2 | PASS |
| amp_noise | ff85 | noise_real_uv | 1.7323 | 1.7455 | +0.01327 |  |  |
| amp_noise | ss-40 | noise_d8_post_uv | - | 1.7436 |  | <= 2 | PASS |
| amp_noise | ss-40 | noise_real_uv | 1.3865 | 1.3957 | +0.009206 |  |  |
| amp_noise | typ | noise_d8_post_uv | - | 1.904 |  | <= 2 | PASS |
| amp_noise | typ | noise_real_uv | 1.4954 | 1.5061 | +0.01077 |  |  |
| amp_noise | typ | noise_real_fn1_uv | 4.8792 | 4.9156 | +0.03639 |  |  |
| amp_loop | ff85 | pm_deg | 76.935 | 436.62 | +359.7 | >= 60 | PASS |
| amp_loop | ff85 | fu_hz | 3.6302e+05 | 3.5714e+05 | -5884 |  |  |
| amp_loop | ff85 | t_100hz_db | 58.701 | 46.942 | -11.76 |  |  |
| amp_loop | ss-40 | pm_deg | 81.375 | 441.13 | +359.8 | >= 60 | PASS |
| amp_loop | ss-40 | fu_hz | 1.8948e+05 | 1.8709e+05 | -2391 |  |  |
| amp_loop | ss-40 | t_100hz_db | 58.529 | 48.598 | -9.931 |  |  |
| amp_loop | typ | pm_deg | 79.573 | 439.28 | +359.7 | >= 60 | PASS |
| amp_loop | typ | fu_hz | 2.5375e+05 | 2.5013e+05 | -3621 |  |  |
| amp_loop | typ | t_100hz_db | 58.878 | 48.392 | -10.49 |  |  |
| amp_psrr | ff85 | supply_gain_50hz | 0.57988 | 0.6662 | +0.08632 | 0.32 .. 0.68 | PASS |
| amp_psrr | ff85 | supply_gain_60hz | 0.57959 | 0.66577 | +0.08619 |  |  |
| amp_psrr | ff85 | supply_gain_300hz | 0.55796 | 0.63908 | +0.08112 |  |  |
| amp_psrr | ff85 | supply_gain_1khz | 0.42417 | 0.4781 | +0.05394 |  |  |
| amp_psrr | ss-40 | supply_gain_50hz | 0.56733 | 0.6189 | +0.05157 | 0.32 .. 0.68 | PASS |
| amp_psrr | ss-40 | supply_gain_60hz | 0.56574 | 0.61698 | +0.05124 |  |  |
| amp_psrr | ss-40 | supply_gain_300hz | 0.47326 | 0.50949 | +0.03623 |  |  |
| amp_psrr | ss-40 | supply_gain_1khz | 0.24466 | 0.25639 | +0.01173 |  |  |
| amp_psrr | typ | supply_gain_50hz | 0.57239 | 0.6374 | +0.06501 | 0.32 .. 0.68 | PASS |
| amp_psrr | typ | supply_gain_60hz | 0.57172 | 0.63654 | +0.06482 |  |  |
| amp_psrr | typ | supply_gain_300hz | 0.52594 | 0.58185 | +0.05591 |  |  |
| amp_psrr | typ | supply_gain_1khz | 0.33496 | 0.36169 | +0.02673 |  |  |
| amp_thd | ff85 | thd_pct | 2.4027 | 0.93126 | -1.471 | <= 4.5 | PASS |
| amp_thd | ff85 | out_max_v | 2.1895 | 2.2046 | +0.01511 | >= 2.13 | PASS |
| amp_thd | ff85 | out_min_v | 1.2203 | 1.2375 | +0.0172 | <= 1.25 | PASS |
| amp_thd | ff85 | gain_db | 59.908 | 59.742 | -0.1658 | 58.8 .. 61 | PASS |
| amp_thd | ff85 | hd2_dbc | -36.248 | -44.798 | -8.55 |  |  |
| amp_thd | ff85 | hd3_dbc | -37.909 | -46.377 | -8.468 |  |  |
| amp_thd | ss-40 | thd_pct | 0.056811 | 0.051814 | -0.004997 | <= 0.5 | PASS |
| amp_thd | ss-40 | out_max_v | 2.1494 | 2.1628 | +0.0134 | >= 2.13 | PASS |
| amp_thd | ss-40 | out_min_v | 1.145 | 1.179 | +0.03399 | <= 1.19 | PASS |
| amp_thd | ss-40 | gain_db | 60.034 | 59.812 | -0.2223 | 58.8 .. 61 | PASS |
| amp_thd | ss-40 | hd2_dbc | -90.366 | -73.898 | +16.47 |  |  |
| amp_thd | ss-40 | hd3_dbc | -64.995 | -66.475 | -1.48 |  |  |
| amp_thd | typ | thd_pct | 0.041988 | 0.039706 | -0.002282 | <= 0.5 | PASS |
| amp_thd | typ | out_max_v | 2.1511 | 2.1648 | +0.01376 | >= 2.13 | PASS |
| amp_thd | typ | out_min_v | 1.1449 | 1.1809 | +0.03595 | <= 1.19 | PASS |
| amp_thd | typ | gain_db | 60.049 | 59.81 | -0.2393 | 58.8 .. 61 | PASS |
| amp_thd | typ | hd2_dbc | -82.962 | -72.741 | +10.22 |  |  |
| amp_thd | typ | hd3_dbc | -67.746 | -69.865 | -2.119 |  |  |
| amp_pwrup | ff85 | err_1s_mv | 0.09506 | 891.71 | +891.6 | <= 50 | FAIL |
| amp_pwrup | ff85 | vout_before_v | 1.1413 | 1.1489 | +0.007626 |  |  |
| amp_pwrup | ss-40 | err_1s_mv | 0.61939 | 441.75 | +441.1 | <= 50 | FAIL |
| amp_pwrup | ss-40 | vout_before_v | 1.8006 | 1.0653 | -0.7353 |  |  |
| amp_pwrup | typ | err_1s_mv | 0.23517 | 1186.8 | +1187 | <= 50 | FAIL |
| amp_pwrup | typ | vout_before_v | 2.4605 | 2.5505 | +0.09006 |  |  |
| amp_reset | ff85 | t_fs_ms_os10m | 1.6282 | 1.6049 | -0.02327 | x / baseline 0.7 .. 1.4 | PASS |
| amp_reset | ff85 | t_1mv_s_os0 | 2.9885 | 5.5001 | +2.512 | <= 6.75 | PASS |
| amp_reset | ff85 | t_1mv_s_os1m | 2.3341 | 5.4995 | +3.165 | <= 6.75 | PASS |
| amp_reset | ff85 | t_1mv_s_os10m | 4.3769 | nan |  | no value | FAIL |
| amp_reset | ff85 | t_1mv_s_os100m | 5.4605 | 37.412 | +31.95 | <= 12 | FAIL |
| amp_reset | ff85 | final_v_os100m | 1.6511 | 1.6504 | -0.0007215 | 1.6 .. 1.7 | PASS |
| amp_reset | ff85 | final_v_os10m | 1.651 | 1.2864 | -0.3646 | 1.6 .. 1.7 | FAIL |
| amp_reset | ff85 | peak_mv_os100m | 169.46 | 917.19 | +747.7 |  |  |
| amp_reset | ff85 | rel_step_mv_os10m | 4.0326 | -355.98 | -360 |  |  |
| amp_reset | ff85 | drift_mv_s_os10m | -0.77377 | -324.81 | -324 |  |  |
| amp_reset | ss-40 | t_fs_ms_os10m | 5.7918 | 5.8286 | +0.03688 | x / baseline 0.7 .. 1.4 | PASS |
| amp_reset | ss-40 | t_1mv_s_os0 | 0.6545 | nan |  | no value | FAIL |
| amp_reset | ss-40 | t_1mv_s_os1m | 0.39849 | nan |  | no value | FAIL |
| amp_reset | ss-40 | t_1mv_s_os10m | 2.7357 | 10.396 | +7.66 | <= 9.75 | FAIL |
| amp_reset | ss-40 | t_1mv_s_os100m | 6.8473 | 11.533 | +4.685 | <= 12 | PASS |
| amp_reset | ss-40 | final_v_os100m | 1.6503 | 1.6503 | -1.964e-05 | 1.6 .. 1.7 | PASS |
| amp_reset | ss-40 | final_v_os10m | 1.6502 | 1.6495 | -0.0006764 | 1.6 .. 1.7 | PASS |
| amp_reset | ss-40 | peak_mv_os100m | 53.334 | 1090.5 | +1037 |  |  |
| amp_reset | ss-40 | rel_step_mv_os10m | 0.00206 | 0.00178 | -0.00028 |  |  |
| amp_reset | ss-40 | drift_mv_s_os10m | -0.32478 | -59.34 | -59.02 |  |  |
| amp_reset | typ | t_fs_ms_os10m | 3.0966 | 3.0228 | -0.07376 | x / baseline 0.7 .. 1.4 | PASS |
| amp_reset | typ | t_1mv_s_os0 | 1.7995 | nan |  | no value | FAIL |
| amp_reset | typ | t_1mv_s_os1m | 1.3957 | nan |  | no value | FAIL |
| amp_reset | typ | t_1mv_s_os10m | 3.8016 | 11.387 | +7.585 | <= 9.75 | FAIL |
| amp_reset | typ | t_1mv_s_os100m | 8.4225 | 19.929 | +11.51 | <= 12 | FAIL |
| amp_reset | typ | final_v_os100m | 1.6507 | 1.6507 | +1.139e-06 | 1.6 .. 1.7 | PASS |
| amp_reset | typ | final_v_os10m | 1.6507 | 1.6457 | -0.004926 | 1.6 .. 1.7 | PASS |
| amp_reset | typ | peak_mv_os100m | 57.939 | 1148.4 | +1090 |  |  |
| amp_reset | typ | rel_step_mv_os10m | -7.8744 | -388.38 | -380.5 |  |  |
| amp_reset | typ | drift_mv_s_os10m | -0.53498 | -305.56 | -305 |  |  |
| amp_reset_host | ff85 | t_1mv_s_os10m | 3.7084 | 11.06 | +7.351 | <= 9.75 | FAIL |
| amp_reset_host | ff85 | t_1mv_s_os100m | 8.0417 | nan |  | no value | FAIL |
| amp_reset_host | ff85 | final_v_os100m | 1.6511 | 1.2958 | -0.3553 | 1.6 .. 1.7 | FAIL |
| amp_reset_host | ss-40 | t_1mv_s_os10m | 2.8915 | 10.716 | +7.824 | <= 9.75 | FAIL |
| amp_reset_host | ss-40 | t_1mv_s_os100m | 6.5169 | 12.425 | +5.908 | <= 12 | FAIL |
| amp_reset_host | ss-40 | final_v_os100m | 1.6503 | 1.6503 | -4.142e-06 | 1.6 .. 1.7 | PASS |
| amp_reset_host | typ | t_1mv_s_os10m | 3.8841 | 10.483 | +6.599 | <= 9.75 | FAIL |
| amp_reset_host | typ | t_1mv_s_os100m | 8.0065 | nan |  | no value | FAIL |
| amp_reset_host | typ | final_v_os100m | 1.6507 | 0.81635 | -0.8344 | 1.6 .. 1.7 | FAIL |
| amp_ac_junction | ff85 | g_mid_db | 60.051 | 59.779 | -0.2722 | 59 .. 61 | PASS |
| amp_ac_junction | ff85 | f_hi_hz | 997.59 | 977.34 | -20.24 | >= 300 | PASS |
| amp_ac_junction | ff85 | vout_v | 1.6517 | 1.6511 | -0.00058 | 1.5 .. 1.8 | PASS |
| amp_ac_junction | ff85 | f_lo_hz | 0.070028 | 0.095228 | +0.0252 | <= 0.5 | PASS |
| amp_ac_junction | ss-40 | g_mid_db | 60.032 | 59.806 | -0.226 | 59 .. 61 | PASS |
| amp_ac_junction | ss-40 | f_hi_hz | 421.73 | 409.01 | -12.73 | >= 300 | PASS |
| amp_ac_junction | ss-40 | vout_v | 1.6367 | 1.6592 | +0.02248 | 1.5 .. 1.8 | PASS |
| amp_ac_junction | ss-40 | f_lo_hz | nan | nan |  | nan allowed | PASS |
| amp_ac_junction | typ | g_mid_db | 60.047 | 59.8 | -0.2471 | 59 .. 61 | PASS |
| amp_ac_junction | typ | f_hi_hz | 653.27 | 635.75 | -17.52 | >= 300 | PASS |
| amp_ac_junction | typ | vout_v | 1.6137 | 1.6644 | +0.05072 | 1.5 .. 1.8 | PASS |
| amp_ac_junction | typ | f_lo_hz | nan | nan |  | nan allowed | PASS |
| amp_pwrup_junction | ff85 | err_1s_mv | 0.94002 | 912.54 | +911.6 |  |  |
| amp_pwrup_junction | ss-40 | err_1s_mv | 1.749 | 793.2 | +791.5 |  |  |
| amp_pwrup_junction | typ | err_1s_mv | 1.0352 | 1203.3 | +1202 |  |  |
| amp_reset_host_junction | ff85 | drift_mv_s_os10m | 1.5242 | -253.6 | -255.1 | |x| <= 30 | WARN |
| amp_reset_host_junction | ff85 | final_v_os10m | 1.6683 | 1.1649 | -0.5034 |  |  |
| amp_reset_host_junction | ff85 | final_v_os100m | 1.8643 | 1.1586 | -0.7057 |  |  |
| amp_reset_host_junction | ff85 | t_1mv_s_os10m | 9.419 | 11.291 | +1.872 |  |  |
| amp_reset_host_junction | ss-40 | drift_mv_s_os10m | 8.6245 | 9.6848 | +1.06 | |x| <= 30 | PASS |
| amp_reset_host_junction | ss-40 | final_v_os10m | 1.7484 | 2.8964 | +1.148 |  |  |
| amp_reset_host_junction | ss-40 | final_v_os100m | 2.9317 | 2.932 | +0.0003094 |  |  |
| amp_reset_host_junction | ss-40 | t_1mv_s_os10m | nan | 10.232 |  |  |  |
| amp_reset_host_junction | typ | drift_mv_s_os10m | 9.5386 | -28.458 | -38 | |x| <= 30 | PASS |
| amp_reset_host_junction | typ | final_v_os10m | 1.7594 | 2.6511 | +0.8917 |  |  |
| amp_reset_host_junction | typ | final_v_os100m | 2.7385 | 2.7353 | -0.003191 |  |  |
| amp_reset_host_junction | typ | t_1mv_s_os10m | nan | nan |  |  |  |

RESULT compare L2b: FAIL  (68 PASS, 1 WARN, 21 FAIL, 0 missing)

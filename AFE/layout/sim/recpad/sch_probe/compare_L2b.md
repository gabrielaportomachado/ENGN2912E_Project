# compare.py L2b: AFE/layout/sim/recpad/sch_probe against AFE/layout/baseline

| check | corner | value | baseline | post-layout | change | limit | result |
|---|---|---|---|---|---|---|---|
| amp_ac | ff85 | g_mid_db | 60.057 | 60.047 | -0.009681 | 59 .. 61 | PASS |
| amp_ac | ff85 | g_mid_db | 60.057 | 60.047 | -0.009681 | |change| <= 0.3 | PASS |
| amp_ac | ff85 | f_lo_hz | 0.28137 | 0.28323 | +0.001861 | <= 0.5 | PASS |
| amp_ac | ff85 | f_hi_hz | 997.67 | 998.61 | +0.9441 | >= 300 | PASS |
| amp_ac | ff85 | idd_ua | 118.81 | 118.81 | +0 | x / baseline 0.95 .. 1.05 | PASS |
| amp_ac | ff85 | vout_v | 1.651 | 1.6509 | -2e-05 | 1.6 .. 1.7 | PASS |
| amp_ac | ff85 | hf_dev_db | - | 0.011719 |  | <= 2 | PASS |
| amp_ac | ff85 | g_300_db | 59.685 | 59.684 | -0.0004971 |  |  |
| amp_ac | ff85 | g_0p5_db | 58.936 | 58.907 | -0.02808 |  |  |
| amp_ac | ff85 | g1_mid_db | 39.986 | 39.976 | -0.009973 |  |  |
| amp_ac | ss-40 | g_mid_db | 60.038 | 60.028 | -0.009851 | 59 .. 61 | PASS |
| amp_ac | ss-40 | g_mid_db | 60.038 | 60.028 | -0.009851 | |change| <= 0.3 | PASS |
| amp_ac | ss-40 | f_lo_hz | 0.2878 | 0.28853 | +0.0007296 | <= 0.5 | PASS |
| amp_ac | ss-40 | f_hi_hz | 422.1 | 422.94 | +0.8352 | >= 300 | PASS |
| amp_ac | ss-40 | idd_ua | 47.133 | 47.133 | -0.0001 | x / baseline 0.95 .. 1.05 | PASS |
| amp_ac | ss-40 | vout_v | 1.6502 | 1.6502 | -1e-05 | 1.6 .. 1.7 | PASS |
| amp_ac | ss-40 | hf_dev_db | - | 0.012901 |  | <= 2 | PASS |
| amp_ac | ss-40 | g_300_db | 58.271 | 58.271 | -0.0006482 |  |  |
| amp_ac | ss-40 | g_0p5_db | 58.894 | 58.872 | -0.02183 |  |  |
| amp_ac | ss-40 | g1_mid_db | 39.988 | 39.978 | -0.009851 |  |  |
| amp_ac | typ | g_mid_db | 60.053 | 60.043 | -0.009855 | 59 .. 61 | PASS |
| amp_ac | typ | g_mid_db | 60.053 | 60.043 | -0.009855 | |change| <= 0.3 | PASS |
| amp_ac | typ | f_lo_hz | 0.24588 | 0.24663 | +0.0007502 | <= 0.5 | PASS |
| amp_ac | typ | f_hi_hz | 653.5 | 654.47 | +0.9665 | >= 300 | PASS |
| amp_ac | typ | idd_ua | 74.43 | 74.43 | -0.0001 | x / baseline 0.95 .. 1.05 | PASS |
| amp_ac | typ | vout_v | 1.6506 | 1.6506 | +1e-05 | 1.6 .. 1.7 | PASS |
| amp_ac | typ | hf_dev_db | - | 0.011591 |  | <= 2 | PASS |
| amp_ac | typ | g_300_db | 59.228 | 59.227 | -0.0006505 |  |  |
| amp_ac | typ | g_0p5_db | 59.198 | 59.177 | -0.02189 |  |  |
| amp_ac | typ | g1_mid_db | 39.988 | 39.978 | -0.009855 |  |  |
| amp_noise | ff85 | noise_d8_post_uv | - | 2.1419 |  | <= 2.2 | PASS |
| amp_noise | ff85 | noise_real_uv | 1.7323 | 1.7345 | +0.002214 |  |  |
| amp_noise | ss-40 | noise_d8_post_uv | - | 1.7341 |  | <= 2 | PASS |
| amp_noise | ss-40 | noise_real_uv | 1.3865 | 1.3881 | +0.001591 |  |  |
| amp_noise | typ | noise_d8_post_uv | - | 1.8925 |  | <= 2 | PASS |
| amp_noise | typ | noise_real_uv | 1.4954 | 1.4971 | +0.001688 |  |  |
| amp_noise | typ | noise_real_fn1_uv | 4.8792 | 4.8847 | +0.005518 |  |  |
| amp_loop | ff85 | pm_deg | 76.935 | 76.922 | -0.0127 | >= 60 | PASS |
| amp_loop | ff85 | fu_hz | 3.6302e+05 | 3.6329e+05 | +269 |  |  |
| amp_loop | ff85 | t_100hz_db | 58.701 | 58.7 | -0.0006 |  |  |
| amp_loop | ss-40 | pm_deg | 81.375 | 81.372 | -0.003 | >= 60 | PASS |
| amp_loop | ss-40 | fu_hz | 1.8948e+05 | 1.8953e+05 | +48 |  |  |
| amp_loop | ss-40 | t_100hz_db | 58.529 | 58.529 | -0.0003 |  |  |
| amp_loop | typ | pm_deg | 79.573 | 79.567 | -0.0058 | >= 60 | PASS |
| amp_loop | typ | fu_hz | 2.5375e+05 | 2.5385e+05 | +106 |  |  |
| amp_loop | typ | t_100hz_db | 58.878 | 58.877 | -0.0005 |  |  |
| amp_psrr | ff85 | supply_gain_50hz | 0.57988 | 0.5812 | +0.001324 | 0.32 .. 0.68 | PASS |
| amp_psrr | ff85 | supply_gain_60hz | 0.57959 | 0.58093 | +0.001341 |  |  |
| amp_psrr | ff85 | supply_gain_300hz | 0.55796 | 0.55924 | +0.001279 |  |  |
| amp_psrr | ff85 | supply_gain_1khz | 0.42417 | 0.42518 | +0.001011 |  |  |
| amp_psrr | ss-40 | supply_gain_50hz | 0.56733 | 0.5688 | +0.00147 | 0.32 .. 0.68 | PASS |
| amp_psrr | ss-40 | supply_gain_60hz | 0.56574 | 0.56722 | +0.001487 |  |  |
| amp_psrr | ss-40 | supply_gain_300hz | 0.47326 | 0.47453 | +0.001274 |  |  |
| amp_psrr | ss-40 | supply_gain_1khz | 0.24466 | 0.24538 | +0.00072 |  |  |
| amp_psrr | typ | supply_gain_50hz | 0.57239 | 0.57378 | +0.001393 | 0.32 .. 0.68 | PASS |
| amp_psrr | typ | supply_gain_60hz | 0.57172 | 0.57313 | +0.00141 |  |  |
| amp_psrr | typ | supply_gain_300hz | 0.52594 | 0.52723 | +0.001297 |  |  |
| amp_psrr | typ | supply_gain_1khz | 0.33496 | 0.33586 | +0.000899 |  |  |
| amp_thd | ff85 | thd_pct | 2.4027 | 2.3878 | -0.01496 | <= 4.5 | PASS |
| amp_thd | ff85 | out_max_v | 2.1895 | 2.1887 | -0.0007878 | >= 2.13 | PASS |
| amp_thd | ff85 | out_min_v | 1.2203 | 1.2204 | +0.0001057 | <= 1.25 | PASS |
| amp_thd | ff85 | gain_db | 59.908 | 59.899 | -0.00885 | 58.8 .. 61 | PASS |
| amp_thd | ff85 | hd2_dbc | -36.248 | -36.306 | -0.05796 |  |  |
| amp_thd | ff85 | hd3_dbc | -37.909 | -37.966 | -0.05714 |  |  |
| amp_thd | ss-40 | thd_pct | 0.056811 | 0.057163 | +0.0003521 | <= 0.5 | PASS |
| amp_thd | ss-40 | out_max_v | 2.1494 | 2.1466 | -0.002814 | >= 2.13 | PASS |
| amp_thd | ss-40 | out_min_v | 1.145 | 1.1435 | -0.001459 | <= 1.19 | PASS |
| amp_thd | ss-40 | gain_db | 60.034 | 60.024 | -0.009851 | 58.8 .. 61 | PASS |
| amp_thd | ss-40 | hd2_dbc | -90.366 | -82.453 | +7.913 |  |  |
| amp_thd | ss-40 | hd3_dbc | -64.995 | -65.006 | -0.01125 |  |  |
| amp_thd | typ | thd_pct | 0.041988 | 0.042233 | +0.000245 | <= 0.5 | PASS |
| amp_thd | typ | out_max_v | 2.1511 | 2.1486 | -0.002491 | >= 2.13 | PASS |
| amp_thd | typ | out_min_v | 1.1449 | 1.1437 | -0.001168 | <= 1.19 | PASS |
| amp_thd | typ | gain_db | 60.049 | 60.04 | -0.009856 | 58.8 .. 61 | PASS |
| amp_thd | typ | hd2_dbc | -82.962 | -81.339 | +1.623 |  |  |
| amp_thd | typ | hd3_dbc | -67.746 | -67.753 | -0.006622 |  |  |
| amp_pwrup | ff85 | err_1s_mv | 0.09506 | 2.5398 | +2.445 | <= 50 | PASS |
| amp_pwrup | ff85 | vout_before_v | 1.1413 | 1.1414 | +0.0001398 |  |  |
| amp_pwrup | ss-40 | err_1s_mv | 0.61939 | 2.7749 | +2.156 | <= 50 | PASS |
| amp_pwrup | ss-40 | vout_before_v | 1.8006 | 0.39923 | -1.401 |  |  |
| amp_pwrup | typ | err_1s_mv | 0.23517 | 2.9564 | +2.721 | <= 50 | PASS |
| amp_pwrup | typ | vout_before_v | 2.4605 | 2.6934 | +0.2329 |  |  |
| amp_reset | ff85 | t_fs_ms_os10m | 1.6282 | 1.6996 | +0.07142 | x / baseline 0.7 .. 1.4 | PASS |
| amp_reset | ff85 | t_1mv_s_os0 | 2.9885 | 5.6516 | +2.663 | <= 6.75 | PASS |
| amp_reset | ff85 | t_1mv_s_os1m | 2.3341 | 5.5822 | +3.248 | <= 6.75 | PASS |
| amp_reset | ff85 | t_1mv_s_os10m | 4.3769 | 9.4335 | +5.057 | <= 9.75 | PASS |
| amp_reset | ff85 | t_1mv_s_os100m | 5.4605 | 10.438 | +4.977 | <= 12 | PASS |
| amp_reset | ff85 | final_v_os100m | 1.6511 | 1.6511 | -4.451e-05 | 1.6 .. 1.7 | PASS |
| amp_reset | ff85 | final_v_os10m | 1.651 | 1.6513 | +0.0003059 | 1.6 .. 1.7 | PASS |
| amp_reset | ff85 | peak_mv_os100m | 169.46 | 500.8 | +331.3 |  |  |
| amp_reset | ff85 | rel_step_mv_os10m | 4.0326 | 421.83 | +417.8 |  |  |
| amp_reset | ff85 | drift_mv_s_os10m | -0.77377 | -12.479 | -11.71 |  |  |
| amp_reset | ss-40 | t_fs_ms_os10m | 5.7918 | 5.8201 | +0.02837 | x / baseline 0.7 .. 1.4 | PASS |
| amp_reset | ss-40 | t_1mv_s_os0 | 0.6545 | nan |  | no value | FAIL |
| amp_reset | ss-40 | t_1mv_s_os1m | 0.39849 | nan |  | no value | FAIL |
| amp_reset | ss-40 | t_1mv_s_os10m | 2.7357 | nan |  | no value | FAIL |
| amp_reset | ss-40 | t_1mv_s_os100m | 6.8473 | 20.78 | +13.93 | <= 12 | FAIL |
| amp_reset | ss-40 | final_v_os100m | 1.6503 | 1.6503 | -2.556e-05 | 1.6 .. 1.7 | PASS |
| amp_reset | ss-40 | final_v_os10m | 1.6502 | 1.7933 | +0.1431 | 1.6 .. 1.7 | FAIL |
| amp_reset | ss-40 | peak_mv_os100m | 53.334 | 1250.9 | +1198 |  |  |
| amp_reset | ss-40 | rel_step_mv_os10m | 0.00206 | 0.10409 | +0.102 |  |  |
| amp_reset | ss-40 | drift_mv_s_os10m | -0.32478 | 3.9114 | +4.236 |  |  |
| amp_reset | typ | t_fs_ms_os10m | 3.0966 | 2.9438 | -0.1528 | x / baseline 0.7 .. 1.4 | PASS |
| amp_reset | typ | t_1mv_s_os0 | 1.7995 | nan |  | no value | FAIL |
| amp_reset | typ | t_1mv_s_os1m | 1.3957 | nan |  | no value | FAIL |
| amp_reset | typ | t_1mv_s_os10m | 3.8016 | nan |  | no value | FAIL |
| amp_reset | typ | t_1mv_s_os100m | 8.4225 | 16.929 | +8.507 | <= 12 | FAIL |
| amp_reset | typ | final_v_os100m | 1.6507 | 1.6507 | -7.646e-06 | 1.6 .. 1.7 | PASS |
| amp_reset | typ | final_v_os10m | 1.6507 | 1.6601 | +0.009453 | 1.6 .. 1.7 | PASS |
| amp_reset | typ | peak_mv_os100m | 57.939 | 871.26 | +813.3 |  |  |
| amp_reset | typ | rel_step_mv_os10m | -7.8744 | -854.5 | -846.6 |  |  |
| amp_reset | typ | drift_mv_s_os10m | -0.53498 | 290.26 | +290.8 |  |  |
| amp_reset_host | ff85 | t_1mv_s_os10m | 3.7084 | 1.0699 | -2.638 | <= 9.75 | PASS |
| amp_reset_host | ff85 | t_1mv_s_os100m | 8.0417 | 7.9363 | -0.1054 | <= 12 | PASS |
| amp_reset_host | ff85 | final_v_os100m | 1.6511 | 1.6511 | -1.249e-05 | 1.6 .. 1.7 | PASS |
| amp_reset_host | ss-40 | t_1mv_s_os10m | 2.8915 | 1.1527 | -1.739 | <= 9.75 | PASS |
| amp_reset_host | ss-40 | t_1mv_s_os100m | 6.5169 | 6.4223 | -0.0946 | <= 12 | PASS |
| amp_reset_host | ss-40 | final_v_os100m | 1.6503 | 1.6503 | -9.34e-06 | 1.6 .. 1.7 | PASS |
| amp_reset_host | typ | t_1mv_s_os10m | 3.8841 | 1.1966 | -2.688 | <= 9.75 | PASS |
| amp_reset_host | typ | t_1mv_s_os100m | 8.0065 | 7.9047 | -0.1018 | <= 12 | PASS |
| amp_reset_host | typ | final_v_os100m | 1.6507 | 1.6507 | -1.147e-05 | 1.6 .. 1.7 | PASS |
| amp_ac_junction | ff85 | g_mid_db | 60.051 | 60.041 | -0.009958 | 59 .. 61 | PASS |
| amp_ac_junction | ff85 | f_hi_hz | 997.59 | 998.9 | +1.317 | >= 300 | PASS |
| amp_ac_junction | ff85 | vout_v | 1.6517 | 1.6511 | -0.00064 | 1.5 .. 1.8 | PASS |
| amp_ac_junction | ff85 | f_lo_hz | 0.070028 | 0.073738 | +0.00371 | <= 0.5 | PASS |
| amp_ac_junction | ss-40 | g_mid_db | 60.032 | -3.8859 | -63.92 | 59 .. 61 | FAIL |
| amp_ac_junction | ss-40 | f_hi_hz | 421.73 | 2.3466e+05 | +2.342e+05 | >= 300 | PASS |
| amp_ac_junction | ss-40 | vout_v | 1.6367 | 0.39967 | -1.237 | 1.5 .. 1.8 | FAIL |
| amp_ac_junction | ss-40 | f_lo_hz | nan | 10753 |  | <= 0.5 | FAIL |
| amp_ac_junction | typ | g_mid_db | 60.047 | 26.595 | -33.45 | 59 .. 61 | FAIL |
| amp_ac_junction | typ | f_hi_hz | 653.27 | 11031 | +1.038e+04 | >= 300 | PASS |
| amp_ac_junction | typ | vout_v | 1.6137 | 0.79702 | -0.8167 | 1.5 .. 1.8 | FAIL |
| amp_ac_junction | typ | f_lo_hz | nan | 0.0027268 |  | <= 0.5 | PASS |
| amp_pwrup_junction | ff85 | err_1s_mv | 0.94002 | 6.7197 | +5.78 |  |  |
| amp_pwrup_junction | ss-40 | err_1s_mv | 1.749 | 8.137 | +6.388 |  |  |
| amp_pwrup_junction | typ | err_1s_mv | 1.0352 | 8.0889 | +7.054 |  |  |
| amp_reset_host_junction | ff85 | drift_mv_s_os10m | 1.5242 | 0.9502 | -0.574 | |x| <= 30 | PASS |
| amp_reset_host_junction | ff85 | final_v_os10m | 1.6683 | 1.6506 | -0.0177 |  |  |
| amp_reset_host_junction | ff85 | final_v_os100m | 1.8643 | 1.8283 | -0.03602 |  |  |
| amp_reset_host_junction | ff85 | t_1mv_s_os10m | 9.419 | 5.7356 | -3.683 |  |  |
| amp_reset_host_junction | ss-40 | drift_mv_s_os10m | 8.6245 | -1.635 | -10.26 | |x| <= 30 | PASS |
| amp_reset_host_junction | ss-40 | final_v_os10m | 1.7484 | 1.6367 | -0.1117 |  |  |
| amp_reset_host_junction | ss-40 | final_v_os100m | 2.9317 | 2.9309 | -0.0008447 |  |  |
| amp_reset_host_junction | ss-40 | t_1mv_s_os10m | nan | 11.067 |  |  |  |
| amp_reset_host_junction | typ | drift_mv_s_os10m | 9.5386 | -0.51941 | -10.06 | |x| <= 30 | PASS |
| amp_reset_host_junction | typ | final_v_os10m | 1.7594 | 1.6329 | -0.1264 |  |  |
| amp_reset_host_junction | typ | final_v_os100m | 2.7385 | 2.7341 | -0.004443 |  |  |
| amp_reset_host_junction | typ | t_1mv_s_os10m | nan | 9.7594 |  |  |  |

RESULT compare L2b: FAIL  (76 PASS, 0 WARN, 14 FAIL, 0 missing)

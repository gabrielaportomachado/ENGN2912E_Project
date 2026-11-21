# compare.py L2b: AFE/layout/sim/recpad/pex_probe against AFE/layout/baseline

| check | corner | value | baseline | post-layout | change | limit | result |
|---|---|---|---|---|---|---|---|
| amp_ac | ff85 | g_mid_db | 60.057 | 59.81 | -0.2469 | 59 .. 61 | PASS |
| amp_ac | ff85 | g_mid_db | 60.057 | 59.81 | -0.2469 | |change| <= 0.3 | PASS |
| amp_ac | ff85 | f_lo_hz | 0.28137 | 0.27733 | -0.004044 | <= 0.5 | PASS |
| amp_ac | ff85 | f_hi_hz | 997.67 | 974.06 | -23.61 | >= 300 | PASS |
| amp_ac | ff85 | idd_ua | 118.81 | 118.81 | +0 | x / baseline 0.95 .. 1.05 | PASS |
| amp_ac | ff85 | vout_v | 1.651 | 1.651 | -1e-05 | 1.6 .. 1.7 | PASS |
| amp_ac | ff85 | hf_dev_db | - | 1.0696 |  | <= 2 | PASS |
| amp_ac | ff85 | g_300_db | 59.685 | 59.419 | -0.266 |  |  |
| amp_ac | ff85 | g_0p5_db | 58.936 | 58.714 | -0.2215 |  |  |
| amp_ac | ff85 | g1_mid_db | 39.986 | 39.82 | -0.1657 |  |  |
| amp_ac | ss-40 | g_mid_db | 60.038 | 59.834 | -0.2046 | 59 .. 61 | PASS |
| amp_ac | ss-40 | g_mid_db | 60.038 | 59.834 | -0.2046 | |change| <= 0.3 | PASS |
| amp_ac | ss-40 | f_lo_hz | 0.2878 | 0.2837 | -0.004099 | <= 0.5 | PASS |
| amp_ac | ss-40 | f_hi_hz | 422.1 | 409.39 | -12.72 | >= 300 | PASS |
| amp_ac | ss-40 | idd_ua | 47.133 | 47.133 | -0.0001 | x / baseline 0.95 .. 1.05 | PASS |
| amp_ac | ss-40 | vout_v | 1.6502 | 1.6502 | -1e-05 | 1.6 .. 1.7 | PASS |
| amp_ac | ss-40 | hf_dev_db | - | 1.3146 |  | <= 2 | PASS |
| amp_ac | ss-40 | g_300_db | 58.271 | 57.976 | -0.2952 |  |  |
| amp_ac | ss-40 | g_0p5_db | 58.894 | 58.715 | -0.1793 |  |  |
| amp_ac | ss-40 | g1_mid_db | 39.988 | 39.849 | -0.1392 |  |  |
| amp_ac | typ | g_mid_db | 60.053 | 59.829 | -0.2237 | 59 .. 61 | PASS |
| amp_ac | typ | g_mid_db | 60.053 | 59.829 | -0.2237 | |change| <= 0.3 | PASS |
| amp_ac | typ | f_lo_hz | 0.24588 | 0.24206 | -0.003824 | <= 0.5 | PASS |
| amp_ac | typ | f_hi_hz | 653.5 | 635.6 | -17.9 | >= 300 | PASS |
| amp_ac | typ | idd_ua | 74.43 | 74.43 | -0.0001 | x / baseline 0.95 .. 1.05 | PASS |
| amp_ac | typ | vout_v | 1.6506 | 1.6506 | -1e-05 | 1.6 .. 1.7 | PASS |
| amp_ac | typ | hf_dev_db | - | 1.0688 |  | <= 2 | PASS |
| amp_ac | typ | g_300_db | 59.228 | 58.961 | -0.2668 |  |  |
| amp_ac | typ | g_0p5_db | 59.198 | 58.994 | -0.204 |  |  |
| amp_ac | typ | g1_mid_db | 39.988 | 39.837 | -0.1511 |  |  |
| amp_noise | ff85 | noise_d8_post_uv | - | 2.156 |  | <= 2.2 | PASS |
| amp_noise | ff85 | noise_real_uv | 1.7323 | 1.7459 | +0.01359 |  |  |
| amp_noise | ss-40 | noise_d8_post_uv | - | 1.7436 |  | <= 2 | PASS |
| amp_noise | ss-40 | noise_real_uv | 1.3865 | 1.3957 | +0.00919 |  |  |
| amp_noise | typ | noise_d8_post_uv | - | 1.904 |  | <= 2 | PASS |
| amp_noise | typ | noise_real_uv | 1.4954 | 1.5061 | +0.01077 |  |  |
| amp_noise | typ | noise_real_fn1_uv | 4.8792 | 4.9156 | +0.03637 |  |  |
| amp_loop | ff85 | pm_deg | 76.935 | 436.62 | +359.7 | >= 60 | PASS |
| amp_loop | ff85 | fu_hz | 3.6302e+05 | 3.5713e+05 | -5886 |  |  |
| amp_loop | ff85 | t_100hz_db | 58.701 | 46.942 | -11.76 |  |  |
| amp_loop | ss-40 | pm_deg | 81.375 | 441.13 | +359.8 | >= 60 | PASS |
| amp_loop | ss-40 | fu_hz | 1.8948e+05 | 1.8709e+05 | -2392 |  |  |
| amp_loop | ss-40 | t_100hz_db | 58.529 | 48.598 | -9.931 |  |  |
| amp_loop | typ | pm_deg | 79.573 | 439.3 | +359.7 | >= 60 | PASS |
| amp_loop | typ | fu_hz | 2.5375e+05 | 2.5013e+05 | -3616 |  |  |
| amp_loop | typ | t_100hz_db | 58.878 | 48.167 | -10.71 |  |  |
| amp_psrr | ff85 | supply_gain_50hz | 0.57988 | 0.66602 | +0.08614 | 0.32 .. 0.68 | PASS |
| amp_psrr | ff85 | supply_gain_60hz | 0.57959 | 0.66553 | +0.08595 |  |  |
| amp_psrr | ff85 | supply_gain_300hz | 0.55796 | 0.63862 | +0.08066 |  |  |
| amp_psrr | ff85 | supply_gain_1khz | 0.42417 | 0.47775 | +0.05359 |  |  |
| amp_psrr | ss-40 | supply_gain_50hz | 0.56733 | 0.61885 | +0.05152 | 0.32 .. 0.68 | PASS |
| amp_psrr | ss-40 | supply_gain_60hz | 0.56574 | 0.61687 | +0.05113 |  |  |
| amp_psrr | ss-40 | supply_gain_300hz | 0.47326 | 0.50919 | +0.03593 |  |  |
| amp_psrr | ss-40 | supply_gain_1khz | 0.24466 | 0.25625 | +0.01159 |  |  |
| amp_psrr | typ | supply_gain_50hz | 0.57239 | 0.63724 | +0.06485 | 0.32 .. 0.68 | PASS |
| amp_psrr | typ | supply_gain_60hz | 0.57172 | 0.63632 | +0.0646 |  |  |
| amp_psrr | typ | supply_gain_300hz | 0.52594 | 0.58145 | +0.05551 |  |  |
| amp_psrr | typ | supply_gain_1khz | 0.33496 | 0.36145 | +0.02649 |  |  |
| amp_thd | ff85 | thd_pct | 2.4027 | 0.93192 | -1.471 | <= 4.5 | PASS |
| amp_thd | ff85 | out_max_v | 2.1895 | 2.2046 | +0.01511 | >= 2.13 | PASS |
| amp_thd | ff85 | out_min_v | 1.2203 | 1.2375 | +0.0172 | <= 1.25 | PASS |
| amp_thd | ff85 | gain_db | 59.908 | 59.742 | -0.1656 | 58.8 .. 61 | PASS |
| amp_thd | ff85 | hd2_dbc | -36.248 | -44.788 | -8.54 |  |  |
| amp_thd | ff85 | hd3_dbc | -37.909 | -46.374 | -8.465 |  |  |
| amp_thd | ss-40 | thd_pct | 0.056811 | 0.051202 | -0.005609 | <= 0.5 | PASS |
| amp_thd | ss-40 | out_max_v | 2.1494 | 2.1607 | +0.01128 | >= 2.13 | PASS |
| amp_thd | ss-40 | out_min_v | 1.145 | 1.177 | +0.03207 | <= 1.19 | PASS |
| amp_thd | ss-40 | gain_db | 60.034 | 59.812 | -0.2223 | 58.8 .. 61 | PASS |
| amp_thd | ss-40 | hd2_dbc | -90.366 | -74.612 | +15.75 |  |  |
| amp_thd | ss-40 | hd3_dbc | -64.995 | -66.475 | -1.481 |  |  |
| amp_thd | typ | thd_pct | 0.041988 | 0.039217 | -0.002771 | <= 0.5 | PASS |
| amp_thd | typ | out_max_v | 2.1511 | 2.1632 | +0.01214 | >= 2.13 | PASS |
| amp_thd | typ | out_min_v | 1.1449 | 1.1794 | +0.03447 | <= 1.19 | PASS |
| amp_thd | typ | gain_db | 60.049 | 59.81 | -0.2393 | 58.8 .. 61 | PASS |
| amp_thd | typ | hd2_dbc | -82.962 | -73.084 | +9.879 |  |  |
| amp_thd | typ | hd3_dbc | -67.746 | -69.856 | -2.11 |  |  |
| amp_pwrup | ff85 | err_1s_mv | 0.09506 | 21.582 | +21.49 | <= 50 | PASS |
| amp_pwrup | ff85 | vout_before_v | 1.1413 | 1.1492 | +0.007873 |  |  |
| amp_pwrup | ss-40 | err_1s_mv | 0.61939 | 26.319 | +25.7 | <= 50 | PASS |
| amp_pwrup | ss-40 | vout_before_v | 1.8006 | 0.40144 | -1.399 |  |  |
| amp_pwrup | typ | err_1s_mv | 0.23517 | 33.893 | +33.66 | <= 50 | PASS |
| amp_pwrup | typ | vout_before_v | 2.4605 | 2.74 | +0.2795 |  |  |
| amp_reset | ff85 | t_fs_ms_os10m | 1.6282 | 1.7396 | +0.1114 | x / baseline 0.7 .. 1.4 | PASS |
| amp_reset | ff85 | t_1mv_s_os0 | 2.9885 | 5.3286 | +2.34 | <= 6.75 | PASS |
| amp_reset | ff85 | t_1mv_s_os1m | 2.3341 | nan |  | no value | FAIL |
| amp_reset | ff85 | t_1mv_s_os10m | 4.3769 | 9.0006 | +4.624 | <= 9.75 | PASS |
| amp_reset | ff85 | t_1mv_s_os100m | 5.4605 | 10.952 | +5.491 | <= 12 | PASS |
| amp_reset | ff85 | final_v_os100m | 1.6511 | 1.6511 | -4.828e-05 | 1.6 .. 1.7 | PASS |
| amp_reset | ff85 | final_v_os10m | 1.651 | 1.6512 | +0.0002265 | 1.6 .. 1.7 | PASS |
| amp_reset | ff85 | peak_mv_os100m | 169.46 | 495.72 | +326.3 |  |  |
| amp_reset | ff85 | rel_step_mv_os10m | 4.0326 | 224.57 | +220.5 |  |  |
| amp_reset | ff85 | drift_mv_s_os10m | -0.77377 | -7.3998 | -6.626 |  |  |
| amp_reset | ss-40 | t_fs_ms_os10m | 5.7918 | 6.0077 | +0.216 | x / baseline 0.7 .. 1.4 | PASS |
| amp_reset | ss-40 | t_1mv_s_os0 | 0.6545 | nan |  | no value | FAIL |
| amp_reset | ss-40 | t_1mv_s_os1m | 0.39849 | nan |  | no value | FAIL |
| amp_reset | ss-40 | t_1mv_s_os10m | 2.7357 | nan |  | no value | FAIL |
| amp_reset | ss-40 | t_1mv_s_os100m | 6.8473 | 22.017 | +15.17 | <= 12 | FAIL |
| amp_reset | ss-40 | final_v_os100m | 1.6503 | 1.6503 | -2.815e-05 | 1.6 .. 1.7 | PASS |
| amp_reset | ss-40 | final_v_os10m | 1.6502 | 1.8233 | +0.1731 | 1.6 .. 1.7 | FAIL |
| amp_reset | ss-40 | peak_mv_os100m | 53.334 | 1248.8 | +1196 |  |  |
| amp_reset | ss-40 | rel_step_mv_os10m | 0.00206 | -33.119 | -33.12 |  |  |
| amp_reset | ss-40 | drift_mv_s_os10m | -0.32478 | 2.9491 | +3.274 |  |  |
| amp_reset | typ | t_fs_ms_os10m | 3.0966 | 2.9734 | -0.1231 | x / baseline 0.7 .. 1.4 | PASS |
| amp_reset | typ | t_1mv_s_os0 | 1.7995 | nan |  | no value | FAIL |
| amp_reset | typ | t_1mv_s_os1m | 1.3957 | nan |  | no value | FAIL |
| amp_reset | typ | t_1mv_s_os10m | 3.8016 | nan |  | no value | FAIL |
| amp_reset | typ | t_1mv_s_os100m | 8.4225 | 16.989 | +8.567 | <= 12 | FAIL |
| amp_reset | typ | final_v_os100m | 1.6507 | 1.6507 | -1.135e-05 | 1.6 .. 1.7 | PASS |
| amp_reset | typ | final_v_os10m | 1.6507 | 1.6934 | +0.04276 | 1.6 .. 1.7 | PASS |
| amp_reset | typ | peak_mv_os100m | 57.939 | 867.83 | +809.9 |  |  |
| amp_reset | typ | rel_step_mv_os10m | -7.8744 | 825.99 | +833.9 |  |  |
| amp_reset | typ | drift_mv_s_os10m | -0.53498 | 333.73 | +334.3 |  |  |
| amp_reset_host | ff85 | t_1mv_s_os10m | 3.7084 | 7.2485 | +3.54 | <= 9.75 | PASS |
| amp_reset_host | ff85 | t_1mv_s_os100m | 8.0417 | 9.024 | +0.9823 | <= 12 | PASS |
| amp_reset_host | ff85 | final_v_os100m | 1.6511 | 1.6511 | -1.529e-05 | 1.6 .. 1.7 | PASS |
| amp_reset_host | ss-40 | t_1mv_s_os10m | 2.8915 | 6.4184 | +3.527 | <= 9.75 | PASS |
| amp_reset_host | ss-40 | t_1mv_s_os100m | 6.5169 | 7.0729 | +0.556 | <= 12 | PASS |
| amp_reset_host | ss-40 | final_v_os100m | 1.6503 | 1.6503 | -1.275e-05 | 1.6 .. 1.7 | PASS |
| amp_reset_host | typ | t_1mv_s_os10m | 3.8841 | 7.5042 | +3.62 | <= 9.75 | PASS |
| amp_reset_host | typ | t_1mv_s_os100m | 8.0065 | 9.0396 | +1.033 | <= 12 | PASS |
| amp_reset_host | typ | final_v_os100m | 1.6507 | 1.6507 | -1.547e-05 | 1.6 .. 1.7 | PASS |
| amp_ac_junction | ff85 | g_mid_db | 60.051 | 59.779 | -0.2718 | 59 .. 61 | PASS |
| amp_ac_junction | ff85 | f_hi_hz | 997.59 | 977.29 | -20.29 | >= 300 | PASS |
| amp_ac_junction | ff85 | vout_v | 1.6517 | 1.651 | -0.00073 | 1.5 .. 1.8 | PASS |
| amp_ac_junction | ff85 | f_lo_hz | 0.070028 | 0.097888 | +0.02786 | <= 0.5 | PASS |
| amp_ac_junction | ss-40 | g_mid_db | 60.032 | -1.9112 | -61.94 | 59 .. 61 | FAIL |
| amp_ac_junction | ss-40 | f_hi_hz | 421.73 | 2.2208e+05 | +2.217e+05 | >= 300 | PASS |
| amp_ac_junction | ss-40 | vout_v | 1.6367 | 0.402 | -1.235 | 1.5 .. 1.8 | FAIL |
| amp_ac_junction | ss-40 | f_lo_hz | nan | 10219 |  | <= 0.5 | FAIL |
| amp_ac_junction | typ | g_mid_db | 60.047 | 28.967 | -31.08 | 59 .. 61 | FAIL |
| amp_ac_junction | typ | f_hi_hz | 653.27 | 9393.2 | +8740 | >= 300 | PASS |
| amp_ac_junction | typ | vout_v | 1.6137 | 0.80447 | -0.8092 | 1.5 .. 1.8 | FAIL |
| amp_ac_junction | typ | f_lo_hz | nan | 0.0025958 |  | <= 0.5 | PASS |
| amp_pwrup_junction | ff85 | err_1s_mv | 0.94002 | 101.92 | +101 |  |  |
| amp_pwrup_junction | ss-40 | err_1s_mv | 1.749 | 185.45 | +183.7 |  |  |
| amp_pwrup_junction | typ | err_1s_mv | 1.0352 | 188.45 | +187.4 |  |  |
| amp_reset_host_junction | ff85 | drift_mv_s_os10m | 1.5242 | 11.819 | +10.3 | |x| <= 30 | PASS |
| amp_reset_host_junction | ff85 | final_v_os10m | 1.6683 | 1.656 | -0.01234 |  |  |
| amp_reset_host_junction | ff85 | final_v_os100m | 1.8643 | 1.661 | -0.2033 |  |  |
| amp_reset_host_junction | ff85 | t_1mv_s_os10m | 9.419 | 6.3679 | -3.051 |  |  |
| amp_reset_host_junction | ss-40 | drift_mv_s_os10m | 8.6245 | -1.3441 | -9.969 | |x| <= 30 | PASS |
| amp_reset_host_junction | ss-40 | final_v_os10m | 1.7484 | 1.445 | -0.3034 |  |  |
| amp_reset_host_junction | ss-40 | final_v_os100m | 2.9317 | 2.9298 | -0.001866 |  |  |
| amp_reset_host_junction | ss-40 | t_1mv_s_os10m | nan | 10.938 |  |  |  |
| amp_reset_host_junction | typ | drift_mv_s_os10m | 9.5386 | -0.021476 | -9.56 | |x| <= 30 | PASS |
| amp_reset_host_junction | typ | final_v_os10m | 1.7594 | 1.4592 | -0.3002 |  |  |
| amp_reset_host_junction | typ | final_v_os100m | 2.7385 | 2.7332 | -0.005347 |  |  |
| amp_reset_host_junction | typ | t_1mv_s_os10m | nan | 0.20687 |  |  |  |

RESULT compare L2b: FAIL  (75 PASS, 0 WARN, 15 FAIL, 0 missing)

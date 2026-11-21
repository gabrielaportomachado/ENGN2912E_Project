# compare.py L2b: AFE/layout/sim/recpad/pex_probe_1G against AFE/layout/baseline

| check | corner | value | baseline | post-layout | change | limit | result |
|---|---|---|---|---|---|---|---|
| amp_ac | ff85 | g_mid_db | 60.057 | 59.82 | -0.2371 | 59 .. 61 | PASS |
| amp_ac | ff85 | g_mid_db | 60.057 | 59.82 | -0.2371 | |change| <= 0.3 | PASS |
| amp_ac | ff85 | f_lo_hz | 0.28137 | 0.2757 | -0.00567 | <= 0.5 | PASS |
| amp_ac | ff85 | f_hi_hz | 997.67 | 972.51 | -25.17 | >= 300 | PASS |
| amp_ac | ff85 | idd_ua | 118.81 | 118.81 | +0 | x / baseline 0.95 .. 1.05 | PASS |
| amp_ac | ff85 | vout_v | 1.651 | 1.651 | -1e-05 | 1.6 .. 1.7 | PASS |
| amp_ac | ff85 | hf_dev_db | - | 1.079 |  | <= 2 | PASS |
| amp_ac | ff85 | g_300_db | 59.685 | 59.419 | -0.2656 |  |  |
| amp_ac | ff85 | g_0p5_db | 58.936 | 58.742 | -0.1939 |  |  |
| amp_ac | ff85 | g1_mid_db | 39.986 | 39.83 | -0.1559 |  |  |
| amp_ac | ss-40 | g_mid_db | 60.038 | 59.843 | -0.1949 | 59 .. 61 | PASS |
| amp_ac | ss-40 | g_mid_db | 60.038 | 59.843 | -0.1949 | |change| <= 0.3 | PASS |
| amp_ac | ss-40 | f_lo_hz | 0.2878 | 0.28301 | -0.004786 | <= 0.5 | PASS |
| amp_ac | ss-40 | f_hi_hz | 422.1 | 408.64 | -13.47 | >= 300 | PASS |
| amp_ac | ss-40 | idd_ua | 47.133 | 47.133 | +0 | x / baseline 0.95 .. 1.05 | PASS |
| amp_ac | ss-40 | vout_v | 1.6502 | 1.6502 | +2e-05 | 1.6 .. 1.7 | PASS |
| amp_ac | ss-40 | hf_dev_db | - | 1.3215 |  | <= 2 | PASS |
| amp_ac | ss-40 | g_300_db | 58.271 | 57.977 | -0.2939 |  |  |
| amp_ac | ss-40 | g_0p5_db | 58.894 | 58.736 | -0.1576 |  |  |
| amp_ac | ss-40 | g1_mid_db | 39.988 | 39.858 | -0.1295 |  |  |
| amp_ac | typ | g_mid_db | 60.053 | 59.839 | -0.214 | 59 .. 61 | PASS |
| amp_ac | typ | g_mid_db | 60.053 | 59.839 | -0.214 | |change| <= 0.3 | PASS |
| amp_ac | typ | f_lo_hz | 0.24588 | 0.2414 | -0.004483 | <= 0.5 | PASS |
| amp_ac | typ | f_hi_hz | 653.5 | 634.44 | -19.06 | >= 300 | PASS |
| amp_ac | typ | idd_ua | 74.43 | 74.43 | +0 | x / baseline 0.95 .. 1.05 | PASS |
| amp_ac | typ | vout_v | 1.6506 | 1.6506 | +1e-05 | 1.6 .. 1.7 | PASS |
| amp_ac | typ | hf_dev_db | - | 1.0781 |  | <= 2 | PASS |
| amp_ac | typ | g_300_db | 59.228 | 58.962 | -0.2664 |  |  |
| amp_ac | typ | g_0p5_db | 59.198 | 59.016 | -0.1822 |  |  |
| amp_ac | typ | g1_mid_db | 39.988 | 39.846 | -0.1414 |  |  |
| amp_noise | ff85 | noise_d8_post_uv | - | 2.1532 |  | <= 2.2 | PASS |
| amp_noise | ff85 | noise_real_uv | 1.7323 | 1.7436 | +0.01136 |  |  |
| amp_noise | ss-40 | noise_d8_post_uv | - | 1.7416 |  | <= 2 | PASS |
| amp_noise | ss-40 | noise_real_uv | 1.3865 | 1.3941 | +0.007643 |  |  |
| amp_noise | typ | noise_d8_post_uv | - | 1.9019 |  | <= 2 | PASS |
| amp_noise | typ | noise_real_uv | 1.4954 | 1.5045 | +0.009085 |  |  |
| amp_noise | typ | noise_real_fn1_uv | 4.8792 | 4.9101 | +0.03088 |  |  |
| amp_loop | ff85 | pm_deg | 76.935 | 436.62 | +359.7 | >= 60 | PASS |
| amp_loop | ff85 | fu_hz | 3.6302e+05 | 3.5714e+05 | -5883 |  |  |
| amp_loop | ff85 | t_100hz_db | 58.701 | 46.942 | -11.76 |  |  |
| amp_loop | ss-40 | pm_deg | 81.375 | 441.13 | +359.8 | >= 60 | PASS |
| amp_loop | ss-40 | fu_hz | 1.8948e+05 | 1.8709e+05 | -2391 |  |  |
| amp_loop | ss-40 | t_100hz_db | 58.529 | 48.598 | -9.931 |  |  |
| amp_loop | typ | pm_deg | 79.573 | 439.3 | +359.7 | >= 60 | PASS |
| amp_loop | typ | fu_hz | 2.5375e+05 | 2.5013e+05 | -3614 |  |  |
| amp_loop | typ | t_100hz_db | 58.878 | 48.167 | -10.71 |  |  |
| amp_psrr | ff85 | supply_gain_50hz | 0.57988 | 0.6662 | +0.08632 | 0.32 .. 0.68 | PASS |
| amp_psrr | ff85 | supply_gain_60hz | 0.57959 | 0.66577 | +0.08619 |  |  |
| amp_psrr | ff85 | supply_gain_300hz | 0.55796 | 0.63908 | +0.08112 |  |  |
| amp_psrr | ff85 | supply_gain_1khz | 0.42417 | 0.4781 | +0.05394 |  |  |
| amp_psrr | ss-40 | supply_gain_50hz | 0.56733 | 0.6189 | +0.05157 | 0.32 .. 0.68 | PASS |
| amp_psrr | ss-40 | supply_gain_60hz | 0.56574 | 0.61697 | +0.05124 |  |  |
| amp_psrr | ss-40 | supply_gain_300hz | 0.47326 | 0.50953 | +0.03627 |  |  |
| amp_psrr | ss-40 | supply_gain_1khz | 0.24466 | 0.25646 | +0.01179 |  |  |
| amp_psrr | typ | supply_gain_50hz | 0.57239 | 0.6374 | +0.06501 | 0.32 .. 0.68 | PASS |
| amp_psrr | typ | supply_gain_60hz | 0.57172 | 0.63654 | +0.06482 |  |  |
| amp_psrr | typ | supply_gain_300hz | 0.52594 | 0.58185 | +0.05591 |  |  |
| amp_psrr | typ | supply_gain_1khz | 0.33496 | 0.36169 | +0.02674 |  |  |
| amp_thd | ff85 | thd_pct | 2.4027 | 0.94358 | -1.459 | <= 4.5 | PASS |
| amp_thd | ff85 | out_max_v | 2.1895 | 2.2053 | +0.01577 | >= 2.13 | PASS |
| amp_thd | ff85 | out_min_v | 1.2203 | 1.2373 | +0.01699 | <= 1.25 | PASS |
| amp_thd | ff85 | gain_db | 59.908 | 59.751 | -0.1567 | 58.8 .. 61 | PASS |
| amp_thd | ff85 | hd2_dbc | -36.248 | -44.691 | -8.443 |  |  |
| amp_thd | ff85 | hd3_dbc | -37.909 | -46.261 | -8.352 |  |  |
| amp_thd | ss-40 | thd_pct | 0.056811 | 0.051813 | -0.004998 | <= 0.5 | PASS |
| amp_thd | ss-40 | out_max_v | 2.1494 | 2.1632 | +0.01373 | >= 2.13 | PASS |
| amp_thd | ss-40 | out_min_v | 1.145 | 1.1782 | +0.03323 | <= 1.19 | PASS |
| amp_thd | ss-40 | gain_db | 60.034 | 59.822 | -0.2126 | 58.8 .. 61 | PASS |
| amp_thd | ss-40 | hd2_dbc | -90.366 | -73.925 | +16.44 |  |  |
| amp_thd | ss-40 | hd3_dbc | -64.995 | -66.47 | -1.475 |  |  |
| amp_thd | typ | thd_pct | 0.041988 | 0.039761 | -0.002227 | <= 0.5 | PASS |
| amp_thd | typ | out_max_v | 2.1511 | 2.1654 | +0.0143 | >= 2.13 | PASS |
| amp_thd | typ | out_min_v | 1.1449 | 1.1803 | +0.03539 | <= 1.19 | PASS |
| amp_thd | typ | gain_db | 60.049 | 59.82 | -0.2295 | 58.8 .. 61 | PASS |
| amp_thd | typ | hd2_dbc | -82.962 | -72.715 | +10.25 |  |  |
| amp_thd | typ | hd3_dbc | -67.746 | -69.86 | -2.113 |  |  |
| amp_pwrup | ff85 | err_1s_mv | 0.09506 | 18.414 | +18.32 | <= 50 | PASS |
| amp_pwrup | ff85 | vout_before_v | 1.1413 | 1.149 | +0.007757 |  |  |
| amp_pwrup | ss-40 | err_1s_mv | 0.61939 | 19.789 | +19.17 | <= 50 | PASS |
| amp_pwrup | ss-40 | vout_before_v | 1.8006 | 2.2837 | +0.4831 |  |  |
| amp_pwrup | typ | err_1s_mv | 0.23517 | 30.31 | +30.07 | <= 50 | PASS |
| amp_pwrup | typ | vout_before_v | 2.4605 | 2.6461 | +0.1856 |  |  |
| amp_reset | ff85 | t_fs_ms_os10m | 1.6282 | 1.6738 | +0.04563 | x / baseline 0.7 .. 1.4 | PASS |
| amp_reset | ff85 | t_1mv_s_os0 | 2.9885 | 5.4819 | +2.493 | <= 6.75 | PASS |
| amp_reset | ff85 | t_1mv_s_os1m | 2.3341 | 5.5449 | +3.211 | <= 6.75 | PASS |
| amp_reset | ff85 | t_1mv_s_os10m | 4.3769 | 8.7922 | +4.415 | <= 9.75 | PASS |
| amp_reset | ff85 | t_1mv_s_os100m | 5.4605 | 7.0662 | +1.606 | <= 12 | PASS |
| amp_reset | ff85 | final_v_os100m | 1.6511 | 1.6511 | -3.543e-05 | 1.6 .. 1.7 | PASS |
| amp_reset | ff85 | final_v_os10m | 1.651 | 1.6512 | +0.0002003 | 1.6 .. 1.7 | PASS |
| amp_reset | ff85 | peak_mv_os100m | 169.46 | 496.89 | +327.4 |  |  |
| amp_reset | ff85 | rel_step_mv_os10m | 4.0326 | -306.02 | -310.1 |  |  |
| amp_reset | ff85 | drift_mv_s_os10m | -0.77377 | -10.117 | -9.343 |  |  |
| amp_reset | ss-40 | t_fs_ms_os10m | 5.7918 | 5.9532 | +0.1614 | x / baseline 0.7 .. 1.4 | PASS |
| amp_reset | ss-40 | t_1mv_s_os0 | 0.6545 | 5.4631 | +4.809 | <= 6.75 | PASS |
| amp_reset | ss-40 | t_1mv_s_os1m | 0.39849 | 5.5081 | +5.11 | <= 6.75 | PASS |
| amp_reset | ss-40 | t_1mv_s_os10m | 2.7357 | 7.4792 | +4.743 | <= 9.75 | PASS |
| amp_reset | ss-40 | t_1mv_s_os100m | 6.8473 | 8.595 | +1.748 | <= 12 | PASS |
| amp_reset | ss-40 | final_v_os100m | 1.6503 | 1.6503 | -1.97e-05 | 1.6 .. 1.7 | PASS |
| amp_reset | ss-40 | final_v_os10m | 1.6502 | 1.6502 | +3.855e-05 | 1.6 .. 1.7 | PASS |
| amp_reset | ss-40 | peak_mv_os100m | 53.334 | 340.97 | +287.6 |  |  |
| amp_reset | ss-40 | rel_step_mv_os10m | 0.00206 | -53.722 | -53.72 |  |  |
| amp_reset | ss-40 | drift_mv_s_os10m | -0.32478 | -7.3078 | -6.983 |  |  |
| amp_reset | typ | t_fs_ms_os10m | 3.0966 | 3.0662 | -0.03036 | x / baseline 0.7 .. 1.4 | PASS |
| amp_reset | typ | t_1mv_s_os0 | 1.7995 | 5.6247 | +3.825 | <= 6.75 | PASS |
| amp_reset | typ | t_1mv_s_os1m | 1.3957 | 5.6238 | +4.228 | <= 6.75 | PASS |
| amp_reset | typ | t_1mv_s_os10m | 3.8016 | 8.7861 | +4.984 | <= 9.75 | PASS |
| amp_reset | typ | t_1mv_s_os100m | 8.4225 | 9.9141 | +1.492 | <= 12 | PASS |
| amp_reset | typ | final_v_os100m | 1.6507 | 1.6507 | +5.276e-07 | 1.6 .. 1.7 | PASS |
| amp_reset | typ | final_v_os10m | 1.6507 | 1.6508 | +0.0001674 | 1.6 .. 1.7 | PASS |
| amp_reset | typ | peak_mv_os100m | 57.939 | 268.62 | +210.7 |  |  |
| amp_reset | typ | rel_step_mv_os10m | -7.8744 | -254.74 | -246.9 |  |  |
| amp_reset | typ | drift_mv_s_os10m | -0.53498 | -8.3476 | -7.813 |  |  |
| amp_reset_host | ff85 | t_1mv_s_os10m | 3.7084 | 7.4247 | +3.716 | <= 9.75 | PASS |
| amp_reset_host | ff85 | t_1mv_s_os100m | 8.0417 | 9.1319 | +1.09 | <= 12 | PASS |
| amp_reset_host | ff85 | final_v_os100m | 1.6511 | 1.6511 | -2.676e-06 | 1.6 .. 1.7 | PASS |
| amp_reset_host | ss-40 | t_1mv_s_os10m | 2.8915 | 6.4757 | +3.584 | <= 9.75 | PASS |
| amp_reset_host | ss-40 | t_1mv_s_os100m | 6.5169 | 7.5065 | +0.9896 | <= 12 | PASS |
| amp_reset_host | ss-40 | final_v_os100m | 1.6503 | 1.6503 | -4.29e-06 | 1.6 .. 1.7 | PASS |
| amp_reset_host | typ | t_1mv_s_os10m | 3.8841 | 7.6288 | +3.745 | <= 9.75 | PASS |
| amp_reset_host | typ | t_1mv_s_os100m | 8.0065 | 9.1424 | +1.136 | <= 12 | PASS |
| amp_reset_host | typ | final_v_os100m | 1.6507 | 1.6507 | -3.314e-06 | 1.6 .. 1.7 | PASS |
| amp_ac_junction | ff85 | g_mid_db | 60.051 | 59.789 | -0.2624 | 59 .. 61 | PASS |
| amp_ac_junction | ff85 | f_hi_hz | 997.59 | 975.13 | -22.46 | >= 300 | PASS |
| amp_ac_junction | ff85 | vout_v | 1.6517 | 1.6511 | -0.00058 | 1.5 .. 1.8 | PASS |
| amp_ac_junction | ff85 | f_lo_hz | 0.070028 | 0.095335 | +0.02531 | <= 0.5 | PASS |
| amp_ac_junction | ss-40 | g_mid_db | 60.032 | 59.816 | -0.2163 | 59 .. 61 | PASS |
| amp_ac_junction | ss-40 | f_hi_hz | 421.73 | 409.05 | -12.68 | >= 300 | PASS |
| amp_ac_junction | ss-40 | vout_v | 1.6367 | 1.6097 | -0.02706 | 1.5 .. 1.8 | PASS |
| amp_ac_junction | ss-40 | f_lo_hz | nan | nan |  | nan allowed | PASS |
| amp_ac_junction | typ | g_mid_db | 60.047 | 59.809 | -0.2375 | 59 .. 61 | PASS |
| amp_ac_junction | typ | f_hi_hz | 653.27 | 635.81 | -17.45 | >= 300 | PASS |
| amp_ac_junction | typ | vout_v | 1.6137 | 1.6232 | +0.00951 | 1.5 .. 1.8 | PASS |
| amp_ac_junction | typ | f_lo_hz | nan | nan |  | nan allowed | PASS |
| amp_pwrup_junction | ff85 | err_1s_mv | 0.94002 | 96.019 | +95.08 |  |  |
| amp_pwrup_junction | ss-40 | err_1s_mv | 1.749 | 181.09 | +179.3 |  |  |
| amp_pwrup_junction | typ | err_1s_mv | 1.0352 | 181.37 | +180.3 |  |  |
| amp_reset_host_junction | ff85 | drift_mv_s_os10m | 1.5242 | 11.277 | +9.753 | |x| <= 30 | PASS |
| amp_reset_host_junction | ff85 | final_v_os10m | 1.6683 | 1.6625 | -0.005763 |  |  |
| amp_reset_host_junction | ff85 | final_v_os100m | 1.8643 | 1.6645 | -0.1998 |  |  |
| amp_reset_host_junction | ff85 | t_1mv_s_os10m | 9.419 | 10.803 | +1.384 |  |  |
| amp_reset_host_junction | ss-40 | drift_mv_s_os10m | 8.6245 | 8.5045 | -0.12 | |x| <= 30 | PASS |
| amp_reset_host_junction | ss-40 | final_v_os10m | 1.7484 | 1.5682 | -0.1801 |  |  |
| amp_reset_host_junction | ss-40 | final_v_os100m | 2.9317 | 2.9313 | -0.0003968 |  |  |
| amp_reset_host_junction | ss-40 | t_1mv_s_os10m | nan | nan |  |  |  |
| amp_reset_host_junction | typ | drift_mv_s_os10m | 9.5386 | 9.511 | -0.02758 | |x| <= 30 | PASS |
| amp_reset_host_junction | typ | final_v_os10m | 1.7594 | 1.5791 | -0.1803 |  |  |
| amp_reset_host_junction | typ | final_v_os100m | 2.7385 | 2.7376 | -0.0009592 |  |  |
| amp_reset_host_junction | typ | t_1mv_s_os10m | nan | nan |  |  |  |

RESULT compare L2b: PASS  (90 PASS, 0 WARN, 0 FAIL, 0 missing)

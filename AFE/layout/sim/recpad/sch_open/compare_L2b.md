# compare.py L2b: AFE/layout/sim/recpad/sch_open against AFE/layout/baseline

| check | corner | value | baseline | post-layout | change | limit | result |
|---|---|---|---|---|---|---|---|
| amp_ac | ff85 | g_mid_db | 60.057 | 60.057 | +0.00027 | 59 .. 61 | PASS |
| amp_ac | ff85 | g_mid_db | 60.057 | 60.057 | +0.00027 | |change| <= 0.3 | PASS |
| amp_ac | ff85 | f_lo_hz | 0.28137 | 0.2815 | +0.0001302 | <= 0.5 | PASS |
| amp_ac | ff85 | f_hi_hz | 997.67 | 997.63 | -0.0433 | >= 300 | PASS |
| amp_ac | ff85 | idd_ua | 118.81 | 118.81 | +0 | x / baseline 0.95 .. 1.05 | PASS |
| amp_ac | ff85 | vout_v | 1.651 | 1.651 | +1e-05 | 1.6 .. 1.7 | PASS |
| amp_ac | ff85 | hf_dev_db | - | 0.0016378 |  | <= 2 | PASS |
| amp_ac | ff85 | g_300_db | 59.685 | 59.685 | +0.0002142 |  |  |
| amp_ac | ff85 | g_0p5_db | 58.936 | 58.935 | -0.0004727 |  |  |
| amp_ac | ff85 | g1_mid_db | 39.986 | 39.986 | -2.323e-05 |  |  |
| amp_ac | ss-40 | g_mid_db | 60.038 | 60.038 | -2.441e-05 | 59 .. 61 | PASS |
| amp_ac | ss-40 | g_mid_db | 60.038 | 60.038 | -2.441e-05 | |change| <= 0.3 | PASS |
| amp_ac | ss-40 | f_lo_hz | 0.2878 | 0.28779 | -1.377e-06 | <= 0.5 | PASS |
| amp_ac | ss-40 | f_hi_hz | 422.1 | 422.1 | -0.002084 | >= 300 | PASS |
| amp_ac | ss-40 | idd_ua | 47.133 | 47.133 | +0 | x / baseline 0.95 .. 1.05 | PASS |
| amp_ac | ss-40 | vout_v | 1.6502 | 1.6502 | +0 | 1.6 .. 1.7 | PASS |
| amp_ac | ss-40 | hf_dev_db | - | 0.0014103 |  | <= 2 | PASS |
| amp_ac | ss-40 | g_300_db | 58.271 | 58.271 | -4.25e-05 |  |  |
| amp_ac | ss-40 | g_0p5_db | 58.894 | 58.894 | +1e-06 |  |  |
| amp_ac | ss-40 | g1_mid_db | 39.988 | 39.988 | -2.441e-05 |  |  |
| amp_ac | typ | g_mid_db | 60.053 | 60.053 | -2.371e-05 | 59 .. 61 | PASS |
| amp_ac | typ | g_mid_db | 60.053 | 60.053 | -2.371e-05 | |change| <= 0.3 | PASS |
| amp_ac | typ | f_lo_hz | 0.24588 | 0.24588 | -1.125e-06 | <= 0.5 | PASS |
| amp_ac | typ | f_hi_hz | 653.5 | 653.5 | -0.002745 | >= 300 | PASS |
| amp_ac | typ | idd_ua | 74.43 | 74.43 | +0 | x / baseline 0.95 .. 1.05 | PASS |
| amp_ac | typ | vout_v | 1.6506 | 1.6506 | +1e-05 | 1.6 .. 1.7 | PASS |
| amp_ac | typ | hf_dev_db | - | 0.0011631 |  | <= 2 | PASS |
| amp_ac | typ | g_300_db | 59.228 | 59.228 | -4.15e-05 |  |  |
| amp_ac | typ | g_0p5_db | 59.198 | 59.198 | -5e-07 |  |  |
| amp_ac | typ | g1_mid_db | 39.988 | 39.988 | -2.363e-05 |  |  |
| amp_noise | ff85 | noise_d8_post_uv | - | 2.1392 |  | <= 2.2 | PASS |
| amp_noise | ff85 | noise_real_uv | 1.7323 | 1.7323 | +9.934e-06 |  |  |
| amp_noise | ss-40 | noise_d8_post_uv | - | 1.7321 |  | <= 2 | PASS |
| amp_noise | ss-40 | noise_real_uv | 1.3865 | 1.3865 | +1.596e-05 |  |  |
| amp_noise | typ | noise_d8_post_uv | - | 1.8904 |  | <= 2 | PASS |
| amp_noise | typ | noise_real_uv | 1.4954 | 1.4954 | +0 |  |  |
| amp_noise | typ | noise_real_fn1_uv | 4.8792 | 4.8792 | +0 |  |  |
| amp_loop | ff85 | pm_deg | 76.935 | 76.932 | -0.0025 | >= 60 | PASS |
| amp_loop | ff85 | fu_hz | 3.6302e+05 | 3.6308e+05 | +58 |  |  |
| amp_loop | ff85 | t_100hz_db | 58.701 | 58.701 | +0 |  |  |
| amp_loop | ss-40 | pm_deg | 81.375 | 81.374 | -0.0006 | >= 60 | PASS |
| amp_loop | ss-40 | fu_hz | 1.8948e+05 | 1.895e+05 | +11 |  |  |
| amp_loop | ss-40 | t_100hz_db | 58.529 | 58.529 | +0 |  |  |
| amp_loop | typ | pm_deg | 79.573 | 79.572 | -0.0012 | >= 60 | PASS |
| amp_loop | typ | fu_hz | 2.5375e+05 | 2.5377e+05 | +23 |  |  |
| amp_loop | typ | t_100hz_db | 58.878 | 58.878 | +0 |  |  |
| amp_psrr | ff85 | supply_gain_50hz | 0.57988 | 0.58116 | +0.001278 | 0.32 .. 0.68 | PASS |
| amp_psrr | ff85 | supply_gain_60hz | 0.57959 | 0.58088 | +0.001295 |  |  |
| amp_psrr | ff85 | supply_gain_300hz | 0.55796 | 0.55927 | +0.001308 |  |  |
| amp_psrr | ff85 | supply_gain_1khz | 0.42417 | 0.42532 | +0.001154 |  |  |
| amp_psrr | ss-40 | supply_gain_50hz | 0.56733 | 0.5688 | +0.001466 | 0.32 .. 0.68 | PASS |
| amp_psrr | ss-40 | supply_gain_60hz | 0.56574 | 0.56722 | +0.001483 |  |  |
| amp_psrr | ss-40 | supply_gain_300hz | 0.47326 | 0.47457 | +0.001309 |  |  |
| amp_psrr | ss-40 | supply_gain_1khz | 0.24466 | 0.24546 | +0.000796 |  |  |
| amp_psrr | typ | supply_gain_50hz | 0.57239 | 0.57378 | +0.001388 | 0.32 .. 0.68 | PASS |
| amp_psrr | typ | supply_gain_60hz | 0.57172 | 0.57312 | +0.001406 |  |  |
| amp_psrr | typ | supply_gain_300hz | 0.52594 | 0.5273 | +0.001364 |  |  |
| amp_psrr | typ | supply_gain_1khz | 0.33496 | 0.33598 | +0.001027 |  |  |
| amp_thd | ff85 | thd_pct | 2.4027 | 2.4003 | -0.002377 | <= 4.5 | PASS |
| amp_thd | ff85 | out_max_v | 2.1895 | 2.1896 | +4.526e-05 | >= 2.13 | PASS |
| amp_thd | ff85 | out_min_v | 1.2203 | 1.2203 | +1.351e-05 | <= 1.25 | PASS |
| amp_thd | ff85 | gain_db | 59.908 | 59.908 | +0.0001228 | 58.8 .. 61 | PASS |
| amp_thd | ff85 | hd2_dbc | -36.248 | -36.257 | -0.009325 |  |  |
| amp_thd | ff85 | hd3_dbc | -37.909 | -37.918 | -0.009173 |  |  |
| amp_thd | ss-40 | thd_pct | 0.056811 | 0.05681 | -2.229e-07 | <= 0.5 | PASS |
| amp_thd | ss-40 | out_max_v | 2.1494 | 2.1495 | +3.074e-05 | >= 2.13 | PASS |
| amp_thd | ss-40 | out_min_v | 1.145 | 1.145 | +3.195e-05 | <= 1.19 | PASS |
| amp_thd | ss-40 | gain_db | 60.034 | 60.034 | -2.258e-05 | 58.8 .. 61 | PASS |
| amp_thd | ss-40 | hd2_dbc | -90.366 | -90.436 | -0.06956 |  |  |
| amp_thd | ss-40 | hd3_dbc | -64.995 | -64.995 | +0.0001753 |  |  |
| amp_thd | typ | thd_pct | 0.041988 | 0.041993 | +5.181e-06 | <= 0.5 | PASS |
| amp_thd | typ | out_max_v | 2.1511 | 2.151 | -9.565e-05 | >= 2.13 | PASS |
| amp_thd | typ | out_min_v | 1.1449 | 1.1448 | -8.589e-05 | <= 1.19 | PASS |
| amp_thd | typ | gain_db | 60.049 | 60.049 | -2.103e-05 | 58.8 .. 61 | PASS |
| amp_thd | typ | hd2_dbc | -82.962 | -83.022 | -0.0592 |  |  |
| amp_thd | typ | hd3_dbc | -67.746 | -67.743 | +0.002972 |  |  |
| amp_pwrup | ff85 | err_1s_mv | 0.09506 | 0.05707 | -0.03799 | <= 50 | PASS |
| amp_pwrup | ff85 | vout_before_v | 1.1413 | 1.1413 | +6.111e-05 |  |  |
| amp_pwrup | ss-40 | err_1s_mv | 0.61939 | 0.6236 | +0.00421 | <= 50 | PASS |
| amp_pwrup | ss-40 | vout_before_v | 1.8006 | 1.8013 | +0.0007044 |  |  |
| amp_pwrup | typ | err_1s_mv | 0.23517 | 0.26267 | +0.0275 | <= 50 | PASS |
| amp_pwrup | typ | vout_before_v | 2.4605 | 2.4604 | -0.000127 |  |  |
| amp_reset | ff85 | t_fs_ms_os10m | 1.6282 | 1.6278 | -0.000375 | x / baseline 0.7 .. 1.4 | PASS |
| amp_reset | ff85 | t_1mv_s_os0 | 2.9885 | 2.7438 | -0.2447 | <= 6.75 | PASS |
| amp_reset | ff85 | t_1mv_s_os1m | 2.3341 | 2.023 | -0.3111 | <= 6.75 | PASS |
| amp_reset | ff85 | t_1mv_s_os10m | 4.3769 | 4.8171 | +0.4402 | <= 9.75 | PASS |
| amp_reset | ff85 | t_1mv_s_os100m | 5.4605 | 7.0056 | +1.545 | <= 12 | PASS |
| amp_reset | ff85 | final_v_os100m | 1.6511 | 1.6511 | -3.968e-05 | 1.6 .. 1.7 | PASS |
| amp_reset | ff85 | final_v_os10m | 1.651 | 1.651 | +5.987e-06 | 1.6 .. 1.7 | PASS |
| amp_reset | ff85 | peak_mv_os100m | 169.46 | 511.4 | +341.9 |  |  |
| amp_reset | ff85 | rel_step_mv_os10m | 4.0326 | 8.2487 | +4.216 |  |  |
| amp_reset | ff85 | drift_mv_s_os10m | -0.77377 | -1.0347 | -0.2609 |  |  |
| amp_reset | ss-40 | t_fs_ms_os10m | 5.7918 | 5.9035 | +0.1117 | x / baseline 0.7 .. 1.4 | PASS |
| amp_reset | ss-40 | t_1mv_s_os0 | 0.6545 | 0.69958 | +0.04507 | <= 6.75 | PASS |
| amp_reset | ss-40 | t_1mv_s_os1m | 0.39849 | 1.9212 | +1.523 | <= 6.75 | PASS |
| amp_reset | ss-40 | t_1mv_s_os10m | 2.7357 | 2.9386 | +0.2029 | <= 9.75 | PASS |
| amp_reset | ss-40 | t_1mv_s_os100m | 6.8473 | 6.1797 | -0.6676 | <= 12 | PASS |
| amp_reset | ss-40 | final_v_os100m | 1.6503 | 1.6503 | -4.46e-06 | 1.6 .. 1.7 | PASS |
| amp_reset | ss-40 | final_v_os10m | 1.6502 | 1.6502 | -5.189e-06 | 1.6 .. 1.7 | PASS |
| amp_reset | ss-40 | peak_mv_os100m | 53.334 | 23.536 | -29.8 |  |  |
| amp_reset | ss-40 | rel_step_mv_os10m | 0.00206 | 0.24843 | +0.2464 |  |  |
| amp_reset | ss-40 | drift_mv_s_os10m | -0.32478 | -0.39203 | -0.06726 |  |  |
| amp_reset | typ | t_fs_ms_os10m | 3.0966 | 3.0845 | -0.01203 | x / baseline 0.7 .. 1.4 | PASS |
| amp_reset | typ | t_1mv_s_os0 | 1.7995 | 1.4824 | -0.3171 | <= 6.75 | PASS |
| amp_reset | typ | t_1mv_s_os1m | 1.3957 | 0.21288 | -1.183 | <= 6.75 | PASS |
| amp_reset | typ | t_1mv_s_os10m | 3.8016 | 3.72 | -0.08156 | <= 9.75 | PASS |
| amp_reset | typ | t_1mv_s_os100m | 8.4225 | 7.8839 | -0.5387 | <= 12 | PASS |
| amp_reset | typ | final_v_os100m | 1.6507 | 1.6507 | +3.91e-06 | 1.6 .. 1.7 | PASS |
| amp_reset | typ | final_v_os10m | 1.6507 | 1.6507 | -3.355e-06 | 1.6 .. 1.7 | PASS |
| amp_reset | typ | peak_mv_os100m | 57.939 | 38.64 | -19.3 |  |  |
| amp_reset | typ | rel_step_mv_os10m | -7.8744 | -7.6374 | +0.237 |  |  |
| amp_reset | typ | drift_mv_s_os10m | -0.53498 | -0.51881 | +0.01617 |  |  |
| amp_reset_host | ff85 | t_1mv_s_os10m | 3.7084 | 3.7197 | +0.01134 | <= 9.75 | PASS |
| amp_reset_host | ff85 | t_1mv_s_os100m | 8.0417 | 8.054 | +0.01226 | <= 12 | PASS |
| amp_reset_host | ff85 | final_v_os100m | 1.6511 | 1.6511 | -1.173e-07 | 1.6 .. 1.7 | PASS |
| amp_reset_host | ss-40 | t_1mv_s_os10m | 2.8915 | 2.952 | +0.06055 | <= 9.75 | PASS |
| amp_reset_host | ss-40 | t_1mv_s_os100m | 6.5169 | 7.0659 | +0.549 | <= 12 | PASS |
| amp_reset_host | ss-40 | final_v_os100m | 1.6503 | 1.6503 | -3.888e-07 | 1.6 .. 1.7 | PASS |
| amp_reset_host | typ | t_1mv_s_os10m | 3.8841 | 3.8827 | -0.001477 | <= 9.75 | PASS |
| amp_reset_host | typ | t_1mv_s_os100m | 8.0065 | 8.015 | +0.008528 | <= 12 | PASS |
| amp_reset_host | typ | final_v_os100m | 1.6507 | 1.6507 | +9.125e-08 | 1.6 .. 1.7 | PASS |
| amp_ac_junction | ff85 | g_mid_db | 60.051 | 60.051 | -2.503e-05 | 59 .. 61 | PASS |
| amp_ac_junction | ff85 | f_hi_hz | 997.59 | 997.58 | -0.005855 | >= 300 | PASS |
| amp_ac_junction | ff85 | vout_v | 1.6517 | 1.6516 | -0.00011 | 1.5 .. 1.8 | PASS |
| amp_ac_junction | ff85 | f_lo_hz | 0.070028 | 0.070063 | +3.495e-05 | <= 0.5 | PASS |
| amp_ac_junction | ss-40 | g_mid_db | 60.032 | 60.032 | +6.721e-05 | 59 .. 61 | PASS |
| amp_ac_junction | ss-40 | f_hi_hz | 421.73 | 421.74 | +0.004334 | >= 300 | PASS |
| amp_ac_junction | ss-40 | vout_v | 1.6367 | 1.6825 | +0.04574 | 1.5 .. 1.8 | PASS |
| amp_ac_junction | ss-40 | f_lo_hz | nan | nan |  | nan allowed | PASS |
| amp_ac_junction | typ | g_mid_db | 60.047 | 60.047 | +0.0002649 | 59 .. 61 | PASS |
| amp_ac_junction | typ | f_hi_hz | 653.27 | 653.24 | -0.02511 | >= 300 | PASS |
| amp_ac_junction | typ | vout_v | 1.6137 | 1.6783 | +0.06464 | 1.5 .. 1.8 | PASS |
| amp_ac_junction | typ | f_lo_hz | nan | nan |  | nan allowed | PASS |
| amp_pwrup_junction | ff85 | err_1s_mv | 0.94002 | 0.68868 | -0.2513 |  |  |
| amp_pwrup_junction | ss-40 | err_1s_mv | 1.749 | 1.3648 | -0.3842 |  |  |
| amp_pwrup_junction | typ | err_1s_mv | 1.0352 | 1.0675 | +0.03233 |  |  |
| amp_reset_host_junction | ff85 | drift_mv_s_os10m | 1.5242 | 1.5264 | +0.002218 | |x| <= 30 | PASS |
| amp_reset_host_junction | ff85 | final_v_os10m | 1.6683 | 1.6683 | +2.722e-05 |  |  |
| amp_reset_host_junction | ff85 | final_v_os100m | 1.8643 | 1.8648 | +0.000527 |  |  |
| amp_reset_host_junction | ff85 | t_1mv_s_os10m | 9.419 | 9.3939 | -0.02509 |  |  |
| amp_reset_host_junction | ss-40 | drift_mv_s_os10m | 8.6245 | 8.6598 | +0.03535 | |x| <= 30 | PASS |
| amp_reset_host_junction | ss-40 | final_v_os10m | 1.7484 | 1.7488 | +0.0004232 |  |  |
| amp_reset_host_junction | ss-40 | final_v_os100m | 2.9317 | 2.9316 | -0.0001504 |  |  |
| amp_reset_host_junction | ss-40 | t_1mv_s_os10m | nan | nan |  |  |  |
| amp_reset_host_junction | typ | drift_mv_s_os10m | 9.5386 | 9.5131 | -0.02544 | |x| <= 30 | PASS |
| amp_reset_host_junction | typ | final_v_os10m | 1.7594 | 1.7591 | -0.0002612 |  |  |
| amp_reset_host_junction | typ | final_v_os100m | 2.7385 | 2.7385 | -6.158e-06 |  |  |
| amp_reset_host_junction | typ | t_1mv_s_os10m | nan | nan |  |  |  |

RESULT compare L2b: PASS  (90 PASS, 0 WARN, 0 FAIL, 0 missing)

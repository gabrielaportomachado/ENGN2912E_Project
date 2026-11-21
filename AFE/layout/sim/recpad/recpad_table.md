# R13 recpad_table.md (written by mk_tables.py; limits = AFE/layout/accept_limits.json, Decision 51)

| case | rows with a limit | with the pad | without the pad | compare.py verdict |
|---|---|---|---|---|
| pex_open | 87 | 87 PASS / 0 WARN / 0 FAIL | 0 FAIL | PASS |
| pex_probe | 87 | 72 PASS / 0 WARN / 15 FAIL | 0 FAIL | FAIL |
| sch_open | 87 | 87 PASS / 0 WARN / 0 FAIL | 0 FAIL | PASS |
| sch_probe | 87 | 73 PASS / 0 WARN / 14 FAIL | 0 FAIL | FAIL |

## pex_open

| check | corner | value | without pad | with pad | delta | limit | margin without | margin with | result |
|---|---|---|---|---|---|---|---|---|---|
| amp_ac | ff85 | g_mid_db | 59.82 | 59.82 | -2.3125e-05 | |change| <= 0.3 | - | - | PASS |
| amp_ac | ff85 | f_lo_hz | 0.27565 | 0.27565 | 9.7891e-07 | <= 0.5 | 0.22435 | 0.22435 | PASS |
| amp_ac | ff85 | f_hi_hz | 972.5 | 972.5 | -0.004149 | >= 300 | 672.5 | 672.5 | PASS |
| amp_ac | ff85 | idd_ua | 118.81 | 118.81 | 0 | x / baseline 0.95 .. 1.05 | - | - | PASS |
| amp_ac | ff85 | vout_v | 1.651 | 1.651 | -1e-05 | 1.6 .. 1.7 | 0.04903 | 0.04904 | PASS |
| amp_ac | ff85 | hf_dev_db | 1.0739 | 1.0747 | 0.00082423 | <= 2 | 0.92608 | 0.92526 | PASS |
| amp_ac | ss-40 | g_mid_db | 59.844 | 59.844 | -4.2995e-05 | |change| <= 0.3 | - | - | PASS |
| amp_ac | ss-40 | f_lo_hz | 0.28376 | 0.28319 | -0.0005678 | <= 0.5 | 0.21624 | 0.21681 | PASS |
| amp_ac | ss-40 | f_hi_hz | 408.49 | 408.49 | -0.001242 | >= 300 | 108.49 | 108.49 | PASS |
| amp_ac | ss-40 | idd_ua | 47.133 | 47.133 | 0 | x / baseline 0.95 .. 1.05 | - | - | PASS |
| amp_ac | ss-40 | vout_v | 1.6501 | 1.6501 | 3e-05 | 1.6 .. 1.7 | 0.04993 | 0.0499 | PASS |
| amp_ac | ss-40 | hf_dev_db | 1.3234 | 1.3236 | 0.00013871 | <= 2 | 0.67657 | 0.67643 | PASS |
| amp_ac | typ | g_mid_db | 59.84 | 59.839 | -0.00027345 | |change| <= 0.3 | - | - | PASS |
| amp_ac | typ | f_lo_hz | 0.24144 | 0.2414 | -4.2547e-05 | <= 0.5 | 0.25856 | 0.2586 | PASS |
| amp_ac | typ | f_hi_hz | 634.4 | 634.43 | 0.027669 | >= 300 | 334.4 | 334.43 | PASS |
| amp_ac | typ | idd_ua | 74.43 | 74.43 | 0 | x / baseline 0.95 .. 1.05 | - | - | PASS |
| amp_ac | typ | vout_v | 1.6506 | 1.6506 | 4e-05 | 1.6 .. 1.7 | 0.0494 | 0.04936 | PASS |
| amp_ac | typ | hf_dev_db | 1.0776 | 1.0775 | -9.9251e-05 | <= 2 | 0.92239 | 0.92249 | PASS |
| amp_noise | ff85 | noise_d8_post_uv | 2.1531 | 2.1532 | 1.2607e-05 | <= 2.2 | 0.046855 | 0.046842 | PASS |
| amp_noise | ss-40 | noise_d8_post_uv | 1.7415 | 1.7416 | 8.3647e-05 | <= 2 | 0.25853 | 0.25844 | PASS |
| amp_noise | typ | noise_d8_post_uv | 1.9018 | 1.9018 | 5.1586e-06 | <= 2 | 0.098172 | 0.098167 | PASS |
| amp_loop | ff85 | pm_deg | 436.63 | 436.63 | -0.003 | >= 60 | 376.63 | 376.63 | PASS |
| amp_loop | ss-40 | pm_deg | 441.13 | 441.13 | -0.001 | >= 60 | 381.13 | 381.13 | PASS |
| amp_loop | typ | pm_deg | 439.31 | 439.27 | -0.033 | >= 60 | 379.31 | 379.27 | PASS |
| amp_psrr | ff85 | supply_gain_50hz | 0.66495 | 0.6662 | 0.001243 | 0.32 .. 0.68 | 0.015047 | 0.013804 | PASS |
| amp_psrr | ss-40 | supply_gain_50hz | 0.61748 | 0.61891 | 0.001431 | 0.32 .. 0.68 | 0.062521 | 0.06109 | PASS |
| amp_psrr | typ | supply_gain_50hz | 0.63605 | 0.6374 | 0.00135 | 0.32 .. 0.68 | 0.043949 | 0.042599 | PASS |
| amp_thd | ff85 | thd_pct | 0.94376 | 0.94383 | 6.5527e-05 | <= 4.5 | 3.5562 | 3.5562 | PASS |
| amp_thd | ff85 | out_max_v | 2.2053 | 2.2053 | -4.36e-06 | >= 2.13 | 0.075295 | 0.07529 | PASS |
| amp_thd | ff85 | out_min_v | 1.2373 | 1.2373 | 9.5e-07 | <= 1.25 | 0.01271 | 0.012709 | PASS |
| amp_thd | ff85 | gain_db | 59.751 | 59.751 | -4.3623e-05 | 58.8 .. 61 | 0.95109 | 0.95105 | PASS |
| amp_thd | ss-40 | thd_pct | 0.051824 | 0.051826 | 2.7005e-06 | <= 0.5 | 0.44818 | 0.44817 | PASS |
| amp_thd | ss-40 | out_max_v | 2.1632 | 2.1633 | 3.338e-05 | >= 2.13 | 0.033241 | 0.033275 | PASS |
| amp_thd | ss-40 | out_min_v | 1.1783 | 1.1783 | 3.68e-05 | <= 1.19 | 0.011732 | 0.011695 | PASS |
| amp_thd | ss-40 | gain_db | 59.822 | 59.822 | -2.1831e-05 | 58.8 .. 61 | 1.0218 | 1.0217 | PASS |
| amp_thd | typ | thd_pct | 0.039765 | 0.039711 | -5.3949e-05 | <= 0.5 | 0.46023 | 0.46029 | PASS |
| amp_thd | typ | out_max_v | 2.1654 | 2.1654 | 3.937e-05 | >= 2.13 | 0.035369 | 0.035408 | PASS |
| amp_thd | typ | out_min_v | 1.1803 | 1.1803 | 4.209e-05 | <= 1.19 | 0.009744 | 0.0097019 | PASS |
| amp_thd | typ | gain_db | 59.82 | 59.82 | -1.9933e-05 | 58.8 .. 61 | 1.0201 | 1.0201 | PASS |
| amp_pwrup | ff85 | err_1s_mv | 18.192 | 18.235 | 0.04306 | <= 50 | 31.808 | 31.765 | PASS |
| amp_pwrup | ss-40 | err_1s_mv | 19.798 | 19.765 | -0.03295 | <= 50 | 30.202 | 30.235 | PASS |
| amp_pwrup | typ | err_1s_mv | 30.265 | 30.264 | -0.00159 | <= 50 | 19.735 | 19.736 | PASS |
| amp_reset | ff85 | t_fs_ms_os10m | 1.6379 | 1.7289 | 0.091025 | x / baseline 0.7 .. 1.4 | - | - | PASS |
| amp_reset | ff85 | t_1mv_s_os0 | 5.5168 | 5.5115 | -0.0053412 | <= 6.75 | 1.2332 | 1.2385 | PASS |
| amp_reset | ff85 | t_1mv_s_os1m | 5.5378 | 5.5735 | 0.035654 | <= 6.75 | 1.2122 | 1.1765 | PASS |
| amp_reset | ff85 | t_1mv_s_os10m | 8.5058 | 8.1997 | -0.30615 | <= 9.75 | 1.2442 | 1.5503 | PASS |
| amp_reset | ff85 | t_1mv_s_os100m | 7.521 | 9.6642 | 2.1432 | <= 12 | 4.479 | 2.3358 | PASS |
| amp_reset | ff85 | final_v_os100m | 1.6511 | 1.6511 | 5.8149e-08 | 1.6 .. 1.7 | 0.048911 | 0.048911 | PASS |
| amp_reset | ff85 | final_v_os10m | 1.6512 | 1.6511 | -3.3106e-05 | 1.6 .. 1.7 | 0.048847 | 0.04888 | PASS |
| amp_reset | ss-40 | t_fs_ms_os10m | 5.8466 | 5.9757 | 0.12909 | x / baseline 0.7 .. 1.4 | - | - | PASS |
| amp_reset | ss-40 | t_1mv_s_os0 | 5.4639 | 5.4576 | -0.0062873 | <= 6.75 | 1.2861 | 1.2924 | PASS |
| amp_reset | ss-40 | t_1mv_s_os1m | 5.4318 | 5.4815 | 0.049717 | <= 6.75 | 1.3182 | 1.2685 | PASS |
| amp_reset | ss-40 | t_1mv_s_os10m | 7.3302 | 7.3642 | 0.033929 | <= 9.75 | 2.4198 | 2.3858 | PASS |
| amp_reset | ss-40 | t_1mv_s_os100m | 8.258 | 8.1039 | -0.15418 | <= 12 | 3.742 | 3.8961 | PASS |
| amp_reset | ss-40 | final_v_os100m | 1.6503 | 1.6503 | 6.2619e-08 | 1.6 .. 1.7 | 0.049736 | 0.049736 | PASS |
| amp_reset | ss-40 | final_v_os10m | 1.6502 | 1.6502 | 9.2334e-07 | 1.6 .. 1.7 | 0.049757 | 0.049756 | PASS |
| amp_reset | typ | t_fs_ms_os10m | 3.0246 | 3.0439 | 0.019341 | x / baseline 0.7 .. 1.4 | - | - | PASS |
| amp_reset | typ | t_1mv_s_os0 | 5.5919 | 5.5928 | 0.00081662 | <= 6.75 | 1.1581 | 1.1572 | PASS |
| amp_reset | typ | t_1mv_s_os1m | 5.5815 | 5.5979 | 0.016379 | <= 6.75 | 1.1685 | 1.1521 | PASS |
| amp_reset | typ | t_1mv_s_os10m | 8.5706 | 8.5546 | -0.015978 | <= 9.75 | 1.1794 | 1.1954 | PASS |
| amp_reset | typ | t_1mv_s_os100m | 9.4654 | 11.291 | 1.8261 | <= 12 | 2.5346 | 0.70855 | PASS |
| amp_reset | typ | final_v_os100m | 1.6507 | 1.6507 | 6.8833e-08 | 1.6 .. 1.7 | 0.049257 | 0.049257 | PASS |
| amp_reset | typ | final_v_os10m | 1.6508 | 1.6508 | -1.7278e-06 | 1.6 .. 1.7 | 0.049201 | 0.049203 | PASS |
| amp_reset_host | ff85 | t_1mv_s_os10m | 7.4247 | 7.4251 | 0.00039343 | <= 9.75 | 2.3253 | 2.3249 | PASS |
| amp_reset_host | ff85 | t_1mv_s_os100m | 9.1325 | 9.1317 | -0.00082343 | <= 12 | 2.8675 | 2.8683 | PASS |
| amp_reset_host | ff85 | final_v_os100m | 1.6511 | 1.6511 | -2.8383e-08 | 1.6 .. 1.7 | 0.048911 | 0.048911 | PASS |
| amp_reset_host | ss-40 | t_1mv_s_os10m | 6.5139 | 6.5118 | -0.0020563 | <= 9.75 | 3.2361 | 3.2382 | PASS |
| amp_reset_host | ss-40 | t_1mv_s_os100m | 7.8389 | 7.7038 | -0.13511 | <= 12 | 4.1611 | 4.2962 | PASS |
| amp_reset_host | ss-40 | final_v_os100m | 1.6503 | 1.6503 | -7.9792e-10 | 1.6 .. 1.7 | 0.049737 | 0.049737 | PASS |
| amp_reset_host | typ | t_1mv_s_os10m | 7.6287 | 7.6303 | 0.0015701 | <= 9.75 | 2.1213 | 2.1197 | PASS |
| amp_reset_host | typ | t_1mv_s_os100m | 9.1432 | 9.1416 | -0.0015876 | <= 12 | 2.8568 | 2.8584 | PASS |
| amp_reset_host | typ | final_v_os100m | 1.6507 | 1.6507 | 4.082e-08 | 1.6 .. 1.7 | 0.049257 | 0.049257 | PASS |
| amp_ac_junction | ff85 | g_mid_db | 59.789 | 59.789 | -2.3207e-05 | 59 .. 61 | 0.78902 | 0.789 | PASS |
| amp_ac_junction | ff85 | f_hi_hz | 975.12 | 975.11 | -0.0081859 | >= 300 | 675.12 | 675.11 | PASS |
| amp_ac_junction | ff85 | vout_v | 1.6511 | 1.6511 | 0 | 1.5 .. 1.8 | 0.14886 | 0.14886 | PASS |
| amp_ac_junction | ff85 | f_lo_hz | 0.095322 | 0.095322 | -8.8423e-08 | <= 0.5 | 0.40468 | 0.40468 | PASS |
| amp_ac_junction | ss-40 | g_mid_db | 59.816 | 59.816 | -2.4207e-05 | 59 .. 61 | 0.81645 | 0.81642 | PASS |
| amp_ac_junction | ss-40 | f_hi_hz | 409.06 | 409.06 | -0.0039591 | >= 300 | 109.06 | 109.06 | PASS |
| amp_ac_junction | ss-40 | vout_v | 1.6592 | 1.6592 | 0 | 1.5 .. 1.8 | 0.14077 | 0.14077 | PASS |
| amp_ac_junction | ss-40 | f_lo_hz | nan | nan | nan | nan allowed | - | - | PASS |
| amp_ac_junction | typ | g_mid_db | 59.81 | 59.81 | -2.3807e-05 | 59 .. 61 | 0.80975 | 0.80973 | PASS |
| amp_ac_junction | typ | f_hi_hz | 635.83 | 635.82 | -0.0061075 | >= 300 | 335.83 | 335.82 | PASS |
| amp_ac_junction | typ | vout_v | 1.6644 | 1.6644 | 0 | 1.5 .. 1.8 | 0.13559 | 0.13559 | PASS |
| amp_ac_junction | typ | f_lo_hz | nan | nan | nan | nan allowed | - | - | PASS |
| amp_reset_host_junction | ff85 | drift_mv_s_os10m | 11.265 | 11.267 | 0.0020322 | |x| <= 30 | 18.735 | 18.733 | PASS |
| amp_reset_host_junction | ss-40 | drift_mv_s_os10m | 8.6048 | 8.6038 | -0.0010408 | |x| <= 30 | 21.395 | 21.396 | PASS |
| amp_reset_host_junction | typ | drift_mv_s_os10m | 9.609 | 9.6075 | -0.0015078 | |x| <= 30 | 20.391 | 20.393 | PASS |

## pex_probe

| check | corner | value | without pad | with pad | delta | limit | margin without | margin with | result |
|---|---|---|---|---|---|---|---|---|---|
| amp_ac | ff85 | g_mid_db | 59.82 | 59.81 | -0.0099292 | |change| <= 0.3 | - | - | PASS |
| amp_ac | ff85 | f_lo_hz | 0.27565 | 0.27733 | 0.0016762 | <= 0.5 | 0.22435 | 0.22267 | PASS |
| amp_ac | ff85 | f_hi_hz | 972.5 | 974.06 | 1.5545 | >= 300 | 672.5 | 674.06 | PASS |
| amp_ac | ff85 | idd_ua | 118.81 | 118.81 | 0 | x / baseline 0.95 .. 1.05 | - | - | PASS |
| amp_ac | ff85 | vout_v | 1.651 | 1.651 | -1e-05 | 1.6 .. 1.7 | 0.04903 | 0.04904 | PASS |
| amp_ac | ff85 | hf_dev_db | 1.0739 | 1.0696 | -0.0043084 | <= 2 | 0.92608 | 0.93039 | PASS |
| amp_ac | ss-40 | g_mid_db | 59.844 | 59.834 | -0.01011 | |change| <= 0.3 | - | - | PASS |
| amp_ac | ss-40 | f_lo_hz | 0.28376 | 0.2837 | -6.2199e-05 | <= 0.5 | 0.21624 | 0.2163 | PASS |
| amp_ac | ss-40 | f_hi_hz | 408.49 | 409.39 | 0.89126 | >= 300 | 108.49 | 109.39 | PASS |
| amp_ac | ss-40 | idd_ua | 47.133 | 47.133 | -0.0001 | x / baseline 0.95 .. 1.05 | - | - | PASS |
| amp_ac | ss-40 | vout_v | 1.6501 | 1.6502 | 0.00012 | 1.6 .. 1.7 | 0.04993 | 0.04981 | PASS |
| amp_ac | ss-40 | hf_dev_db | 1.3234 | 1.3146 | -0.0087943 | <= 2 | 0.67657 | 0.68536 | PASS |
| amp_ac | typ | g_mid_db | 59.84 | 59.829 | -0.010135 | |change| <= 0.3 | - | - | PASS |
| amp_ac | typ | f_lo_hz | 0.24144 | 0.24206 | 0.00061473 | <= 0.5 | 0.25856 | 0.25794 | PASS |
| amp_ac | typ | f_hi_hz | 634.4 | 635.6 | 1.198 | >= 300 | 334.4 | 335.6 | PASS |
| amp_ac | typ | idd_ua | 74.43 | 74.43 | -0.0001 | x / baseline 0.95 .. 1.05 | - | - | PASS |
| amp_ac | typ | vout_v | 1.6506 | 1.6506 | 2e-05 | 1.6 .. 1.7 | 0.0494 | 0.04938 | PASS |
| amp_ac | typ | hf_dev_db | 1.0776 | 1.0688 | -0.0088287 | <= 2 | 0.92239 | 0.93122 | PASS |
| amp_noise | ff85 | noise_d8_post_uv | 2.1531 | 2.156 | 0.0028464 | <= 2.2 | 0.046855 | 0.044008 | PASS |
| amp_noise | ss-40 | noise_d8_post_uv | 1.7415 | 1.7436 | 0.0020844 | <= 2 | 0.25853 | 0.25644 | PASS |
| amp_noise | typ | noise_d8_post_uv | 1.9018 | 1.904 | 0.0021741 | <= 2 | 0.098172 | 0.095998 | PASS |
| amp_loop | ff85 | pm_deg | 436.63 | 436.62 | -0.013 | >= 60 | 376.63 | 376.62 | PASS |
| amp_loop | ss-40 | pm_deg | 441.13 | 441.13 | -0.003 | >= 60 | 381.13 | 381.13 | PASS |
| amp_loop | typ | pm_deg | 439.31 | 439.3 | -0.006 | >= 60 | 379.31 | 379.3 | PASS |
| amp_psrr | ff85 | supply_gain_50hz | 0.66495 | 0.66602 | 0.001067 | 0.32 .. 0.68 | 0.015047 | 0.01398 | PASS |
| amp_psrr | ss-40 | supply_gain_50hz | 0.61748 | 0.61885 | 0.001371 | 0.32 .. 0.68 | 0.062521 | 0.06115 | PASS |
| amp_psrr | typ | supply_gain_50hz | 0.63605 | 0.63724 | 0.001189 | 0.32 .. 0.68 | 0.043949 | 0.04276 | PASS |
| amp_thd | ff85 | thd_pct | 0.94376 | 0.93192 | -0.011838 | <= 4.5 | 3.5562 | 3.5681 | PASS |
| amp_thd | ff85 | out_max_v | 2.2053 | 2.2046 | -0.00067576 | >= 2.13 | 0.075295 | 0.074619 | PASS |
| amp_thd | ff85 | out_min_v | 1.2373 | 1.2375 | 0.00020916 | <= 1.25 | 0.01271 | 0.012501 | PASS |
| amp_thd | ff85 | gain_db | 59.751 | 59.742 | -0.0090729 | 58.8 .. 61 | 0.95109 | 0.94202 | PASS |
| amp_thd | ss-40 | thd_pct | 0.051824 | 0.051202 | -0.00062164 | <= 0.5 | 0.44818 | 0.4488 | PASS |
| amp_thd | ss-40 | out_max_v | 2.1632 | 2.1607 | -0.0025389 | >= 2.13 | 0.033241 | 0.030702 | PASS |
| amp_thd | ss-40 | out_min_v | 1.1783 | 1.177 | -0.0012194 | <= 1.19 | 0.011732 | 0.012951 | PASS |
| amp_thd | ss-40 | gain_db | 59.822 | 59.812 | -0.0099208 | 58.8 .. 61 | 1.0218 | 1.0118 | PASS |
| amp_thd | typ | thd_pct | 0.039765 | 0.039217 | -0.0005487 | <= 0.5 | 0.46023 | 0.46078 | PASS |
| amp_thd | typ | out_max_v | 2.1654 | 2.1632 | -0.0021468 | >= 2.13 | 0.035369 | 0.033222 | PASS |
| amp_thd | typ | out_min_v | 1.1803 | 1.1794 | -0.0008764 | <= 1.19 | 0.009744 | 0.01062 | PASS |
| amp_thd | typ | gain_db | 59.82 | 59.81 | -0.0099255 | 58.8 .. 61 | 1.0201 | 1.0102 | PASS |
| amp_pwrup | ff85 | err_1s_mv | 18.192 | 21.582 | 3.3893 | <= 50 | 31.808 | 28.418 | PASS |
| amp_pwrup | ss-40 | err_1s_mv | 19.798 | 26.319 | 6.5211 | <= 50 | 30.202 | 23.681 | PASS |
| amp_pwrup | typ | err_1s_mv | 30.265 | 33.893 | 3.6281 | <= 50 | 19.735 | 16.107 | PASS |
| amp_reset | ff85 | t_fs_ms_os10m | 1.6379 | 1.7396 | 0.10167 | x / baseline 0.7 .. 1.4 | - | - | PASS |
| amp_reset | ff85 | t_1mv_s_os0 | 5.5168 | 5.3286 | -0.18819 | <= 6.75 | 1.2332 | 1.4214 | PASS |
| amp_reset | ff85 | t_1mv_s_os1m | 5.5378 | nan | nan | no value | - | - | FAIL |
| amp_reset | ff85 | t_1mv_s_os10m | 8.5058 | 9.0006 | 0.49481 | <= 9.75 | 1.2442 | 0.74935 | PASS |
| amp_reset | ff85 | t_1mv_s_os100m | 7.521 | 10.952 | 3.4306 | <= 12 | 4.479 | 1.0484 | PASS |
| amp_reset | ff85 | final_v_os100m | 1.6511 | 1.6511 | -1.2885e-05 | 1.6 .. 1.7 | 0.048911 | 0.048924 | PASS |
| amp_reset | ff85 | final_v_os10m | 1.6512 | 1.6512 | 6.5491e-05 | 1.6 .. 1.7 | 0.048847 | 0.048781 | PASS |
| amp_reset | ss-40 | t_fs_ms_os10m | 5.8466 | 6.0077 | 0.16118 | x / baseline 0.7 .. 1.4 | - | - | PASS |
| amp_reset | ss-40 | t_1mv_s_os0 | 5.4639 | nan | nan | no value | - | - | FAIL |
| amp_reset | ss-40 | t_1mv_s_os1m | 5.4318 | nan | nan | no value | - | - | FAIL |
| amp_reset | ss-40 | t_1mv_s_os10m | 7.3302 | nan | nan | no value | - | - | FAIL |
| amp_reset | ss-40 | t_1mv_s_os100m | 8.258 | 22.017 | 13.759 | <= 12 | 3.742 | -10.017 | FAIL |
| amp_reset | ss-40 | final_v_os100m | 1.6503 | 1.6503 | -8.5259e-06 | 1.6 .. 1.7 | 0.049736 | 0.049745 | PASS |
| amp_reset | ss-40 | final_v_os10m | 1.6502 | 1.8233 | 0.17307 | 1.6 .. 1.7 | 0.049757 | -0.12331 | FAIL |
| amp_reset | typ | t_fs_ms_os10m | 3.0246 | 2.9734 | -0.051133 | x / baseline 0.7 .. 1.4 | - | - | PASS |
| amp_reset | typ | t_1mv_s_os0 | 5.5919 | nan | nan | no value | - | - | FAIL |
| amp_reset | typ | t_1mv_s_os1m | 5.5815 | nan | nan | no value | - | - | FAIL |
| amp_reset | typ | t_1mv_s_os10m | 8.5706 | nan | nan | no value | - | - | FAIL |
| amp_reset | typ | t_1mv_s_os100m | 9.4654 | 16.989 | 7.5237 | <= 12 | 2.5346 | -4.9891 | FAIL |
| amp_reset | typ | final_v_os100m | 1.6507 | 1.6507 | -1.2145e-05 | 1.6 .. 1.7 | 0.049257 | 0.049269 | PASS |
| amp_reset | typ | final_v_os10m | 1.6508 | 1.6934 | 0.042618 | 1.6 .. 1.7 | 0.049201 | 0.0065825 | PASS |
| amp_reset_host | ff85 | t_1mv_s_os10m | 7.4247 | 7.2485 | -0.17618 | <= 9.75 | 2.3253 | 2.5015 | PASS |
| amp_reset_host | ff85 | t_1mv_s_os100m | 9.1325 | 9.024 | -0.1085 | <= 12 | 2.8675 | 2.976 | PASS |
| amp_reset_host | ff85 | final_v_os100m | 1.6511 | 1.6511 | -1.2623e-05 | 1.6 .. 1.7 | 0.048911 | 0.048924 | PASS |
| amp_reset_host | ss-40 | t_1mv_s_os10m | 6.5139 | 6.4184 | -0.095505 | <= 9.75 | 3.2361 | 3.3316 | PASS |
| amp_reset_host | ss-40 | t_1mv_s_os100m | 7.8389 | 7.0729 | -0.76604 | <= 12 | 4.1611 | 4.9271 | PASS |
| amp_reset_host | ss-40 | final_v_os100m | 1.6503 | 1.6503 | -8.5662e-06 | 1.6 .. 1.7 | 0.049737 | 0.049745 | PASS |
| amp_reset_host | typ | t_1mv_s_os10m | 7.6287 | 7.5042 | -0.12453 | <= 9.75 | 2.1213 | 2.2458 | PASS |
| amp_reset_host | typ | t_1mv_s_os100m | 9.1432 | 9.0396 | -0.1036 | <= 12 | 2.8568 | 2.9604 | PASS |
| amp_reset_host | typ | final_v_os100m | 1.6507 | 1.6507 | -1.2312e-05 | 1.6 .. 1.7 | 0.049257 | 0.049269 | PASS |
| amp_ac_junction | ff85 | g_mid_db | 59.789 | 59.779 | -0.0096107 | 59 .. 61 | 0.78902 | 0.77941 | PASS |
| amp_ac_junction | ff85 | f_hi_hz | 975.12 | 977.29 | 2.1711 | >= 300 | 675.12 | 677.29 | PASS |
| amp_ac_junction | ff85 | vout_v | 1.6511 | 1.651 | -0.00014 | 1.5 .. 1.8 | 0.14886 | 0.149 | PASS |
| amp_ac_junction | ff85 | f_lo_hz | 0.095322 | 0.097888 | 0.0025658 | <= 0.5 | 0.40468 | 0.40211 | PASS |
| amp_ac_junction | ss-40 | g_mid_db | 59.816 | -1.9112 | -61.728 | 59 .. 61 | 0.81645 | -60.911 | FAIL |
| amp_ac_junction | ss-40 | f_hi_hz | 409.06 | 2.2208e+05 | 2.2167e+05 | >= 300 | 109.06 | 2.2178e+05 | PASS |
| amp_ac_junction | ss-40 | vout_v | 1.6592 | 0.402 | -1.2572 | 1.5 .. 1.8 | 0.14077 | -1.098 | FAIL |
| amp_ac_junction | ss-40 | f_lo_hz | nan | 10219 | nan | <= 0.5 | nan | -10219 | FAIL |
| amp_ac_junction | typ | g_mid_db | 59.81 | 28.967 | -30.843 | 59 .. 61 | 0.80975 | -30.033 | FAIL |
| amp_ac_junction | typ | f_hi_hz | 635.83 | 9393.2 | 8757.4 | >= 300 | 335.83 | 9093.2 | PASS |
| amp_ac_junction | typ | vout_v | 1.6644 | 0.80447 | -0.85994 | 1.5 .. 1.8 | 0.13559 | -0.69553 | FAIL |
| amp_ac_junction | typ | f_lo_hz | nan | 0.0025958 | nan | <= 0.5 | nan | 0.4974 | PASS |
| amp_reset_host_junction | ff85 | drift_mv_s_os10m | 11.265 | 11.819 | 0.55454 | |x| <= 30 | 18.735 | 18.181 | PASS |
| amp_reset_host_junction | ss-40 | drift_mv_s_os10m | 8.6048 | -1.3441 | -9.9489 | |x| <= 30 | 21.395 | 28.656 | PASS |
| amp_reset_host_junction | typ | drift_mv_s_os10m | 9.609 | -0.021476 | -9.6305 | |x| <= 30 | 20.391 | 29.979 | PASS |

## sch_open

| check | corner | value | without pad | with pad | delta | limit | margin without | margin with | result |
|---|---|---|---|---|---|---|---|---|---|
| amp_ac | ff85 | g_mid_db | 60.057 | 60.057 | 0.00026997 | |change| <= 0.3 | - | - | PASS |
| amp_ac | ff85 | f_lo_hz | 0.28137 | 0.2815 | 0.00013017 | <= 0.5 | 0.21863 | 0.2185 | PASS |
| amp_ac | ff85 | f_hi_hz | 997.67 | 997.63 | -0.043299 | >= 300 | 697.67 | 697.63 | PASS |
| amp_ac | ff85 | idd_ua | 118.81 | 118.81 | 0 | x / baseline 0.95 .. 1.05 | - | - | PASS |
| amp_ac | ff85 | vout_v | 1.651 | 1.651 | 1e-05 | 1.6 .. 1.7 | 0.04903 | 0.04902 | PASS |
| amp_ac | ff85 | hf_dev_db | 0 | 0.0016378 | 0.0016378 | <= 2 | 2 | 1.9984 | PASS |
| amp_ac | ss-40 | g_mid_db | 60.038 | 60.038 | -2.4407e-05 | |change| <= 0.3 | - | - | PASS |
| amp_ac | ss-40 | f_lo_hz | 0.2878 | 0.28779 | -1.3769e-06 | <= 0.5 | 0.2122 | 0.21221 | PASS |
| amp_ac | ss-40 | f_hi_hz | 422.1 | 422.1 | -0.0020845 | >= 300 | 122.1 | 122.1 | PASS |
| amp_ac | ss-40 | idd_ua | 47.133 | 47.133 | 0 | x / baseline 0.95 .. 1.05 | - | - | PASS |
| amp_ac | ss-40 | vout_v | 1.6502 | 1.6502 | 0 | 1.6 .. 1.7 | 0.0498 | 0.0498 | PASS |
| amp_ac | ss-40 | hf_dev_db | 0 | 0.0014103 | 0.0014103 | <= 2 | 2 | 1.9986 | PASS |
| amp_ac | typ | g_mid_db | 60.053 | 60.053 | -2.3707e-05 | |change| <= 0.3 | - | - | PASS |
| amp_ac | typ | f_lo_hz | 0.24588 | 0.24588 | -1.1245e-06 | <= 0.5 | 0.25412 | 0.25412 | PASS |
| amp_ac | typ | f_hi_hz | 653.5 | 653.5 | -0.0027451 | >= 300 | 353.5 | 353.5 | PASS |
| amp_ac | typ | idd_ua | 74.43 | 74.43 | 0 | x / baseline 0.95 .. 1.05 | - | - | PASS |
| amp_ac | typ | vout_v | 1.6506 | 1.6506 | 1e-05 | 1.6 .. 1.7 | 0.04937 | 0.04936 | PASS |
| amp_ac | typ | hf_dev_db | 0 | 0.0011631 | 0.0011631 | <= 2 | 2 | 1.9988 | PASS |
| amp_noise | ff85 | noise_d8_post_uv | 2.1392 | 2.1392 | 1.2268e-05 | <= 2.2 | 0.060793 | 0.06078 | PASS |
| amp_noise | ss-40 | noise_d8_post_uv | 1.7321 | 1.7321 | 1.9941e-05 | <= 2 | 0.26792 | 0.2679 | PASS |
| amp_noise | typ | noise_d8_post_uv | 1.8904 | 1.8904 | 0 | <= 2 | 0.10961 | 0.10961 | PASS |
| amp_loop | ff85 | pm_deg | 76.935 | 76.932 | -0.0025 | >= 60 | 16.935 | 16.932 | PASS |
| amp_loop | ss-40 | pm_deg | 81.375 | 81.374 | -0.0006 | >= 60 | 21.375 | 21.374 | PASS |
| amp_loop | typ | pm_deg | 79.573 | 79.572 | -0.0012 | >= 60 | 19.573 | 19.572 | PASS |
| amp_psrr | ff85 | supply_gain_50hz | 0.57988 | 0.58116 | 0.001278 | 0.32 .. 0.68 | 0.10012 | 0.098844 | PASS |
| amp_psrr | ss-40 | supply_gain_50hz | 0.56733 | 0.5688 | 0.001466 | 0.32 .. 0.68 | 0.11267 | 0.1112 | PASS |
| amp_psrr | typ | supply_gain_50hz | 0.57239 | 0.57378 | 0.001388 | 0.32 .. 0.68 | 0.10761 | 0.10622 | PASS |
| amp_thd | ff85 | thd_pct | 2.4027 | 2.4003 | -0.0023767 | <= 4.5 | 2.0973 | 2.0997 | PASS |
| amp_thd | ff85 | out_max_v | 2.1895 | 2.1896 | 4.526e-05 | >= 2.13 | 0.059511 | 0.059557 | PASS |
| amp_thd | ff85 | out_min_v | 1.2203 | 1.2203 | 1.351e-05 | <= 1.25 | 0.029697 | 0.029684 | PASS |
| amp_thd | ff85 | gain_db | 59.908 | 59.908 | 0.00012275 | 58.8 .. 61 | 1.0924 | 1.0923 | PASS |
| amp_thd | ss-40 | thd_pct | 0.056811 | 0.05681 | -2.2292e-07 | <= 0.5 | 0.44319 | 0.44319 | PASS |
| amp_thd | ss-40 | out_max_v | 2.1494 | 2.1495 | 3.074e-05 | >= 2.13 | 0.01942 | 0.01945 | PASS |
| amp_thd | ss-40 | out_min_v | 1.145 | 1.145 | 3.195e-05 | <= 1.19 | 0.04502 | 0.044988 | PASS |
| amp_thd | ss-40 | gain_db | 60.034 | 60.034 | -2.2582e-05 | 58.8 .. 61 | 0.96587 | 0.96589 | PASS |
| amp_thd | typ | thd_pct | 0.041988 | 0.041993 | 5.1814e-06 | <= 0.5 | 0.45801 | 0.45801 | PASS |
| amp_thd | typ | out_max_v | 2.1511 | 2.151 | -9.565e-05 | >= 2.13 | 0.02108 | 0.020985 | PASS |
| amp_thd | typ | out_min_v | 1.1449 | 1.1448 | -8.589e-05 | <= 1.19 | 0.045095 | 0.045181 | PASS |
| amp_thd | typ | gain_db | 60.049 | 60.049 | -2.1032e-05 | 58.8 .. 61 | 0.95059 | 0.95061 | PASS |
| amp_pwrup | ff85 | err_1s_mv | 0.09506 | 0.05707 | -0.03799 | <= 50 | 49.905 | 49.943 | PASS |
| amp_pwrup | ss-40 | err_1s_mv | 0.61939 | 0.6236 | 0.00421 | <= 50 | 49.381 | 49.376 | PASS |
| amp_pwrup | typ | err_1s_mv | 0.23517 | 0.26267 | 0.0275 | <= 50 | 49.765 | 49.737 | PASS |
| amp_reset | ff85 | t_fs_ms_os10m | 1.6282 | 1.6278 | -0.000375 | x / baseline 0.7 .. 1.4 | - | - | PASS |
| amp_reset | ff85 | t_1mv_s_os0 | 2.9885 | 2.7438 | -0.24474 | <= 6.75 | 3.7615 | 4.0062 | PASS |
| amp_reset | ff85 | t_1mv_s_os1m | 2.3341 | 2.023 | -0.31109 | <= 6.75 | 4.4159 | 4.727 | PASS |
| amp_reset | ff85 | t_1mv_s_os10m | 4.3769 | 4.8171 | 0.4402 | <= 9.75 | 5.3731 | 4.9329 | PASS |
| amp_reset | ff85 | t_1mv_s_os100m | 5.4605 | 7.0056 | 1.5451 | <= 12 | 6.5395 | 4.9944 | PASS |
| amp_reset | ff85 | final_v_os100m | 1.6511 | 1.6511 | -3.9683e-05 | 1.6 .. 1.7 | 0.048876 | 0.048915 | PASS |
| amp_reset | ff85 | final_v_os10m | 1.651 | 1.651 | 5.9869e-06 | 1.6 .. 1.7 | 0.049008 | 0.049002 | PASS |
| amp_reset | ss-40 | t_fs_ms_os10m | 5.7918 | 5.9035 | 0.11172 | x / baseline 0.7 .. 1.4 | - | - | PASS |
| amp_reset | ss-40 | t_1mv_s_os0 | 0.6545 | 0.69958 | 0.045075 | <= 6.75 | 6.0955 | 6.0504 | PASS |
| amp_reset | ss-40 | t_1mv_s_os1m | 0.39849 | 1.9212 | 1.5227 | <= 6.75 | 6.3515 | 4.8288 | PASS |
| amp_reset | ss-40 | t_1mv_s_os10m | 2.7357 | 2.9386 | 0.20291 | <= 9.75 | 7.0143 | 6.8114 | PASS |
| amp_reset | ss-40 | t_1mv_s_os100m | 6.8473 | 6.1797 | -0.66762 | <= 12 | 5.1527 | 5.8203 | PASS |
| amp_reset | ss-40 | final_v_os100m | 1.6503 | 1.6503 | -4.4605e-06 | 1.6 .. 1.7 | 0.049717 | 0.049721 | PASS |
| amp_reset | ss-40 | final_v_os10m | 1.6502 | 1.6502 | -5.1889e-06 | 1.6 .. 1.7 | 0.049791 | 0.049796 | PASS |
| amp_reset | typ | t_fs_ms_os10m | 3.0966 | 3.0845 | -0.012033 | x / baseline 0.7 .. 1.4 | - | - | PASS |
| amp_reset | typ | t_1mv_s_os0 | 1.7995 | 1.4824 | -0.31709 | <= 6.75 | 4.9505 | 5.2676 | PASS |
| amp_reset | typ | t_1mv_s_os1m | 1.3957 | 0.21288 | -1.1829 | <= 6.75 | 5.3543 | 6.5371 | PASS |
| amp_reset | typ | t_1mv_s_os10m | 3.8016 | 3.72 | -0.081556 | <= 9.75 | 5.9484 | 6.03 | PASS |
| amp_reset | typ | t_1mv_s_os100m | 8.4225 | 7.8839 | -0.53866 | <= 12 | 3.5775 | 4.1161 | PASS |
| amp_reset | typ | final_v_os100m | 1.6507 | 1.6507 | 3.9098e-06 | 1.6 .. 1.7 | 0.049258 | 0.049254 | PASS |
| amp_reset | typ | final_v_os10m | 1.6507 | 1.6507 | -3.3552e-06 | 1.6 .. 1.7 | 0.049341 | 0.049345 | PASS |
| amp_reset_host | ff85 | t_1mv_s_os10m | 3.7084 | 3.7197 | 0.011336 | <= 9.75 | 6.0416 | 6.0303 | PASS |
| amp_reset_host | ff85 | t_1mv_s_os100m | 8.0417 | 8.054 | 0.012261 | <= 12 | 3.9583 | 3.946 | PASS |
| amp_reset_host | ff85 | final_v_os100m | 1.6511 | 1.6511 | -1.1732e-07 | 1.6 .. 1.7 | 0.048908 | 0.048909 | PASS |
| amp_reset_host | ss-40 | t_1mv_s_os10m | 2.8915 | 2.952 | 0.060546 | <= 9.75 | 6.8585 | 6.798 | PASS |
| amp_reset_host | ss-40 | t_1mv_s_os100m | 6.5169 | 7.0659 | 0.549 | <= 12 | 5.4831 | 4.9341 | PASS |
| amp_reset_host | ss-40 | final_v_os100m | 1.6503 | 1.6503 | -3.8884e-07 | 1.6 .. 1.7 | 0.049732 | 0.049733 | PASS |
| amp_reset_host | typ | t_1mv_s_os10m | 3.8841 | 3.8827 | -0.0014768 | <= 9.75 | 5.8659 | 5.8673 | PASS |
| amp_reset_host | typ | t_1mv_s_os100m | 8.0065 | 8.015 | 0.0085279 | <= 12 | 3.9935 | 3.985 | PASS |
| amp_reset_host | typ | final_v_os100m | 1.6507 | 1.6507 | 9.1252e-08 | 1.6 .. 1.7 | 0.049254 | 0.049254 | PASS |
| amp_ac_junction | ff85 | g_mid_db | 60.051 | 60.051 | -2.5025e-05 | 59 .. 61 | 0.94878 | 0.94881 | PASS |
| amp_ac_junction | ff85 | f_hi_hz | 997.59 | 997.58 | -0.0058554 | >= 300 | 697.59 | 697.58 | PASS |
| amp_ac_junction | ff85 | vout_v | 1.6517 | 1.6516 | -0.00011 | 1.5 .. 1.8 | 0.14827 | 0.14838 | PASS |
| amp_ac_junction | ff85 | f_lo_hz | 0.070028 | 0.070063 | 3.4953e-05 | <= 0.5 | 0.42997 | 0.42994 | PASS |
| amp_ac_junction | ss-40 | g_mid_db | 60.032 | 60.032 | 6.7212e-05 | 59 .. 61 | 0.96758 | 0.96751 | PASS |
| amp_ac_junction | ss-40 | f_hi_hz | 421.73 | 421.74 | 0.0043336 | >= 300 | 121.73 | 121.74 | PASS |
| amp_ac_junction | ss-40 | vout_v | 1.6367 | 1.6825 | 0.04574 | 1.5 .. 1.8 | 0.13675 | 0.11751 | PASS |
| amp_ac_junction | ss-40 | f_lo_hz | nan | nan | nan | nan allowed | - | - | PASS |
| amp_ac_junction | typ | g_mid_db | 60.047 | 60.047 | 0.00026487 | 59 .. 61 | 0.95317 | 0.95291 | PASS |
| amp_ac_junction | typ | f_hi_hz | 653.27 | 653.24 | -0.02511 | >= 300 | 353.27 | 353.24 | PASS |
| amp_ac_junction | typ | vout_v | 1.6137 | 1.6783 | 0.06464 | 1.5 .. 1.8 | 0.11369 | 0.12167 | PASS |
| amp_ac_junction | typ | f_lo_hz | nan | nan | nan | nan allowed | - | - | PASS |
| amp_reset_host_junction | ff85 | drift_mv_s_os10m | 1.5242 | 1.5264 | 0.0022182 | |x| <= 30 | 28.476 | 28.474 | PASS |
| amp_reset_host_junction | ss-40 | drift_mv_s_os10m | 8.6245 | 8.6598 | 0.035348 | |x| <= 30 | 21.376 | 21.34 | PASS |
| amp_reset_host_junction | typ | drift_mv_s_os10m | 9.5386 | 9.5131 | -0.025436 | |x| <= 30 | 20.461 | 20.487 | PASS |

## sch_probe

| check | corner | value | without pad | with pad | delta | limit | margin without | margin with | result |
|---|---|---|---|---|---|---|---|---|---|
| amp_ac | ff85 | g_mid_db | 60.057 | 60.047 | -0.009681 | |change| <= 0.3 | - | - | PASS |
| amp_ac | ff85 | f_lo_hz | 0.28137 | 0.28323 | 0.0018608 | <= 0.5 | 0.21863 | 0.21677 | PASS |
| amp_ac | ff85 | f_hi_hz | 997.67 | 998.61 | 0.94414 | >= 300 | 697.67 | 698.61 | PASS |
| amp_ac | ff85 | idd_ua | 118.81 | 118.81 | 0 | x / baseline 0.95 .. 1.05 | - | - | PASS |
| amp_ac | ff85 | vout_v | 1.651 | 1.6509 | -2e-05 | 1.6 .. 1.7 | 0.04903 | 0.04905 | PASS |
| amp_ac | ff85 | hf_dev_db | 0 | 0.011719 | 0.011719 | <= 2 | 2 | 1.9883 | PASS |
| amp_ac | ss-40 | g_mid_db | 60.038 | 60.028 | -0.009851 | |change| <= 0.3 | - | - | PASS |
| amp_ac | ss-40 | f_lo_hz | 0.2878 | 0.28853 | 0.00072963 | <= 0.5 | 0.2122 | 0.21147 | PASS |
| amp_ac | ss-40 | f_hi_hz | 422.1 | 422.94 | 0.83524 | >= 300 | 122.1 | 122.94 | PASS |
| amp_ac | ss-40 | idd_ua | 47.133 | 47.133 | -0.0001 | x / baseline 0.95 .. 1.05 | - | - | PASS |
| amp_ac | ss-40 | vout_v | 1.6502 | 1.6502 | -1e-05 | 1.6 .. 1.7 | 0.0498 | 0.04981 | PASS |
| amp_ac | ss-40 | hf_dev_db | 0 | 0.012901 | 0.012901 | <= 2 | 2 | 1.9871 | PASS |
| amp_ac | typ | g_mid_db | 60.053 | 60.043 | -0.0098547 | |change| <= 0.3 | - | - | PASS |
| amp_ac | typ | f_lo_hz | 0.24588 | 0.24663 | 0.00075022 | <= 0.5 | 0.25412 | 0.25337 | PASS |
| amp_ac | typ | f_hi_hz | 653.5 | 654.47 | 0.96654 | >= 300 | 353.5 | 354.47 | PASS |
| amp_ac | typ | idd_ua | 74.43 | 74.43 | -0.0001 | x / baseline 0.95 .. 1.05 | - | - | PASS |
| amp_ac | typ | vout_v | 1.6506 | 1.6506 | 1e-05 | 1.6 .. 1.7 | 0.04937 | 0.04936 | PASS |
| amp_ac | typ | hf_dev_db | 0 | 0.011591 | 0.011591 | <= 2 | 2 | 1.9884 | PASS |
| amp_noise | ff85 | noise_d8_post_uv | 2.1392 | 2.1419 | 0.0027345 | <= 2.2 | 0.060793 | 0.058058 | PASS |
| amp_noise | ss-40 | noise_d8_post_uv | 1.7321 | 1.7341 | 0.0019878 | <= 2 | 0.26792 | 0.26594 | PASS |
| amp_noise | typ | noise_d8_post_uv | 1.8904 | 1.8925 | 0.0021341 | <= 2 | 0.10961 | 0.10747 | PASS |
| amp_loop | ff85 | pm_deg | 76.935 | 76.922 | -0.0127 | >= 60 | 16.935 | 16.922 | PASS |
| amp_loop | ss-40 | pm_deg | 81.375 | 81.372 | -0.003 | >= 60 | 21.375 | 21.372 | PASS |
| amp_loop | typ | pm_deg | 79.573 | 79.567 | -0.0058 | >= 60 | 19.573 | 19.567 | PASS |
| amp_psrr | ff85 | supply_gain_50hz | 0.57988 | 0.5812 | 0.001324 | 0.32 .. 0.68 | 0.10012 | 0.098798 | PASS |
| amp_psrr | ss-40 | supply_gain_50hz | 0.56733 | 0.5688 | 0.00147 | 0.32 .. 0.68 | 0.11267 | 0.1112 | PASS |
| amp_psrr | typ | supply_gain_50hz | 0.57239 | 0.57378 | 0.001393 | 0.32 .. 0.68 | 0.10761 | 0.10622 | PASS |
| amp_thd | ff85 | thd_pct | 2.4027 | 2.3878 | -0.01496 | <= 4.5 | 2.0973 | 2.1122 | PASS |
| amp_thd | ff85 | out_max_v | 2.1895 | 2.1887 | -0.00078777 | >= 2.13 | 0.059511 | 0.058724 | PASS |
| amp_thd | ff85 | out_min_v | 1.2203 | 1.2204 | 0.00010566 | <= 1.25 | 0.029697 | 0.029592 | PASS |
| amp_thd | ff85 | gain_db | 59.908 | 59.899 | -0.00885 | 58.8 .. 61 | 1.0924 | 1.0987 | PASS |
| amp_thd | ss-40 | thd_pct | 0.056811 | 0.057163 | 0.00035213 | <= 0.5 | 0.44319 | 0.44284 | PASS |
| amp_thd | ss-40 | out_max_v | 2.1494 | 2.1466 | -0.0028142 | >= 2.13 | 0.01942 | 0.016605 | PASS |
| amp_thd | ss-40 | out_min_v | 1.145 | 1.1435 | -0.0014586 | <= 1.19 | 0.04502 | 0.046479 | PASS |
| amp_thd | ss-40 | gain_db | 60.034 | 60.024 | -0.0098509 | 58.8 .. 61 | 0.96587 | 0.97572 | PASS |
| amp_thd | typ | thd_pct | 0.041988 | 0.042233 | 0.00024505 | <= 0.5 | 0.45801 | 0.45777 | PASS |
| amp_thd | typ | out_max_v | 2.1511 | 2.1486 | -0.0024908 | >= 2.13 | 0.02108 | 0.01859 | PASS |
| amp_thd | typ | out_min_v | 1.1449 | 1.1437 | -0.0011682 | <= 1.19 | 0.045095 | 0.046263 | PASS |
| amp_thd | typ | gain_db | 60.049 | 60.04 | -0.0098564 | 58.8 .. 61 | 0.95059 | 0.96045 | PASS |
| amp_pwrup | ff85 | err_1s_mv | 0.09506 | 2.5398 | 2.4448 | <= 50 | 49.905 | 47.46 | PASS |
| amp_pwrup | ss-40 | err_1s_mv | 0.61939 | 2.7749 | 2.1556 | <= 50 | 49.381 | 47.225 | PASS |
| amp_pwrup | typ | err_1s_mv | 0.23517 | 2.9564 | 2.7213 | <= 50 | 49.765 | 47.044 | PASS |
| amp_reset | ff85 | t_fs_ms_os10m | 1.6282 | 1.6996 | 0.071416 | x / baseline 0.7 .. 1.4 | - | - | PASS |
| amp_reset | ff85 | t_1mv_s_os0 | 2.9885 | 5.6516 | 2.6631 | <= 6.75 | 3.7615 | 1.0984 | PASS |
| amp_reset | ff85 | t_1mv_s_os1m | 2.3341 | 5.5822 | 3.2481 | <= 6.75 | 4.4159 | 1.1678 | PASS |
| amp_reset | ff85 | t_1mv_s_os10m | 4.3769 | 9.4335 | 5.0566 | <= 9.75 | 5.3731 | 0.31655 | PASS |
| amp_reset | ff85 | t_1mv_s_os100m | 5.4605 | 10.438 | 4.9771 | <= 12 | 6.5395 | 1.5624 | PASS |
| amp_reset | ff85 | final_v_os100m | 1.6511 | 1.6511 | -4.4507e-05 | 1.6 .. 1.7 | 0.048876 | 0.04892 | PASS |
| amp_reset | ff85 | final_v_os10m | 1.651 | 1.6513 | 0.0003059 | 1.6 .. 1.7 | 0.049008 | 0.048702 | PASS |
| amp_reset | ss-40 | t_fs_ms_os10m | 5.7918 | 5.8201 | 0.02837 | x / baseline 0.7 .. 1.4 | - | - | PASS |
| amp_reset | ss-40 | t_1mv_s_os0 | 0.6545 | nan | nan | no value | - | - | FAIL |
| amp_reset | ss-40 | t_1mv_s_os1m | 0.39849 | nan | nan | no value | - | - | FAIL |
| amp_reset | ss-40 | t_1mv_s_os10m | 2.7357 | nan | nan | no value | - | - | FAIL |
| amp_reset | ss-40 | t_1mv_s_os100m | 6.8473 | 20.78 | 13.932 | <= 12 | 5.1527 | -8.7796 | FAIL |
| amp_reset | ss-40 | final_v_os100m | 1.6503 | 1.6503 | -2.5564e-05 | 1.6 .. 1.7 | 0.049717 | 0.049742 | PASS |
| amp_reset | ss-40 | final_v_os10m | 1.6502 | 1.7933 | 0.14311 | 1.6 .. 1.7 | 0.049791 | -0.093323 | FAIL |
| amp_reset | typ | t_fs_ms_os10m | 3.0966 | 2.9438 | -0.15283 | x / baseline 0.7 .. 1.4 | - | - | PASS |
| amp_reset | typ | t_1mv_s_os0 | 1.7995 | nan | nan | no value | - | - | FAIL |
| amp_reset | typ | t_1mv_s_os1m | 1.3957 | nan | nan | no value | - | - | FAIL |
| amp_reset | typ | t_1mv_s_os10m | 3.8016 | nan | nan | no value | - | - | FAIL |
| amp_reset | typ | t_1mv_s_os100m | 8.4225 | 16.929 | 8.5065 | <= 12 | 3.5775 | -4.929 | FAIL |
| amp_reset | typ | final_v_os100m | 1.6507 | 1.6507 | -7.6457e-06 | 1.6 .. 1.7 | 0.049258 | 0.049265 | PASS |
| amp_reset | typ | final_v_os10m | 1.6507 | 1.6601 | 0.0094528 | 1.6 .. 1.7 | 0.049341 | 0.039889 | PASS |
| amp_reset_host | ff85 | t_1mv_s_os10m | 3.7084 | 1.0699 | -2.6385 | <= 9.75 | 6.0416 | 8.6801 | PASS |
| amp_reset_host | ff85 | t_1mv_s_os100m | 8.0417 | 7.9363 | -0.1054 | <= 12 | 3.9583 | 4.0637 | PASS |
| amp_reset_host | ff85 | final_v_os100m | 1.6511 | 1.6511 | -1.249e-05 | 1.6 .. 1.7 | 0.048908 | 0.048921 | PASS |
| amp_reset_host | ss-40 | t_1mv_s_os10m | 2.8915 | 1.1527 | -1.7388 | <= 9.75 | 6.8585 | 8.5973 | PASS |
| amp_reset_host | ss-40 | t_1mv_s_os100m | 6.5169 | 6.4223 | -0.0946 | <= 12 | 5.4831 | 5.5777 | PASS |
| amp_reset_host | ss-40 | final_v_os100m | 1.6503 | 1.6503 | -9.3405e-06 | 1.6 .. 1.7 | 0.049732 | 0.049742 | PASS |
| amp_reset_host | typ | t_1mv_s_os10m | 3.8841 | 1.1966 | -2.6875 | <= 9.75 | 5.8659 | 8.5534 | PASS |
| amp_reset_host | typ | t_1mv_s_os100m | 8.0065 | 7.9047 | -0.10181 | <= 12 | 3.9935 | 4.0953 | PASS |
| amp_reset_host | typ | final_v_os100m | 1.6507 | 1.6507 | -1.1475e-05 | 1.6 .. 1.7 | 0.049254 | 0.049265 | PASS |
| amp_ac_junction | ff85 | g_mid_db | 60.051 | 60.041 | -0.009958 | 59 .. 61 | 0.94878 | 0.95874 | PASS |
| amp_ac_junction | ff85 | f_hi_hz | 997.59 | 998.9 | 1.3171 | >= 300 | 697.59 | 698.9 | PASS |
| amp_ac_junction | ff85 | vout_v | 1.6517 | 1.6511 | -0.00064 | 1.5 .. 1.8 | 0.14827 | 0.14891 | PASS |
| amp_ac_junction | ff85 | f_lo_hz | 0.070028 | 0.073738 | 0.0037101 | <= 0.5 | 0.42997 | 0.42626 | PASS |
| amp_ac_junction | ss-40 | g_mid_db | 60.032 | -3.8859 | -63.918 | 59 .. 61 | 0.96758 | -62.886 | FAIL |
| amp_ac_junction | ss-40 | f_hi_hz | 421.73 | 2.3466e+05 | 2.3424e+05 | >= 300 | 121.73 | 2.3436e+05 | PASS |
| amp_ac_junction | ss-40 | vout_v | 1.6367 | 0.39967 | -1.2371 | 1.5 .. 1.8 | 0.13675 | -1.1003 | FAIL |
| amp_ac_junction | ss-40 | f_lo_hz | nan | 10753 | nan | <= 0.5 | nan | -10752 | FAIL |
| amp_ac_junction | typ | g_mid_db | 60.047 | 26.595 | -33.452 | 59 .. 61 | 0.95317 | -32.405 | FAIL |
| amp_ac_junction | typ | f_hi_hz | 653.27 | 11031 | 10377 | >= 300 | 353.27 | 10731 | PASS |
| amp_ac_junction | typ | vout_v | 1.6137 | 0.79702 | -0.81667 | 1.5 .. 1.8 | 0.11369 | -0.70298 | FAIL |
| amp_ac_junction | typ | f_lo_hz | nan | 0.0027268 | nan | <= 0.5 | nan | 0.49727 | PASS |
| amp_reset_host_junction | ff85 | drift_mv_s_os10m | 1.5242 | 0.9502 | -0.57396 | |x| <= 30 | 28.476 | 29.05 | PASS |
| amp_reset_host_junction | ss-40 | drift_mv_s_os10m | 8.6245 | -1.635 | -10.259 | |x| <= 30 | 21.376 | 28.365 | PASS |
| amp_reset_host_junction | typ | drift_mv_s_os10m | 9.5386 | -0.51941 | -10.058 | |x| <= 30 | 20.461 | 29.481 | PASS |

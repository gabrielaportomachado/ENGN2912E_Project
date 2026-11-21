# compare.py L1b: AFE/layout/sim/post against AFE/layout/baseline

| check | corner | value | baseline | post-layout | change | limit | result |
|---|---|---|---|---|---|---|---|
| adc_codes | ff-40 | code_offset_lsb | -36.1 | -38.1 | -2 | |change| <= 15 | PASS |
| adc_codes | ff-40 | inl_lo_lsb | 0.27801 | 1.3238 | +1.046 | <= 1 | FAIL |
| adc_codes | ff-40 | inl_code_lo_lsb | 0.6218 | 1.3416 | +0.7198 | <= 1.5 | PASS |
| adc_codes | ff-40 | top_2v15_lsb | 2.9759 | 1.8106 | -1.165 | change <= +1.5 | PASS |
| adc_codes | ff-40 | top_2v10_lsb | 2.0037 | -0.014477 | -2.018 |  |  |
| adc_codes | ff-40 | alpha | 0.98048 | 0.97555 | -0.004929 | |change| <= 0.02 | PASS |
| adc_codes | ff-40 | gain_err_pct | -0.018341 | 0.18794 | +0.2063 | -0.5 .. 0.5 | PASS |
| adc_codes | ff-40 | unresolved | 0 | 0 | +0 | <= 0 | PASS |
| adc_codes | ff-40 | failed | 0 | 0 | +0 | <= 0 | PASS |
| adc_codes | ff-40 | first_conv_dlsb | 0.24041 | 0.29751 | +0.0571 |  |  |
| adc_codes | ff85 | code_offset_lsb | -40.1 | -42.4 | -2.3 | |change| <= 15 | PASS |
| adc_codes | ff85 | inl_lo_lsb | 1.5656 | 2.0849 | +0.5193 | <= 2.5 | PASS |
| adc_codes | ff85 | inl_code_lo_lsb | 1.0697 | 1.7697 | +0.7 | <= 2 | PASS |
| adc_codes | ff85 | top_2v15_lsb | 4.427 | 3.7148 | -0.7121 | change <= +1.5 | PASS |
| adc_codes | ff85 | top_2v10_lsb | 3.5135 | 1.2373 | -2.276 |  |  |
| adc_codes | ff85 | alpha | 0.9801 | 0.97513 | -0.004968 | |change| <= 0.02 | PASS |
| adc_codes | ff85 | gain_err_pct | -0.10831 | -0.0093253 | +0.09898 | -0.5 .. 0.5 | PASS |
| adc_codes | ff85 | unresolved | 0 | 0 | +0 | <= 0 | PASS |
| adc_codes | ff85 | failed | 0 | 0 | +0 | <= 0 | PASS |
| adc_codes | ff85 | first_conv_dlsb | 0.023873 | 0.033236 | +0.009362 |  |  |
| adc_codes | ss-40 | code_offset_lsb | -22 | -23.5 | -1.5 | |change| <= 15 | PASS |
| adc_codes | ss-40 | inl_lo_lsb | 0.15968 | 1.1901 | +1.03 | <= 1 | FAIL |
| adc_codes | ss-40 | inl_code_lo_lsb | 0.31894 | 1.059 | +0.74 | <= 1.5 | PASS |
| adc_codes | ss-40 | top_2v15_lsb | 0.13177 | -0.56366 | -0.6954 | change <= +1.5 | PASS |
| adc_codes | ss-40 | top_2v10_lsb | 0.011686 | -1.3809 | -1.393 |  |  |
| adc_codes | ss-40 | alpha | 0.98191 | 0.97785 | -0.004066 | |change| <= 0.02 | PASS |
| adc_codes | ss-40 | gain_err_pct | -0.0021655 | 0.12976 | +0.1319 | -0.5 .. 0.5 | PASS |
| adc_codes | ss-40 | unresolved | 0 | 0 | +0 | <= 0 | PASS |
| adc_codes | ss-40 | failed | 0 | 0 | +0 | <= 0 | PASS |
| adc_codes | ss-40 | first_conv_dlsb | 0.31163 | 0.37468 | +0.06305 |  |  |
| adc_codes | ss125 | code_offset_lsb | -26.4 | -28.5 | -2.1 | |change| <= 15 | PASS |
| adc_codes | ss125 | inl_lo_lsb | 0.13219 | 1.2568 | +1.125 | <= 1 | FAIL |
| adc_codes | ss125 | inl_code_lo_lsb | 0.25051 | 1.059 | +0.8085 | <= 1.5 | PASS |
| adc_codes | ss125 | top_2v15_lsb | 1.5782 | 0.93801 | -0.6402 | change <= +1.5 | PASS |
| adc_codes | ss125 | top_2v10_lsb | 0.87123 | -0.85107 | -1.722 |  |  |
| adc_codes | ss125 | alpha | 0.98166 | 0.97754 | -0.004117 | |change| <= 0.02 | PASS |
| adc_codes | ss125 | gain_err_pct | -0.0082461 | 0.07418 | +0.08243 | -0.5 .. 0.5 | PASS |
| adc_codes | ss125 | unresolved | 0 | 0 | +0 | <= 0 | PASS |
| adc_codes | ss125 | failed | 0 | 0 | +0 | <= 0 | PASS |
| adc_codes | ss125 | first_conv_dlsb | 0.062637 | 0.30635 | +0.2437 |  |  |
| adc_codes | typ | code_offset_lsb | -30.2 | -32.7 | -2.5 | |change| <= 15 | PASS |
| adc_codes | typ | inl_lo_lsb | 0.11853 | 1.148 | +1.029 | <= 1 | FAIL |
| adc_codes | typ | inl_code_lo_lsb | 0.51894 | 0.85897 | +0.34 | <= 1.5 | PASS |
| adc_codes | typ | top_2v15_lsb | 2.063 | 1.0314 | -1.032 | change <= +1.5 | PASS |
| adc_codes | typ | top_2v10_lsb | 1.1851 | -0.63508 | -1.82 |  |  |
| adc_codes | typ | alpha | 0.98121 | 0.97674 | -0.00447 | |change| <= 0.02 | PASS |
| adc_codes | typ | gain_err_pct | -0.0079357 | 0.17666 | +0.1846 | -0.5 .. 0.5 | PASS |
| adc_codes | typ | unresolved | 0 | 0 | +0 | <= 0 | PASS |
| adc_codes | typ | failed | 0 | 0 | +0 | <= 0 | PASS |
| adc_codes | typ | first_conv_dlsb | 0.35929 | 0.41063 | +0.05135 |  |  |
| adc_steps | ff85 | step_1536_lsb | -1.0796 | 1.2802 | +2.36 | |x| <= 2 | PASS |
| adc_steps | ff85 | step_2048_lsb | 1.5454 | 3.9204 | +2.375 | |x| <= 2 | FAIL |
| adc_steps | ff85 | step_2112_lsb | 0.17043 | -0.32957 | -0.5 | |x| <= 0.5 | PASS |
| adc_steps | ss-40 | step_1536_lsb | -1.0796 | 0.92043 | +2 | |x| <= 2 | PASS |
| adc_steps | ss-40 | step_2048_lsb | 0.42043 | 2.1704 | +1.75 | |x| <= 2 | FAIL |
| adc_steps | ss-40 | step_2112_lsb | 0.17043 | -0.079568 | -0.25 | |x| <= 0.5 | PASS |
| adc_steps | typ | step_1536_lsb | -1.0796 | 1.1691 | +2.249 | |x| <= 2 | PASS |
| adc_steps | typ | step_2048_lsb | 1.2954 | 2.9204 | +1.625 | |x| <= 2 | FAIL |
| adc_steps | typ | step_2112_lsb | 0.045432 | -0.32957 | -0.375 | |x| <= 0.5 | PASS |
| adc_timing | ff-40 | settle_worst_lsb | 0.098028 | 0.14426 | +0.04623 | <= 0.5 | PASS |
| adc_timing | ff-40 | late | 0 | 0 | +0 | <= 0 | PASS |
| adc_timing | ff-40 | failed | 0 | 0 | +0 | <= 0 | PASS |
| adc_timing | ff-40 | td_max_ns | 0.94645 | 1.3325 | +0.386 |  |  |
| adc_timing | ff-40 | settle_trial1_lsb | 0.0058649 | 0.010165 | +0.0043 |  |  |
| adc_timing | ff-40 | settle_trial2_lsb | 0.098028 | 0.14426 | +0.04623 |  |  |
| adc_timing | ff-40 | settle_top_lsb | 1.4548 | 1.4091 | -0.04578 | change <= +0.5 | PASS |
| adc_timing | ss-40x | settle_worst_lsb | 0.64952 | 0.79394 | +0.1444 | <= 1 | PASS |
| adc_timing | ss-40x | late | 0 | 0 | +0 | <= 0 | PASS |
| adc_timing | ss-40x | failed | 0 | 0 | +0 | <= 0 | PASS |
| adc_timing | ss-40x | td_max_ns | 1.5485 | 2.256 | +0.7076 |  |  |
| adc_timing | ss-40x | settle_trial1_lsb | 0.64952 | 0.79394 | +0.1444 |  |  |
| adc_timing | ss-40x | settle_trial2_lsb | 0.42611 | 0.57119 | +0.1451 |  |  |
| adc_timing | ss-40x | settle_top_lsb | 0.74646 | 0.86192 | +0.1155 | change <= +0.5 | PASS |
| adc_timing | ss125 | settle_worst_lsb | 0.11297 | 0.1094 | -0.003574 | <= 0.5 | PASS |
| adc_timing | ss125 | late | 0 | 0 | +0 | <= 0 | PASS |
| adc_timing | ss125 | failed | 0 | 0 | +0 | <= 0 | PASS |
| adc_timing | ss125 | td_max_ns | 2.643 | 3.7056 | +1.063 |  |  |
| adc_timing | ss125 | settle_trial1_lsb | 0.0013209 | 0.001326 | +5.187e-06 |  |  |
| adc_timing | ss125 | settle_trial2_lsb | 0.11297 | 0.1094 | -0.003574 |  |  |
| adc_timing | ss125 | settle_top_lsb | 0.279 | 0.2684 | -0.01059 | change <= +0.5 | PASS |
| adc_timing | typ | settle_worst_lsb | 0.073943 | 0.10227 | +0.02833 | <= 0.5 | PASS |
| adc_timing | typ | late | 0 | 0 | +0 | <= 0 | PASS |
| adc_timing | typ | failed | 0 | 0 | +0 | <= 0 | PASS |
| adc_timing | typ | td_max_ns | 1.5331 | 2.0958 | +0.5627 |  |  |
| adc_timing | typ | settle_trial1_lsb | 0.0012661 | 0.00049581 | -0.0007703 |  |  |
| adc_timing | typ | settle_trial2_lsb | 0.073943 | 0.10227 | +0.02833 |  |  |
| adc_timing | typ | settle_top_lsb | 0.65249 | 0.60596 | -0.04652 | change <= +0.5 | PASS |
| adc_overlap | ff-40 | dt_max_lsb | 0.0041409 | 0.0029524 | -0.001189 | <= 0.2 | PASS |
| adc_overlap | ff-40 | dcode_max | 0 | 0 | +0 | <= 1 | PASS |
| adc_overlap | typ | dt_max_lsb | 0.0036841 | 0.0022451 | -0.001439 | <= 0.2 | PASS |
| adc_overlap | typ | dcode_max | 0 | 0 | +0 | <= 1 | PASS |

RESULT compare L1b: FAIL  (62 PASS, 0 WARN, 7 FAIL, 0 missing)

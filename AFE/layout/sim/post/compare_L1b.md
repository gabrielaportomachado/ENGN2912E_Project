# compare.py L1b: AFE/layout/sim/post against AFE/layout/baseline

| check | corner | value | baseline | post-layout | change | limit | result |
|---|---|---|---|---|---|---|---|
| adc_codes | ff-40 | code_offset_lsb | -36.1 | -37.8 | -1.7 | |change| <= 15 | PASS |
| adc_codes | ff-40 | inl_lo_lsb | 0.27801 | 1.0961 | +0.8181 | <= 1 | FAIL |
| adc_codes | ff-40 | inl_code_lo_lsb | 0.6218 | 0.64158 | +0.01978 | <= 1.5 | PASS |
| adc_codes | ff-40 | top_2v15_lsb | 2.9759 | 2.6515 | -0.3244 | change <= +1.5 | PASS |
| adc_codes | ff-40 | top_2v10_lsb | 2.0037 | 0.90165 | -1.102 |  |  |
| adc_codes | ff-40 | alpha | 0.98048 | 0.97562 | -0.00486 | |change| <= 0.02 | PASS |
| adc_codes | ff-40 | gain_err_pct | -0.018341 | -0.024843 | -0.006502 | -0.5 .. 0.5 | PASS |
| adc_codes | ff-40 | unresolved | 0 | 0 | +0 | <= 0 | PASS |
| adc_codes | ff-40 | failed | 0 | 0 | +0 | <= 0 | PASS |
| adc_codes | ff-40 | first_conv_dlsb | 0.24041 | 0.299 | +0.05859 |  |  |
| adc_codes | ff85 | code_offset_lsb | -40.1 | -42.2 | -2.1 | |change| <= 15 | PASS |
| adc_codes | ff85 | inl_lo_lsb | 1.5656 | 3.0792 | +1.514 | <= 2.5 | FAIL |
| adc_codes | ff85 | inl_code_lo_lsb | 1.0697 | 2.9697 | +1.9 | <= 2 | FAIL |
| adc_codes | ff85 | top_2v15_lsb | 4.427 | 4.6835 | +0.2565 | change <= +1.5 | PASS |
| adc_codes | ff85 | top_2v10_lsb | 3.5135 | 2.199 | -1.315 |  |  |
| adc_codes | ff85 | alpha | 0.9801 | 0.9752 | -0.004897 | |change| <= 0.02 | PASS |
| adc_codes | ff85 | gain_err_pct | -0.10831 | -0.21563 | -0.1073 | -0.5 .. 0.5 | PASS |
| adc_codes | ff85 | unresolved | 0 | 0 | +0 | <= 0 | PASS |
| adc_codes | ff85 | failed | 0 | 0 | +0 | <= 0 | PASS |
| adc_codes | ff85 | first_conv_dlsb | 0.023873 | 0.036794 | +0.01292 |  |  |
| adc_codes | ss-40 | code_offset_lsb | -22 | -23.4 | -1.4 | |change| <= 15 | PASS |
| adc_codes | ss-40 | inl_lo_lsb | 0.15968 | 0.75921 | +0.5995 | <= 1 | PASS |
| adc_codes | ss-40 | inl_code_lo_lsb | 0.31894 | 0.74275 | +0.4238 | <= 1.5 | PASS |
| adc_codes | ss-40 | top_2v15_lsb | 0.13177 | 0.12097 | -0.0108 | change <= +1.5 | PASS |
| adc_codes | ss-40 | top_2v10_lsb | 0.011686 | -0.63314 | -0.6448 |  |  |
| adc_codes | ss-40 | alpha | 0.98191 | 0.9779 | -0.004009 | |change| <= 0.02 | PASS |
| adc_codes | ss-40 | gain_err_pct | -0.0021655 | -0.042433 | -0.04027 | -0.5 .. 0.5 | PASS |
| adc_codes | ss-40 | unresolved | 0 | 0 | +0 | <= 0 | PASS |
| adc_codes | ss-40 | failed | 0 | 0 | +0 | <= 0 | PASS |
| adc_codes | ss-40 | first_conv_dlsb | 0.31163 | 0.36978 | +0.05815 |  |  |
| adc_codes | ss125 | code_offset_lsb | -26.4 | -28.6 | -2.2 | |change| <= 15 | PASS |
| adc_codes | ss125 | inl_lo_lsb | 0.13219 | 1.0525 | +0.9203 | <= 1 | FAIL |
| adc_codes | ss125 | inl_code_lo_lsb | 0.25051 | 0.94275 | +0.6922 | <= 1.5 | PASS |
| adc_codes | ss125 | top_2v15_lsb | 1.5782 | 1.5985 | +0.02023 | change <= +1.5 | PASS |
| adc_codes | ss125 | top_2v10_lsb | 0.87123 | -0.12529 | -0.9965 |  |  |
| adc_codes | ss125 | alpha | 0.98166 | 0.9776 | -0.00406 | |change| <= 0.02 | PASS |
| adc_codes | ss125 | gain_err_pct | -0.0082461 | -0.094988 | -0.08674 | -0.5 .. 0.5 | PASS |
| adc_codes | ss125 | unresolved | 0 | 0 | +0 | <= 0 | PASS |
| adc_codes | ss125 | failed | 0 | 0 | +0 | <= 0 | PASS |
| adc_codes | ss125 | first_conv_dlsb | 0.062637 | 0.12926 | +0.06662 |  |  |
| adc_codes | typ | code_offset_lsb | -30.2 | -32.6 | -2.4 | |change| <= 15 | PASS |
| adc_codes | typ | inl_lo_lsb | 0.11853 | 0.94897 | +0.8304 | <= 1 | PASS |
| adc_codes | typ | inl_code_lo_lsb | 0.51894 | 0.94275 | +0.4238 | <= 1.5 | PASS |
| adc_codes | typ | top_2v15_lsb | 2.063 | 1.7579 | -0.3052 | change <= +1.5 | PASS |
| adc_codes | typ | top_2v10_lsb | 1.1851 | 0.19206 | -0.9931 |  |  |
| adc_codes | typ | alpha | 0.98121 | 0.9768 | -0.004408 | |change| <= 0.02 | PASS |
| adc_codes | typ | gain_err_pct | -0.0079357 | -0.012862 | -0.004926 | -0.5 .. 0.5 | PASS |
| adc_codes | typ | unresolved | 0 | 0 | +0 | <= 0 | PASS |
| adc_codes | typ | failed | 0 | 0 | +0 | <= 0 | PASS |
| adc_codes | typ | first_conv_dlsb | 0.35929 | 0.41472 | +0.05543 |  |  |
| adc_steps | ff85 | step_1536_lsb | -1.0796 | 1.4204 | +2.5 | |x| <= 2 | PASS |
| adc_steps | ff85 | step_2048_lsb | 1.5454 | 2.2954 | +0.75 | |x| <= 2 | FAIL |
| adc_steps | ff85 | step_2112_lsb | 0.17043 | -0.45457 | -0.625 | |x| <= 0.5 | PASS |
| adc_steps | ss-40 | step_1536_lsb | -1.0796 | 1.0454 | +2.125 | |x| <= 2 | PASS |
| adc_steps | ss-40 | step_2048_lsb | 0.42043 | 0.8516 | +0.4312 | |x| <= 2 | PASS |
| adc_steps | ss-40 | step_2112_lsb | 0.17043 | -0.20457 | -0.375 | |x| <= 0.5 | PASS |
| adc_steps | typ | step_1536_lsb | -1.0796 | 1.0454 | +2.125 | |x| <= 2 | PASS |
| adc_steps | typ | step_2048_lsb | 1.2954 | 1.2643 | -0.03113 | |x| <= 2 | PASS |
| adc_steps | typ | step_2112_lsb | 0.045432 | -0.20457 | -0.25 | |x| <= 0.5 | PASS |
| adc_timing | ff-40 | settle_worst_lsb | 0.098028 | 0.14446 | +0.04643 | <= 0.5 | PASS |
| adc_timing | ff-40 | late | 0 | 0 | +0 | <= 0 | PASS |
| adc_timing | ff-40 | failed | 0 | 0 | +0 | <= 0 | PASS |
| adc_timing | ff-40 | td_max_ns | 0.94645 | 1.394 | +0.4475 |  |  |
| adc_timing | ff-40 | settle_trial1_lsb | 0.0058649 | 0.010717 | +0.004852 |  |  |
| adc_timing | ff-40 | settle_trial2_lsb | 0.098028 | 0.14446 | +0.04643 |  |  |
| adc_timing | ff-40 | settle_top_lsb | 1.4548 | 1.4088 | -0.04603 | change <= +0.5 | PASS |
| adc_timing | ss-40x | settle_worst_lsb | 0.64952 | 0.80349 | +0.154 | <= 1 | PASS |
| adc_timing | ss-40x | late | 0 | 0 | +0 | <= 0 | PASS |
| adc_timing | ss-40x | failed | 0 | 0 | +0 | <= 0 | PASS |
| adc_timing | ss-40x | td_max_ns | 1.5485 | 2.1398 | +0.5913 |  |  |
| adc_timing | ss-40x | settle_trial1_lsb | 0.64952 | 0.80349 | +0.154 |  |  |
| adc_timing | ss-40x | settle_trial2_lsb | 0.42611 | 0.57579 | +0.1497 |  |  |
| adc_timing | ss-40x | settle_top_lsb | 0.74646 | 0.86992 | +0.1235 | change <= +0.5 | PASS |
| adc_timing | ss125 | settle_worst_lsb | 0.11297 | 0.10951 | -0.003466 | <= 0.5 | PASS |
| adc_timing | ss125 | late | 0 | 0 | +0 | <= 0 | PASS |
| adc_timing | ss125 | failed | 0 | 0 | +0 | <= 0 | PASS |
| adc_timing | ss125 | td_max_ns | 2.643 | 3.8003 | +1.157 |  |  |
| adc_timing | ss125 | settle_trial1_lsb | 0.0013209 | 0.0012969 | -2.392e-05 |  |  |
| adc_timing | ss125 | settle_trial2_lsb | 0.11297 | 0.10951 | -0.003466 |  |  |
| adc_timing | ss125 | settle_top_lsb | 0.279 | 0.26826 | -0.01073 | change <= +0.5 | PASS |
| adc_timing | typ | settle_worst_lsb | 0.073943 | 0.10253 | +0.02859 | <= 0.5 | PASS |
| adc_timing | typ | late | 0 | 0 | +0 | <= 0 | PASS |
| adc_timing | typ | failed | 0 | 0 | +0 | <= 0 | PASS |
| adc_timing | typ | td_max_ns | 1.5331 | 2.153 | +0.6199 |  |  |
| adc_timing | typ | settle_trial1_lsb | 0.0012661 | 0.00051137 | -0.0007547 |  |  |
| adc_timing | typ | settle_trial2_lsb | 0.073943 | 0.10253 | +0.02859 |  |  |
| adc_timing | typ | settle_top_lsb | 0.65249 | 0.60576 | -0.04673 | change <= +0.5 | PASS |
| adc_overlap | ff-40 | dt_max_lsb | 0.0041409 | 0.0064314 | +0.00229 | <= 0.2 | PASS |
| adc_overlap | ff-40 | dcode_max | 0 | 0 | +0 | <= 1 | PASS |
| adc_overlap | typ | dt_max_lsb | 0.0036841 | 0.0024291 | -0.001255 | <= 0.2 | PASS |
| adc_overlap | typ | dcode_max | 0 | 0 | +0 | <= 1 | PASS |

RESULT compare L1b: FAIL  (64 PASS, 0 WARN, 5 FAIL, 0 missing)

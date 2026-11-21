# R13 noise_check.md: why lptb.rec_patch integrates the noise spectrum itself

Fact (ngspice 46 here): `noise ...` followed by `echo $&onoise_total` returns **nan** as soon as a PDK diode (the ESD diodes of the pad cell) is in the circuit, although the
spectrum onoise_spectrum is finite. The golden noise bench AFE/layout/tb/tb_amp_noise.py reads onoise_total, so with `--rec-load` AFE/layout/tb/lptb.py (`rec_patch`) replaces that line by the
log-trapezoid integral of onoise_spectrum over the same 100 points per decade, 0.5 .. 300 Hz, and prints the simulator's own total as `vo_ng` next to it. Without --rec-load nothing changes.

Validation (a pad WITHOUT diodes, AFE/layout/sim/recpad/models/pad_check_nodiodes.spice = 2.87 pF on rec, keeps onoise_total finite):

    bash AFE/layout/sim/recpad/run_noisecheck.sh      (first command: tb_amp_noise.py --netlist schematic --corner typ --rec-load .../pad_check_nodiodes.spice --out .../noise_check)
    ngspice log AFE/layout/sim/recpad/noise_check/ngspice_n_sch_typ_real.log (copy of the scratch log), line 24:
    RESULT gm_db=60.053 vo=0.00150452 vo_ng=0.00150452

integral (vo) = simulator total (vo_ng) to 6 digits = 1.50452 mV at the output = 1.4954 uV input-referred = the committed baseline AFE/layout/baseline/amp_noise.json (typ noise_real_uv 1.4954; a capacitor on rec
changes nothing in this source-driven bench), see AFE/layout/sim/recpad/noise_check/amp_noise.json. So the integral is a faithful replacement and the pad numbers of amp_noise are valid.

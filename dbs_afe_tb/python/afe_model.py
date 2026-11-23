"""Behavioral (first-order) model of the dbs_afe_top analog path: neuron signal -> amplifier -> ADC code.

Deliberately crude. Everything here is an ASSUMPTION unless the README of the chip says otherwise; the
numbers are collected in one place (constants below) so they can be refined later.

Chain per channel:  electrode (uV) -> x1000 (60 dB) -> HP 0.27 Hz -> LP 1 kHz -> + VCM_OUT -> 12-bit ADC
ADC code convention (ASSUMED, see README): code = v / 3.3 V * 4096 + CODE_OFFSET, so 1.65 V -> 2048 + offset
(=2018, as in the chip test plan) and 1 LSB = 0.806 mV = 0.806 uV at the electrode.
"""
import numpy as np
from scipy import signal

VDD = 3.3
GAIN = 1000.0                 # 60 dB
VCM_OUT = 1.65                # amplifier output at rest
LSB_V = VDD / 4096.0          # 0.806 mV
CODE_OFFSET = -30             # typ corner, fixed code shift (README: -30 / -40 / -22 LSB)
F_HP = 0.27                   # Hz  (design 0.25-0.29)
F_LP = 700.0                  # Hz  (design 0.42-1.0 kHz)
FS_FRAME = 4000.0             # frames (samples) per second per channel
OSR = 8                       # internal rate = OSR * FS_FRAME (32 kHz)
FS_HI = FS_FRAME * OSR


def neural_signal(duration_s, seed=0, rate_hz=15.0, spike_uv=150.0, noise_uv=1.9,
                  lfp_uv=40.0, dc_mv=0.0):
    """Electrode voltage in volts at FS_HI plus the ground-truth spike times (s).

    Spike = biphasic template (fast negative lobe, slower positive lobe), Poisson timing with 3 ms refractory.
    Noise = white, scaled so the 0.5-300 Hz rms is ~noise_uv (chip figure 1.89 uV typ).
    lfp   = a couple of slow sinusoids (local field potential stand-in).
    dc_mv = electrode DC offset (the amplifier is AC coupled and removes it).
    """
    rng = np.random.default_rng(seed)
    n = int(round(duration_s * FS_HI))
    t = np.arange(n) / FS_HI
    # template
    tt = np.arange(0, 1.5e-3, 1 / FS_HI)
    tmpl = -np.exp(-0.5 * ((tt - 0.3e-3) / 0.1e-3) ** 2) + 0.3 * np.exp(-0.5 * ((tt - 0.7e-3) / 0.25e-3) ** 2)
    tmpl /= np.abs(tmpl).max()
    x = np.zeros(n)
    times, tcur = [], 0.0
    while True:
        tcur += max(rng.exponential(1.0 / rate_hz), 3e-3)
        if tcur >= duration_s - 2e-3:
            break
        times.append(tcur)
        i = int(tcur * FS_HI)
        x[i:i + len(tmpl)] += spike_uv * 1e-6 * tmpl[: n - i]
    # white noise: 0.5-300 Hz is a fraction f_band/(fs/2) of the white power
    sigma = noise_uv * 1e-6 / np.sqrt(300.0 / (FS_HI / 2))
    x += rng.normal(0, sigma, n)
    for f, a in ((4.0, 1.0), (9.0, 0.6), (23.0, 0.3)):
        x += a * lfp_uv * 1e-6 * np.sin(2 * np.pi * f * t + rng.uniform(0, 6.28))
    x += dc_mv * 1e-3
    return x, np.array(times)


def amplifier(x_v, gain=GAIN):
    """HP (0.27 Hz) + LP and gain; output includes VCM_OUT. Filter starts at rest."""
    bh, ah = signal.butter(1, F_HP / (FS_HI / 2), "high")
    bl, al = signal.butter(1, F_LP / (FS_HI / 2), "low")
    # start the HP in the state it would have if it had seen x[0] forever (AC coupling already settled)
    zi = signal.lfilter_zi(bh, ah) * x_v[0]
    y, _ = signal.lfilter(bh, ah, x_v, zi=zi)
    y = signal.lfilter(bl, al, y)
    return VCM_OUT + gain * y


def v_to_code(v, offset=CODE_OFFSET):
    return np.clip(np.round(v / LSB_V).astype(int) + offset, 0, 4095)


class FrontEnd:
    """4-channel front end. codes(k, en, mode, rst_amp) -> four codes for frame k.

    en/mode/rst_amp are the *held* configuration read from the DUT. A channel only sees its electrode when
    mode == 1 (record) and en[k] == 1 and RST_AMP == 0; otherwise its output sits at VCM_OUT (parked / reset).
    """

    def __init__(self, duration_s, seed=1, **kw):
        self.truth, self.wave_v = [], []
        for ch in range(4):
            x, times = neural_signal(duration_s, seed=seed + ch, **kw)
            self.truth.append(times)
            self.wave_v.append(amplifier(x))
        self.n_frames = int(duration_s * FS_FRAME)

    def codes(self, k, en, mode, rst_amp):
        out = []
        for ch in range(4):
            connected = bool(mode) and bool((en >> ch) & 1) and not rst_amp
            v = self.wave_v[ch][k * OSR] if connected else VCM_OUT
            out.append(int(v_to_code(np.array([v]))[0]))
        return out


def detect_spikes(codes, fs=FS_FRAME, k=5.0, refractory_s=2e-3):
    """Negative-threshold detector at -k * robust sigma. Returns spike times in seconds."""
    c = np.asarray(codes, dtype=float)
    # spike band: zero-phase 2nd-order high-pass at 300 Hz removes LFP / drift (host-side filtering)
    c = signal.sosfiltfilt(signal.butter(2, 300.0 / (fs / 2), "high", output="sos"), c)
    sigma = np.median(np.abs(c)) / 0.6745
    thr = -k * max(sigma, 1.0)
    idx = np.where((c[1:] < thr) & (c[:-1] >= thr))[0] + 1
    out, last = [], -1e9
    for i in idx:
        if i / fs - last >= refractory_s:
            out.append(i / fs)
            last = i / fs
    return np.array(out)


def match(detected, truth, tol=2.5e-3):
    """(hits, misses, false_alarms)"""
    used, hits = set(), 0
    for t in truth:
        cand = [j for j, d in enumerate(detected) if j not in used and abs(d - t) <= tol]
        if cand:
            used.add(cand[0])
            hits += 1
    return hits, len(truth) - hits, len(detected) - len(used)
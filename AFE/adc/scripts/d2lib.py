#!/usr/bin/env python3
"""D2 helpers: PDK MIM capacitance formula, split-capacitor DAC network (exact linear charge-sharing model), DNL/INL.
Everything here is algebra on the capacitor network; the ngspice AC-weight check (tb_dac_ac.spice) verifies it against the PDK netlist."""
import numpy as np
COX, CSW = 1.99e-3, 2.383e-10        # PDK cap_mim_2f0 (typ): F/m2, F/m   (sm141064_mim.ngspice)
CORNER = {'typical': 1.0, 'ff': 0.9, 'ss': 1.1}   # mim_corner_2p0fF
VDD = 3.3; LSB = VDD / 4096
def mim_c(L, W, corner='typical'): return (COX * L * W + CSW * 2 * (L + W)) * CORNER[corner]
def width_for(C, L=5e-6, corner='typical'):
    """c_width that gives capacitance C with c_length = L (area + perimeter formula is linear in W)"""
    k = CORNER[corner]; return (C / k - 2 * CSW * L) / (COX * L + 2 * CSW)
CU = mim_c(5e-6, 5e-6)               # 54.52 fF
class Dac:
    """m MSB-array bits (to node T) + l LSB-array bits (to node M) + 1 dummy unit on M + bridge cb between T and M.
    cu: nominal unit cap; du[k]: relative error of every physical unit (index order: LSB array units, dummy, MSB array units); db: bridge relative error.
    cpt, cpm: parasitic capacitance to ground on T and M (F).  cb: bridge value (F); default = ideal 2^l/(2^l-1) units."""
    def __init__(self, m=6, l=6, cu=CU, sig=0.0, rng=None, cpt=0.0, cpm=0.0, cb=None, sigb=None):
        self.m, self.l, self.cu, self.cpt, self.cpm = m, l, cu, cpt, cpm
        nl = 2**l; nm = 2**m - 1                         # LSB array: 2^l units (2^l - 1 in bits + 1 dummy); MSB array 2^m - 1 units
        n = nl + nm
        d = rng.normal(0, sig, n) if (rng is not None and sig > 0) else np.zeros(n)
        self.units = cu * (1 + d)
        cbn = (cu * nl / (nl - 1) if nl > 1 else 1.0) if cb is None else cb   # l = 0 (binary): bridge = 1 F, i.e. a short
        self.cb = cbn * (1 + (rng.normal(0, sig if sigb is None else sigb) if (rng is not None and sig > 0) else 0.0))
        # bit -> list of unit indices
        idx = 0; self.bit_units = []
        for k in range(l):                                # LSB array bit k = 2^k units (node M)
            self.bit_units.append(list(range(idx, idx + 2**k))); idx += 2**k
        self.dummy = [idx]; idx += 1                      # one dummy unit (node M), bottom grounded after sampling
        for k in range(m):                                # MSB array bit l+k = 2^k units (node T)
            self.bit_units.append(list(range(idx, idx + 2**k))); idx += 2**k
        assert idx == n
    def weights(self):
        """V_T = sum_j w_j * Vb_j  (sources on all bottoms incl. dummy); returns w for bits 0..l+m-1 and the dummy weight"""
        cbit = np.array([self.units[u].sum() for u in self.bit_units]); cd = self.units[self.dummy].sum()
        ctop = cbit[self.l:].sum() + self.cpt; cm = cbit[:self.l].sum() + cd + self.cpm
        A = np.array([[ctop + self.cb, -self.cb], [-self.cb, cm + self.cb]])
        Ainv = np.linalg.inv(A)                           # [vT, vM] = Ainv @ [sum C_T Vb, sum C_M Vb]
        wT = np.zeros(len(cbit) + 1); 
        for j, c in enumerate(cbit):
            src = np.array([c, 0.0]) if j >= self.l else np.array([0.0, c])
            wT[j] = (Ainv @ src)[0]
        wT[-1] = (Ainv @ np.array([0.0, cd]))[0]
        return wT[:-1], wT[-1]
    def levels(self, w=None):
        """DAC output levels (V at the input) for all codes: Vth(c) = VDD * sum w_j b_j / (sum w_j + w_dummy)  (the sampled full-scale gain)"""
        if w is None: w, wd = self.weights()
        else: wd = None
        nb = self.l + self.m; codes = np.arange(2**nb)
        bits = ((codes[:, None] >> np.arange(nb)) & 1).astype(float)
        wall = w.sum() + (wd if wd is not None else self.weights()[1])
        return VDD * (bits @ w) / wall
def dnl_inl(lv, nb=12):
    n = 2**nb; step = (lv[-1] - lv[0]) / (n - 1)
    dnl = np.diff(lv) / step - 1
    inl = (lv - lv[0] - np.arange(n) * step) / step
    return dnl, inl, step

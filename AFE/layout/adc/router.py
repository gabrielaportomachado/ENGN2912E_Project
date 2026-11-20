"""router.py (L2a): a small grid router for the signal wiring of amp_ch (Metal2 / Metal3 / Metal4, access to Metal1 terminals through Via1).
Pure python + numpy, runs inside KLayout's python (kl.sh) or plain python3.

Model
  grid pitch 1.0 um, wire width 0.5 um (spacing to a parallel neighbour track 0.5 um >= the 0.28 um of M2..M4), via pad = 0.5 um square, via cut 0.26 um (Via1..Via3).
  layers 0 / 1 / 2 = Metal2 / Metal3 / Metal4; preferred direction horizontal / vertical / horizontal (the other direction costs x3).
  an obstacle (any rectangle on a layer, with the net it belongs to) blocks every grid node within HW + CLR of it for all other nets.
  a terminal is a rectangle (>= 0.5 x 0.5 um) on Metal1 (reached by Via1), Metal2, Metal3 or Metal4; nets are routed one terminal at a time (multi-source A* from the tree built so far).
  FINDING: pad squares at every used node and rectangles between consecutive nodes give the same shapes as a track router with 0.5 um wires, no off-grid shapes (all coordinates are multiples of 5 nm).
"""
import heapq
import numpy as np

VIA_NAME = ('via1', 'via2', 'via3')          # via k joins routing layer k-1 and k (k = 0: Metal1 and layer 0)
LAYER_NAME = ('metal2', 'metal3', 'metal4')
PREF = ('h', 'v', 'h')


class Router:
    def __init__(self, x0, y0, x1, y1, pitch=1.0, hw=0.25, clr=0.30, via_cost=5.0, wrong=3.0, halo_cost=40.0):
        self.x0, self.y0, self.p = x0, y0, pitch
        self.nx = int(round((x1 - x0) / pitch)) + 1
        self.ny = int(round((y1 - y0) / pitch)) + 1
        self.hw, self.clr = hw, clr
        self.exp = hw + clr
        self.via_cost, self.wrong, self.halo_cost = via_cost, wrong, halo_cost
        n = (3, self.nx, self.ny)
        self.occ = np.zeros(n, dtype=np.int32)        # net occupying the node (0 = free)
        self.blk = np.zeros(n, dtype=np.int32)        # obstacle net (0 free, -1 blocked for everybody)
        self.halo = np.zeros(n, dtype=np.int32)       # sensitive-node clearance: blocked for every net except the owner
        self.hard = np.zeros(n, dtype=np.int32)       # extra clearance of a shape (MIMTM.1): blocked for every net except the owner (-1: for all)
        self.ovl = np.zeros(n, dtype=np.int32)        # net of a fixed shape that the pad of this node OVERLAPS (an own-net node that only comes near a shape would violate the spacing rule)
        self.netid = {}
        self.names = {0: ''}
        self.terms = {}                                # net -> list of (layer code, rect)
        self.fixed = []                                # (layer index, rect, net)
        self.paths = {}                                # net -> list of paths (each: list of (l, i, j))
        self.failed = []
        self.banned = {}                               # net id -> bool array (R5): nodes this net may not use (keep-out zones of control nets)

    # ---------------------------------------------------------------- bookkeeping
    def nid(self, net):
        if net not in self.netid:
            self.netid[net] = len(self.netid) + 1
            self.names[self.netid[net]] = net
        return self.netid[net]

    def xy(self, i, j):
        return (self.x0 + i * self.p, self.y0 + j * self.p)

    def ij_range(self, rect, e):
        x1, y1, x2, y2 = rect
        i1 = max(0, int(np.ceil((x1 - e - self.x0) / self.p - 1e-9)))
        i2 = min(self.nx - 1, int(np.floor((x2 + e - self.x0) / self.p + 1e-9)))
        j1 = max(0, int(np.ceil((y1 - e - self.y0) / self.p - 1e-9)))
        j2 = min(self.ny - 1, int(np.floor((y2 + e - self.y0) / self.p + 1e-9)))
        return i1, i2, j1, j2

    def obstacle(self, layer, rect, net=None, extra=0.0):
        """layer: 0..2 (metal2..metal4); net=None blocks for everybody.  extra = additional clearance (um) that only keeps OTHER nets away (the owner may come as close as the spacing rule)"""
        nid = self.nid(net) if net is not None else -1
        i1, i2, j1, j2 = self.ij_range(rect, self.exp)
        if i1 <= i2 and j1 <= j2:
            if net is not None:
                o1, o2, p1, p2 = self.ij_range(rect, self.hw + 0.005)
                if o1 <= o2 and p1 <= p2:
                    ov = self.ovl[layer, o1:o2 + 1, p1:p2 + 1]
                    ov[ov == 0] = nid
            a = self.blk[layer, i1:i2 + 1, j1:j2 + 1]
            if nid == -1:
                a[:, :] = -1
            else:
                m0 = (a == 0)
                mo = (a != 0) & (a != nid)
                a[m0] = nid
                a[mo] = -1
        if extra > 0:
            e1, e2, f1, f2 = self.ij_range(rect, self.exp + extra)
            if e1 <= e2 and f1 <= f2:
                h = self.hard[layer, e1:e2 + 1, f1:f2 + 1]
                if nid == -1:
                    h[:, :] = -1
                else:
                    h[h == 0] = nid
                    h[(h != 0) & (h != nid)] = -1
        self.fixed.append((layer, rect, net))

    def add_halo(self, layer, rect, net, extra):
        """nodes within HW + CLR + extra of `rect` are blocked for every net but `net` (leakage / noise clearance of sensitive nodes: no other net within ~2 um)"""
        i1, i2, j1, j2 = self.ij_range(rect, self.exp + extra)
        if i1 > i2 or j1 > j2:
            return
        nid = self.nid(net)
        a = self.halo[layer, i1:i2 + 1, j1:j2 + 1]
        a[a == 0] = nid
        a[(a != 0) & (a != nid)] = -1

    def ban(self, nets, rect, layers=(0, 1, 2)):
        """R5: the nets may not use the nodes inside rect (keep-out of control wires around the sensitive plates); other nets are not affected"""
        i1, i2, j1, j2 = self.ij_range(rect, 0.0)
        for net in nets:
            n = self.nid(net)
            a = self.banned.setdefault(n, np.zeros((3, self.nx, self.ny), dtype=bool))
            for l in layers:
                a[l, max(i1, 0):i2 + 1, max(j1, 0):j2 + 1] = True

    def block_all(self, rect, layers=(0, 1, 2), extra=0.0):
        for l in layers:
            self.obstacle(l, rect, None, extra)

    def terminal(self, net, code, rect):
        """code: 'metal1' | 'metal2' | 'metal3' | 'metal4' (the layer of the terminal shape)"""
        self.nid(net)
        self.terms.setdefault(net, []).append((code, tuple(rect)))

    # ---------------------------------------------------------------- search
    def free(self, l, i, j, n, halo=False):
        """halo is SOFT by default: a node inside the clearance of a sensitive net costs HALO_COST extra (see astar) but stays usable; halo=True makes it a hard obstacle"""
        h = self.hard[l, i, j]
        if h != 0 and h != n:
            return False
        if self.banned and n in self.banned and self.banned[n][l, i, j]:
            return False
        h = self.halo[l, i, j]
        if halo and h != 0 and h != n:
            return False
        b = self.blk[l, i, j]
        if b != 0 and not (b == n and self.ovl[l, i, j] == n):
            return False
        return self.occ[l, i, j] in (0, n)

    def cand(self, code, rect, n):
        """grid nodes (l, i, j) inside the terminal rectangle where a 0.5 um pad fits and the node is usable by net n"""
        l = {'metal1': 0, 'metal2': 0, 'metal3': 1, 'metal4': 2}[code]
        x1, y1, x2, y2 = rect
        m = self.hw - 1e-6
        i1, i2, j1, j2 = self.ij_range((x1 + m, y1 + m, x2 - m, y2 - m), 0.0)
        out = []
        for i in range(i1, i2 + 1):
            x = self.x0 + i * self.p
            if x < x1 + m - 1e-6 or x > x2 - m + 1e-6:
                continue
            for j in range(j1, j2 + 1):
                y = self.y0 + j * self.p
                if y < y1 + m - 1e-6 or y > y2 - m + 1e-6:
                    continue
                # the node must be free for the net: the terminal's own obstacles carry the net id, so they do not block
                if self.free(l, i, j, n, halo=False):
                    out.append((l, i, j))
        return out

    def reserve(self, maxc=6):
        """mark the access nodes of every terminal that has few of them as occupied by its net (an M2 / M3 wire of another net over a Metal1 pad would otherwise lock the pad)"""
        for net, terms in self.terms.items():
            n = self.nid(net)
            for (c, r) in terms:
                cs = self.cand(c, r, n)
                if len(cs) > maxc:
                    cs = [cs[0], cs[len(cs) // 2], cs[-1]]
                for (l, i, j) in cs:
                    if self.occ[l, i, j] == 0:
                        self.occ[l, i, j] = n

    def route_net(self, net, order=None):
        n = self.nid(net)
        terms = list(self.terms.get(net, []))
        if len(terms) < 2:
            return True
        cands = [self.cand(c, r, n) for (c, r) in terms]
        for t, c in zip(terms, cands):
            if not c:
                code, r = t
                l = {'metal1': 0, 'metal2': 0, 'metal3': 1, 'metal4': 2}[code]
                i1, i2, j1, j2 = self.ij_range(r, 0.0)
                why = []
                for i in range(i1, min(i2, i1 + 3) + 1):
                    for j in range(j1, min(j2, j1 + 3) + 1):
                        why.append(((l, i, j), int(self.blk[l, i, j]), self.names.get(int(self.blk[l, i, j]), '?') if self.blk[l, i, j] > 0 else '', int(self.occ[l, i, j]), self.names.get(int(self.occ[l, i, j]), '?')))
                self.failed.append((net, 'terminal without free access node', t, why[:6]))
                return False
        # start with the terminal that has the fewest candidates, then connect the nearest remaining one each time
        remaining = list(range(len(terms)))
        first = min(remaining, key=lambda k: len(cands[k]))
        remaining.remove(first)
        tree = set()
        # the first terminal contributes ALL its candidates as potential sources only for the very first connection
        sources = set(cands[first])
        paths = []
        ok = True
        used_first = False
        while remaining:
            # pick the remaining terminal closest to the current sources
            def dist(k):
                cs = cands[k]
                ax = np.mean([self.xy(i, j)[0] for (_, i, j) in cs])
                ay = np.mean([self.xy(i, j)[1] for (_, i, j) in cs])
                best = 1e18
                for (_, i, j) in list(sources)[:400]:
                    x, y = self.xy(i, j)
                    best = min(best, abs(x - ax) + abs(y - ay))
                return best
            k = min(remaining, key=dist)
            remaining.remove(k)
            path = self.astar(sources, set(cands[k]), n)
            if path is None:
                self.failed.append((net, 'no path', terms[k]))
                ok = False
                continue
            for (l, i, j) in path:
                self.occ[l, i, j] = n
            paths.append(path)
            tree |= set(path)
            sources = set(tree)
            used_first = True
        self.paths.setdefault(net, []).extend(paths)
        return ok

    def astar(self, sources, targets, n):
        tg = list(targets)
        txs = [self.xy(i, j) for (_, i, j) in tg]
        tx1, tx2 = min(x for x, _ in txs), max(x for x, _ in txs)
        ty1, ty2 = min(y for _, y in txs), max(y for _, y in txs)

        def h(l, i, j):
            x, y = self.xy(i, j)
            dx = max(tx1 - x, 0.0, x - tx2)
            dy = max(ty1 - y, 0.0, y - ty2)
            return (dx + dy) / self.p

        pq = []
        best = {}
        prev = {}
        for s in sources:
            best[s] = 0.0
            heapq.heappush(pq, (h(*s), 0.0, s))
        tset = set(targets)
        nx, ny = self.nx, self.ny
        while pq:
            f, g, u = heapq.heappop(pq)
            if best.get(u, 1e18) < g - 1e-9:
                continue
            if u in tset:
                path = [u]
                while u in prev:
                    u = prev[u]
                    path.append(u)
                return path[::-1]
            l, i, j = u
            for (dl, di, dj) in ((0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1), (1, 0, 0), (-1, 0, 0)):
                nl, ni, nj = l + dl, i + di, j + dj
                if nl < 0 or nl > 2 or ni < 0 or ni >= nx or nj < 0 or nj >= ny:
                    continue
                if not self.free(nl, ni, nj, n):
                    continue
                if dl:
                    c = self.via_cost
                else:
                    horiz = (di != 0)
                    c = 1.0 if (horiz == (PREF[l] == 'h')) else self.wrong
                v = (nl, ni, nj)
                hh = self.halo[nl, ni, nj]
                if hh != 0 and hh != n:
                    c += self.halo_cost
                ng = g + c
                if ng < best.get(v, 1e18) - 1e-9:
                    best[v] = ng
                    prev[v] = u
                    heapq.heappush(pq, (ng + h(nl, ni, nj), ng, v))
        return None

    # ---------------------------------------------------------------- shapes
    def shapes(self):
        """-> dict net -> {'wires': [(layer name, rect)], 'vias': [(via name, rect)]}; terminal access vias (Metal1 -> Metal2) included"""
        res = {}
        hw = self.hw
        for net, paths in self.paths.items():
            w, v = [], []
            for path in paths:
                for a in range(len(path)):
                    l, i, j = path[a]
                    x, y = self.xy(i, j)
                    w.append((LAYER_NAME[l], (x - hw, y - hw, x + hw, y + hw)))
                    if a + 1 < len(path):
                        l2, i2, j2 = path[a + 1]
                        x2, y2 = self.xy(i2, j2)
                        if l2 == l:
                            w.append((LAYER_NAME[l], (min(x, x2) - hw, min(y, y2) - hw, max(x, x2) + hw, max(y, y2) + hw)))
                        else:
                            lo = min(l, l2)
                            v.append((VIA_NAME[lo + 1], (x - 0.13, y - 0.13, x + 0.13, y + 0.13)))
                # access vias to Metal1 terminals at both ends (checked against the terminal list)
            res[net] = {'wires': w, 'vias': v}
        return res

    def access_vias(self):
        """Via1 (Metal1 terminal -> Metal2 pad) at every path node that lies in a Metal1 terminal of the net; also the Metal1 pad (0.5 um square)"""
        out = []
        hw = self.hw
        for net, paths in self.paths.items():
            t1 = [r for (c, r) in self.terms.get(net, []) if c == 'metal1']
            if not t1:
                continue
            seen = set()
            for path in paths:
                for (l, i, j) in path:
                    if l != 0 or (i, j) in seen:
                        continue
                    x, y = self.xy(i, j)
                    for r in t1:
                        if r[0] + hw - 1e-6 <= x <= r[2] - hw + 1e-6 and r[1] + hw - 1e-6 <= y <= r[3] - hw + 1e-6:
                            # only the end nodes of a path (a path that merely crosses a rail on Metal2 must not drop a Via1)
                            seen.add((i, j))
                            out.append((net, (x, y)))
                            break
        return out

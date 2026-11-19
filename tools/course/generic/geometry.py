"""Geometry for the generic courses: a loop drawn as a rounded polygon, chutes carried straight on from its straights.

Frame (u, v), metres: u along the home straight away from the winning post (the horses run towards -u there), v into
the infield. The post is on the home straight at (post_u, 0). The loop is given by its corners in running order after
the post (the last corner is the home bend, at the far end of the home straight) and a radius for each corner.
"""
import math
import numpy as np


class Loop:
    def __init__(self, corners, radii, post_u=None, step=1.0, post_gap=None):
        V = [np.array(c, float) for c in corners]
        n = len(V)
        self.corner = []                    # per corner: A (bend starts), B (bend ends), d_in, d_out, theta, r
        for i in range(n):
            P, C, N = V[i - 1], V[i], V[(i + 1) % n]
            di = (C - P) / np.linalg.norm(C - P); do = (N - C) / np.linalg.norm(N - C)
            th = math.acos(max(-1.0, min(1.0, float(di @ do))))
            t = radii[i] * math.tan(th / 2)
            self.corner.append(dict(V=C, A=C - di * t, B=C + do * t, d_in=di, d_out=do, th=th, r=radii[i], t=t))
        # sample: from corner i's B along the straight to corner i+1's A, then round corner i+1
        pts, kinds = [], []
        for i in range(n):
            c0, c1 = self.corner[i], self.corner[(i + 1) % n]
            L = np.linalg.norm(c1["A"] - c0["B"])
            if L < -1e-6: raise SystemExit("corners too close for their radii")
            for s in np.arange(0, L, step):
                pts.append(c0["B"] + (c1["A"] - c0["B"]) * (s / max(L, 1e-9))); kinds.append(("straight", (i + 1) % n))
            # the arc round c1: centre on the inside (the turn's side)
            di, do = c1["d_in"], c1["d_out"]
            cross = di[0] * do[1] - di[1] * do[0]
            sgn = 1.0 if cross > 0 else -1.0
            nrm = np.array([-di[1], di[0]]) * sgn
            cen = c1["A"] + nrm * c1["r"]
            a0 = math.atan2(*(c1["A"] - cen)[::-1]); a1 = a0 + sgn * c1["th"]
            m = max(2, int(c1["r"] * c1["th"] / step))
            for k in range(m):
                a = a0 + (a1 - a0) * k / m
                pts.append(cen + c1["r"] * np.array([math.cos(a), math.sin(a)])); kinds.append(("bend", (i + 1) % n))
        P = np.array(pts)
        seg = np.hypot(*np.diff(np.vstack([P, P[:1]]), axis=0).T)
        s = np.concatenate([[0], np.cumsum(seg)])
        self.L = float(s[-1])
        # put s = 0 at the post (on the straight into corner 0, i.e. the home straight); post_gap: the post that many
        # metres before the post-end bend starts
        if post_gap is not None: post_u = float(self.corner[0]["A"][0]) + post_gap
        self.post_u = post_u
        post = np.array([post_u, 0.0])
        j = int(np.argmin(np.hypot(*(P - post).T)))
        self.P = np.roll(P, -j, axis=0); self.kind = kinds[j:] + kinds[:j]
        seg = np.hypot(*np.diff(np.vstack([self.P, self.P[:1]]), axis=0).T)
        self.s = np.concatenate([[0], np.cumsum(seg)])[:-1]
        self.L = float(np.sum(seg))
        self.sB = {}                         # s (metres after the post, 0..L) of each corner's B and A
        for i, c in enumerate(self.corner):
            self.sB[i] = self.s[int(np.argmin(np.hypot(*(self.P - c["B"]).T)))]
        self.sA = {i: self.s[int(np.argmin(np.hypot(*(self.P - c["A"]).T)))] for i, c in enumerate(self.corner)}

    def at(self, s):
        s = s % self.L
        i = int(np.searchsorted(self.s, s, side="right") - 1); i = max(0, min(i, len(self.P) - 1))
        a, b = self.P[i], self.P[(i + 1) % len(self.P)]
        sb = self.s[i + 1] if i + 1 < len(self.s) else self.L
        k = (s - self.s[i]) / max(1e-9, sb - self.s[i])
        d = b - a; return a + d * k, d / (np.linalg.norm(d) or 1)

    def where(self, s):
        s = s % self.L
        i = int(np.searchsorted(self.s, s, side="right") - 1); i = max(0, min(i, len(self.P) - 1))
        return self.kind[i]

    def route(self, behind, run_out, chute=None, chute_len=0.0, step=2.0, laps=0):
        """the inside rail in running order: (chute), the loop from 'behind' metres before the post to 'run_out' after.
        chute = corner index: the straight after that corner carried on backwards beyond it for chute_len metres; the
        route then joins the loop where that straight starts (the corner's B)."""
        pts = []
        if chute is not None:
            c = self.corner[chute]
            for x in np.arange(chute_len, 0, -step):
                pts.append(c["B"] - c["d_out"] * x)
            sj = self.sB[chute]
            s0 = sj - self.L if sj > 0 else sj          # metres before the post (negative)
            start = s0 - laps * self.L
        else:
            start = -behind
        for s in np.arange(start, run_out + 1e-6, step):
            pts.append(self.at(s)[0])
        return np.array(pts)

    def back_of(self, chute):
        """metres to go at the corner's B (where a chute off it joins), going back from the post"""
        sj = self.sB[chute]
        return self.L - sj if sj > 0 else 0.0

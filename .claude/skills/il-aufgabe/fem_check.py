#!/usr/bin/env python
"""Numeric cross-check of a plane frame: support reactions from a small FE model.

Shares no algebra with the Kraftgroessenverfahren, so agreement is real
evidence rather than a restatement. Bending only by default (EA set rigid),
matching the usual assumption in these exercises.

    python fem_check.py model.json

model.json:
{
  "EI": 1, "n": 200,
  "nodes":    {"A": [0,0], "K": [0,1], "B": [0,2], "C": [-2,1]},
  "members":  [["A","K"], ["K","B"], ["K","C"]],
  "supports": {"A": ["ux","uy"], "B": ["ux"], "C": ["uy"]},
  "loads":    [{"member": ["A","K"], "q0": [-1,0], "q1": [-1,0]},
               {"member": ["K","C"], "q0": [0,0],  "q1": [0,-1]}]
}

"q0"/"q1" are global-direction load intensities at the member's start and end
node: equal values give a uniform load, [0,0] -> [0,-q] a triangular one.
"supports" lists the blocked dofs per node ("ux", "uy", "rot"); a printed
reaction is positive in +x / +y. The script solves at two mesh densities --
if the two rows disagree in the digits you care about, raise "n".
"""
import json
import sys

import numpy as np

OFF = {"ux": 0, "uy": 1, "rot": 2}


def solve(m):
    EI = m.get("EI", 1.0)
    EA = m.get("EA", 1e9)
    n = m.get("n", 200)
    P = {k: np.array(v, float) for k, v in m["nodes"].items()}
    load = {}
    for L in m.get("loads", []):
        load[tuple(L["member"])] = (np.array(L.get("q0", [0, 0]), float),
                                    np.array(L.get("q1", [0, 0]), float))
    pts, idx = [], {}

    def node(p):
        key = (round(float(p[0]), 9), round(float(p[1]), 9))
        if key not in idx:
            idx[key] = len(pts)
            pts.append(np.array(p, float))
        return idx[key]

    els = []
    for a, b in m["members"]:
        pa, pb = P[a], P[b]
        q0, q1 = load.get((a, b), (np.zeros(2), np.zeros(2)))
        for i in range(n):
            t0, t1 = i / n, (i + 1) / n
            tm = 0.5 * (t0 + t1)
            els.append((node(pa + (pb - pa) * t0),
                        node(pa + (pb - pa) * t1),
                        q0 + (q1 - q0) * tm))

    N = len(pts)
    K = np.zeros((3 * N, 3 * N))
    F = np.zeros(3 * N)
    for i, j, q in els:
        d = pts[j] - pts[i]
        Le = float(np.hypot(d[0], d[1]))
        c, s = d[0] / Le, d[1] / Le
        kl = np.zeros((6, 6))
        kl[0, 0] = kl[3, 3] = EA / Le
        kl[0, 3] = kl[3, 0] = -EA / Le
        kl[1, 1] = kl[4, 4] = 12 * EI / Le ** 3
        kl[1, 4] = kl[4, 1] = -12 * EI / Le ** 3
        kl[1, 2] = kl[2, 1] = kl[1, 5] = kl[5, 1] = 6 * EI / Le ** 2
        kl[2, 4] = kl[4, 2] = kl[5, 4] = kl[4, 5] = -6 * EI / Le ** 2
        kl[2, 2] = kl[5, 5] = 4 * EI / Le
        kl[2, 5] = kl[5, 2] = 2 * EI / Le
        T = np.zeros((6, 6))
        for o in (0, 3):
            T[o, o] = c
            T[o, o + 1] = s
            T[o + 1, o] = -s
            T[o + 1, o + 1] = c
            T[o + 2, o + 2] = 1.0
        ke = T.T @ kl @ T
        wa = q[0] * c + q[1] * s
        wt = -q[0] * s + q[1] * c
        fl = np.array([wa * Le / 2, wt * Le / 2, wt * Le ** 2 / 12,
                       wa * Le / 2, wt * Le / 2, -wt * Le ** 2 / 12])
        fe = T.T @ fl
        dofs = [3 * i, 3 * i + 1, 3 * i + 2, 3 * j, 3 * j + 1, 3 * j + 2]
        F[dofs] += fe
        K[np.ix_(dofs, dofs)] += ke

    fixed = set()
    for name, dirs in m["supports"].items():
        k = node(P[name])
        for dname in dirs:
            fixed.add(3 * k + OFF[dname])
    free = [k for k in range(3 * N) if k not in fixed]
    u = np.zeros(3 * N)
    u[free] = np.linalg.solve(K[np.ix_(free, free)], F[free])
    R = K @ u - F

    out = {}
    for name, dirs in m["supports"].items():
        k = node(P[name])
        for dname in dirs:
            out[f"{name}.{dname}"] = float(R[3 * k + OFF[dname]])
    return out


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    with open(sys.argv[1], encoding="utf-8") as fh:
        model = json.load(fh)
    fine = int(model.get("n", 200))
    for n in (max(fine // 4, 1), fine):
        model["n"] = n
        r = solve(model)
        print(f"n={n:5d}  " + "  ".join(f"{k}={v:+.6f}" for k, v in r.items()))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""README showcase figures (light and dark SVG), generated from recorded results only.

    python3 analysis/readme_figures.py            # writes docs/figures/*.svg
    python3 analysis/readme_figures.py --out DIR  # elsewhere (used by the up-to-date check)

Inputs: the authoritative run results/modal/20261115T065950Z, its R analysis outputs in
reports/figures/modal_20261115T065950Z, and results/agent_usage.csv. Standard library only.
Colour roles follow a validated categorical palette: Python, C++ and Rust keep one hue each in
every figure; pipeline phases use one-hue ordinal steps; support policies use two further hues.
"""
import argparse
import csv
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RUN = "20261115T065950Z"
RES = ROOT / "results" / "modal" / RUN
ANA = ROOT / "reports" / "figures" / f"modal_{RUN}"

FONT = 'system-ui, -apple-system, &quot;Segoe UI&quot;, Roboto, Helvetica, Arial, sans-serif'
W = 860

THEMES = {
    "light": dict(surface="#fcfcfb", border="rgba(11,11,11,0.10)", ink="#0b0b0b", ink2="#52514e",
                  muted="#898781", grid="#e1e0d9", axis="#c3c2b7", neutral="#9b9a94", on_fill="#ffffff",
                  lang={"python": "#2a78d6", "cpp": "#eb6834", "rust": "#1baf7a"},
                  pol={"strict": "#6250d6", "permissive": "#e87ba4"},
                  phase=["#86b6ef", "#5598e7", "#2a78d6", "#1c5cab", "#104281"], phase_ink=["#0b0b0b"] + ["#ffffff"] * 4),
    "dark": dict(surface="#1a1a19", border="rgba(255,255,255,0.10)", ink="#f0efec", ink2="#c3c2b7",
                 muted="#898781", grid="#2c2c2a", axis="#383835", neutral="#6f6e69", on_fill="#ffffff",
                 lang={"python": "#3987e5", "cpp": "#d95926", "rust": "#199e70"},
                 pol={"strict": "#9085e9", "permissive": "#d55181"},
                 phase=["#184f95", "#256abf", "#3987e5", "#6da7ec", "#9ec5f4"], phase_ink=["#ffffff"] * 3 + ["#0b0b0b"] * 2),
}
LANG_NAME = {"python": "Python", "cpp": "C++17", "rust": "Rust"}
LANGS = ["python", "cpp", "rust"]


def tsv(path):
    return list(csv.DictReader(open(path), delimiter="\t"))


def fmt_int(x):
    return f"{x:,.0f}"


def tw(text, size):
    """Approximate rendered text width (px) for layout decisions."""
    return len(text) * size * 0.56


class Svg:
    def __init__(self, t, h, title, subtitle, source):
        self.t, self.h, self.parts = t, h, []
        self.parts.append(f'<rect x="0.5" y="0.5" width="{W - 1}" height="{h - 1}" rx="12" fill="{t["surface"]}" stroke="{t["border"]}"/>')
        self.text(28, 38, title, 17, t["ink"], weight=600)
        if subtitle:
            self.text(28, 60, subtitle, 12.5, t["ink2"])
        if source:
            self.text(28, h - 16, source, 11, t["muted"])

    def text(self, x, y, s, size, fill, anchor="start", weight=400, baseline=None):
        b = f' dominant-baseline="{baseline}"' if baseline else ""
        s = s.replace("&", "&amp;").replace("<", "&lt;")
        self.parts.append(f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" font-weight="{weight}" fill="{fill}" '
                          f'text-anchor="{anchor}"{b}>{s}</text>')

    def line(self, x1, y1, x2, y2, stroke, width=1, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.parts.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{stroke}" stroke-width="{width}"{d}/>')

    def path(self, d, stroke="none", fill="none", width=2, opacity=None, extra=""):
        o = f' opacity="{opacity}"' if opacity is not None else ""
        self.parts.append(f'<path d="{d}" stroke="{stroke}" fill="{fill}" stroke-width="{width}" '
                          f'stroke-linejoin="round" stroke-linecap="round"{o}{extra}/>')

    def bar_h(self, x, y, w, h, fill, round_right=True, r=4):
        """Horizontal bar anchored at x (square baseline end, rounded data end)."""
        r = min(r, w / 2, h / 2) if round_right else 0
        self.path(f"M{x:.1f},{y:.1f} H{x + w - r:.1f} Q{x + w:.1f},{y:.1f} {x + w:.1f},{y + r:.1f} "
                  f"V{y + h - r:.1f} Q{x + w:.1f},{y + h:.1f} {x + w - r:.1f},{y + h:.1f} H{x:.1f} Z", fill=fill, width=0)

    def bar_v(self, x, y0, w, hgt, fill, r=4):
        """Vertical column anchored at baseline y0 (rounded top)."""
        r = min(r, w / 2, hgt)
        y = y0 - hgt
        self.path(f"M{x:.1f},{y0:.1f} V{y + r:.1f} Q{x:.1f},{y:.1f} {x + r:.1f},{y:.1f} H{x + w - r:.1f} "
                  f"Q{x + w:.1f},{y:.1f} {x + w:.1f},{y + r:.1f} V{y0:.1f} Z", fill=fill, width=0)

    def dot(self, x, y, fill):
        self.parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4.5" fill="{fill}" stroke="{self.t["surface"]}" stroke-width="2"/>')

    def swatch_legend(self, x, y, items, kind="line"):
        for label, color in items:
            if kind == "line":
                self.line(x, y, x + 18, y, color, 2.5)
                self.dot(x + 9, y, color)
            else:
                self.parts.append(f'<rect x="{x:.1f}" y="{y - 6:.1f}" width="12" height="12" rx="3" fill="{color}"/>')
            self.text(x + 26, y, label, 12.5, self.t["ink2"], baseline="central")
            x += 26 + tw(label, 12.5) + 22

    def render(self, desc):
        body = "\n".join(self.parts)
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {self.h}" width="{W}" height="{self.h}" '
                f'role="img" font-family="{FONT}">\n<title>{desc}</title>\n{body}\n</svg>\n')


# ---------------------------------------------------------------- data

def load():
    rs = {(r["workload"], r["impl"]): r for r in tsv(ANA / "runtime_summary.tsv")}
    sp = tsv(ANA / "speedup.tsv")
    rq1 = tsv(ANA / "rq1_replicate_stats.tsv")
    meta = json.load(open(RES / "metadata.json"))
    cross = tsv(RES / "cross_language.tsv")
    usage = [r for r in csv.DictReader(open(ROOT / "results" / "agent_usage.csv"))]
    return rs, sp, rq1, meta, cross, usage


SOURCE = f"Source: Modal run {RUN} (1 vCPU, Debian, GCC 12.2, Rust 1.99.1, Python 3.12) · median of 7 runs"


# ---------------------------------------------------------------- figures

def fig_hero(t, d):
    rs, sp, _, _, cross, usage = d
    best = max(sp, key=lambda r: float(r["rust_vs_python_search"]))
    rust_x, cpp_x = float(best["rust_vs_python_search"]), float(best["cpp_vs_python_search"])
    thr = {i: float(rs[("stress_s800000", i)]["throughput_states_per_s_median"]) / 1e6 for i in LANGS}
    ident = sum(1 for r in cross if r["result"] == "identical")
    tok = sum(int(r["total_tokens"]) for r in usage if r["total_tokens"].isdigit())
    tiles = [
        (f"{rust_x:.0f}×", "faster search than Python", "Rust, stress graph", f"C++ {cpp_x:.0f}×"),
        (f"{thr['rust']:.1f} M", "search states per second", f"Rust · C++ {thr['cpp']:.1f} M", f"Python {thr['python']:.2f} M"),
        (f"{ident} / {len(cross)}", "workloads byte-identical", "outputs of Python,", "C++ and Rust"),
        (f"{tok / 1000:.0f} k", "agent tokens recorded", "lower bound:", "Opus usage not exposed"),
    ]
    h = 164
    s = Svg(t, h, "", "", "")
    s.parts = s.parts[:1]
    tile_w, gap, x0 = (W - 2 * 20 - 3 * 12) / 4, 12, 20
    for i, (big, label, n1, n2) in enumerate(tiles):
        x = x0 + i * (tile_w + gap)
        s.parts.append(f'<rect x="{x:.1f}" y="20" width="{tile_w:.1f}" height="{h - 40}" rx="10" fill="none" stroke="{t["border"]}"/>')
        s.text(x + 18, 66, big, 34, t["ink"], weight=650)
        s.text(x + 18, 92, label, 13, t["ink2"], weight=500)
        s.text(x + 18, 112, n1, 11, t["muted"])
        s.text(x + 18, 127, n2, 11, t["muted"])
    return s.render("ColorFrame key numbers: " + "; ".join(f"{b} {l} ({n1} {n2})" for b, l, n1, n2 in tiles))


def fig_scaling(t, d):
    rs = d[0]
    ns = [50, 200, 500, 2000, 10000]
    h = 420
    s = Svg(t, h, "Search time grows linearly with graph size, in every language",
            "Median search-phase time (ms) on high-branching synthetic graphs · log–log scale", SOURCE)
    L, R, T, B = 78, W - 150, 112, h - 82
    xmin, xmax, ymin, ymax = math.log10(40), math.log10(12500), math.log10(0.1), math.log10(3000)
    X = lambda n: L + (math.log10(n) - xmin) / (xmax - xmin) * (R - L)
    Y = lambda v: B - (math.log10(v) - ymin) / (ymax - ymin) * (B - T)
    for v, lab in [(0.1, "0.1"), (1, "1"), (10, "10"), (100, "100"), (1000, "1,000")]:
        s.line(L, Y(v), R, Y(v), t["grid"])
        s.text(L - 10, Y(v), lab, 11, t["muted"], anchor="end", baseline="central")
    s.line(L, B, R, B, t["axis"])
    for n in ns:
        s.text(X(n), B + 20, fmt_int(n), 11, t["muted"], anchor="middle")
    s.text((L + R) / 2, B + 40, "nodes in graph", 11.5, t["ink2"], anchor="middle")
    s.swatch_legend(28, 84, [(LANG_NAME[i], t["lang"][i]) for i in LANGS])
    ends = []
    for i in LANGS:
        pts = [(X(n), Y(float(rs[(f"perf_n{n}_high", i)]["search_ms_median"]))) for n in ns]
        s.path("M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts), stroke=t["lang"][i], width=2)
        for x, y in pts:
            s.dot(x, y, t["lang"][i])
        ends.append([pts[-1][1], i, float(rs[(f"perf_n10000_high", i)]["search_ms_median"])])
    ends.sort()
    for k in range(1, len(ends)):                       # separate colliding end labels, with connectors
        ends[k][0] = max(ends[k][0], ends[k - 1][0] + 18)
    for ly, i, v in ends:
        s.line(R + 6, Y(v), R + 14, ly, t["axis"])
        s.text(R + 18, ly, f"{LANG_NAME[i]}  {v:,.0f} ms", 12, t["ink"], baseline="central", weight=500)
    return s.render("Line chart: median search time versus graph size for Python, C++ and Rust; at 10,000 nodes "
                    + ", ".join(f"{LANG_NAME[i]} {float(rs[('perf_n10000_high', i)]['search_ms_median']):.0f} ms" for i in LANGS))


def fig_phases(t, d):
    rs = d[0]
    wl = "perf_n10000_high"
    phases = ["parse", "validate", "search", "canonicalize", "write"]
    h = 268
    s = Svg(t, h, "Where the time goes on a 10,000-node graph",
            "Share of in-process time by pipeline phase (56,264 candidates written); total at right", SOURCE)
    s.swatch_legend(28, 84, [(p, t["phase"][k]) for k, p in enumerate(phases)], kind="box")
    L, R, y, bh = 104, W - 128, 112, 24
    for i in LANGS:
        r = rs[(wl, i)]
        tot = float(r["total_ms_median"])
        vals = {p: float(r[f"{p}_ms_median"]) for p in phases[:-1]}
        vals["write"] = tot - sum(vals.values())
        s.text(L - 12, y + bh / 2, LANG_NAME[i], 12.5, t["ink"], anchor="end", baseline="central", weight=500)
        x = L
        for k, p in enumerate(phases):
            w = vals[p] / tot * (R - L)
            last = k == len(phases) - 1
            s.bar_h(x, y, max(w - (0 if last else 2), 0.5), bh, t["phase"][k], round_right=last)
            pct = vals[p] / tot * 100
            lab = f"{p} {pct:.0f}%" if w > tw(f"{p} {pct:.0f}%", 11) + 14 else (f"{pct:.0f}%" if w > tw("00%", 11) + 10 else "")
            if lab:
                s.text(x + w / 2 - 1, y + bh / 2, lab, 11, t["phase_ink"][k], anchor="middle", baseline="central", weight=500)
            x += w
        s.text(R + 12, y + bh / 2, f"{tot:,.0f} ms", 12.5, t["ink"], baseline="central", weight=600)
        y += bh + 18
    return s.render("Stacked bars: share of time per phase on the 10,000-node graph; totals "
                    + ", ".join(f"{LANG_NAME[i]} {float(rs[(wl, i)]['total_ms_median']):.0f} ms" for i in LANGS))


def fig_memory(t, d):
    rs, meta = d[0], d[3]
    base = meta["measurement_baselines"]
    groups = [("stress_s800000", "stress graph", "800,000 search states"),
              ("perf_n500_high", "500-node graph", "2,579 candidates"),
              ("perf_n10000_high", "10,000-node graph", "56,264 candidates")]
    h = 356
    s = Svg(t, h, "Peak memory: small for the search, dominated by stored candidates",
            f"Whole-process peak RSS (MB), measured through /usr/bin/time · floor {base['wrapper_floor_true']['peak_rss_mb_median']:.1f} MB, "
            f"Python interpreter alone {base['python_interpreter']['peak_rss_mb_median']:.1f} MB", SOURCE)
    s.swatch_legend(28, 84, [(LANG_NAME[i], t["lang"][i]) for i in LANGS], kind="box")
    L, R, T, B = 70, W - 30, 124, h - 84
    vmax = 120
    Y = lambda v: B - v / vmax * (B - T)
    for v in (0, 30, 60, 90, 120):
        s.line(L, Y(v), R, Y(v), t["grid"] if v else t["axis"])
        s.text(L - 10, Y(v), str(v), 11, t["muted"], anchor="end", baseline="central")
    gw = (R - L) / len(groups)
    cw, gap = 24, 6
    for g, (wl, name, note) in enumerate(groups):
        cx = L + gw * g + gw / 2
        x = cx - (3 * cw + 2 * gap) / 2
        for i in LANGS:
            v = float(rs[(wl, i)]["peak_rss_mb_median"])
            s.bar_v(x, B, cw, Y(0) - Y(v), t["lang"][i])
            s.text(x + cw / 2, Y(v) - 7, f"{v:.0f}" if v >= 10 else f"{v:.1f}", 11, t["ink2"], anchor="middle", weight=500)
            x += cw + gap
        s.text(cx, B + 20, name, 12, t["ink"], anchor="middle", weight=500)
        s.text(cx, B + 36, note, 11, t["muted"], anchor="middle")
    return s.render("Grouped columns: peak memory in MB per implementation for three workloads")


def fig_rq1(t, d):
    rq1 = d[2]

    def series(cond, pol, metric):
        rows = sorted((r for r in rq1 if r["condition"] == cond and r["policy"] == pol and r["metric"] == metric),
                      key=lambda r: float(r["p_true_observation"]))
        return [(float(r["p_true_observation"]), float(r["mean"]), max(0.0, float(r["ci95_low"]) if r["ci95_low"] not in ("", "NA") else float(r["mean"])),
                 float(r["ci95_high"]) if r["ci95_high"] not in ("", "NA") else float(r["mean"])) for r in rows]

    h = 392
    s = Svg(t, h, "Strict vs permissive support on synthetic ground truth (RQ1)",
            "10 paired replicates × 100 planted ORFs · mean and exploratory 95% interval",
            f"Source: Modal run {RUN}, rq1_replicate_stats.tsv · synthetic recovery only, not gene validation")
    s.swatch_legend(28, 84, [("strict: one sample shared by all nodes", t["pol"]["strict"]),
                             ("permissive: some sample on every node", t["pol"]["permissive"])])
    panels = [("clean", "true_ceiling", "Clean: planted ORFs meeting the policy's true-sample criterion", 100, [0, 25, 50, 75, 100]),
              ("noisy", "recovered_via_spurious_only", "Noisy: recovered without meeting that criterion", 15, [0, 5, 10, 15])]
    pw = (W - 56 - 40) / 2
    for k, (cond, metric, ptitle, vmax, ticks) in enumerate(panels):
        L = 28 + 36 + k * (pw + 40)
        R, T, B = L + pw - 36, 140, h - 74
        X = lambda p: L + p * (R - L)
        Y = lambda v: B - v / vmax * (B - T)
        s.text(L - 36, 120, ptitle, 12.5, t["ink"], weight=600)
        for v in ticks:
            s.line(L, Y(v), R, Y(v), t["grid"] if v else t["axis"])
            s.text(L - 8, Y(v), str(v), 11, t["muted"], anchor="end", baseline="central")
        for p in (0.1, 0.3, 0.5, 0.7, 0.9):
            s.text(X(p), B + 18, f"{p:.1f}", 11, t["muted"], anchor="middle")
        s.text((L + R) / 2, B + 36, "probability a true sample is observed on a node", 11, t["ink2"], anchor="middle")
        for pol in ("strict", "permissive"):
            pts = series(cond, pol, metric)
            c = t["pol"][pol]
            band = "M" + " L".join(f"{X(p):.1f},{Y(hi):.1f}" for p, _, _, hi in pts) + " L" + \
                   " L".join(f"{X(p):.1f},{Y(lo):.1f}" for p, _, lo, _ in reversed(pts)) + " Z"
            s.path(band, fill=c, width=0, opacity=0.16)
            s.path("M" + " L".join(f"{X(p):.1f},{Y(m):.1f}" for p, m, _, _ in pts), stroke=c, width=2)
            for p, m, _, _ in pts:
                s.dot(X(p), Y(m), c)
        if cond == "clean":
            at = {pol: next(m for p, m, _, _ in series(cond, pol, metric) if abs(p - 0.3) < 1e-9) for pol in ("strict", "permissive")}
            s.text(X(0.3) + 10, Y(at["permissive"]) - 6, f"{at['permissive']:.1f}", 11.5, t["ink"], weight=600)
            s.text(X(0.3) + 10, Y(at["strict"]) + 14, f"{at['strict']:.1f}", 11.5, t["ink"], weight=600)
        else:
            pk = max(series(cond, "permissive", metric), key=lambda r: r[1])
            s.text(X(pk[0]) + 10, Y(pk[1]) - 8, f"{pk[1]:.1f} per replicate", 11.5, t["ink"], weight=600)
    return s.render("RQ1: planted ORFs meeting the strict and permissive true-support criteria versus observation probability, "
                    "and ORFs recovered without the criterion under noise")


def fig_tokens(t, d):
    usage = d[5]
    done = {}
    for r in usage:
        if r["total_tokens"].isdigit():
            done[r["agent"]] = (int(r["total_tokens"]), float(r["duration_seconds"]), r["model"])
    rows = [("python-agent", "Python implementation", "python"), ("cpp-agent", "C++17 implementation", "cpp"),
            ("rust-agent", "Rust implementation", "rust"), ("lit-agent", "Literature verification", None),
            ("ci-agent", "CI and Makefile", None), ("dev-agent-coordinator", "Spec, review, analysis, remediation", None)]
    model = {"claude-sonnet-5-5": "Sonnet", "claude-haiku-5-5": "Haiku", "claude-opus-5-5": "Opus"}
    h = 372
    s = Svg(t, h, "AI-assisted development: recorded tokens and agent time",
            "Completed agent legs only · legs cut off without usage data are not counted, so totals are lower bounds",
            "Source: results/agent_usage.csv · descriptive process record, not a comparison of languages")
    L, R, y, bh = 268, W - 190, 92, 22
    vmax = 140000
    for k in range(0, 140001, 35000):
        x = L + k / vmax * (R - L)
        s.line(x, y - 6, x, y + 6 * (bh + 14) - 6, t["grid"] if k else t["axis"])
        s.text(x, y + 6 * (bh + 14) + 12, f"{k // 1000} k" if k else "0", 11, t["muted"], anchor="middle")
    s.text((L + R) / 2, y + 6 * (bh + 14) + 30, "tokens", 11, t["ink2"], anchor="middle")
    for agent, label, lang in rows:
        s.text(L - 12, y + bh / 2 - 7, label, 12.5, t["ink"], anchor="end", baseline="central", weight=500)
        mdl = "Opus" if agent == "dev-agent-coordinator" else model.get(done.get(agent, (0, 0, ""))[2], "")
        s.text(L - 12, y + bh / 2 + 9, mdl, 11, t["muted"], anchor="end", baseline="central")
        if agent in done:
            tok, sec, _ = done[agent]
            w = tok / vmax * (R - L)
            s.bar_h(L, y, w, bh, t["lang"][lang] if lang else t["neutral"])
            s.text(L + w + 10, y + bh / 2, f"{tok / 1000:.0f} k tokens · {sec:.0f} s", 12, t["ink"], baseline="central", weight=500)
        else:
            s.parts.append(f'<rect x="{L:.1f}" y="{y:.1f}" width="{(R - L) * 0.5:.1f}" height="{bh}" rx="4" fill="none" '
                           f'stroke="{t["muted"]}" stroke-dasharray="4 3"/>')
            s.text(L + 12, y + bh / 2, "not exposed by the harness", 11.5, t["ink2"], baseline="central")
        y += bh + 14
    return s.render("Horizontal bars: recorded tokens and duration per AI agent; coordinator usage not exposed")


FIGS = {"hero": fig_hero, "scaling": fig_scaling, "phases": fig_phases, "memory": fig_memory, "rq1": fig_rq1, "tokens": fig_tokens}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "docs" / "figures"))
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)
    d = load()
    for name, fn in FIGS.items():
        for mode, t in THEMES.items():
            (out / (f"{name}.svg" if mode == "light" else f"{name}-dark.svg")).write_text(fn(t, d))
    print(f"wrote {2 * len(FIGS)} figures to {out}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
plots_task2.py

Parses trace1..trace4 from two directories:
 - outputs/no_prefetcher/         (exclusive)
 - outputs_latest/exclusive_no/   (non-inclusive baseline)

Creates:
 - Beautiful side-by-side plots for IPC, L1D MPKI, L2 MPKI, LLC MPKI
 - A polished IPC speedup plot with values written above each bar (3 decimals)
 - A high-quality PNG summary table (unchanged behavior)

Saves everything to: outputs_latest/plots_task2/
"""

import re
import os
import glob
import math
import numpy as np
import pandas as pd

# Use non-interactive backend early to avoid Qt warnings on headless machines
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import rcParams

# --- Config: adjust if necessary ---
DIR_NONINCLUSIVE = "outputs/no_prefetcher"
DIR_EXCLUSIVE = "outputs_latest/exclusive_no"
OUTPUT_DIR = "outputs_latest/plots_task2"
TRACE_FILENAMES = ["trace1.txt", "trace2.txt", "trace3.txt", "trace4.txt"]  # expected file names
# -----------------------------------

os.makedirs(OUTPUT_DIR, exist_ok=True)

# plotting defaults for a polished look
rcParams.update({
    "font.size": 11,
    "axes.titlesize": 14,
    "axes.labelsize": 11,
    "legend.fontsize": 10,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "figure.dpi": 150,
})

# Choose a colorblind-friendly palette (matplotlib's tab10 is good)
PALETTE = plt.get_cmap("tab10")
COLOR_EXCL = PALETTE(0)   # exclusive
COLOR_NONINC = PALETTE(1) # non-inclusive
SPEEDUP_COLOR = PALETTE(4)

def parse_metrics_from_text(text):
    """Return dict with keys: ipc, l1d_mpki, l2_mpki, llc_mpki (float or np.nan)."""
    def search_first(pattern, text, flags=0):
        m = re.search(pattern, text, flags)
        return m.group(1) if m else None

    ipc_s = search_first(r"CPU\s*0\s+cumulative\s+IPC:\s*([0-9]*\.?[0-9]+)", text)
    if ipc_s is None:
        ipc_s = search_first(r"cumulative\s+IPC:\s*([0-9]*\.?[0-9]+)", text)

    l1d_s = search_first(r"L1D(?:\s+TOTAL)?[\s\S]{0,200}?MPKI:\s*([0-9]*\.?[0-9]+)", text)
    l2_s = search_first(r"L2C(?:\s+TOTAL)?[\s\S]{0,200}?MPKI:\s*([0-9]*\.?[0-9]+)", text)
    if l2_s is None:
        l2_s = search_first(r"\nL2(?:\s+TOTAL)?[\s\S]{0,200}?MPKI:\s*([0-9]*\.?[0-9]+)", text)
    llc_s = search_first(r"LLC(?:\s+TOTAL)?[\s\S]{0,200}?MPKI:\s*([0-9]*\.?[0-9]+)", text)

    def tofloat(s):
        try:
            return float(s) if s is not None else np.nan
        except:
            return np.nan

    return {
        "ipc": tofloat(ipc_s),
        "l1d_mpki": tofloat(l1d_s),
        "l2_mpki": tofloat(l2_s),
        "llc_mpki": tofloat(llc_s),
    }

def parse_file(path):
    if not os.path.isfile(path):
        return None
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        text = f.read()
    return parse_metrics_from_text(text)

def collect_for_dir(directory, label):
    rows = []
    # try expected filenames first
    for fname in TRACE_FILENAMES:
        p = os.path.join(directory, fname)
        if os.path.isfile(p):
            trace_no = int(re.search(r"trace(\d+)\.txt", fname).group(1))
            parsed = parse_file(p)
            if parsed is None:
                parsed = {"ipc": np.nan, "l1d_mpki": np.nan, "l2_mpki": np.nan, "llc_mpki": np.nan}
            parsed.update({"trace": trace_no, "policy": label, "file": p})
            rows.append(parsed)
    # fallback: glob trace*.txt
    if len(rows) == 0:
        for p in sorted(glob.glob(os.path.join(directory, "trace*.txt"))):
            m = re.search(r"trace(\d+)\.txt", os.path.basename(p))
            trace_no = int(m.group(1)) if m else None
            parsed = parse_file(p)
            if parsed is None:
                parsed = {"ipc": np.nan, "l1d_mpki": np.nan, "l2_mpki": np.nan, "llc_mpki": np.nan}
            parsed.update({"trace": trace_no, "policy": label, "file": p})
            rows.append(parsed)
    rows = sorted(rows, key=lambda r: (r["trace"] if r["trace"] is not None else 999))
    return rows

# collect data
exclusive_rows = collect_for_dir(DIR_EXCLUSIVE, "exclusive")
noninc_rows = collect_for_dir(DIR_NONINCLUSIVE, "noninclusive")

if not exclusive_rows and not noninc_rows:
    raise SystemExit("No trace files found in either directory. Please check paths.")

df = pd.DataFrame(exclusive_rows + noninc_rows)
df['trace'] = df['trace'].astype(pd.Int64Dtype())

# plotting utilities
def plot_side_by_side(df, metric_key, metric_label, output_path):
    pivot = df.pivot(index='trace', columns='policy', values=metric_key).sort_index()
    traces = pivot.index.tolist()
    n = len(traces)
    # ensure both columns exist
    for p in ["exclusive", "noninclusive"]:
        if p not in pivot.columns:
            pivot[p] = np.nan

    x = np.arange(n)
    width = 0.36

    fig, ax = plt.subplots(figsize=(max(7, n*1.4), 5))
    bars1 = ax.bar(x - width/2, pivot["exclusive"].values, width,
                   label="exclusive", color=COLOR_EXCL, edgecolor='k', linewidth=0.4)
    bars2 = ax.bar(x + width/2, pivot["noninclusive"].values, width,
                   label="non-inclusive (baseline)", color=COLOR_NONINC, edgecolor='k', linewidth=0.4, alpha=0.95)

    # Add small value labels on top of bars (optional - smaller font)
    for bar in list(bars1) + list(bars2):
        h = bar.get_height()
        if not np.isnan(h):
            ax.text(bar.get_x() + bar.get_width()/2, h + (0.015 * max(1.0, h)), f"{h:.2f}",
                    ha='center', va='bottom', fontsize=9, color='black', alpha=0.9)

    # cosmetics
    ax.set_xticks(x)
    tick_labels = [str(int(t)) if (not pd.isna(t)) else "?" for t in traces]
    ax.set_xticklabels(tick_labels)
    ax.set_xlabel("Trace number")
    ax.set_ylabel(metric_label)
    ax.set_title(f"{metric_label}: exclusive vs non-inclusive", pad=14)
    ax.legend(frameon=True, edgecolor='#444444')
    ax.grid(axis='y', linestyle='--', linewidth=0.6, alpha=0.6)
    # subtle shadow effect - draw a faint rectangle behind
    ax.set_axisbelow(True)
    plt.tight_layout()
    fig.savefig(output_path, dpi=300, bbox_inches='tight', pad_inches=0.15)
    plt.close(fig)
    print(f"Saved plot: {output_path}")

# nicer speedup plot with 3-decimal labels
def plot_ipc_speedup(df, output_path):
    pivot_ipc = df.pivot(index='trace', columns='policy', values='ipc').sort_index()
    # ensure both columns exist
    for p in ["exclusive", "noninclusive"]:
        if p not in pivot_ipc.columns:
            pivot_ipc[p] = np.nan
    speedup = pivot_ipc["exclusive"] / pivot_ipc["noninclusive"]
    speedup = speedup.replace([np.inf, -np.inf], np.nan)

    traces = speedup.index.tolist()
    x = np.arange(len(traces))

    fig, ax = plt.subplots(figsize=(max(7, len(traces)*1.4), 5))

    bars = ax.bar(x, speedup.values, width=0.6, color=SPEEDUP_COLOR, edgecolor='k', linewidth=0.6)
    # annotate each bar with 3 decimal places, centered above bar
    for bar, val in zip(bars, speedup.values):
        h = 0 if np.isnan(val) else val
        label = "-" if np.isnan(val) else f"{val:.3f}"
        # position label slightly above bar top
        ax.text(bar.get_x() + bar.get_width()/2, h + 0.02 * max(1.0, np.nanmax(speedup.values[~np.isnan(speedup.values)]) if np.any(~np.isnan(speedup.values)) else 1.0),
                label, ha='center', va='bottom', fontsize=10, fontweight='bold', color='black')

    # draw reference line at speedup = 1.0
    ax.axhline(1.0, linestyle='--', linewidth=1.0, color='#333333', alpha=0.7)
    ax.text(0.98, 1.02, "baseline = 1.0", ha='right', va='bottom', transform=ax.get_yaxis_transform(), fontsize=9, color='#333333')

    ax.set_xticks(x)
    tick_labels = [str(int(t)) if (not pd.isna(t)) else "?" for t in traces]
    ax.set_xticklabels(tick_labels)
    ax.set_xlabel("Trace number")
    ax.set_ylabel("IPC speedup (exclusive / non-inclusive)")
    ax.set_title("IPC speedup: exclusive / non-inclusive (baseline)", pad=14)
    ax.grid(axis='y', linestyle='--', linewidth=0.6, alpha=0.6)
    plt.tight_layout()
    fig.savefig(output_path, dpi=300, bbox_inches='tight', pad_inches=0.12)
    plt.close(fig)
    print(f"Saved speedup plot: {output_path}")

# Create the plots
metrics = [
    ("ipc", "Cumulative IPC"),
    ("l1d_mpki", "L1D MPKI"),
    ("l2_mpki", "L2 (L2C) MPKI"),
    ("llc_mpki", "LLC MPKI"),
]

for key, label in metrics:
    out_png = os.path.join(OUTPUT_DIR, f"{key}.png")
    plot_side_by_side(df, key, label, out_png)

speedup_png = os.path.join(OUTPUT_DIR, "ipc_speedup.png")
plot_ipc_speedup(df, speedup_png)

# ------------------------
# Build a single combined summary table (per-trace)
# ------------------------
def build_summary_table(df):
    def pivot_metric(metric):
        p = df.pivot(index='trace', columns='policy', values=metric).sort_index()
        for c in ["exclusive", "noninclusive"]:
            if c not in p.columns:
                p[c] = np.nan
        return p.rename(columns={"exclusive": f"exclusive_{metric}", "noninclusive": f"noninclusive_{metric}"})

    p_ipc = pivot_metric("ipc")
    p_l1d = pivot_metric("l1d_mpki")
    p_l2  = pivot_metric("l2_mpki")
    p_llc = pivot_metric("llc_mpki")

    combined = pd.concat([p_ipc, p_l1d, p_l2, p_llc], axis=1)
    combined["speedup_ipc"] = combined["exclusive_ipc"] / combined["noninclusive_ipc"]
    combined = combined.reset_index().rename(columns={"trace": "Trace"})
    cols = ["Trace",
            "exclusive_ipc", "noninclusive_ipc", "speedup_ipc",
            "exclusive_l1d_mpki", "noninclusive_l1d_mpki",
            "exclusive_l2_mpki", "noninclusive_l2_mpki",
            "exclusive_llc_mpki", "noninclusive_llc_mpki"]
    existing_cols = [c for c in cols if c in combined.columns]
    combined = combined[existing_cols]
    return combined

summary_df = build_summary_table(df)

def format_val(col, v):
    if pd.isna(v):
        return "-"
    if "ipc" in col and "speedup" not in col:
        return f"{v:.3f}"
    if "speedup" in col:
        return f"{v:.3f}"
    if "mpki" in col:
        return f"{v:.2f}"
    return f"{v}"

display_df = summary_df.copy()
for col in display_df.columns:
    display_df[col] = display_df[col].apply(lambda v, c=col: format_val(c, v))

# Save table PNG (robust version)
def save_table_png(table_df: pd.DataFrame, outpath: str, title: str = None, dpi: int = 300):
    nrows, ncols = table_df.shape
    col_width = 1.6
    row_height = 0.45
    header_height = 0.8
    fig_w = max(6, ncols * col_width)
    fig_h = max(2.4, nrows * row_height + header_height)

    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    ax.axis('off')

    if title:
        ax.text(0.5, 0.98, title, fontsize=14, fontweight='bold',
                ha='center', va='top', transform=fig.transFigure)

    header_color = "#2E4053"
    header_text_color = "white"
    row_colors = ["#ffffff", "#f7fbfc"]

    cell_text = table_df.values.tolist()
    col_labels = table_df.columns.tolist()

    # equal column widths
    col_widths = [1.0 / max(1, ncols)] * ncols
    the_table = ax.table(cellText=cell_text,
                         colLabels=col_labels,
                         loc='center',
                         cellLoc='center',
                         colWidths=col_widths)

    the_table.auto_set_font_size(False)
    font_size = max(8, min(12, int(180 / max(6, ncols))))
    the_table.set_fontsize(font_size)

    for (row, col), cell in the_table.get_celld().items():
        if row == 0:
            cell.set_facecolor(header_color)
            cell.set_text_props(weight='bold', color=header_text_color)
            cell.set_height(header_height / fig_h)
        else:
            cell.set_facecolor(row_colors[(row - 1) % 2])
            if col == 0:
                cell.set_text_props(weight='bold')

    the_table.scale(1, 1.15)
    plt.tight_layout()
    fig.savefig(outpath, dpi=dpi, bbox_inches='tight', pad_inches=0.3)
    plt.close(fig)
    print(f"Saved table PNG: {outpath}")

table_png_path = os.path.join(OUTPUT_DIR, "metrics_summary_table.png")
title = "Per-trace metrics: Exclusive vs Non-Inclusive (speedup = exclusive / non-inclusive)"
save_table_png(display_df, table_png_path, title=title, dpi=300)

print("Done. Files saved to:", OUTPUT_DIR)
print("Plots:")
for name in ["ipc.png", "l1d_mpki.png", "l2_mpki.png", "llc_mpki.png", "ipc_speedup.png", "metrics_summary_table.png"]:
    print(" -", os.path.join(OUTPUT_DIR, name))

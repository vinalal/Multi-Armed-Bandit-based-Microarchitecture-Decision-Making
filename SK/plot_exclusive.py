import os
import re
import glob
import matplotlib.pyplot as plt
import numpy as np

def parse_final_ipc(filepath):
    """
    Parses a ChampSim output file to find the final cumulative IPC value.

    Args:
        filepath (str): The path to the simulation output file.

    Returns:
        float: The final cumulative IPC, or None if not found.
    """
    cumulative_ipc = None
    try:
        with open(filepath, 'r') as f:
            # Read all lines to easily find the last occurrence
            lines = f.readlines()
            # Iterate backwards through the file to find the last IPC entry efficiently
            for line in reversed(lines):
                if "cumulative IPC" in line:
                    match = re.search(r"cumulative IPC: (\d+\.\d+)", line)
                    if match:
                        cumulative_ipc = float(match.group(1))
                        break # Found the last one, no need to continue
    except FileNotFoundError:
        print(f"Warning: Could not find the file: {filepath}")
        return None
    
    return cumulative_ipc

def generate_plot():
    """
    Generates and saves a bar chart comparing the speedup of an exclusive
    cache policy relative to a non-inclusive (baseline) policy.
    """
    # --- 1. Setup Directories ---
    baseline_dir = "outputs/exclusive_no"
    exclusive_dir = "outputs/exclusive_offset_prefetcher"
    plot_dir = "outputs/plots"

    if not os.path.isdir(baseline_dir):
        print(f"Error: Baseline directory not found at '{baseline_dir}'")
        return
    if not os.path.isdir(exclusive_dir):
        print(f"Error: Exclusive cache directory not found at '{exclusive_dir}'")
        return

    os.makedirs(plot_dir, exist_ok=True)

    # --- 2. Data Extraction and Speedup Calculation ---
    trace_files = sorted(glob.glob(os.path.join(baseline_dir, "trace*.txt")))
    trace_files_prefetch = sorted(glob.glob(os.path.join(exclusive_dir, "trace*.txt")))
    
    if not trace_files:
        print(f"Error: No trace files found in '{baseline_dir}'. Make sure your simulation outputs are there.")
        return

    results = {}
    for prefetch_filepath, baseline_filepath in zip(trace_files_prefetch, trace_files):
        filename = os.path.basename(prefetch_filepath)
        exclusive_filepath = os.path.join(exclusive_dir, filename)

        ipc_baseline = parse_final_ipc(baseline_filepath)
        ipc_exclusive = parse_final_ipc(exclusive_filepath)
        
        trace_name = filename.replace('.txt', '') # For cleaner labels on the graph

        if ipc_baseline is not None and ipc_exclusive is not None:
            if ipc_baseline > 0:
                speedup = ipc_exclusive / ipc_baseline
                results[trace_name] = speedup
                print(f"Processed {trace_name}: Baseline IPC={ipc_baseline:.3f}, Exclusive IPC={ipc_exclusive:.3f}, Speedup={speedup:.3f}")
            else:
                print(f"Warning: Baseline IPC for {trace_name} is 0. Cannot calculate speedup.")
        else:
            print(f"Warning: Skipping {trace_name} due to missing data in one of the files.")

    if not results:
        print("Could not generate plot because no valid result pairs were found.")
        return

    # --- 3. Plotting ---
    labels = list(results.keys())
    values = list(results.values())

    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Use a vibrant color palette
    colors = plt.cm.plasma(np.linspace(0.4, 0.9, len(labels)))

    bars = ax.bar(labels, values, color=colors, edgecolor='black', alpha=0.8, width=0.6)

    # Add a horizontal line at y=1.0 for the baseline reference
    ax.axhline(1.0, color='crimson', linestyle='--', linewidth=1.5, zorder=5, label='Baseline (Non-Inclusive)')

    # Add text labels on top of each bar for clarity
    for bar in bars:
        height = bar.get_height()
        # FIX: The 'pad' property is invalid. Added a small offset to the 'height' (y-coordinate) to create padding.
        ax.text(bar.get_x() + bar.get_width() / 2.0, height + 0.02, f'{height:.3f}', ha='center', va='bottom', fontsize=11, fontweight='bold')

    # --- 4. Aesthetics and Labels ---
    ax.set_title('Exclusive Cache with prefetcher Speedup vs. Exclusive Cache no prefetcher', fontsize=14, fontweight='bold', pad=20)
    ax.set_xlabel('Trace Benchmark', fontsize=14, fontweight='bold', labelpad=15)
    ax.set_ylabel('Speedup (IPC Exclusive / IPC Baseline)', fontsize=14, fontweight='bold', labelpad=15)
    
    # Set y-axis limits to better frame the data, ensuring 1.0 is visible
    min_val = min(values) if values else 1.0
    max_val = max(values) if values else 1.0
    ax.set_ylim([min(0.9, min_val - 0.05), max_val + 0.1])
    
    ax.tick_params(axis='x', rotation=30, labelsize=12)
    ax.tick_params(axis='y', labelsize=12)
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    ax.legend(fontsize=12)
    
    fig.tight_layout()

    # --- 5. Save the Plot ---
    output_path = os.path.join(plot_dir, 'plot_task3.png')
    plt.savefig(output_path, dpi=300)
    print(f"\n[Success] Graph saved to: {output_path}")


if __name__ == "__main__":
    generate_plot()


#!/bin/bash

# --- Configuration ---
# The C++ source file containing the parameters to modify.
# IMPORTANT: Make sure this path is correct.
PREFETCHER_FILE="prefetcher/offset_prefetcher.l2c_pref"

# The directory where you want to save the output files.
OUTPUT_DIR="outputs_latest/offset_prefetcher"

# --- Traces to Run ---
# Add or remove trace names from this list.
# TRACES=("trace1" "trace2" "trace3" "trace4")
TRACES=("trace1" "trace2" "trace3" "trace4")

# --- Parameters to Test ---
# Add or remove values from these lists to change the experiments.
TABLE_SIZES=(32 64 128)
SCORE_THRESHOLDS=(4 8)
LOW_DEGREES=(2 3)
HIGH_DEGREES=(4 8)

# --- Automation Logic ---

# Create the output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

# Ensure the prefetcher file exists before starting
if [ ! -f "$PREFETCHER_FILE" ]; then
    echo "❌ ERROR: Prefetcher file not found at '$PREFETCHER_FILE'"
    echo "Please update the PREFETCHER_FILE variable in the script."
    exit 1
fi

echo "🚀 Starting full parameter sweep across all specified traces..."

# Outermost loop for iterating through trace files
for trace_name in "${TRACES[@]}"; do
  TRACE_FILE="../../traces/${trace_name}.champsimtrace.xz"

  # Check if the trace file for this iteration exists
  if [ ! -f "$TRACE_FILE" ]; then
      echo "⚠️ WARNING: Trace file not found at '$TRACE_FILE'. Skipping this trace."
      continue # Skip to the next trace
  fi

  echo "========================================================"
  echo "🏃‍♂️ Processing Trace: $trace_name"
  echo "========================================================"

  # Loop over every combination of parameters for the current trace
  for ts in "${TABLE_SIZES[@]}"; do
    for st in "${SCORE_THRESHOLDS[@]}"; do
      for ld in "${LOW_DEGREES[@]}"; do
        for hd in "${HIGH_DEGREES[@]}"; do

          echo "--------------------------------------------------------"
          echo "🧪 Testing with: TS=$ts, ST=$st, LD=$ld, HD=$hd"
          echo "--------------------------------------------------------"

          # 1. Modify the source code
          sed -i "s/#define TABLE_SIZE .*/#define TABLE_SIZE $ts/" "$PREFETCHER_FILE"
          sed -i "s/#define SCORE_THRESHOLD .*/#define SCORE_THRESHOLD $st/" "$PREFETCHER_FILE"
          sed -i "s/#define LOW_PREFETCH_DEGREE .*/#define LOW_PREFETCH_DEGREE $ld/" "$PREFETCHER_FILE"
          sed -i "s/#define HIGH_PREFETCH_DEGREE .*/#define HIGH_PREFETCH_DEGREE $hd/" "$PREFETCHER_FILE"
          
          # 2. Recompile the simulator
          echo "⚙️  Compiling..."
          ./build_champsim.sh offset_prefetcher
          if [ $? -ne 0 ]; then
              echo "❌ Compilation failed. Aborting."
              git checkout -- "$PREFETCHER_FILE" # Revert changes before exiting
              exit 1
          fi

          # 3. Run the simulation and save the output
          output_file="${OUTPUT_DIR}/${trace_name}_ts${ts}_st${st}_ld${ld}_hd${hd}.txt"
          echo "🏁 Running simulation... Outputting to $output_file"
          
          ./bin/champsim-offset_prefetcher -warmup_instructions 25000000 -simulation_instructions 25000000 -traces "$TRACE_FILE" > "$output_file" 2>&1
          
          echo "✅ Done."

        done
      done
    done
  done
done

echo "*****************************************************"
echo "🎉 All experiments for all traces completed successfully!"
echo "*****************************************************"

# As a good practice, restore the original source file to a default state.
echo "Restoring original source file..."
git checkout -- "$PREFETCHER_FILE"
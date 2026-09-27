#!/usr/bin/env python3
"""Bootstrap Minisim price trajectories from Binance candle closes.

Usage:
    python3 bootstrap.py CANDLES.json OUTPUT_DIR BLOCK_LENGTH TRAJECTORIES
        [SEED] [--ignore]

BLOCK_LENGTH uses d for days or w for weeks, for example 7d or 2w.
The default random seed is 0.
--ignore skips candles whose close time does not advance.
"""

import json
import matplotlib.pyplot as plt
from pathlib import Path
import random
from statistics import median
import sys


arguments = sys.argv[1:]
ignore_nonmonotonic_candles = "--ignore" in arguments

if ignore_nonmonotonic_candles:
    arguments.remove("--ignore")

input_name = arguments[0]
output_dir = Path(arguments[1])
block_length = arguments[2]
number_of_trajectories = int(arguments[3])
seed = int(arguments[4]) if len(arguments) == 5 else 0

period_number = int(block_length[:-1])
period_unit = block_length[-1]
returns_per_period = {
    "d": 24 * 60,
    "w": 7 * 24 * 60,
}[period_unit]
period_name = {"d": "day", "w": "week"}[period_unit]
block_size = period_number * returns_per_period

with open(input_name) as input_file:
    candles = json.load(input_file)

if ignore_nonmonotonic_candles:
    input_candle_count = len(candles)
    increasing_candles = []
    last_close_time = -1

    for candle in candles:
        close_time = int(candle[6])

        if close_time > last_close_time:
            increasing_candles.append(candle)
            last_close_time = close_time

    candles = increasing_candles
    print(
        f"Ignored {input_candle_count - len(candles)} candles "
        "whose close time did not advance"
    )

# Copy the three Binance columns used by the bootstrap.
close_times = []
close_prices = []
volumes = []

for candle in candles:
    close_times.append(int(candle[6]))
    close_prices.append(float(candle[4]))
    volumes.append(candle[5])

# Prices p_0, p_1, p_2, ... become multiplicative returns
# 1, r_1 = p_1/p_0, r_2 = p_2/p_1, ... . The initial 1 only marks
# the starting price, so price_returns stores r_1, r_2, ... .
price_returns = []
return_volumes = []

for i in range(len(close_prices) - 1):
    price_return = close_prices[i + 1] / close_prices[i]
    price_returns.append(price_return)
    return_volumes.append(volumes[i + 1])

time_steps = []

for i in range(len(close_times) - 1):
    time_step = close_times[i + 1] - close_times[i]
    assert time_step > 0  # time is monotone
    time_steps.append(time_step)

# Treat intervals within 10% of the median as uninterrupted data.
usual_time_step = median(time_steps)
shortest_allowed = 0.9 * usual_time_step
longest_allowed = 1.1 * usual_time_step

# time_breaks contains the indexes of returns that cross an interruption.
time_breaks = []

for i, time_step in enumerate(time_steps):
    if time_step < shortest_allowed or time_step > longest_allowed:
        time_breaks.append(i)

# Keep only blocks made entirely from uninterrupted consecutive returns.
block_starts = []

for block_start in range(len(price_returns) - block_size + 1):
    block_end = block_start + block_size
    block_crosses_break = False

    for time_break in time_breaks:
        # This block contains return indexes from block_start to block_end - 1.
        if block_start <= time_break < block_end:
            block_crosses_break = True
            break

    if not block_crosses_break:
        block_starts.append(block_start)

print(
    f"Read {len(candles)} candles; usual time step {usual_time_step:g}; "
    f"found {len(time_breaks)} time breaks"
)

output_dir.mkdir(parents=True, exist_ok=True)
random.seed(seed)

# We need this for visualization: the heatmap which records
# the source days or weeks used by each real trajectory.
number_of_periods = (
    len(price_returns) + returns_per_period - 1
) // returns_per_period
selection_counts = []

for trajectory_number in range(number_of_trajectories):
    selection_counts.append([0] * number_of_periods)

for trajectory_number in range(1, number_of_trajectories + 1):
    trajectory = [[close_times[0], close_prices[0], volumes[0]]]
    p_0 = close_prices[0]
    p_previous = p_0
    trajectory_selection_counts = selection_counts[trajectory_number - 1]

    # Attach sampled return blocks to get 1, r_1, r_2, r_3, ... .
    while len(trajectory) < len(close_prices):
        block_start = random.choice(block_starts)

        for block_i in range(block_size):
            if len(trajectory) == len(close_prices):
                break

            output_i = len(trajectory)
            return_index = block_start + block_i
            r_i = price_returns[return_index]
            v_i = return_volumes[return_index]
            t_i = close_times[output_i]

            source_period = return_index // returns_per_period
            trajectory_selection_counts[source_period] += 1

            # p_i = p_previous * r_i, so p_i is p_0 multiplied by
            # all sampled returns from r_1 through r_i.
            p_i = p_previous * r_i
            trajectory.append([t_i, p_i, v_i])
            p_previous = p_i

    output_name = output_dir / f"trajectory_{trajectory_number:04d}.json"
    with open(output_name, "w") as output_file:
        json.dump(trajectory, output_file)
        output_file.write("\n")

# core logic end, below only plotting
# Plot the exact source periods selected while writing the trajectories above.
total_selection_counts = [0] * number_of_periods

for period_i in range(number_of_periods):
    for trajectory_selection_counts in selection_counts:
        total_selection_counts[period_i] += trajectory_selection_counts[period_i]

figure, axes = plt.subplots(
    2,
    1,
    figsize=(14, 7),
    gridspec_kw={"height_ratios": [4, 1]},
)

axes[0].imshow(
    selection_counts,
    aspect="auto",
    cmap="Blues",
)
trajectory_tick_step = max(1, number_of_trajectories // 10)
trajectory_ticks = list(range(0, number_of_trajectories, trajectory_tick_step))
axes[0].set_yticks(trajectory_ticks)
axes[0].set_yticklabels([i + 1 for i in trajectory_ticks])
axes[0].set_ylabel("trajectory")
axes[0].set_title(
    f"Source {period_name}s selected by each trajectory (color = sampled returns)"
)

axes[1].imshow([total_selection_counts], aspect="auto", cmap="Blues")
axes[1].set_yticks([])
axes[1].set_xlabel(f"source {period_name}")
axes[1].set_title("Total selection frequency")

for time_break in time_breaks:
    break_position = time_break / returns_per_period
    axes[0].axvline(break_position, color="#D55E00", linewidth=1.5)
    axes[1].axvline(break_position, color="#D55E00", linewidth=1.5)

figure.tight_layout()
heatmap_name = output_dir / "selection_heatmap.png"
figure.savefig(heatmap_name, dpi=140)
print(f"Wrote {heatmap_name}")

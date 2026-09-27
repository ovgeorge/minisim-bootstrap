#!/usr/bin/env python3
"""Visualize moving-block bootstrap selection and price reconstruction.

This fixed example writes docs/bootstrap_animation.gif and
docs/bootstrap_diagram.png. Run it after installing Matplotlib and Pillow.
"""

from pathlib import Path
import random

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
from matplotlib.patches import Rectangle


BLOCK_SIZE = 4
OUTPUT_SIZE = 24
SEED = 5
HEATMAP_TRAJECTORIES = 500

# Return number 11 crosses a time interruption and cannot enter any block.
TIME_BREAKS = [11]
SOURCE_RETURNS = [
    1.012, 0.994, 1.008, 1.016, 0.989, 1.006,
    1.011, 0.997, 1.018, 0.992, 1.005, 1.009,
    0.970, 1.014, 0.996, 1.007, 1.012, 0.991,
    1.004, 1.015, 0.995, 1.010, 0.988, 1.006,
]

# Okabe-Ito colors remain distinguishable for common forms of color blindness.
BLOCK_COLORS = [
    "#0072B2", "#E69F00", "#009E73",
    "#CC79A7", "#D55E00", "#56B4E9",
]
DARK_COLORS = ["#0072B2", "#009E73", "#D55E00"]
EMPTY_COLOR = "#F3F5F7"
GAP_COLOR = "#F4B6AE"
EDGE_COLOR = "#46515C"


# A candidate block is usable only when none of its returns crosses the gap.
block_starts = []

for block_start in range(len(SOURCE_RETURNS) - BLOCK_SIZE + 1):
    block_end = block_start + BLOCK_SIZE
    crosses_break = False

    for time_break in TIME_BREAKS:
        if block_start <= time_break < block_end:
            crosses_break = True
            break

    if not crosses_break:
        block_starts.append(block_start)


# Select the blocks shown in both the animation and the static diagram.
rng = random.Random(SEED)
selected_blocks = []

while len(selected_blocks) * BLOCK_SIZE < OUTPUT_SIZE:
    block_start = rng.choice(block_starts)
    block_returns = SOURCE_RETURNS[block_start:block_start + BLOCK_SIZE]
    selected_blocks.append(
        {
            "start": block_start,
            "returns": block_returns,
            "color": BLOCK_COLORS[len(selected_blocks) % len(BLOCK_COLORS)],
        }
    )


def completed_output(number_of_blocks):
    returns = []
    colors = []

    for block in selected_blocks[:number_of_blocks]:
        returns.extend(block["returns"])
        colors.extend([block["color"]] * len(block["returns"]))

    return returns, colors


all_output_returns, all_output_colors = completed_output(len(selected_blocks))
all_output_prices = [100.0]

for r_i in all_output_returns:
    all_output_prices.append(all_output_prices[-1] * r_i)

source_prices = [100.0]

for r_i in SOURCE_RETURNS:
    source_prices.append(source_prices[-1] * r_i)


def draw_cells(ax, values, colors, gap_indexes):
    for i in range(len(SOURCE_RETURNS)):
        color = EMPTY_COLOR
        label = ""

        if i < len(values):
            color = colors[i]
            label = f"{100 * (values[i] - 1):+.1f}%"

        if i in gap_indexes:
            color = GAP_COLOR
            label = "gap"

        cell = Rectangle((i, 0), 0.92, 1, facecolor=color,
                         edgecolor=EDGE_COLOR, linewidth=1)
        ax.add_patch(cell)
        text_color = "white" if color in DARK_COLORS else "#222222"
        ax.text(i + 0.46, 0.50, label, ha="center", va="center", fontsize=8,
                color=text_color)
        ax.text(i + 0.46, 1.10, str(i), ha="center", va="bottom",
                fontsize=7, color=EDGE_COLOR)


def draw_source(ax, completed_blocks, active_block):
    source_colors = [EMPTY_COLOR] * len(SOURCE_RETURNS)

    if active_block is not None:
        block = selected_blocks[active_block]
        for i in range(block["start"], block["start"] + BLOCK_SIZE):
            source_colors[i] = block["color"]

    price_low = 1.75
    price_high = 3.05
    source_min = min(source_prices)
    source_max = max(source_prices)
    source_price_y = [
        price_low + (price - source_min) / (source_max - source_min)
        * (price_high - price_low)
        for price in source_prices
    ]

    for i in range(len(SOURCE_RETURNS)):
        color = GAP_COLOR if i in TIME_BREAKS else EDGE_COLOR
        line_style = "--" if i in TIME_BREAKS else "-"
        ax.plot([i, i + 1], [source_price_y[i], source_price_y[i + 1]],
                color=color, linestyle=line_style, linewidth=2.5)

    ax.scatter(range(len(source_prices)), source_price_y,
               color="#222222", s=13, zorder=3)

    if active_block is not None:
        block = selected_blocks[active_block]
        for i in range(block["start"], block["start"] + BLOCK_SIZE):
            ax.plot([i, i + 1], [source_price_y[i], source_price_y[i + 1]],
                    color=block["color"], linewidth=4)

    ax.text(0, source_price_y[0] + 0.10, f"p_0 = {source_prices[0]:.1f}",
            ha="left", va="bottom", fontsize=8)
    ax.text(len(SOURCE_RETURNS), source_price_y[-1] + 0.10,
            f"p_{len(SOURCE_RETURNS)} = {source_prices[-1]:.1f}",
            ha="right", va="bottom", fontsize=8)
    ax.text(TIME_BREAKS[0] + 0.5, price_high + 0.10, "time interruption",
            color="#A33A2B", ha="center", va="bottom", fontsize=8)
    ax.text(-0.45, 2.38, "original\nprice path", ha="right", va="center",
            fontsize=9, color=EDGE_COLOR)

    draw_cells(ax, SOURCE_RETURNS, source_colors, TIME_BREAKS)
    ax.text(-0.45, 0.50, "returns", ha="right", va="center",
            fontsize=9, color=EDGE_COLOR)

    history = list(range(completed_blocks))
    if active_block is not None:
        history.append(active_block)

    for row, block_number in enumerate(history):
        block = selected_blocks[block_number]
        y = -0.18 - 0.13 * row
        start = block["start"] + 0.08
        end = block["start"] + BLOCK_SIZE - 0.16
        ax.plot([start, end], [y, y], color=block["color"], linewidth=7,
                solid_capstyle="butt")
        ax.text((start + end) / 2, y, f"B{block_number + 1}", color="white",
                ha="center", va="center", fontsize=7, fontweight="bold")

    ax.set_xlim(-0.2, len(SOURCE_RETURNS) + 0.1)
    ax.set_ylim(-1.05, 3.45)
    ax.set_title("1. Original price path and returns: red marks an interruption",
                 loc="left")
    ax.axis("off")


def draw_output(ax, completed_blocks):
    output_returns, output_colors = completed_output(completed_blocks)
    draw_cells(ax, output_returns, output_colors, [])

    for block_number in range(completed_blocks):
        x = block_number * BLOCK_SIZE + BLOCK_SIZE / 2
        ax.text(x, 1.32, f"B{block_number + 1}", ha="center", va="center",
                color=selected_blocks[block_number]["color"], fontweight="bold")

    ax.set_xlim(-0.2, len(SOURCE_RETURNS) + 0.1)
    ax.set_ylim(-0.25, 1.55)
    ax.set_title("2. Selected blocks are attached in a new order", loc="left")
    ax.axis("off")


def draw_prices(ax, completed_blocks):
    output_returns, output_colors = completed_output(completed_blocks)
    prices = [100.0]

    for r_i in output_returns:
        prices.append(prices[-1] * r_i)

    for i, color in enumerate(output_colors):
        ax.plot([i, i + 1], [prices[i], prices[i + 1]],
                color=color, linewidth=3)

    ax.scatter(range(len(prices)), prices, color="#222222", s=15, zorder=3)
    price_padding = 0.08 * (max(all_output_prices) - min(all_output_prices))
    ax.set_xlim(0, OUTPUT_SIZE)
    ax.set_ylim(min(all_output_prices) - price_padding,
                max(all_output_prices) + price_padding)
    ax.grid(axis="y", color="#D7DCE1", linewidth=0.8)
    ax.set_xlabel("output index i")
    ax.set_ylabel(r"price $p_i$")
    ax.set_title(r"3. Reconstruct prices with $p_i = p_{i-1} \times r_i$",
                 loc="left")


def draw_diagram(fig, axes, completed_blocks, active_block, title):
    for ax in axes:
        ax.clear()

    draw_source(axes[0], completed_blocks, active_block)
    draw_output(axes[1], completed_blocks)
    draw_prices(axes[2], completed_blocks)
    fig.suptitle(title, fontsize=16, fontweight="bold")
    fig.tight_layout(rect=(0.02, 0.02, 0.98, 0.94))


# Each animation step first highlights a source block, then appends it.
animation_steps = [(0, None, "Start with the source returns")]

for block_number, block in enumerate(selected_blocks):
    start = block["start"]
    end = start + BLOCK_SIZE - 1
    animation_steps.append(
        (block_number, block_number,
         f"Select block B{block_number + 1} from source indexes {start}–{end}")
    )
    animation_steps.append(
        (block_number + 1, None,
         f"Append block B{block_number + 1} and reconstruct its prices")
    )


animation_figure, animation_axes = plt.subplots(
    3, 1, figsize=(15, 10), gridspec_kw={"height_ratios": [1.8, 0.9, 1.4]}
)


def animate(frame_number):
    completed_blocks, active_block, title = animation_steps[frame_number]
    draw_diagram(
        animation_figure,
        animation_axes,
        completed_blocks,
        active_block,
        title,
    )


animation = FuncAnimation(
    animation_figure,
    animate,
    frames=len(animation_steps),
    interval=900,
    repeat=True,
)


# Count source-return selections across many trajectories for the heatmap.
selection_counts = [0] * len(SOURCE_RETURNS)
heatmap_rng = random.Random(SEED + 1)

for trajectory_number in range(HEATMAP_TRAJECTORIES):
    number_of_blocks = OUTPUT_SIZE // BLOCK_SIZE

    for block_number in range(number_of_blocks):
        block_start = heatmap_rng.choice(block_starts)

        for i in range(block_start, block_start + BLOCK_SIZE):
            selection_counts[i] += 1


static_figure, static_axes = plt.subplots(
    4, 1, figsize=(15, 12),
    gridspec_kw={"height_ratios": [1.8, 0.9, 1.4, 0.65]},
)
draw_source(static_axes[0], len(selected_blocks), None)
draw_output(static_axes[1], len(selected_blocks))
draw_prices(static_axes[2], len(selected_blocks))

heatmap_ax = static_axes[3]
heatmap_ax.imshow([selection_counts], cmap="Blues", aspect="auto",
                  extent=(0, len(SOURCE_RETURNS), 0, 1))

for i, count in enumerate(selection_counts):
    if i not in TIME_BREAKS:
        text_color = "white" if count > 0.55 * max(selection_counts) else "#222222"
        heatmap_ax.text(i + 0.5, 0.5, str(count), ha="center", va="center",
                        fontsize=8, color=text_color)

for time_break in TIME_BREAKS:
    gap = Rectangle((time_break, 0), 1, 1, facecolor=GAP_COLOR,
                    edgecolor=EDGE_COLOR, linewidth=1.5)
    heatmap_ax.add_patch(gap)
    heatmap_ax.text(time_break + 0.5, 0.5, "gap", ha="center", va="center",
                    fontsize=8)

heatmap_ax.set_xlim(0, len(SOURCE_RETURNS))
heatmap_ax.set_yticks([])
heatmap_ax.set_xticks([i + 0.5 for i in range(len(SOURCE_RETURNS))])
heatmap_ax.set_xticklabels(range(len(SOURCE_RETURNS)), fontsize=7)
heatmap_ax.set_xlabel("source return index")
heatmap_ax.set_title(
    f"Selection frequency across {HEATMAP_TRAJECTORIES} trajectories",
    loc="left",
)

static_figure.suptitle(
    "Moving-block bootstrap: select, attach, and reconstruct",
    fontsize=16,
    fontweight="bold",
)
static_figure.tight_layout(rect=(0.02, 0.02, 0.98, 0.95))


output_dir = Path(__file__).resolve().parent / "docs"
output_dir.mkdir(exist_ok=True)
animation_name = output_dir / "bootstrap_animation.gif"
diagram_name = output_dir / "bootstrap_diagram.png"

animation.save(animation_name, writer=PillowWriter(fps=1), dpi=90)
static_figure.savefig(diagram_name, dpi=140, bbox_inches="tight")

print(f"Wrote {animation_name}")
print(f"Wrote {diagram_name}")

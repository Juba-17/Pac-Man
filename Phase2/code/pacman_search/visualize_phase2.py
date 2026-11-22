"""
visualize_phase2.py
===================
Phase II charts (the maze pictures of visualize.py are re-used for Greedy and A*).

    plot_heuristic_effect   nodes expanded and path cost: UCS vs A* vs Greedy, with h1 and h2
    plot_convergence        solution quality over iterations / generations (HC, SA, GA)
    plot_final_costs        how often each final cost occurred over the seeded runs
    plot_sa_trace           one simulated-annealing run: current cost, best cost, temperature
    plot_tuning_grid        parameter sensitivity as a heat map (SA and GA)
    plot_budget_vs_success  reliability of the local-search methods against their budget
    plot_scaling_local      larger mazes: local search and random sampling against the optimum
    plot_summary_all        summary chart comparing all algorithms of both phases
    plot_routes             routes found by local search drawn in the maze
"""

import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Rectangle
from matplotlib.ticker import FuncFormatter, MaxNLocator

from . import visualize as viz
from .visualize import (
    AQUA, BLUE, HEAT, INK, INK_SOFT, MUTED, ORANGE, SURFACE, apply_style, bar_panel, plain_number,
    save_figure, spans_orders_of_magnitude, text_color_on)

# One colour per family of algorithms (used by the summary chart). The random-sampling
# baseline is grey: it is a yardstick, not one of the algorithms.
FAMILY_COLOR = {"uninformed": BLUE, "informed": ORANGE, "local search": AQUA, "baseline": MUTED}
QUIET = "#b9b8b1"       # de-emphasised lines (individual runs)


def plot_heuristic_effect(rows_by_layout, path, optimal_by_layout):
    """Top row: nodes expanded. Bottom row: path cost (line = optimal). One column per layout.

    rows_by_layout: {layout: [row, ...]} with rows for UCS, Greedy (h1), Greedy (h2), A* (h1), A* (h2).
    """
    apply_style()
    layouts = list(rows_by_layout)
    n_rows = len(next(iter(rows_by_layout.values())))
    fig, axes = plt.subplots(2, len(layouts), figsize=(7.6, 2 * (0.26 * n_rows + 0.85)), squeeze=False)
    for column, layout in enumerate(layouts):
        rows = rows_by_layout[layout]
        labels = [row["algorithm"] for row in rows]
        bar_panel(axes[0][column], labels, [row["nodes_expanded"] for row in rows],
                  f"Nodes expanded - {layout}")
        bar_panel(axes[1][column], labels, [row["path_cost"] for row in rows],
                  f"Path cost - {layout} (optimal {optimal_by_layout[layout]:g})",
                  reference=optimal_by_layout[layout])
        if column > 0:                                   # algorithm names only on the left
            axes[0][column].set_yticklabels([])
            axes[1][column].set_yticklabels([])
    fig.tight_layout(w_pad=1.0, h_pad=1.2)
    return save_figure(fig, path)


def _padded(histories):
    """Make all histories the same length by repeating each one's final value."""
    longest = max(len(history) for history in histories)
    return [history + [history[-1]] * (longest - len(history)) for history in histories]


def plot_convergence(runs_by_algorithm, optimum, path, title=None):
    """Convergence plot: best cost found so far versus iteration (HC, SA) or generation (GA).

    runs_by_algorithm: {name: [LocalSearchResult, ...]} - one result per seed.
    Grey lines = individual runs, blue line = their average, black line = optimal cost.
    """
    apply_style()
    names = list(runs_by_algorithm)
    fig, axes = plt.subplots(1, len(names), figsize=(7.6, 3.1), sharey=True, squeeze=False)
    for ax, name in zip(axes[0], names):
        runs = runs_by_algorithm[name]
        histories = _padded([run.history for run in runs])
        steps = range(len(histories[0]))
        for history in histories:
            ax.plot(steps, history, color=QUIET, linewidth=0.7, alpha=0.7, zorder=2)
        mean = [sum(column) / len(column) for column in zip(*histories)]
        ax.plot(steps, mean, color=BLUE, linewidth=1.9, zorder=4)
        ax.axhline(optimum, color=INK, linewidth=1.0, zorder=3)
        hits = sum(run.cost == optimum for run in runs)
        ax.set_title(name, fontsize=9.5, fontweight="bold", loc="left", pad=15)
        ax.text(0, 1.02, f"{hits} of {len(runs)} runs optimal  |  final mean {mean[-1]:.2f}",
                transform=ax.transAxes, fontsize=7.5, color=INK_SOFT, ha="left", va="bottom")
        unit = "generation" if "Genetic" in name else "iteration"
        if len(histories[0]) > 500:                     # long runs: most progress happens early
            ax.set_xscale("symlog", linthresh=1)
            ax.set_xlim(0, len(histories[0]))
            ax.set_xlabel(f"{unit} (log scale)", fontsize=8.5)
        else:
            ax.xaxis.set_major_locator(MaxNLocator(nbins=6, integer=True))
            ax.set_xlabel(unit, fontsize=8.5)
        ax.xaxis.set_major_formatter(FuncFormatter(plain_number))
        ax.yaxis.grid(True)
        ax.set_axisbelow(True)
        ax.tick_params(which="both", length=0, labelsize=8)
    axes[0][0].set_ylabel("best cost found so far", fontsize=8.5)
    handles = [Line2D([], [], color=QUIET, linewidth=1.0, label="one run (one seed)"),
               Line2D([], [], color=BLUE, linewidth=1.9, label="average of all runs"),
               Line2D([], [], color=INK, linewidth=1.0, label=f"optimal cost ({optimum:g})")]
    fig.legend(handles=handles, loc="lower center", ncol=3, fontsize=8, bbox_to_anchor=(0.5, -0.03))
    if title:
        fig.suptitle(title, fontsize=10.5, fontweight="bold", x=0.01, ha="left")
    fig.tight_layout(rect=(0, 0.04, 1, 0.94 if title else 1), w_pad=1.0)
    return save_figure(fig, path)


def plot_final_costs(runs_by_algorithm, optimum, path, title=None):
    """How often each final cost occurred, one small histogram per algorithm.

    Each bar is one cost value; its length is the number of seeded runs that ended with
    that cost. The bar of the optimal cost is drawn in orange.
    """
    apply_style()
    names = list(runs_by_algorithm)
    all_costs = sorted({run.cost for runs in runs_by_algorithm.values() for run in runs} | {optimum})
    fig, axes = plt.subplots(1, len(names), figsize=(7.6, 0.2 * len(all_costs) + 1.6), sharey=True,
                             squeeze=False)
    for ax, name in zip(axes[0], names):
        costs = [run.cost for run in runs_by_algorithm[name]]
        counts = [costs.count(value) for value in all_costs]
        positions = list(range(len(all_costs)))
        colors = [ORANGE if value == optimum else BLUE for value in all_costs]
        ax.barh(positions, counts, height=0.62, color=colors, zorder=2)
        for position, count in zip(positions, counts):
            if count:
                ax.text(count + len(costs) * 0.02, position, str(count), fontsize=7.5, va="center", ha="left")
        ax.set_xlim(0, len(costs) * 1.18)
        ax.set_yticks(positions)
        ax.set_yticklabels([f"{value:g}" for value in all_costs])
        ax.tick_params(length=0, labelsize=8)
        ax.xaxis.grid(True, zorder=0)
        ax.set_axisbelow(True)
        ax.xaxis.set_major_locator(MaxNLocator(nbins=4, integer=True))
        ax.spines["left"].set_visible(False)
        ax.set_title(name.replace(" (", "\n("), fontsize=9, fontweight="bold", loc="left")
        ax.set_xlabel(f"best {min(costs):g} | worst {max(costs):g}\nmean {sum(costs) / len(costs):.2f}",
                      fontsize=7.5)
    axes[0][0].set_ylabel("final cost", fontsize=8.5)
    handles = [Patch(facecolor=ORANGE, edgecolor="none", label=f"runs that reach the optimal cost ({optimum:g})"),
               Patch(facecolor=BLUE, edgecolor="none", label="runs that end with a higher cost")]
    fig.legend(handles=handles, loc="lower center", ncol=2, fontsize=8, bbox_to_anchor=(0.5, -0.02))
    if title:
        fig.suptitle(title, fontsize=10.5, fontweight="bold", x=0.01, ha="left")
    fig.tight_layout(rect=(0, 0.05, 1, 0.94 if title else 1), w_pad=1.0)
    return save_figure(fig, path)


def plot_sa_trace(result, optimum, path, title=None):
    """One simulated-annealing run. Top: cost of the current order (grey) and best cost so
    far (blue). Bottom: the temperature (geometric cooling), on a logarithmic axis."""
    apply_style()
    current = result.extra["current_history"]
    steps = range(len(current))
    start = result.extra["start_temperature"]
    rate = result.extra["cooling_rate"]
    temperature = [start * rate ** step for step in steps]
    fig, (top, bottom) = plt.subplots(2, 1, figsize=(6.8, 4.2), sharex=True,
                                      gridspec_kw={"height_ratios": [2.2, 1]})
    top.plot(steps, current, color=QUIET, linewidth=0.7, label="cost of the current order")
    top.plot(steps, result.history, color=BLUE, linewidth=1.9, label="best cost found so far")
    top.axhline(optimum, color=INK, linewidth=1.0, label=f"optimal cost ({optimum:g})")
    top.set_ylabel("cost")
    top.legend(loc="upper right", fontsize=8)
    top.set_title(title or f"Simulated annealing (seed {result.seed}): uphill moves are accepted while "
                  "it is hot", fontsize=10.5, fontweight="bold", loc="left")
    bottom.plot(steps, temperature, color=BLUE, linewidth=1.9)
    bottom.set_yscale("log")
    bottom.yaxis.set_major_formatter(FuncFormatter(plain_number))
    bottom.set_ylabel("temperature (log)")
    bottom.set_xlabel("iteration")
    bottom.xaxis.set_major_formatter(FuncFormatter(plain_number))
    for ax in (top, bottom):
        ax.yaxis.grid(True)
        ax.set_axisbelow(True)
        ax.tick_params(which="both", length=0, labelsize=8)
    fig.tight_layout(h_pad=0.8)
    return save_figure(fig, path)


def plot_tuning_grid(cells, row_values, col_values, row_label, col_label, path, title, chosen=None,
                     runs_per_cell=30):
    """Parameter sensitivity as a heat map.

    cells   {(row_value, col_value): {"hits": runs that found the optimum,
                                      "evaluations": objective evaluations per run}}
    chosen  optional (row_value, col_value) - the setting used in the final experiments (outlined)
    Colour = share of runs that reached the optimal cost (darker = more reliable). Each
    cell also shows the budget (evaluations per run), because a setting that looks better
    may simply be spending more evaluations.
    """
    apply_style()
    fig, ax = plt.subplots(figsize=(1.05 * len(col_values) + 1.9, 0.5 * len(row_values) + 1.5))
    for r, row_value in enumerate(row_values):
        for c, col_value in enumerate(col_values):
            cell = cells[(row_value, col_value)]
            share = cell["hits"] / runs_per_cell
            face = HEAT(share)
            ax.add_patch(Rectangle((c, r), 1, 1, facecolor=face, edgecolor=SURFACE, linewidth=2))
            ax.text(c + 0.5, r + 0.5, f"{share * 100:.0f}%\n{cell['evaluations']:,} eval.",
                    ha="center", va="center", fontsize=7.5, color=text_color_on(face))
    if chosen is not None and chosen[0] in row_values and chosen[1] in col_values:
        r, c = row_values.index(chosen[0]), col_values.index(chosen[1])
        ax.add_patch(Rectangle((c + 0.04, r + 0.04), 0.92, 0.92, fill=False, edgecolor=ORANGE,
                               linewidth=2.2, zorder=5))
    ax.set_xlim(0, len(col_values))
    ax.set_ylim(len(row_values), 0)
    ax.set_xticks([c + 0.5 for c in range(len(col_values))])
    ax.set_xticklabels([f"{value:g}" for value in col_values])
    ax.set_yticks([r + 0.5 for r in range(len(row_values))])
    ax.set_yticklabels([f"{value:g}" for value in row_values])
    ax.set_xlabel(col_label, fontsize=8.5)
    ax.set_ylabel(row_label, fontsize=8.5)
    ax.tick_params(length=0, labelsize=8)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_title(title, fontsize=9.5, fontweight="bold", loc="left", pad=20)
    note = f"cell: % of {runs_per_cell} runs that reach the optimum / evaluations per run"
    if chosen is not None:
        note += "  |  orange frame = setting used"
    ax.text(0, 1.03, note, transform=ax.transAxes, fontsize=7.5, color=INK_SOFT, ha="left", va="bottom")
    bar = fig.colorbar(plt.cm.ScalarMappable(norm=Normalize(0, 100), cmap=HEAT), ax=ax, fraction=0.045, pad=0.03)
    bar.outline.set_visible(False)
    bar.set_label("runs reaching the optimum (%)", fontsize=7.5, color=INK_SOFT)
    bar.ax.tick_params(labelsize=7, length=2)
    return save_figure(fig, path)


def plot_budget_vs_success(series, path, title=None, runs=100, baseline=None):
    """Reliability against budget for the local-search methods.

    series: {name: [(evaluations per run, % of runs that reach the optimum, parameter value), ...]}
    One line per algorithm; every point is one parameter setting, and the legend lists the
    settings from the cheapest to the most expensive point. The further left and the
    higher a point is, the better: reliable with few evaluations.
    baseline: optional (label, [(evaluations, %), ...]) drawn as a grey dashed curve - the
    success rate of blind random sampling with the same number of evaluations.
    """
    apply_style()
    fig, ax = plt.subplots(figsize=(6.8, 3.9))
    if baseline:
        label, curve = baseline
        ax.plot([x for x, _ in curve], [y for _, y in curve], color=MUTED, linewidth=1.6,
                linestyle=(0, (4, 3)), label=label, zorder=1)
    for color, (name, points) in zip(viz.SERIES, series.items()):
        points = sorted(points)
        xs = [x for x, _, _ in points]
        ys = [y for _, y, _ in points]
        values = ", ".join(str(value) for _, _, value in points)
        ax.plot(xs, ys, color=color, linewidth=1.8, marker="o", markersize=6,
                markeredgecolor=SURFACE, markeredgewidth=1.2, label=f"{name}: {values}")
    ax.set_xscale("log")
    ax.xaxis.set_major_formatter(FuncFormatter(plain_number))
    ax.set_ylim(0, 108)
    ax.set_xlabel("objective evaluations per run (log scale)", fontsize=8.5)
    ax.set_ylabel(f"runs reaching the optimum (% of {runs})", fontsize=8.5)
    ax.yaxis.grid(True)
    ax.set_axisbelow(True)
    ax.tick_params(which="both", length=0, labelsize=8)
    ax.set_title(title or "Reliability against budget", fontsize=10.5, fontweight="bold", loc="left")
    ax.legend(loc="lower right", fontsize=7.5, title="points from left to right", title_fontsize=7.5)
    return save_figure(fig, path)


def plot_scaling_local(method_rows, instance_rows, path, budget, runs, title=None):
    """The scaling experiment on larger mazes, in two panels.

    Left:  how far above the optimal cost each method ends on average (in percent), against
           the number of pellets - every method uses about `budget` evaluations per run.
    Right: nodes expanded by A* with h2, which solves every instance optimally.
    method_rows / instance_rows come from pacman_search.scaling.scaling_study().
    """
    apply_style()
    fig, (left, right) = plt.subplots(1, 2, figsize=(7.6, 3.3), gridspec_kw={"width_ratios": [1.55, 1]})
    methods = list(dict.fromkeys(row["method"] for row in method_rows))
    colors = dict(zip([name for name in methods if name != "Random sampling"], viz.SERIES))
    for name in methods:
        rows = sorted((row for row in method_rows if row["method"] == name), key=lambda row: row["pellets"])
        xs = [row["pellets"] for row in rows]
        ys = [row["mean_percent_above_optimum"] for row in rows]
        if name == "Random sampling":                    # the baseline: grey and dashed
            left.plot(xs, ys, color=MUTED, linewidth=1.6, linestyle=(0, (4, 3)), marker="o", markersize=5,
                      markeredgecolor=SURFACE, markeredgewidth=1.0, label=f"{name} (baseline)")
        else:
            left.plot(xs, ys, color=colors[name], linewidth=1.8, marker="o", markersize=6,
                      markeredgecolor=SURFACE, markeredgewidth=1.2, label=name)
        left.annotate(f"{ys[-1]:g}%", (xs[-1], ys[-1]), xytext=(6, 0), textcoords="offset points",
                      fontsize=7.5, va="center")
    pellets = [row["pellets"] for row in instance_rows]
    left.set_xticks(pellets)
    left.set_xlim(pellets[0] - 1, pellets[-1] + 3.2)
    left.set_ylim(bottom=-1)
    left.set_xlabel("pellets in the maze", fontsize=8.5)
    left.set_ylabel("mean cost above the optimum (%)", fontsize=8.5)
    left.set_title(f"Local search, {budget:,} evaluations per run", fontsize=9.5, fontweight="bold", loc="left",
                   pad=14)
    left.text(0, 1.02, f"mean of {runs} seeded runs; 0% = always optimal", transform=left.transAxes,
              fontsize=7.5, color=INK_SOFT, ha="left", va="bottom")
    left.legend(loc="upper left", fontsize=7.5)

    expanded = [row["astar_h2_nodes_expanded"] for row in instance_rows]
    right.bar(pellets, expanded, width=2.2, color=ORANGE, zorder=2)
    for x, value in zip(pellets, expanded):
        right.text(x, value, f"{value:,}", ha="center", va="bottom", fontsize=7.5)
    right.set_xticks(pellets)
    right.set_ylim(0, max(expanded) * 1.15)
    right.set_xlabel("pellets in the maze", fontsize=8.5)
    right.set_ylabel("nodes expanded", fontsize=8.5)
    right.set_title("A* with h2 (always optimal)", fontsize=9.5, fontweight="bold", loc="left", pad=14)
    right.yaxis.set_major_formatter(FuncFormatter(plain_number))
    for ax in (left, right):
        ax.yaxis.grid(True, zorder=0)
        ax.set_axisbelow(True)
        ax.tick_params(which="both", length=0, labelsize=8)
    if title:
        fig.suptitle(title, fontsize=10.5, fontweight="bold", x=0.01, ha="left")
    fig.tight_layout(rect=(0, 0, 1, 0.93 if title else 1), w_pad=1.6)
    return save_figure(fig, path)


def plot_summary_all(rows, path, optimum, title=None, runs=30):
    """Summary chart: every algorithm of both phases on one layout.

    rows: list of dictionaries with keys
        algorithm, family, cost, cost_range, time_ms, peak_memory_kib, effort
    Four panels (cost, time, memory, search effort); bar colour = family of the algorithm.
    For the randomised methods the bar is the mean over `runs` seeds and the thin black
    line spans best to worst. A panel whose values span several orders of magnitude is
    drawn on a logarithmic axis (its title says so), otherwise the small bars would vanish.
    """
    apply_style()
    labels = [row["algorithm"] for row in rows]
    colors = [FAMILY_COLOR[row["family"]] for row in rows]
    panels = [
        ("cost", f"Solution cost (line = optimal, {optimum:g})", "{:,.1f}"),
        ("time_ms", "Running time (ms)", "{:,.2f}"),
        ("peak_memory_kib", "Peak memory (KiB)", "{:,.0f}"),
        ("effort", "Effort: nodes expanded / evaluations", "{:,.0f}"),
    ]
    fig, axes = plt.subplots(2, 2, figsize=(7.6, 2 * (0.24 * len(rows) + 0.75) + 0.6))
    for index, (ax, (key, heading, fmt)) in enumerate(zip(axes.flat, panels)):
        values = [row[key] for row in rows]
        if key == "cost":                                # labels go after the best-worst whisker
            ends = [row["cost_range"][1] if row.get("cost_range") else row["cost"] for row in rows]
            bar_panel(ax, labels, values, heading, fmt, color=colors, reference=optimum, label_from=ends)
            for position, row in enumerate(rows):
                if row.get("cost_range"):
                    low, high = row["cost_range"]
                    ax.plot([low, high], [position, position], color=INK, linewidth=1.1, zorder=4,
                            marker="|", markersize=5)
        else:
            bar_panel(ax, labels, values, heading, fmt, color=colors, log=spans_orders_of_magnitude(values))
        if index % 2 == 1:                               # algorithm names only on the left
            ax.set_yticklabels([])
    families = list(dict.fromkeys(row["family"] for row in rows))
    handles = [Patch(facecolor=FAMILY_COLOR[family], edgecolor="none", label=family) for family in families]
    handles.append(Line2D([], [], color=INK, linewidth=1.1, marker="|", markersize=5,
                          label=f"randomised: bar = mean, line = best to worst of {runs} runs"))
    fig.legend(handles=handles, loc="lower center", ncol=len(handles), fontsize=8,
               bbox_to_anchor=(0.5, -0.01), columnspacing=1.2, handlelength=1.5)
    if title:
        fig.suptitle(title, fontsize=10.5, fontweight="bold", x=0.01, ha="left")
    fig.tight_layout(rect=(0, 0.035, 1, 0.95 if title else 1), w_pad=1.0, h_pad=1.2)
    return save_figure(fig, path)


def plot_routes(problem, routes, path, title=None):
    """Routes found by local search, drawn in the maze.

    routes: list of (heading, note, actions) - the actions are replayed in the problem model.
    """
    apply_style()
    crop = viz.BORDER_CROP
    panel_w = max(3.3, (problem.width - 2 * crop) * 0.42)
    panel_h = panel_w * (problem.height - 2 * crop) / (problem.width - 2 * crop)
    head, gap, side, bottom = 0.5, 0.35, 0.15, 0.5
    top = 0.5 if title else 0.1
    fig_w = 2 * side + len(routes) * panel_w + (len(routes) - 1) * gap
    fig_h = top + head + panel_h + bottom
    fig = plt.figure(figsize=(fig_w, fig_h))
    for index, (heading, note, actions) in enumerate(routes):
        left = side + index * (panel_w + gap)
        ax = fig.add_axes([left / fig_w, bottom / fig_h, panel_w / fig_w, panel_h / fig_h])
        states, _ = problem.execute(actions)
        viz.draw_maze(ax, problem, label_food=True)
        viz.draw_path(ax, states)
        fig.text(left / fig_w, 1 - (top + head - 0.3) / fig_h, heading, fontsize=10.5, fontweight="bold",
                 ha="left", va="baseline")
        fig.text(left / fig_w, 1 - (top + head - 0.09) / fig_h, note, fontsize=8, color=INK_SOFT,
                 ha="left", va="baseline")
    if title:
        fig.text(side / fig_w, 1 - 0.3 / fig_h, title, fontsize=11.5, fontweight="bold",
                 ha="left", va="baseline")
    handles = viz.symbol_handles()
    fig.legend(handles=handles, loc="lower center", ncol=len(handles), fontsize=7.5,
               bbox_to_anchor=(0.5, 0.0), handlelength=1.5, columnspacing=1.0)
    return save_figure(fig, path)

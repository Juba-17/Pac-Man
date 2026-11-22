"""
visualize.py
============
All the pictures of the project, drawn with Matplotlib. No other third-party library is
used, except Pillow (installed together with Matplotlib) to save the animated GIFs.

Maze pictures
    plot_layouts          the maze layouts side by side
    plot_explored         one panel per algorithm: which states were explored + final path
    animate_search        animated GIF: exploration order, then Pac-Man walking the solution
Search trees
    plot_search_tree      the tree of expanded nodes, numbered in expansion order
    plot_search_trees     the trees of several algorithms side by side
    plot_ids_trees        the same for several depth limits of iterative deepening
Charts
    plot_metric_bars      generated / expanded / frontier / memory / time / cost per algorithm
    plot_frontier_history frontier size while the search is running
    plot_ids_iterations   work done by IDS at every depth limit
    plot_scaling          nodes expanded versus state-space size

Every function writes an image file and returns its path; no window is opened.
"""

import math

import matplotlib

matplotlib.use("Agg")  # render straight to image files

import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.cm import ScalarMappable  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap, Normalize, to_rgb  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Circle, FancyBboxPatch, Patch, Rectangle  # noqa: E402
from matplotlib.ticker import FuncFormatter, MaxNLocator  # noqa: E402

# --------------------------------------------------------------------------------------
# One small colour palette shared by every figure
# --------------------------------------------------------------------------------------
SURFACE = "#fcfcfb"     # figure background
INK = "#0b0b0b"         # main text
INK_SOFT = "#52514e"    # secondary text
MUTED = "#898781"       # axis labels
GRID = "#e1e0d9"        # hairlines
AXIS = "#c3c2b7"
WALL = "#3f3e3a"

BLUE = "#2a78d6"
ORANGE = "#eb6834"
AQUA = "#1baf7a"
YELLOW = "#eda100"
MAGENTA = "#e87ba4"
GREEN = "#008300"
VIOLET = "#6250d6"
RED = "#e34948"
SERIES = [BLUE, ORANGE, AQUA, YELLOW, MAGENTA, GREEN, VIOLET, RED]   # fixed order for line colours
DANGER = "#d03b3b"      # ghosts and danger cells

# One-hue ramp (light -> dark) used for "how much was explored here".
BLUE_RAMP = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
HEAT = LinearSegmentedColormap.from_list("explored", BLUE_RAMP)

BORDER_CROP = 0.62      # how much of the outer wall ring is cut away in maze pictures


def apply_style():
    """Common look for all charts: light surface, thin grey axes, no top/right frame."""
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Segoe UI", "Helvetica Neue", "Arial", "DejaVu Sans"],
        "font.size": 9,
        "figure.facecolor": SURFACE,
        "axes.facecolor": SURFACE,
        "savefig.facecolor": SURFACE,
        "axes.edgecolor": AXIS,
        "axes.labelcolor": INK_SOFT,
        "axes.titlecolor": INK,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": False,
        "grid.color": GRID,
        "grid.linewidth": 0.8,
        "xtick.color": MUTED,
        "ytick.color": MUTED,
        "xtick.labelcolor": INK_SOFT,
        "ytick.labelcolor": INK_SOFT,
        "text.color": INK,
        "legend.frameon": False,
    })


def save_figure(fig, path, dpi=200):
    """Write the figure to `path`, close it and return the path."""
    fig.savefig(path, dpi=dpi, bbox_inches="tight", facecolor=SURFACE)
    plt.close(fig)
    return path


def text_color_on(fill):
    """Black or white - whichever is easier to read on top of the colour `fill`.

    Uses the standard web-accessibility (WCAG) formulas: the relative luminance of a
    colour, and the contrast ratio (L1 + 0.05) / (L2 + 0.05) between two colours.
    """
    def luminance(color):
        channels = []
        for value in to_rgb(color):
            channels.append(value / 12.92 if value <= 0.03928 else ((value + 0.055) / 1.055) ** 2.4)
        return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]

    fill_lum = luminance(fill)
    contrast_white = 1.05 / (fill_lum + 0.05)
    contrast_ink = (fill_lum + 0.05) / (luminance(INK) + 0.05)
    return "white" if contrast_white > contrast_ink else INK


def plain_number(value, _position=None):
    """Tick label with thousands separators (1,000 instead of 10^3)."""
    if value >= 10 or value == 0:
        return f"{value:,.0f}"
    return f"{value:g}"


# --------------------------------------------------------------------------------------
# Drawing a maze
# --------------------------------------------------------------------------------------
def draw_maze(ax, problem, heat=None, heat_max=None, food_left=None, agent=None,
              label_food=True, show_start=True):
    """Draw the maze of `problem` on the axes `ax`.

    heat       optional {cell: number}; those cells are shaded with the blue ramp
    heat_max   value that maps to the darkest blue (default: the largest value in heat)
    food_left  optional bitmask - draw only the pellets that are still on the board
    agent      optional (row, col): draw Pac-Man at this cell (used by the animation)
    """
    if food_left is None:
        food_left = problem.all_food
    if heat and heat_max is None:
        heat_max = max(heat.values())
    ax.set_xlim(BORDER_CROP, problem.width - BORDER_CROP)
    ax.set_ylim(problem.height - BORDER_CROP, BORDER_CROP)      # row 0 at the top
    ax.set_aspect("equal")
    ax.axis("off")

    label_color = {}                         # text colour that is readable on each cell
    for r in range(problem.height):
        for c in range(problem.width):
            cell = (r, c)
            if cell in problem.walls:
                ax.add_patch(Rectangle((c, r), 1, 1, facecolor=WALL, edgecolor=WALL, linewidth=0.6))
                continue
            value = heat.get(cell, 0) if heat else 0
            face = HEAT(value / heat_max) if value > 0 else SURFACE
            label_color[cell] = text_color_on(face)
            ax.add_patch(Rectangle((c, r), 1, 1, facecolor=face, edgecolor=GRID, linewidth=0.6))

    # danger cells: red inner frame + the cost of entering them
    for (r, c) in problem.danger_cells:
        ax.add_patch(Rectangle((c + 0.07, r + 0.07), 0.86, 0.86, fill=False,
                               edgecolor=DANGER, linewidth=1.3, zorder=3))
        ax.text(c + 0.25, r + 0.27, str(problem.danger_cost), fontsize=6, ha="center", va="center",
                color=label_color[(r, c)] if label_color[(r, c)] == "white" else INK_SOFT, zorder=4)

    # ghosts
    for (r, c) in problem.ghosts:
        ax.add_patch(FancyBboxPatch((c + 0.14, r + 0.14), 0.72, 0.72,
                                    boxstyle="round,pad=0,rounding_size=0.2",
                                    facecolor=DANGER, edgecolor="none", zorder=3))
        ax.text(c + 0.5, r + 0.5, "G", fontsize=8, fontweight="bold", color="white",
                ha="center", va="center", zorder=4)

    # pellets (numbered: pellet i is bit i of the food mask)
    for index, (r, c) in enumerate(problem.food_cells):
        if not food_left & (1 << index):
            continue
        ax.add_patch(Circle((c + 0.5, r + 0.5), 0.15, facecolor=YELLOW, edgecolor=SURFACE,
                            linewidth=1.0, zorder=4))
        if label_food:
            ax.text(c + 0.8, r + 0.22, str(index), fontsize=6, ha="center", va="center",
                    color=label_color[(r, c)] if label_color[(r, c)] == "white" else INK_SOFT, zorder=4)

    # start cell
    if show_start:
        r, c = problem.start
        ax.add_patch(Circle((c + 0.5, r + 0.5), 0.31, facecolor="none", edgecolor=label_color[(r, c)],
                            linewidth=1.3, zorder=4))
        if agent is None:
            ax.text(c + 0.5, r + 0.5, "P", fontsize=7.5, fontweight="bold", ha="center", va="center",
                    color=label_color[(r, c)], zorder=5)

    # Pac-Man's current position (animation frames only)
    if agent is not None:
        r, c = agent
        ax.add_patch(Circle((c + 0.5, r + 0.5), 0.27, facecolor=INK, edgecolor=SURFACE,
                            linewidth=1.2, zorder=8))


def draw_path(ax, states, color=ORANGE, lane=0.14, number_food=True, arrows=True):
    """Draw a solution path on a maze.

    Each move is shifted a little to the right-hand side of its direction of travel, so a
    corridor that is walked in both directions shows two parallel lines instead of one.
    """
    if len(states) < 2:
        return
    xs, ys, moves = [], [], []
    for a, b in zip(states, states[1:]):
        (r0, c0), (r1, c1) = a.pos, b.pos
        dx, dy = c1 - c0, r1 - r0
        ox, oy = -dy * lane, dx * lane
        x0, y0, x1, y1 = c0 + 0.5 + ox, r0 + 0.5 + oy, c1 + 0.5 + ox, r1 + 0.5 + oy
        xs += [x0, x1]
        ys += [y0, y1]
        moves.append((x0, y0, x1, y1, dx, dy))

    ax.plot(xs, ys, color=SURFACE, linewidth=4.0, solid_capstyle="round",
            solid_joinstyle="round", zorder=5)                      # light casing under the line
    ax.plot(xs, ys, color=color, linewidth=1.9, solid_capstyle="round",
            solid_joinstyle="round", zorder=6)

    if arrows:
        every = max(1, len(moves) // 16)
        for x0, y0, x1, y1, dx, dy in moves[::every]:
            angle = {(0, -1): 0, (0, 1): 180, (1, 0): -90, (-1, 0): 90}[(dx, dy)]
            ax.plot([(x0 + x1) / 2], [(y0 + y1) / 2], marker=(3, 0, angle), markersize=6.5,
                    color=color, markeredgecolor=SURFACE, markeredgewidth=0.6, zorder=7)

    if number_food:                                                  # order in which pellets are eaten
        order = 0
        for a, b in zip(states, states[1:]):
            if b.food != a.food:
                order += 1
                r, c = b.pos
                ax.add_patch(Circle((c + 0.2, r + 0.8), 0.15, facecolor=SURFACE, edgecolor=color,
                                    linewidth=0.9, zorder=8))
                ax.text(c + 0.2, r + 0.8, str(order), fontsize=5.5, fontweight="bold", color=INK,
                        ha="center", va="center", zorder=9)


def expanded_per_cell(result):
    """{cell: number of DISTINCT states expanded while Pac-Man stood on that cell}.

    A cell can be counted up to 2^k times, once for each combination of remaining pellets.
    """
    seen = set()
    counts = {}
    for node in result.expanded_nodes:
        if node.state not in seen:
            seen.add(node.state)
            counts[node.state.pos] = counts.get(node.state.pos, 0) + 1
    return counts


def symbol_handles(with_path=True):
    """Legend entries that explain the symbols of a maze picture."""
    handles = [
        Line2D([], [], marker="o", linestyle="none", markersize=9, markerfacecolor="none",
               markeredgecolor=INK, markeredgewidth=1.2, label="start (P)"),
        Line2D([], [], marker="o", linestyle="none", markersize=6, markerfacecolor=YELLOW,
               markeredgecolor=SURFACE, label="food pellet"),
        Patch(facecolor=DANGER, edgecolor="none", label="ghost (G)"),
        Patch(facecolor="none", edgecolor=DANGER, linewidth=1.3, label="danger cell (cost 5)"),
        Patch(facecolor=WALL, edgecolor="none", label="wall"),
    ]
    if with_path:
        handles.append(Line2D([], [], color=ORANGE, linewidth=2,
                              label="returned path (numbers = eating order)"))
    return handles


# --------------------------------------------------------------------------------------
# Maze figures
# --------------------------------------------------------------------------------------
def plot_layouts(problems, path, per_row=2):
    """All layouts (`per_row` next to each other), each with its size written below it."""
    apply_style()
    cell, gap_x, gap_y, side = 0.3, 0.5, 0.2, 0.1      # inches
    head, caption, legend = 0.36, 0.5, 0.4             # name above a maze, text below it, legend

    def span(problem):
        return (problem.width - 2 * BORDER_CROP) * cell

    def tall(problem):
        return (problem.height - 2 * BORDER_CROP) * cell

    rows = [problems[i:i + per_row] for i in range(0, len(problems), per_row)]
    row_heights = [max(tall(p) for p in row) for row in rows]
    fig_w = 2 * side + max(sum(span(p) for p in row) + gap_x * (len(row) - 1) for row in rows)
    fig_h = sum(head + h + caption for h in row_heights) + gap_y * (len(rows) - 1) + legend
    fig = plt.figure(figsize=(fig_w, fig_h))
    top = 0.0
    for row, row_height in zip(rows, row_heights):
        x = side
        for problem in row:
            ax = fig.add_axes([x / fig_w, 1 - (top + head + tall(problem)) / fig_h,
                               span(problem) / fig_w, tall(problem) / fig_h])
            draw_maze(ax, problem)
            # counting the reachable states means visiting all of them: only for small mazes
            countable = len(problem.free_cells) * 2 ** problem.num_food <= 1_000_000
            size = problem.state_space_report(count_reachable=countable)
            states = (f"{size['reachable']:,} reachable states" if countable
                      else f"up to {size['upper_bound']:,} states")
            fig.text(x / fig_w, 1 - (top + head - 0.1) / fig_h, problem.name, fontsize=10.5,
                     fontweight="bold", ha="left", va="baseline")
            fig.text(x / fig_w, 1 - (top + head + tall(problem) + 0.08) / fig_h,
                     f"{problem.height}x{problem.width} grid, {size['free_cells']} free cells, "
                     f"{size['pellets']} pellets\n{states}",
                     fontsize=8, color=INK_SOFT, ha="left", va="top")
            x += span(problem) + gap_x
        top += head + row_height + caption + gap_y
    handles = symbol_handles(with_path=False)
    fig.legend(handles=handles, loc="lower center", ncol=len(handles), fontsize=8,
               bbox_to_anchor=(0.5, 0.0), handlelength=1.6, columnspacing=1.4)
    return save_figure(fig, path)


def plot_explored(problem, results, path, ncols=2, title=None):
    """One maze panel per algorithm.

    Blue shading = how many distinct states were expanded on each cell (darker = more of the
    2^k food combinations were explored there). Orange line = the solution that was returned.
    """
    apply_style()
    heats = [expanded_per_cell(result) for result in results]
    heat_max = max([max(h.values()) for h in heats if h] + [1])
    nrows = (len(results) + ncols - 1) // ncols
    panel_w = max(3.3, (problem.width - 2 * BORDER_CROP) * 0.42)
    panel_h = panel_w * (problem.height - 2 * BORDER_CROP) / (problem.width - 2 * BORDER_CROP)
    head, gap_x, gap_y, side = 0.5, 0.35, 0.3, 0.15     # inches: text above a panel, gaps, margins
    top = 0.55 if title else 0.1
    bottom = 1.05
    fig_w = 2 * side + ncols * panel_w + (ncols - 1) * gap_x
    fig_h = top + nrows * (head + panel_h) + (nrows - 1) * gap_y + bottom
    fig = plt.figure(figsize=(fig_w, fig_h))
    for index, (result, heat) in enumerate(zip(results, heats)):
        row, col = divmod(index, ncols)
        left = side + col * (panel_w + gap_x)
        upper = top + row * (head + panel_h + gap_y) + head            # distance from the top edge
        ax = fig.add_axes([left / fig_w, 1 - (upper + panel_h) / fig_h, panel_w / fig_w, panel_h / fig_h])
        draw_maze(ax, problem, heat=heat, heat_max=heat_max, label_food=False)
        draw_path(ax, result.states)
        fig.text(left / fig_w, 1 - (upper - 0.3) / fig_h, result.algorithm, fontsize=11,
                 fontweight="bold", ha="left", va="baseline")
        if result.found:
            note = (f"cost {result.path_cost:g}  |  {result.depth} steps  |  "
                    f"{result.nodes_expanded:,} nodes expanded")
        else:
            note = f"no solution  |  {result.nodes_expanded:,} nodes expanded"
        fig.text(left / fig_w, 1 - (upper - 0.09) / fig_h, note, fontsize=8.5, color=INK_SOFT,
                 ha="left", va="baseline")
    if title:
        fig.text(side / fig_w, 1 - 0.3 / fig_h, title, fontsize=12.5, fontweight="bold",
                 ha="left", va="baseline")

    colorbar_ax = fig.add_axes([0.28, 0.66 / fig_h, 0.44, 0.1 / fig_h])
    bar = fig.colorbar(ScalarMappable(norm=Normalize(0, heat_max), cmap=HEAT),
                       cax=colorbar_ax, orientation="horizontal")
    bar.outline.set_visible(False)
    bar.ax.tick_params(labelsize=7.5, length=2)
    bar.ax.xaxis.set_major_locator(MaxNLocator(nbins=6, integer=True))
    bar.set_label("distinct states expanded on the cell - one per combination of remaining pellets "
                  "(white = none)", fontsize=8, color=INK_SOFT)
    handles = symbol_handles()
    fig.legend(handles=handles, loc="lower center", ncol=len(handles), fontsize=8,
               bbox_to_anchor=(0.5, 0.0), handlelength=1.6, columnspacing=1.3)
    return save_figure(fig, path)


def animate_search(problem, result, path, search_frames=60, fps=8, hold_frames=14):
    """Animated GIF of one search run.

    Part 1: the blue shading grows in the order in which the algorithm expanded the states.
    Part 2: Pac-Man walks along the returned solution and eats the pellets.
    """
    from PIL import Image

    apply_style()
    order = [node.state for node in result.expanded_nodes]
    total = len(order)
    final_heat = expanded_per_cell(result)
    heat_max = max(list(final_heat.values()) + [1])
    cell_inches = 0.55
    size = ((problem.width - 2 * BORDER_CROP) * cell_inches + 0.5,
            (problem.height - 2 * BORDER_CROP) * cell_inches + 1.1)

    def render(heat, headline, detail, food_left, agent, trail):
        fig, ax = plt.subplots(figsize=size, dpi=110)
        fig.subplots_adjust(left=0.04, right=0.96, top=0.82, bottom=0.03)
        draw_maze(ax, problem, heat=heat, heat_max=heat_max, food_left=food_left, agent=agent,
                  label_food=False)
        if trail:
            draw_path(ax, trail, number_food=False, arrows=False)
        fig.text(0.04, 0.94, headline, fontsize=11, fontweight="bold", ha="left", va="center")
        fig.text(0.04, 0.87, detail, fontsize=8.5, color=INK_SOFT, ha="left", va="center")
        fig.canvas.draw()
        image = Image.frombuffer("RGBA", fig.canvas.get_width_height(), fig.canvas.buffer_rgba())
        image = image.convert("RGB").convert("P", palette=Image.ADAPTIVE, colors=64)
        plt.close(fig)
        return image

    frames = []
    # ---- part 1: exploration ----
    checkpoints = sorted({max(1, round(total * (i + 1) / search_frames)) for i in range(search_frames)})
    heat, seen, done = {}, set(), 0
    for checkpoint in checkpoints if total else []:
        for state in order[done:checkpoint]:
            if state not in seen:
                seen.add(state)
                heat[state.pos] = heat.get(state.pos, 0) + 1
        done = checkpoint
        frames.append(render(dict(heat), f"{result.algorithm}: exploring the state space",
                             f"{checkpoint:,} of {total:,} node expansions",
                             problem.all_food, problem.start, None))
    # ---- part 2: follow the solution ----
    cost_so_far = 0
    for step, state in enumerate(result.states):
        if step > 0:
            cost_so_far += problem.enter_cost(state.pos)
        frames.append(render(final_heat, f"{result.algorithm}: following the returned path",
                             f"step {step} of {result.depth}  |  cost so far {cost_so_far}  |  "
                             f"pellets left {bin(state.food).count('1')}",
                             state.food, state.pos, result.states[:step + 1]))
    if not frames:
        return None
    frames += [frames[-1]] * hold_frames
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=int(1000 / fps), loop=0)
    return path


# --------------------------------------------------------------------------------------
# Search trees
# --------------------------------------------------------------------------------------
TREE_X_GAP = 1.1        # horizontal distance between neighbouring leaves (layout units)
TREE_Y_GAP = 1.22       # vertical distance between two levels
TREE_PAD = 0.95         # free space around the tree


def _layout_tree(nodes, goal_node):
    """Positions for a list of Node objects that form one tree.

    Leaves are spread evenly from left to right and every parent sits above the middle of
    its children. `nodes` are the expanded nodes in expansion order; the goal node is
    added as a leaf when it was not expanded itself.
    """
    all_nodes = list(nodes)
    known = {id(node) for node in all_nodes}
    if goal_node is not None and id(goal_node) not in known:
        all_nodes.append(goal_node)
        known.add(id(goal_node))

    children, root = {}, None
    for node in all_nodes:
        if node.parent is not None and id(node.parent) in known:
            children.setdefault(id(node.parent), []).append(node)
        else:
            root = node

    position = {}
    next_leaf = [0]

    def place(node):
        kids = children.get(id(node), [])
        if kids:
            xs = [place(kid) for kid in kids]
            x = (xs[0] + xs[-1]) / 2
        else:
            x = next_leaf[0] * TREE_X_GAP
            next_leaf[0] += 1
        position[id(node)] = (x, node.depth * TREE_Y_GAP)
        return x

    place(root)
    return {
        "nodes": all_nodes,
        "rank": {id(node): rank for rank, node in enumerate(nodes, start=1)},   # expansion order
        "position": position,
        "solution": {id(node) for node in goal_node.path()} if goal_node is not None else set(),
        "width": (next_leaf[0] - 1) * TREE_X_GAP,
        "height": max(node.depth for node in all_nodes) * TREE_Y_GAP,
    }


def _tree_fill_steps(problem):
    """One blue step per number of eaten pellets (0 eaten = lightest)."""
    k = problem.num_food
    return [BLUE_RAMP[round(i * (len(BLUE_RAMP) - 3) / max(k, 1))] for i in range(k + 1)]


def _draw_tree(ax, problem, tree, show_actions=True, font=6.0):
    """Draw a tree prepared by _layout_tree on the axes `ax`."""
    position, solution, rank = tree["position"], tree["solution"], tree["rank"]
    steps = _tree_fill_steps(problem)
    k = problem.num_food

    for node in tree["nodes"]:                                       # edges first
        if node.parent is None or id(node.parent) not in position:
            continue
        x0, y0 = position[id(node.parent)]
        x1, y1 = position[id(node)]
        on_path = id(node) in solution and id(node.parent) in solution
        ax.plot([x0, x1], [y0, y1], color=ORANGE if on_path else AXIS,
                linewidth=2.2 if on_path else 0.9, zorder=1, solid_capstyle="round")
        if show_actions:
            ax.text((x0 + x1) / 2 + 0.08, (y0 + y1) / 2, node.action[0], fontsize=font - 1.0,
                    color=MUTED, ha="left", va="center", zorder=2)

    for node in tree["nodes"]:                                       # then the nodes
        x, y = position[id(node)]
        fill = steps[k - bin(node.state.food).count("1")]
        on_path = id(node) in solution
        ax.add_patch(Circle((x, y), 0.36, facecolor=fill, edgecolor=ORANGE if on_path else SURFACE,
                            linewidth=1.6 if on_path else 1.0, zorder=3))
        row, col = node.state.pos
        ax.text(x, y, f"{row},{col}", fontsize=font, ha="center", va="center",
                color=text_color_on(fill), zorder=4)
        if id(node) in rank:                                         # order of expansion
            ax.text(x - 0.42, y, str(rank[id(node)]), fontsize=font - 0.4,
                    color=INK_SOFT, ha="right", va="center", zorder=4)
        if problem.is_goal(node.state):
            ax.text(x, y + 0.62, "GOAL", fontsize=font, color=INK, ha="center", va="center",
                    fontweight="bold", zorder=4)

    ax.set_xlim(-TREE_PAD, tree["width"] + TREE_PAD)
    ax.set_ylim(tree["height"] + TREE_PAD, -TREE_PAD)
    ax.axis("off")


def _tree_legend(fig, problem):
    """Legend of a search-tree picture: node colour = pellets left, orange = solution path."""
    k = problem.num_food
    steps = _tree_fill_steps(problem)
    handles = []
    for eaten in range(k + 1):
        left = k - eaten
        label = f"{left} pellet{'s' if left != 1 else ''} left" + (" (goal)" if left == 0 else "")
        handles.append(Line2D([], [], marker="o", linestyle="none", markersize=9,
                              markerfacecolor=steps[eaten], markeredgecolor=SURFACE, label=label))
    handles.append(Line2D([], [], color=ORANGE, linewidth=2.2, label="solution path"))
    fig.legend(handles=handles, loc="lower center", ncol=min(len(handles), 4), fontsize=8,
               bbox_to_anchor=(0.5, 0.0))


def plot_search_tree(problem, result, path, title=None, unit=0.4):
    """The search tree built by one algorithm (expanded nodes + the goal node).

    Node label = Pac-Man's (row,col); the small number beside a node = order of expansion;
    letters on the edges = actions (U, R, D, L). Meant for the tiny layout.
    """
    apply_style()
    nodes = result.expanded_nodes
    final_limit = None
    if "iteration_starts" in result.extra:            # IDS: draw the tree of the final depth limit
        final_limit = len(result.extra["iteration_starts"]) - 1
        nodes = nodes[result.extra["iteration_starts"][-1]:]
    tree = _layout_tree(nodes, result.extra.get("goal_node"))

    ax_w = (tree["width"] + 2 * TREE_PAD) * unit      # the axes box matches the tree exactly,
    ax_h = (tree["height"] + 2 * TREE_PAD) * unit     # so circles stay round
    head, foot = 0.95, 0.55
    fig_w = max(6.4, ax_w + 0.4)
    fig_h = head + ax_h + foot
    fig = plt.figure(figsize=(fig_w, fig_h))
    ax = fig.add_axes([(fig_w - ax_w) / 2 / fig_w, foot / fig_h, ax_w / fig_w, ax_h / fig_h])
    _draw_tree(ax, problem, tree)

    heading = title or f"{result.algorithm} search tree on the '{problem.name}' layout"
    if final_limit is not None:
        heading += f" (final iteration, depth limit {final_limit})"
    fig.text(0.2 / fig_w, 1 - 0.3 / fig_h, heading, fontsize=11, fontweight="bold", ha="left", va="baseline")
    fig.text(0.2 / fig_w, 1 - 0.56 / fig_h,
             f"{result.nodes_expanded} nodes expanded in total, {result.nodes_generated} generated  |  "
             f"solution: {result.depth} steps, cost {result.path_cost:g}",
             fontsize=8, color=INK_SOFT, ha="left", va="baseline")
    fig.text(0.2 / fig_w, 1 - 0.76 / fig_h,
             "node = Pac-Man's (row,col)  |  small number = order of expansion  |  edge letter = action",
             fontsize=8, color=INK_SOFT, ha="left", va="baseline")
    _tree_legend(fig, problem)
    return save_figure(fig, path)


def plot_search_trees(problem, results, path, unit=0.38):
    """The search trees of several algorithms side by side, drawn at the same scale.

    Same conventions as plot_search_tree(). Not meant for IDS (use plot_ids_trees).
    """
    apply_style()
    trees = [_layout_tree(result.expanded_nodes, result.extra.get("goal_node")) for result in results]
    widths = [max((tree["width"] + 2 * TREE_PAD) * unit, 2.0) for tree in trees]
    heights = [(tree["height"] + 2 * TREE_PAD) * unit for tree in trees]
    head, foot, gap, side = 0.95, 0.5, 0.15, 0.15
    fig_w = 2 * side + sum(widths) + gap * (len(trees) - 1)
    fig_h = head + max(heights) + foot
    fig = plt.figure(figsize=(fig_w, fig_h))
    x = side
    for tree, result, width, height in zip(trees, results, widths, heights):
        own_w = (tree["width"] + 2 * TREE_PAD) * unit
        ax = fig.add_axes([(x + (width - own_w) / 2) / fig_w, 1 - (head + height) / fig_h,
                           own_w / fig_w, height / fig_h])
        _draw_tree(ax, problem, tree)
        fig.text(x / fig_w, 1 - 0.3 / fig_h, result.algorithm, fontsize=11, fontweight="bold",
                 ha="left", va="baseline")
        fig.text(x / fig_w, 1 - 0.52 / fig_h,
                 f"{result.nodes_expanded} expanded, {result.nodes_generated} generated",
                 fontsize=8, color=INK_SOFT, ha="left", va="baseline")
        fig.text(x / fig_w, 1 - 0.7 / fig_h, f"solution: {result.depth} steps, cost {result.path_cost:g}",
                 fontsize=8, color=INK_SOFT, ha="left", va="baseline")
        x += width + gap
    _tree_legend(fig, problem)
    return save_figure(fig, path)


def plot_ids_trees(problem, result, path, limits=None, unit=0.36):
    """Iterative deepening: the tree searched at several depth limits, side by side."""
    apply_style()
    starts = result.extra["iteration_starts"]
    nodes = result.expanded_nodes
    last = len(starts) - 1
    if limits is None:
        limits = sorted({max(1, last // 4), max(1, last // 2), max(1, 3 * last // 4), last})
    trees = []
    for limit in limits:
        end = starts[limit + 1] if limit + 1 < len(starts) else len(nodes)
        goal = result.extra.get("goal_node") if limit == last else None
        trees.append(_layout_tree(nodes[starts[limit]:end], goal))

    widths = [max((tree["width"] + 2 * TREE_PAD) * unit, 1.5) for tree in trees]
    heights = [(tree["height"] + 2 * TREE_PAD) * unit for tree in trees]
    head, foot, gap, side = 1.05, 0.55, 0.25, 0.2
    fig_w = max(2 * side + sum(widths) + gap * (len(trees) - 1), 7.0)
    fig_h = head + max(heights) + foot
    fig = plt.figure(figsize=(fig_w, fig_h))
    x = side
    for tree, limit, width, height in zip(trees, limits, widths, heights):
        own_w = (tree["width"] + 2 * TREE_PAD) * unit
        ax = fig.add_axes([(x + (width - own_w) / 2) / fig_w, 1 - (head + height) / fig_h,
                           own_w / fig_w, height / fig_h])
        _draw_tree(ax, problem, tree, show_actions=False, font=5.4)
        fig.text(x / fig_w, 1 - 0.72 / fig_h, f"depth limit {limit}", fontsize=10, fontweight="bold",
                 ha="left", va="baseline")
        fig.text(x / fig_w, 1 - 0.92 / fig_h, f"{len(tree['rank'])} nodes expanded", fontsize=8,
                 color=INK_SOFT, ha="left", va="baseline")
        x += width + gap
    fig.text(side / fig_w, 1 - 0.3 / fig_h,
             f"IDS on the '{problem.name}' layout: the tree is rebuilt from the root for every depth limit",
             fontsize=11, fontweight="bold", ha="left", va="baseline")
    _tree_legend(fig, problem)
    return save_figure(fig, path)


# --------------------------------------------------------------------------------------
# Charts
# --------------------------------------------------------------------------------------
def spans_orders_of_magnitude(values, factor=100):
    """True if the largest value is at least `factor` times the smallest positive one."""
    positive = [value for value in values if value > 0]
    return bool(positive) and max(positive) >= factor * min(positive)


def bar_panel(ax, labels, values, title, fmt="{:,.0f}", color=BLUE, reference=None, label_from=None,
              log=False):
    """Horizontal bars with the value written at the tip of every bar.

    reference   optional x position of a vertical reference line
    label_from  optional list: x position after which each value label is written (used when
                something is drawn beyond the end of the bar); default = the bar's own value
    log         draw the panel on a logarithmic axis. Used when the values span several
                orders of magnitude and the small bars would otherwise be invisible; the
                length of a bar then shows a ratio, and the title says "log scale".
    """
    positions = list(range(len(labels)))
    label_from = [max(a, b) for a, b in zip(values, label_from)] if label_from else values
    ax.set_yticks(positions)
    ax.set_yticklabels(labels)
    ax.set_title(title + (" - log scale" if log else ""), fontsize=8.8, fontweight="bold", loc="left")
    ax.xaxis.grid(True, zorder=0)
    ax.set_axisbelow(True)
    ax.spines["left"].set_visible(False)
    if log:
        smallest = min(value for value in values if value > 0)
        floor = 10.0 ** math.floor(math.log10(smallest))      # left end of the axis: a power of ten
        if smallest < 2 * floor:
            floor /= 10                                       # keep the shortest bar visible
        ax.barh(positions, [max(value, floor) - floor for value in values], left=floor, height=0.55,
                color=color, zorder=2)
        ax.set_xscale("log")
        ax.set_xlim(floor, max(label_from) * 12)              # room for the value labels
        ax.minorticks_off()
        for position, value, start in zip(positions, values, label_from):
            ax.text(max(start, floor) * 1.18, position, fmt.format(value), va="center", ha="left",
                    fontsize=7.5, color=INK)
    else:
        ax.barh(positions, values, height=0.55, color=color, zorder=2)
        top = max(label_from) if max(label_from) > 0 else 1
        ax.set_xlim(0, top * 1.2)
        ax.xaxis.set_major_locator(MaxNLocator(nbins=5))
        for position, value, start in zip(positions, values, label_from):
            ax.text(start + top * 0.02, position, fmt.format(value), va="center", ha="left",
                    fontsize=7.5, color=INK)
    ax.invert_yaxis()
    ax.tick_params(which="both", length=0, labelsize=8)
    ax.xaxis.set_major_formatter(FuncFormatter(plain_number))
    if reference is not None:
        ax.axvline(reference, color=INK, linewidth=1.0, zorder=3)


def plot_metric_bars(rows, path, title=None, optimal_cost=None, panels=None):
    """Small bar charts comparing the algorithms on one layout.

    rows: list of dictionaries as produced by experiments.evaluate_search().
    """
    apply_style()
    labels = [row["algorithm"] for row in rows]
    if panels is None:
        cost_title = "Path cost"
        if optimal_cost:
            cost_title += f" (line = optimal, {optimal_cost:g})"
        panels = [
            ("nodes_generated", "Nodes generated", "{:,.0f}"),
            ("nodes_expanded", "Nodes expanded", "{:,.0f}"),
            ("max_frontier", "Maximum frontier size", "{:,.0f}"),
            ("max_nodes_in_memory", "Maximum nodes in memory", "{:,.0f}"),
            ("time_ms", "Running time (ms)", "{:,.2f}"),
            ("path_cost", cost_title, "{:,.0f}"),
        ]
    ncols = 3
    nrows = (len(panels) + ncols - 1) // ncols
    fig, axes = plt.subplots(nrows, ncols, figsize=(7.6, nrows * (0.26 * len(rows) + 0.85) + 0.4),
                             squeeze=False)
    for ax in axes.flat[len(panels):]:
        ax.axis("off")
    for ax, (key, heading, fmt) in zip(axes.flat, panels):
        values = [row[key] if row[key] is not None else 0 for row in rows]
        reference = optimal_cost if key == "path_cost" and optimal_cost else None
        bar_panel(ax, labels, values, heading, fmt, reference=reference,
                  log=spans_orders_of_magnitude(values))
    if title:
        fig.suptitle(title, fontsize=10.5, fontweight="bold", x=0.01, ha="left")
    fig.tight_layout(rect=(0, 0, 1, 0.94 if title else 1), w_pad=1.2, h_pad=1.2)
    return save_figure(fig, path)


def plot_frontier_history(results, path, title=None, bins=300):
    """Frontier size during the search.

    The x axis is the progress of each run in percent, so that runs of very different
    lengths fit in one chart; the y axis is logarithmic. Each run is cut into `bins` equal
    slices and the largest frontier of the slice is plotted.
    """
    apply_style()
    fig, ax = plt.subplots(figsize=(6.6, 3.2))
    for color, result in zip(SERIES, results):
        history = result.frontier_history
        if not history:
            continue
        slices = min(bins, len(history))
        xs, ys = [], []
        for i in range(slices):
            lo = i * len(history) // slices
            hi = max((i + 1) * len(history) // slices, lo + 1)
            xs.append(100.0 * hi / len(history))
            ys.append(max(history[lo:hi]))
        ax.plot(xs, ys, color=color, linewidth=1.8, solid_joinstyle="round",
                label=f"{result.algorithm} (max {max(history):,})")
        ax.plot([xs[-1]], [ys[-1]], marker="o", markersize=6, color=color,
                markeredgecolor=SURFACE, markeredgewidth=1.2)
    ax.set_yscale("log")
    ax.yaxis.set_major_formatter(FuncFormatter(plain_number))
    ax.set_xlim(0, 103)
    ax.set_xlabel("progress of the search (% of its node expansions)")
    ax.set_ylabel("nodes in the frontier (log scale)")
    ax.yaxis.grid(True)
    ax.set_axisbelow(True)
    ax.tick_params(which="both", length=0)
    ax.set_title(title or "Frontier size while the search is running", fontsize=10.5,
                 fontweight="bold", loc="left")
    ax.legend(loc="upper left", bbox_to_anchor=(1.0, 1.0), fontsize=8.5)
    return save_figure(fig, path)


def plot_ids_iterations(result, path, title=None):
    """Nodes expanded by IDS at every depth limit - shows the repeated work."""
    apply_style()
    iterations = result.extra["iterations"]
    limits = [it["limit"] for it in iterations]
    expanded = [it["expanded"] for it in iterations]
    fig, ax = plt.subplots(figsize=(6.4, 3.0))
    ax.bar(limits, expanded, width=0.62, color=BLUE, zorder=2)
    ax.set_xlabel("depth limit of the iteration")
    ax.set_ylabel("nodes expanded in that iteration")
    ax.yaxis.grid(True, zorder=0)
    ax.yaxis.set_major_formatter(FuncFormatter(plain_number))
    ax.set_axisbelow(True)
    ax.tick_params(length=0)
    ax.set_xlim(-0.8, limits[-1] + 0.8)
    total = sum(expanded)
    ax.text(limits[-1], expanded[-1], f"{expanded[-1]:,}", ha="center", va="bottom", fontsize=8)
    ax.set_title(title or f"IDS: nodes expanded at each depth limit (total {total:,})", fontsize=10.5,
                 fontweight="bold", loc="left")
    return save_figure(fig, path)


def plot_scaling(points, path, title=None, ylabel="nodes expanded (log scale)", layout_names=None):
    """Search effort versus the size of the state space.

    points        {algorithm: [(reachable_states, nodes_expanded), ...]} - one pair per layout
    layout_names  optional {reachable_states: layout name} used to label the x axis
    """
    apply_style()
    fig, ax = plt.subplots(figsize=(6.4, 3.3))
    all_x = set()
    for color, (algorithm, pairs) in zip(SERIES, points.items()):
        pairs = sorted(pairs)
        xs = [x for x, _ in pairs]
        ys = [y for _, y in pairs]
        all_x.update(xs)
        ax.plot(xs, ys, color=color, linewidth=1.8, marker="o", markersize=6,
                markeredgecolor=SURFACE, markeredgewidth=1.2, label=algorithm)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ticks = sorted(all_x)
    ax.set_xticks(ticks)
    ax.set_xticklabels([f"{x:,}" + (f"\n({layout_names[x]})" if layout_names and x in layout_names else "")
                        for x in ticks])
    ax.minorticks_off()
    ax.yaxis.set_major_formatter(FuncFormatter(plain_number))
    ax.set_xlabel("reachable states of the layout (log scale)")
    ax.set_ylabel(ylabel)
    ax.yaxis.grid(True)
    ax.set_axisbelow(True)
    ax.tick_params(which="both", length=0)
    ax.margins(x=0.12)
    ax.set_title(title or "How the search effort grows with the state space", fontsize=10.5,
                 fontweight="bold", loc="left")
    ax.legend(loc="upper left", bbox_to_anchor=(1.0, 1.0), fontsize=8.5)
    return save_figure(fig, path)

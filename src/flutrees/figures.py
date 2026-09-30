"""Headless, paginated node-and-edge figures shared by every visual export."""

from collections import deque
from typing import Optional

from .layout import FigureStyle
from .tree_build import Node
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure


def children(node: Node) -> list[Node]:
    return [child for child in (node.left, node.right) if child is not None]


def tree_pages(root: Node) -> list[list[Node]]:
    """At most four levels per page; boundary nodes continue on named pages."""
    pages = []
    pending = deque([root])
    while pending:
        start = pending.popleft()
        nodes = []
        queue = deque([start])
        while queue:
            node = queue.popleft()
            nodes.append(node)
            descendants = children(node)
            if node.depth - start.depth == 3:
                if descendants:
                    pending.append(node)
            else:
                queue.extend(descendants)
        pages.append(nodes)
    return pages


def tree_figure(nodes: list[Node], total: int, title: str, page_number: int,
                page_map: dict[int, int], style: Optional[FigureStyle] = None) -> Figure:
    """Measure labels, reserve gaps, and fit a whole page without overlapping boxes.

    Geometry uses points with equal-axis scaling. Spacing changes actual gaps
    relative to labels, rather than disappearing through independent autoscaling.
    Labels shrink together only when the requested page cannot contain them at
    their nominal size. Tree pagination bounds every page at fifteen nodes.
    """
    style = style or FigureStyle()
    fig = Figure(figsize=(style.figure_width, style.figure_height))
    canvas = FigureCanvasAgg(fig)
    fig.patch.set_facecolor("#f7fafc")
    labels = {}
    measurements = []
    for node in nodes:
        label = f"#{node.node_id}  {node.label}\n{node.support:,} records  ({node.support / total:.1%} of input)"
        if node.node_id in page_map and node is not nodes[0]:
            label += f"\nContinues on page {page_map[node.node_id]}"
        labels[node.node_id] = label
        measurements.append(fig.text(0, 0, label, fontsize=9, parse_math=False))
    canvas.draw()
    renderer = canvas.get_renderer()
    # Include box padding and a stroke allowance in the measured envelope.
    box_width = max(t.get_window_extent(renderer).width for t in measurements) * 72 / fig.dpi + 14
    box_height = max(t.get_window_extent(renderer).height for t in measurements) * 72 / fig.dpi + 14
    for text in measurements:
        text.remove()
    dx = box_width + 40 * style.level_spacing
    dy = box_height + 16 * style.node_spacing
    positions = {}
    node_ids = {node.node_id for node in nodes}
    cursor = 0

    def place(node):
        nonlocal cursor
        visible = [child for child in children(node) if child.node_id in node_ids]
        ys = [place(child) for child in visible]
        if ys:
            y = sum(ys) / len(ys)
        else:
            y = cursor * dy
            cursor += 1
        positions[node.node_id] = ((node.depth - nodes[0].depth) * dx, y)
        return y

    place(nodes[0])
    xmax = max(x for x, _ in positions.values())
    ymax = max(y for _, y in positions.values())
    width, height = xmax + box_width + 16, ymax + box_height + 16
    factor = min(1.0, style.figure_width * 72 * 0.94 / width,
                 style.figure_height * 72 * 0.71 / height)
    ax = fig.add_axes((0.03, 0.14, 0.94, 0.71))
    ax.set_facecolor("#f7fafc")
    ax.set_aspect("equal", adjustable="box")
    for node in nodes:
        x, y = positions[node.node_id]
        for child in children(node):
            if child.node_id in positions:
                cx, cy = positions[child.node_id]
                bend = (x + cx) / 2
                ax.plot([x, bend, bend, cx], [-y, -y, -cy, -cy], color="#8498a8",
                        lw=style.line_width * factor, zorder=1)
        ax.text(x, -y, labels[node.node_id], ha="center", va="center", fontsize=9 * factor,
                parse_math=False, bbox={"boxstyle": "round,pad=0.6",
                                       "fc": "#e1edf6" if node.label.startswith("Not ") else "#d9f0e7",
                                       "ec": "#598174", "lw": 0.8 * factor}, zorder=2)
    ax.set_xlim(-box_width / 2 - 8, xmax + box_width / 2 + 8)
    ax.set_ylim(-ymax - box_height / 2 - 8, box_height / 2 + 8)
    ax.axis("off")
    decoration_scale = min(1.0, style.figure_width / 10, style.figure_height / 6)
    fig.suptitle(title, x=0.06, y=0.98, ha="left", fontsize=19 * decoration_scale,
                 weight="bold", color="#163849")
    fig.text(0.06, 0.91,
             f"Tree page {page_number} of {len(page_map)} | Mutation decision tree | Record counts, not confidence scores",
             fontsize=10 * decoration_scale)
    fig.text(0.06, 0.04,
             "Branches partition records by a called substitution. This is not an evolutionary tree.\n"
             "Percentages use all input records; pruning can hide groups. Full membership is in results.xlsx.",
             fontsize=9 * decoration_scale)
    return fig


def write_tree_figures(outdir, tree, name, mode="", style=None):
    title = (mode.title() + " - " if mode else "") + name.replace("_", " ").title()
    pages = tree_pages(tree)
    page_map = {nodes[0].node_id: i for i, nodes in enumerate(pages, 1)}
    with PdfPages(outdir / f"{name}.pdf") as pdf, matplotlib.rc_context({"svg.fonttype": "none"}):
        for i, nodes in enumerate(pages, 1):
            fig = tree_figure(nodes, tree.support, title, i, page_map, style)
            stem = name if i == 1 else f"{name}_page_{i:03d}"
            try:
                pdf.savefig(fig)
                fig.savefig(outdir / f"{stem}.svg")
                fig.savefig(outdir / f"{stem}.png", dpi=140)
            finally:
                plt.close(fig)

"""Headless, paginated node-and-edge figures shared by every visual export."""

from collections import deque
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages


def children(node):
    return [child for child in (node.left, node.right) if child is not None]


def tree_pages(root):
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


def tree_figure(nodes, total, title, page_number, page_map):
    positions = {}
    node_ids = {node.node_id for node in nodes}
    cursor = 0

    def place(node):
        nonlocal cursor
        visible = [c for c in children(node) if c.node_id in node_ids]
        ys = [place(c) for c in visible]
        if ys:
            y = sum(ys) / len(ys)
        else:
            y = cursor
            cursor += 1
        positions[node.node_id] = (node.depth - nodes[0].depth, y)
        return y

    place(nodes[0])
    fig, ax = plt.subplots(figsize=(14, 8.5))
    fig.patch.set_facecolor("#f7fafc")
    ax.set_facecolor("#f7fafc")
    for node in nodes:
        x, y = positions[node.node_id]
        for child in children(node):
            if child.node_id in positions:
                cx, cy = positions[child.node_id]
                ax.plot(
                    [x, x + 0.5, x + 0.5, cx], [-y, -y, -cy, -cy], color="#8498a8", lw=1.5, zorder=1
                )
        label = f"#{node.node_id}  {node.label}\n{node.support:,} records  ({node.support / total:.1%} of input)"
        if node.node_id in page_map and node is not nodes[0]:
            label += f"\nContinues on page {page_map[node.node_id]}"
        ax.text(
            x,
            -y,
            label,
            ha="center",
            va="center",
            fontsize=9,
            parse_math=False,
            bbox={
                "boxstyle": "round,pad=0.6",
                "fc": "#e1edf6" if node.label.startswith("Not ") else "#d9f0e7",
                "ec": "#598174",
            },
            zorder=2,
        )
    ax.set_xlim(-0.5, 3.5)
    ax.set_ylim(-max(cursor - 1, 0) - 0.8, 0.8)
    ax.axis("off")
    fig.suptitle(title, x=0.06, ha="left", fontsize=19, weight="bold", color="#163849")
    fig.text(
        0.06,
        0.92,
        f"Tree page {page_number} of {len(page_map)} | Mutation decision tree | Record counts, not confidence scores",
        fontsize=10,
    )
    fig.text(
        0.06,
        0.055,
        "Branches partition records by a called substitution. This is not an evolutionary tree.\n"
        "Percentages use all input records; pruning can hide groups. Full membership is in results.xlsx.",
        fontsize=9,
    )
    fig.subplots_adjust(left=0.02, right=0.98, top=0.86, bottom=0.13)
    return fig


def write_tree_figures(outdir, tree, name, mode=""):
    title = (mode.title() + " - " if mode else "") + name.replace("_", " ").title()
    pages = tree_pages(tree)
    page_map = {nodes[0].node_id: i for i, nodes in enumerate(pages, 1)}
    with PdfPages(outdir / f"{name}.pdf") as pdf, matplotlib.rc_context({"svg.fonttype": "none"}):
        for i, nodes in enumerate(pages, 1):
            fig = tree_figure(nodes, tree.support, title, i, page_map)
            stem = name if i == 1 else f"{name}_page_{i:03d}"
            try:
                pdf.savefig(fig)
                fig.savefig(outdir / f"{stem}.svg")
                fig.savefig(outdir / f"{stem}.png", dpi=140)
            finally:
                plt.close(fig)

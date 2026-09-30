"""Bounded, paginated desktop inspection of already-computed tree JSON.

Only one page is rasterized. Resize/zoom operate on that cached image, never on
Matplotlib in parallel with an analysis worker. No alignment or tree inference
is performed by this viewer.
"""

import json
import math
from pathlib import Path
from typing import Callable, Optional, Any, cast

from .layout import FigureStyle, image_size

from .tree_build import Node
from PIL.Image import Image
from matplotlib.figure import Figure


class TreeViewer:
    def __init__(self, parent: Any, tk: Any, ttk: Any, dialogs: Any,
                 get_style: Callable[[], FigureStyle], is_busy: Callable[[], bool]) -> None:
        self.parent = parent
        self.dialogs = dialogs
        self.get_style = get_style
        self.is_busy = is_busy
        self.paths: dict[str, Path] = {}
        self.pages: list[list[Node]] = []
        self.page = 0
        self.total = 0
        self.zoom = 1.0
        self.figure: Optional[Figure] = None
        self.image: Optional[Image] = None
        self.page_image: Optional[Image] = None
        # ImageTk stays lazy so CLI installations do not require Tk.
        self.photo: Any = None
        self.resize_token: Optional[str] = None
        self.choice = tk.StringVar(value="")
        self.whole_page = tk.BooleanVar(value=False)
        self.message = tk.StringVar(value="Complete an analysis or open a completed results folder to inspect its trees.")
        row = ttk.Frame(parent)
        row.pack(fill="x", pady=(4, 6))
        self.open_button = ttk.Button(row, text="Open saved run...", command=self.open_run)
        self.open_button.pack(side="left", padx=(0, 8))
        self.selector = ttk.Combobox(row, textvariable=self.choice, state="disabled", width=40)
        self.selector.pack(side="left", fill="x", expand=True)
        self.selector.bind("<<ComboboxSelected>>", lambda event: self.select_tree())
        self.page_toggle = ttk.Checkbutton(row, text="Whole page", variable=self.whole_page, command=self.fit_page)
        self.page_toggle.pack(side="left", padx=(8, 0))
        toolbar = ttk.Frame(parent)
        toolbar.pack(fill="x", pady=(0, 6))
        self.previous = ttk.Button(toolbar, text="Previous page", command=lambda: self.change_page(-1))
        self.next = ttk.Button(toolbar, text="Next page", command=lambda: self.change_page(1))
        self.apply = ttk.Button(toolbar, text="Apply layout", command=self.render)
        self.fit = ttk.Button(toolbar, text="Fit", command=self.fit_page)
        self.smaller = ttk.Button(toolbar, text="Zoom -", command=lambda: self.zoom_by(0.5))
        self.larger = ttk.Button(toolbar, text="Zoom +", command=lambda: self.zoom_by(2.0))
        self.save = ttk.Button(toolbar, text="Save page...", command=self.save_page)
        for button in (self.previous, self.next, self.apply, self.fit, self.smaller, self.larger, self.save):
            button.pack(side="left", padx=(0, 5))
        ttk.Label(parent, textvariable=self.message, wraplength=760).pack(anchor="w", pady=(0, 6))
        view = ttk.Frame(parent)
        view.pack(fill="both", expand=True)
        view.rowconfigure(0, weight=1)
        view.columnconfigure(0, weight=1)
        self.canvas = tk.Canvas(view, highlightthickness=0, background="#f7fafc")
        horizontal = ttk.Scrollbar(view, orient="horizontal", command=self.canvas.xview)
        vertical = ttk.Scrollbar(view, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(xscrollcommand=horizontal.set, yscrollcommand=vertical.set)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        horizontal.grid(row=1, column=0, sticky="ew")
        vertical.grid(row=0, column=1, sticky="ns")
        self.canvas.bind("<Configure>", self.on_resize)
        self.canvas.bind("<ButtonPress-1>", lambda event: self.canvas.scan_mark(event.x, event.y))
        self.canvas.bind("<B1-Motion>", lambda event: self.canvas.scan_dragto(event.x, event.y, gain=1))
        self.update_controls()

    def update_controls(self) -> None:
        busy = self.is_busy()
        ready = bool(self.pages) and not busy
        self.open_button.configure(state="disabled" if busy else "normal")
        self.selector.configure(state="readonly" if self.paths and not busy else "disabled")
        self.page_toggle.configure(state="normal" if ready else "disabled")
        self.apply.configure(state="normal" if ready else "disabled")
        for button in (self.fit, self.smaller, self.larger, self.save):
            button.configure(state="normal" if ready and self.figure is not None else "disabled")
        self.previous.configure(state="normal" if ready and self.page > 0 else "disabled")
        self.next.configure(state="normal" if ready and self.page + 1 < len(self.pages) else "disabled")

    def clear_picture(self) -> None:
        self.figure = self.image = self.page_image = self.photo = None
        self.canvas.delete("all")

    def load_run(self, root: Path) -> bool:
        if self.is_busy():
            return False
        self.paths = {}
        self.pages = []
        self.choice.set("")
        self.clear_picture()
        try:
            root = root.resolve()
            status_path = root / "status.json"
            if status_path.stat().st_size > 1024 * 1024:
                raise ValueError("Run status exceeds the 1 MiB metadata limit.")
            status = json.loads(status_path.read_text(encoding="utf-8"))
            if not isinstance(status, dict) or status.get("status") != "complete":
                raise ValueError("Only completed analysis runs can be opened.")
            for path in sorted(root.glob("*/trees/*/tree_*.json")):
                if path.name in {"tree_full.json", "tree_pruned.json"} and path.resolve().is_relative_to(root) and path.is_file():
                    self.paths[path.relative_to(root).as_posix()] = path
            if not self.paths:
                raise ValueError("No tree JSON files found in this run folder.")
            self.selector.configure(values=tuple(self.paths))
            self.choice.set(next(iter(self.paths)))
            self.select_tree()
        except (ValueError, OSError, RecursionError) as error:
            self.message.set(f"Cannot open trees: {error}")
        self.update_controls()
        return self.figure is not None

    def open_run(self) -> None:
        if self.is_busy():
            return
        path = self.dialogs[0].askdirectory(title="Choose a completed FluTrees run folder")
        if path and not self.load_run(Path(path)):
            self.dialogs[1].showerror("Cannot open trees", self.message.get())

    def select_tree(self) -> None:
        if self.is_busy():
            return
        from .tree_io import read_tree
        from .figures import tree_pages

        self.pages = []
        self.clear_picture()
        try:
            path = self.paths[self.choice.get()]
            if path.stat().st_size > 64 * 1024 * 1024:
                raise ValueError("Tree JSON exceeds the 64 MiB desktop preview limit. Use its paginated PDF instead.")
            tree = read_tree(path)
            self.pages = tree_pages(tree)
            self.total = tree.support
            self.page = 0
            self.render()
        except (ValueError, OSError, KeyError, RecursionError) as error:
            self.message.set(f"Cannot display tree: {error}")
        self.update_controls()

    def change_page(self, offset: int) -> None:
        if self.is_busy() or not 0 <= self.page + offset < len(self.pages):
            return
        self.page += offset
        self.render()

    def render(self) -> None:
        if self.is_busy() or not self.pages:
            return
        from PIL import Image
        from .figures import tree_figure
        from matplotlib.backends.backend_agg import FigureCanvasAgg
        from matplotlib.transforms import Bbox
        from matplotlib.patches import FancyBboxPatch

        try:
            style = self.get_style()
            path = self.paths[self.choice.get()]
            title = f"{path.parent.name.title()}: {path.stem.replace('_', ' ').title()}"
            mapping = {nodes[0].node_id: i for i, nodes in enumerate(self.pages, 1)}
            figure = tree_figure(self.pages[self.page], self.total, title, self.page + 1, mapping, style)
            canvas = FigureCanvasAgg(figure)
            canvas.draw()
            image = Image.frombuffer("RGBA", canvas.get_width_height(),
                                     canvas.buffer_rgba(), "raw", "RGBA", 0, 1).copy()
            # Fit the actual tree in the desktop, excluding printed-page margins
            # and decorations. Export retains the full, correctly sized figure.
            renderer = canvas.get_renderer()
            bounds = Bbox.union([cast(FancyBboxPatch, text.get_bbox_patch()).get_window_extent(renderer)
                                 for text in figure.axes[0].texts])
            width, height = image.size
            tree_image = image.crop((max(0, math.floor(bounds.x0) - 16),
                                max(0, height - math.ceil(bounds.y1) - 16),
                                min(width, math.ceil(bounds.x1) + 16),
                                min(height, height - math.floor(bounds.y0) + 16)))
            self.figure, self.image, self.page_image = figure, tree_image, image
            self.zoom = 1.0
            self.redraw()
        except (ValueError, OSError) as error:
            self.clear_picture()
            self.message.set(f"Cannot apply layout: {error}")
        self.update_controls()

    def fit_page(self) -> None:
        if self.is_busy():
            return
        self.zoom = 1.0
        self.redraw()

    def zoom_by(self, factor: float) -> None:
        if self.is_busy():
            return
        self.zoom = min(8.0, max(0.25, self.zoom * factor))
        self.redraw()

    def on_resize(self, event: Any) -> None:
        if self.resize_token is not None:
            self.canvas.after_cancel(self.resize_token)
        self.resize_token = self.canvas.after(80, self.redraw)

    def redraw(self) -> None:
        from PIL import Image, ImageTk

        if self.resize_token is not None:
            self.canvas.after_cancel(self.resize_token)
            self.resize_token = None
        source = self.page_image if self.whole_page.get() else self.image
        if source is None:
            return
        viewport_width, viewport_height = max(1, self.canvas.winfo_width()), max(1, self.canvas.winfo_height())
        width, height = image_size(*source.size, viewport_width, viewport_height, self.zoom)
        self.photo = ImageTk.PhotoImage(source.resize((width, height), Image.Resampling.LANCZOS), master=self.canvas)
        self.canvas.delete("all")
        self.canvas.create_image(max(0, (viewport_width - width) // 2), max(0, (viewport_height - height) // 2),
                                 image=self.photo, anchor="nw")
        self.canvas.configure(scrollregion=(0, 0, max(width, viewport_width), max(height, viewport_height)))
        self.canvas.xview_moveto(max(0.0, (width - viewport_width) / (2 * width)))
        self.canvas.yview_moveto(max(0.0, (height - viewport_height) / (2 * height)))
        fit_width, _ = image_size(*source.size, viewport_width, viewport_height)
        self.message.set(f"Page {self.page + 1} of {len(self.pages)} | Zoom {width / fit_width:.0%} of fit | "
                         f"{len(self.pages[self.page])} visible nodes | Drag to pan; Fit resets zoom.")

    def save_page(self) -> None:
        if self.is_busy() or self.figure is None:
            return
        path = self.dialogs[0].asksaveasfilename(
            title="Save the displayed tree page", defaultextension=".png",
            filetypes=[("PNG image", "*.png"), ("SVG vector", "*.svg"), ("PDF page", "*.pdf")],
        )
        if path:
            try:
                if Path(path).suffix.lower() not in {".png", ".svg", ".pdf"}:
                    raise ValueError("Choose a PNG, SVG, or PDF filename.")
                import matplotlib

                with matplotlib.rc_context({"svg.fonttype": "none"}):
                    self.figure.savefig(path, dpi=140)
            except (ValueError, OSError) as error:
                self.dialogs[1].showerror("Could not save page", str(error))

    def close(self) -> None:
        if self.resize_token is not None:
            self.canvas.after_cancel(self.resize_token)
            self.resize_token = None
        self.clear_picture()
        # Break Launcher -> viewer -> bound callback cycles before Tk teardown.
        self.get_style = FigureStyle
        self.is_busy = lambda: False

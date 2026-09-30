"""Native desktop workspace for the same configuration and pipeline as the CLI."""

import os
import gc
import queue
import shlex
import threading
import webbrowser
from pathlib import Path
from typing import Optional, Sequence, Any

from . import __version__
from .config import RunConfig
from .provenance import validate_run_id
from .layout import FigureStyle, FIGURE_FIELDS
from .gui_viewer import TreeViewer


ALIGNMENT_PROFILES = {"Mode default": None, "Reproducible": True, "Legacy": False}


def parse_number(value, label, convert=int):
    try:
        return convert(value)
    except ValueError as error:
        expected = "a whole number" if convert is int else "a number (for example, 0.05)"
        raise ValueError(f"{label} must be {expected}.") from error


def cli_command(cfg: RunConfig, inputs: Sequence[Path], outdir: Path, run_id: str,
                windows: Optional[bool] = None) -> str:
    """Quote every argument safely for POSIX shells or Windows PowerShell."""
    args = ["flutrees"]
    for path in inputs:
        args.extend(["-i", str(path)])
    args.extend(["--outdir", str(outdir), "--run-id", run_id])
    for flag, value in (
        ("--start", cfg.start_residue), ("--end", cfg.end_residue),
        ("--max-depth", cfg.max_depth), ("--min-split", cfg.min_split),
        ("--min-freq", cfg.min_freq), ("--prune-cutoff", cfg.prune_cutoff),
        ("--tree-mode", cfg.tree_mode), ("--mafft", cfg.mafft),
        ("--threads", cfg.resolved_threads()),
    ):
        args.extend([flag, str(value)])
    if cfg.reference_id is not None:
        args.extend(["--reference-id", cfg.reference_id])
    if cfg.reproducible is not None:
        args.append("--reproducible" if cfg.reproducible else "--legacy-alignment")
    for name in FIGURE_FIELDS:
        args.extend(["--" + name.replace("_", "-"), str(getattr(cfg, name))])
    if windows if windows is not None else os.name == "nt":
        return "& " + " ".join("'" + arg.replace("'", "''") + "'" for arg in args)
    return shlex.join(args)


class Launcher:
    max_depth: Any
    min_split: Any
    min_freq: Any
    prune_cutoff: Any

    def __init__(self, root, tk, ttk, dialogs):
        self.root = root
        self.tk_error = tk.TclError
        self.dialogs = dialogs
        self.inputs = []
        self.result = None
        self.running = False
        self.events: queue.Queue[tuple[str, Any]] = queue.Queue()
        self.controls: list[tuple[Any, str]] = []
        defaults = RunConfig()
        root.title(f"FluTrees {__version__}")
        root.geometry(f"1000x{min(820, max(620, root.winfo_screenheight() - 80))}")
        root.minsize(860, 620)
        root.protocol("WM_DELETE_WINDOW", self.close)
        style = ttk.Style(root)
        if style.theme_use() in {"default", "classic"}:
            style.theme_use("clam")
        if style.theme_use() == "clam":
            style.configure(".", background="#f3f6fa", foreground="#173247")
            style.configure("TNotebook", background="#f3f6fa", borderwidth=0)
            style.configure("TNotebook.Tab", padding=(12, 5))
            style.map("TNotebook.Tab", background=[("selected", "#ffffff")])
            style.configure("TButton", padding=(8, 5), background="#ffffff")
            style.configure("Action.TButton", background="#176b87", foreground="#ffffff")
            style.map("Action.TButton", background=[("disabled", "#dbe3eb"), ("active", "#12576e")],
                      foreground=[("disabled", "#677987")])
            style.configure("TEntry", fieldbackground="#ffffff", padding=3)
            style.configure("TCombobox", fieldbackground="#ffffff", padding=3)
            style.configure("Treeview", background="#ffffff", fieldbackground="#ffffff", rowheight=24)
        style.configure("Title.TLabel", font=("Helvetica", 20, "bold"))
        style.configure("Section.TLabelframe.Label", font=("TkDefaultFont", 10, "bold"))
        style.configure("Action.TButton", padding=(12, 7))
        shell = ttk.Frame(root, padding=18)
        shell.pack(fill="both", expand=True)
        header = ttk.Frame(shell)
        header.pack(fill="x", pady=(0, 12))
        ttk.Label(header, text="FluTrees", style="Title.TLabel").pack(side="left")
        ttk.Label(header, text=f"{__version__}  |  Influenza HA mutation trees").pack(side="left", padx=16)
        self.tabs = ttk.Notebook(shell)
        self.tabs.pack(fill="both", expand=True)
        self.analysis_tab = ttk.Frame(self.tabs)
        self.canvas = tk.Canvas(self.analysis_tab, borderwidth=0, highlightthickness=0)
        settings_scroll = ttk.Scrollbar(self.analysis_tab, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=settings_scroll.set)
        settings_scroll.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.setup_tab = ttk.Frame(self.canvas, padding=12)
        self.settings_window = self.canvas.create_window((0, 0), window=self.setup_tab, anchor="nw")
        self.setup_tab.bind("<Configure>", lambda event: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda event: self.canvas.itemconfigure(self.settings_window, width=event.width))
        root.bind("<MouseWheel>", self.scroll_settings)
        root.bind("<Button-4>", self.scroll_settings)
        root.bind("<Button-5>", self.scroll_settings)
        advanced = ttk.Frame(self.tabs, padding=18)
        self.viewer_tab = ttk.Frame(self.tabs, padding=12)
        self.log_tab = ttk.Frame(self.tabs, padding=12)
        for tab, title in ((self.analysis_tab, "Analysis"), (advanced, "Advanced"),
                           (self.viewer_tab, "Tree viewer"), (self.log_tab, "Run log")):
            self.tabs.add(tab, text=title)

        def section(parent, title):
            box = ttk.LabelFrame(parent, text=title, padding=10, style="Section.TLabelframe")
            box.pack(fill="x", pady=(0, 10))
            return box

        def button(parent, text, command):
            widget = ttk.Button(parent, text=text, command=command)
            widget.pack(side="left", padx=(0, 6))
            self.controls.append((widget, "normal"))
            return widget

        def field(parent, row, column, label, variable, hint, values=None, width=16):
            box = ttk.Frame(parent)
            box.grid(row=row, column=column, sticky="nsew", padx=(0, 12), pady=(0, 7))
            parent.columnconfigure(column, weight=1)
            ttk.Label(box, text=label).pack(anchor="w")
            if values is None:
                widget = ttk.Entry(box, textvariable=variable, width=width)
                state = "normal"
            else:
                widget = ttk.Combobox(box, textvariable=variable, values=values, state="readonly", width=width)
                state = "readonly"
            widget.pack(fill="x", pady=(3, 2))
            help_label = ttk.Label(box, text=hint, wraplength=360 if width > 20 else 175)
            help_label.pack(anchor="w", fill="x")
            box.bind("<Configure>", lambda event: help_label.configure(wraplength=max(1, event.width)))
            self.controls.append((widget, state))
            return widget

        inputs = section(self.setup_tab, "1  Input sequences")
        toolbar = ttk.Frame(inputs)
        toolbar.pack(fill="x", pady=(0, 7))
        button(toolbar, "Add FASTA files...", self.choose_inputs)
        button(toolbar, "Remove selected", self.remove_inputs)
        button(toolbar, "Clear", self.clear_inputs)
        button(toolbar, "Use included example", self.use_example)
        self.selected = tk.StringVar(value="No files selected. Add unaligned HA protein FASTA files, or try the example.")
        table = ttk.Frame(inputs)
        table.pack(fill="x")
        self.file_table = ttk.Treeview(table, columns=("name", "folder"), show="headings", height=3,
                                       selectmode="extended")
        self.file_table.heading("name", text="Dataset")
        self.file_table.heading("folder", text="Folder")
        self.file_table.column("name", width=230, minwidth=140)
        self.file_table.column("folder", width=560, minwidth=180)
        scroll = ttk.Scrollbar(table, orient="vertical", command=self.file_table.yview)
        self.file_table.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.file_table.pack(side="left", fill="x", expand=True)
        ttk.Label(inputs, textvariable=self.selected, wraplength=760).pack(anchor="w", pady=(5, 0))

        results = section(self.setup_tab, "2  Results")
        self.outdir = tk.StringVar(value=str(Path.home() / "FluTrees_results"))
        self.run_id = tk.StringVar(value="")
        field(results, 0, 0, "Results folder", self.outdir, "Each input receives its own dataset folder.", width=42)
        field(results, 0, 1, "Run ID", self.run_id, "Blank = automatic timestamp. Existing runs are never overwritten.", width=28)
        browse = ttk.Button(results, text="Browse...", command=self.choose_output)
        browse.grid(row=0, column=2, padx=(0, 4))
        self.controls.append((browse, "normal"))

        settings = section(self.setup_tab, "3  Analysis settings")
        self.start = tk.StringVar(value=str(defaults.start_residue))
        self.end = tk.StringVar(value=str(defaults.end_residue))
        self.tree_mode = tk.StringVar(value=defaults.tree_mode)
        self.reference_id = tk.StringVar(value="")
        field(settings, 0, 0, "First residue", self.start, "1-based; inclusive.")
        field(settings, 0, 1, "Last residue", self.end, "Inclusive; default 284.")
        field(settings, 0, 2, "Tree view", self.tree_mode, "All: three views, one alignment.",
              values=("frequency", "balanced", "diversity", "all"))
        field(settings, 0, 3, "Reference ID", self.reference_id, "Blank = modal sequence.")
        for column, (label, name, hint) in enumerate((
            ("Max depth", "max_depth", "0-20; 0 = root only."),
            ("Min split", "min_split", "Records per child; at least 1."),
            ("Min freq", "min_freq", "0-0.5; 0.05 = 5%."),
            ("Prune cutoff", "prune_cutoff", "Simplified view only; at least 1."),
        )):
            variable = tk.StringVar(value=str(getattr(defaults, name)))
            setattr(self, name, variable)
            field(settings, 1, column, label, variable, hint)
        ttk.Label(settings, text="Each child must meet Min split and Min freq of its parent. Full-tree assignments are preserved by pruning.",
                  wraplength=760).grid(row=2, column=0, columnspan=4, sticky="w")

        aligner = section(advanced, "Alignment and computing")
        self.mafft = tk.StringVar(value=defaults.mafft)
        self.threads = tk.StringVar(value="")
        self.alignment = tk.StringVar(value="Mode default")
        field(aligner, 0, 0, "MAFFT executable", self.mafft,
              "Executable name on PATH, or the full executable path.", width=42)
        field(aligner, 0, 1, "CPU threads", self.threads,
              "Blank = SLURM_CPUS_PER_TASK when valid, otherwise 8.", width=28)
        field(aligner, 1, 0, "Alignment profile", self.alignment,
              "Mode default preserves the existing behavior for each tree view.",
              values=tuple(ALIGNMENT_PROFILES), width=42)
        ttk.Label(advanced, text="Mode default uses legacy alignment for frequency-only runs and reproducible alignment for balanced, diversity, or all.\n\n"
                  "Reproducible disables multithreaded iterative refinement. Legacy keeps the historical MAFFT flags. "
                  "For comparisons across separate runs, select the same profile and thread count.\n\n"
                  "Use unaligned amino-acid sequences with consistent numbering. The residue window is extracted before alignment. "
                  "An explicit Reference ID must match exactly one original FASTA ID in each input.\n\n"
                  "All parameters and the effective MAFFT command are recorded in the results. These are mutation decision trees, not phylogenetic reconstructions.",
                  wraplength=740, justify="left").pack(anchor="w", pady=(4, 12))

        layout = section(self.viewer_tab, "Tree layout - presentation only")
        for column, (name, label) in enumerate((
            ("figure_width", "Width (in; 6-30)"),
            ("figure_height", "Height (in; 4-24)"),
            ("level_spacing", "Level gap (0.25-4x)"),
            ("node_spacing", "Node gap (0.25-4x)"),
            ("line_width", "Line width (pt; 0.25-5)"),
        )):
            variable = tk.StringVar(value=str(getattr(defaults, name)))
            setattr(self, name, variable)
            layout.columnconfigure(column, weight=1)
            ttk.Label(layout, text=label).grid(row=0, column=column, sticky="w", padx=(0, 8))
            entry = ttk.Entry(layout, textvariable=variable, width=9)
            entry.grid(row=1, column=column, sticky="ew", padx=(0, 8), pady=(3, 0))
            self.controls.append((entry, "normal"))
        self.viewer = TreeViewer(self.viewer_tab, tk, ttk, dialogs, self.figure_style, lambda: self.running)

        ttk.Label(self.log_tab, text="Progress and commands for this session. Runs and diagnostics remain available in the results folder.",
                  wraplength=740).pack(anchor="w", pady=(0, 8))
        log_frame = ttk.Frame(self.log_tab)
        log_frame.pack(fill="both", expand=True)
        self.log = tk.Text(log_frame, wrap="word", state="disabled", font="TkFixedFont",
                           height=14, borderwidth=0, padx=10, pady=10)
        log_scroll = ttk.Scrollbar(log_frame, orient="vertical", command=self.log.yview)
        self.log.configure(yscrollcommand=log_scroll.set)
        log_scroll.pack(side="right", fill="y")
        self.log.pack(fill="both", expand=True)

        footer = ttk.Frame(shell)
        footer.pack(side="bottom", fill="x", pady=(12, 0), before=self.tabs)
        actions = ttk.Frame(footer)
        actions.pack(fill="x")
        self.analyze_button = ttk.Button(actions, text="Analyze sequences", style="Action.TButton", command=self.analyze)
        self.analyze_button.pack(side="left", padx=(0, 8))
        self.copy_button = button(actions, "Copy CLI command", self.copy_command)
        self.open_button = ttk.Button(actions, text="Open results", command=self.open_results, state="disabled")
        self.open_button.pack(side="left", padx=(4, 0))
        self.progress = ttk.Progressbar(footer, mode="indeterminate")
        self.progress.pack(fill="x", pady=(8, 6))
        self.status = tk.StringVar(value="Ready. Choose files, check settings, then analyze. Alignment options are in Advanced.")
        ttk.Label(footer, textvariable=self.status, wraplength=800).pack(anchor="w")
        self.poll_token = root.after(100, self.poll)

    def scroll_settings(self, event):
        if self.tabs.select() != str(self.analysis_tab):
            return
        if event.num in (4, 5):
            units = -1 if event.num == 4 else 1
        elif event.delta:
            units = -1 if event.delta > 0 else 1
        else:
            return
        self.canvas.yview_scroll(units, "units")

    def refresh_inputs(self):
        for item in self.file_table.get_children():
            self.file_table.delete(item)
        for i, path in enumerate(self.inputs):
            self.file_table.insert("", "end", iid=str(i), values=(path.name, str(path.parent)))
        self.selected.set(f"{len(self.inputs)} file(s) selected. Each file is analyzed independently.")

    def choose_inputs(self):
        if self.running:
            return
        paths = self.dialogs[0].askopenfilenames(
            title="Select protein FASTA files",
            filetypes=[("FASTA files", "*.fasta *.fa *.faa *.fas"), ("All files", "*")],
        )
        for value in paths:
            path = Path(value).resolve()
            if path not in self.inputs:
                self.inputs.append(path)
        self.refresh_inputs()

    def remove_inputs(self):
        if self.running:
            return
        selected = set(self.file_table.selection())
        self.inputs = [path for i, path in enumerate(self.inputs) if str(i) not in selected]
        self.refresh_inputs()

    def clear_inputs(self):
        if self.running:
            return
        self.inputs = []
        self.refresh_inputs()

    def use_example(self):
        if self.running:
            return
        from .cli import demo_path

        self.inputs = [demo_path()]
        self.start.set("84")
        self.end.set("284")
        self.refresh_inputs()
        self.selected.set("Synthetic example: 48 protein records in four groups. Current tree settings are retained.")

    def choose_output(self):
        if self.running:
            return
        path = self.dialogs[0].askdirectory(title="Choose where to save results")
        if path:
            self.outdir.set(path)

    def collect_request(self):
        if not self.inputs:
            raise ValueError("Choose at least one FASTA file, or use the included example.")
        if not self.outdir.get().strip():
            raise ValueError("Choose a results folder.")
        mafft = self.mafft.get().strip()
        if not mafft:
            raise ValueError("Enter the MAFFT executable name or full path.")
        profile = self.alignment.get()
        if profile not in ALIGNMENT_PROFILES:
            raise ValueError("Choose Mode default, Reproducible, or Legacy for the alignment profile.")
        layout = self.figure_style()
        cfg = RunConfig(
            start_residue=parse_number(self.start.get(), "First residue"),
            end_residue=parse_number(self.end.get(), "Last residue"),
            max_depth=parse_number(self.max_depth.get(), "Max depth"),
            min_split=parse_number(self.min_split.get(), "Min split"),
            min_freq=parse_number(self.min_freq.get(), "Min freq", float),
            prune_cutoff=parse_number(self.prune_cutoff.get(), "Prune cutoff"),
            threads=parse_number(self.threads.get(), "Threads") if self.threads.get().strip() else None,
            mafft=mafft,
            tree_mode=self.tree_mode.get(),
            reference_id=self.reference_id.get().strip() or None,
            reproducible=ALIGNMENT_PROFILES[profile],
            **{name: getattr(layout, name) for name in FIGURE_FIELDS},
        )
        run_id = self.run_id.get().strip() or cfg.default_run_id()
        validate_run_id(run_id)
        outdir = Path(self.outdir.get()).expanduser().resolve()
        if (outdir / run_id).exists():
            raise ValueError("That run folder already exists. Choose a new Run ID or leave it blank.")
        return cfg, list(self.inputs), outdir, run_id

    def figure_style(self) -> FigureStyle:
        return FigureStyle(**{name: parse_number(getattr(self, name).get(), name.replace("_", " ").title(), float)
                              for name in FIGURE_FIELDS})

    def copy_command(self):
        if self.running:
            return
        try:
            request = self.collect_request()
        except (ValueError, OSError) as error:
            self.dialogs[1].showerror("Check your input", str(error))
            return
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(cli_command(*request))
        except self.tk_error as error:
            self.dialogs[1].showerror("Could not copy command", str(error))
            return
        self.status.set("Command copied (PowerShell on Windows; shell on macOS/Linux). It uses a new run name when Run ID is blank.")

    def append_log(self, message):
        self.log.configure(state="normal")
        self.log.insert("end", message + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def set_running(self, value):
        self.running = value
        for control, state in self.controls:
            control.configure(state="disabled" if value else state)
        self.analyze_button.configure(state="disabled" if value else "normal")
        self.open_button.configure(state="normal" if not value and self.result is not None else "disabled")
        if value:
            self.progress.start(12)
        else:
            self.progress.stop()
        self.viewer.update_controls()

    def analyze(self):
        if self.running:
            return
        try:
            args = self.collect_request()
        except (ValueError, OSError) as error:
            self.dialogs[1].showerror("Check your input", str(error))
            return
        self.result = None
        self.set_running(True)
        self.status.set("Starting analysis... See Run log for progress.")
        self.append_log("\nStarting run: " + args[3])
        self.append_log(cli_command(*args))
        # Tk finalizers must run on the GUI thread, including cycles left by a
        # previously closed window. Never let the worker collect those objects.
        gc.collect()
        try:
            threading.Thread(target=self.worker, args=args, daemon=True).start()
        except (RuntimeError, OSError) as error:
            self.set_running(False)
            self.status.set(f"Could not start analysis: {error}")
            self.append_log(self.status.get())
            self.dialogs[1].showerror("Could not start analysis", str(error))

    def worker(self, cfg, inputs, outdir, run_id):
        from .pipeline import run_many

        try:
            result = run_many(cfg, inputs, outdir, run_id,
                              lambda message: self.events.put(("progress", message)))
            self.events.put(("complete", result))
        except Exception as error:
            self.events.put(("error", str(error)))

    def poll(self):
        while not self.events.empty():
            kind, value = self.events.get_nowait()
            self.append_log(str(value))
            if kind == "progress":
                self.status.set(value)
            else:
                if kind == "complete":
                    self.result = value
                    self.status.set(f"Complete. Click Open results. Files saved in {value}")
                else:
                    self.status.set(f"Analysis could not finish: {value}")
                    self.tabs.select(self.log_tab)
                    self.dialogs[1].showerror("Analysis could not finish", value)
                self.set_running(False)
                if kind == "complete":
                    self.viewer.load_run(value)
        self.poll_token = self.root.after(100, self.poll)

    def open_results(self):
        if self.result is not None:
            if not webbrowser.open((self.result / "START_HERE.html").as_uri()):
                self.dialogs[1].showinfo("Open results", str(self.result / "START_HERE.html"))

    def close(self):
        if self.running:
            self.dialogs[1].showinfo(
                "Analysis is running", "Please wait for this run to finish before closing FluTrees."
            )
        else:
            self.viewer.close()
            self.root.after_cancel(self.poll_token)
            self.root.destroy()


def launch():
    try:
        import tkinter as tk
        from tkinter import ttk, filedialog, messagebox
    except ImportError as error:
        raise SystemExit(
            "The desktop launcher needs Tk. Install Python with Tk support, or use flutrees --demo --open."
        ) from error
    try:
        root = tk.Tk()
    except tk.TclError as error:
        raise SystemExit(
            "No desktop display is available. Use the flutrees command on this machine, then open START_HERE.html on your computer."
        ) from error
    Launcher(root, tk, ttk, (filedialog, messagebox))
    root.mainloop()

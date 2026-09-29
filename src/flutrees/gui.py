"""Desktop file selection and progress display for the analysis pipeline."""

import queue
import threading
import webbrowser
from pathlib import Path

from .config import RunConfig


class Launcher:
    def __init__(self, root, tk, ttk, dialogs):
        self.root = root
        self.dialogs = dialogs
        self.inputs = []
        self.result = None
        self.running = False
        self.events = queue.Queue()
        root.title("FluTrees")
        root.geometry("800x600")
        root.minsize(760, 580)
        root.protocol("WM_DELETE_WINDOW", self.close)
        frame = ttk.Frame(root, padding=24)
        frame.pack(fill="both", expand=True)
        ttk.Label(
            frame,
            text="Influenza HA mutation trees",
            font=("TkDefaultFont", 17, "bold"),
        ).pack(anchor="w")
        ttk.Label(
            frame, text="1. Choose FASTA files   2. Check the residue window   3. Analyze"
        ).pack(anchor="w", pady=8)
        self.selected = tk.StringVar(value="No files selected. Use the example to try FluTrees.")
        ttk.Button(frame, text="Choose FASTA files", command=self.choose_inputs).pack(anchor="w")
        ttk.Button(frame, text="Use included example", command=self.use_example).pack(
            anchor="w", pady=4
        )
        ttk.Label(frame, textvariable=self.selected, wraplength=690).pack(anchor="w")
        self.outdir = tk.StringVar(value=str(Path.home() / "FluTrees_results"))
        ttk.Button(frame, text="Choose results folder", command=self.choose_output).pack(
            anchor="w", pady=(12, 4)
        )
        ttk.Entry(frame, textvariable=self.outdir, width=85).pack(anchor="w", fill="x")
        settings = ttk.Frame(frame)
        settings.pack(anchor="w", pady=12)
        self.start = tk.StringVar(value="84")
        self.end = tk.StringVar(value="284")
        for label, variable in (("First residue", self.start), ("Last residue", self.end)):
            ttk.Label(settings, text=label).pack(side="left", padx=5)
            ttk.Entry(settings, textvariable=variable, width=7).pack(side="left")
        ttk.Label(
            frame,
            text="Use amino-acid HA sequences with consistent numbering. The default window is 84–284 inclusive.",
            wraplength=690,
        ).pack(anchor="w")
        self.analyze_button = ttk.Button(frame, text="Analyze sequences", command=self.analyze)
        self.analyze_button.pack(anchor="w", pady=12)
        self.status = tk.StringVar(
            value="Ready. Results include visual PDF trees, editable figures, and an Excel workbook."
        )
        ttk.Label(frame, textvariable=self.status, wraplength=690).pack(anchor="w")
        self.open_button = ttk.Button(
            frame, text="Open results", command=self.open_results, state="disabled"
        )
        self.open_button.pack(anchor="w", pady=12)
        root.after(100, self.poll)

    def choose_inputs(self):
        paths = self.dialogs[0].askopenfilenames(
            title="Select protein FASTA files",
            filetypes=[("FASTA files", "*.fasta *.fa *.faa *.fas"), ("All files", "*")],
        )
        if paths:
            self.inputs = [Path(p) for p in paths]
            self.selected.set(
                f"{len(paths)} file(s) selected. Preview: "
                + ", ".join(p.name[:60] for p in self.inputs[:3])
            )

    def use_example(self):
        from .cli import demo_path

        self.inputs = [demo_path()]
        self.start.set("84")
        self.end.set("284")
        self.selected.set("Synthetic example: 48 protein records in four groups.")

    def choose_output(self):
        path = self.dialogs[0].askdirectory(title="Choose where to save results")
        if path:
            self.outdir.set(path)

    def analyze(self):
        if self.running:
            return
        try:
            if not self.inputs:
                raise ValueError("Choose at least one FASTA file, or use the included example.")
            if not self.outdir.get().strip():
                raise ValueError("Choose a results folder.")
            cfg = RunConfig(start_residue=int(self.start.get()), end_residue=int(self.end.get()))
        except ValueError as error:
            self.dialogs[1].showerror("Check your input", str(error))
            return
        self.running = True
        self.analyze_button.configure(state="disabled")
        self.open_button.configure(state="disabled")
        self.status.set("Starting analysis...")
        args = (cfg, list(self.inputs), Path(self.outdir.get()).expanduser().resolve())
        threading.Thread(target=self.worker, args=args, daemon=True).start()

    def worker(self, cfg, inputs, outdir):
        from .pipeline import run_many

        try:
            result = run_many(
                cfg,
                inputs,
                outdir,
                cfg.default_run_id(),
                lambda s: self.events.put(("progress", s)),
            )
            self.events.put(("complete", result))
        except Exception as error:
            self.events.put(("error", str(error)))

    def poll(self):
        while not self.events.empty():
            kind, value = self.events.get_nowait()
            if kind == "progress":
                self.status.set(value)
            else:
                self.running = False
                self.analyze_button.configure(state="normal")
                if kind == "complete":
                    self.result = value
                    self.status.set(f"Complete. Click Open results. Files saved in {value}")
                    self.open_button.configure(state="normal")
                else:
                    self.status.set(f"Analysis could not finish: {value}")
                    self.dialogs[1].showerror("Analysis could not finish", value)
        self.root.after(100, self.poll)

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

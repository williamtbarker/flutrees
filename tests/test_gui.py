import builtins
import json
import shlex
import os
import sys
import time
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from flutrees.gui import Launcher, launch, cli_command
from flutrees.config import RunConfig
from dataclasses import asdict
from typer.testing import CliRunner
from flutrees.cli import app


class Variable:
    def __init__(self, value=""):
        self.value = value

    def set(self, value):
        self.value = value

    def get(self):
        return self.value


@pytest.fixture
def view(request):
    root = Mock()
    root.winfo_screenheight.return_value = 1024
    tk = SimpleNamespace(StringVar=Variable, BooleanVar=Variable, Text=Mock(side_effect=lambda *a, **k: Mock()),
                         Canvas=Mock(side_effect=lambda *a, **k: Mock()), TclError=RuntimeError)

    def widget(*args, **kwargs):
        result = Mock()
        result.get_children.return_value = ()
        result.selection.return_value = ()
        return result

    ttk = SimpleNamespace(
        **{
            name: Mock(side_effect=widget)
            for name in ["Frame", "Label", "Button", "Entry", "Combobox", "Style", "LabelFrame",
                         "Notebook", "Treeview", "Scrollbar", "Progressbar", "Checkbutton"]
        }
    )
    theme = getattr(request, "param", "aqua")

    def theme_use(value=None):
        nonlocal theme
        if value is not None:
            theme = value
        return theme

    style = Mock()
    style.theme_use.side_effect = theme_use
    ttk.Style = Mock(return_value=style)
    root.test_style = style
    dialogs = (Mock(), Mock())
    return Launcher(root, tk, ttk, dialogs)


@pytest.mark.parametrize("view", ["default", "classic", "clam", "aqua"], indirect=True)
def test_desktop_preserves_native_theme_or_styles_fallback(view):
    style = view.root.test_style
    if style.theme_use() == "clam":
        style.configure.assert_any_call("TEntry", fieldbackground="#ffffff", padding=3)
        style.map.assert_any_call("TNotebook.Tab", background=[("selected", "#ffffff")])
    else:
        assert style.theme_use() == "aqua"
        assert all(call.args[0] != "TEntry" for call in style.configure.call_args_list)


def test_selection_and_input_validation(view, tmp_path, monkeypatch):
    view.dialogs[0].askopenfilenames.return_value = ()
    view.choose_inputs()
    assert not view.inputs
    view.dialogs[0].askopenfilenames.return_value = [str(tmp_path / "a.fa")]
    view.choose_inputs()
    assert view.inputs == [tmp_path / "a.fa"]
    view.dialogs[0].askdirectory.return_value = ""
    before = view.outdir.get()
    view.choose_output()
    assert view.outdir.get() == before
    view.dialogs[0].askdirectory.return_value = str(tmp_path)
    view.choose_output()
    assert view.outdir.get() == str(tmp_path)
    view.inputs = []
    view.analyze()
    assert view.dialogs[1].showerror.call_count == 1
    view.use_example()
    assert len(view.inputs) == 1 and view.start.get() == "84"
    view.outdir.set("")
    view.analyze()
    assert view.dialogs[1].showerror.call_count == 2
    view.outdir.set(str(tmp_path))
    view.start.set("bad")
    view.analyze()
    assert view.dialogs[1].showerror.call_count == 3
    view.start.set("1")
    view.end.set("6")
    thread = Mock()
    monkeypatch.setattr("flutrees.gui.threading.Thread", thread)
    view.analyze()
    thread.return_value.start.assert_called_once()
    assert view.running
    view.analyze()
    thread.return_value.start.assert_called_once()
    view.close()
    view.dialogs[1].showinfo.assert_called_once()


def test_worker_poll_and_open(view, tmp_path, monkeypatch):
    run = Mock(return_value=tmp_path)

    def good(*args):
        args[-1]("Aligning")
        return tmp_path

    run.side_effect = good
    monkeypatch.setattr("flutrees.pipeline.run_many", run)
    view.running = True
    view.worker(RunConfig(), [], tmp_path, "chosen_run")
    assert run.call_args.args[3] == "chosen_run"
    view.poll()
    assert not view.running and view.result == tmp_path
    assert "Complete" in view.status.get()
    browser = Mock(return_value=True)
    monkeypatch.setattr("flutrees.gui.webbrowser.open", browser)
    view.open_results()
    browser.assert_called_once()
    browser.return_value = False
    view.open_results()
    view.dialogs[1].showinfo.assert_called_once()
    view.result = None
    view.open_results()
    assert browser.call_count == 2
    run.side_effect = ValueError("Failed alignment")
    view.worker(RunConfig(), [], tmp_path, "chosen_run")
    view.poll()
    assert "Failed alignment" in view.status.get()
    view.dialogs[1].showerror.assert_called_once()
    view.poll()
    view.close()
    view.root.destroy.assert_called_once()


def test_launch_errors_and_success(monkeypatch):
    original = builtins.__import__

    def missing(name, *args, **kwargs):
        if name == "tkinter":
            raise ImportError("missing")
        return original(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", missing)
    with pytest.raises(SystemExit, match="needs Tk"):
        launch()
    monkeypatch.setattr(builtins, "__import__", original)

    class DisplayError(Exception):
        pass

    tk = SimpleNamespace(
        Tk=Mock(side_effect=DisplayError("no display")),
        TclError=DisplayError,
        ttk=Mock(),
        filedialog=Mock(),
        messagebox=Mock(),
    )
    monkeypatch.setitem(sys.modules, "tkinter", tk)
    with pytest.raises(SystemExit, match="No desktop"):
        launch()
    root = Mock()
    tk.Tk = Mock(return_value=root)
    gui = Mock()
    monkeypatch.setattr("flutrees.gui.Launcher", gui)
    launch()
    root.mainloop.assert_called_once()
    gui.assert_called_once()


@pytest.mark.parametrize("mode", ["frequency", "balanced", "diversity", "all"])
@pytest.mark.parametrize("profile, override, flag", [
    ("Mode default", None, []),
    ("Reproducible", True, ["--reproducible"]),
    ("Legacy", False, ["--legacy-alignment"]),
])
def test_all_settings_match_cli_and_are_captured_before_thread(
    view, tmp_path, monkeypatch, mode, profile, override, flag
):
    view.use_example()
    view.outdir.set(str(tmp_path))
    settings = dict(start="85", end="280", max_depth="3", min_split="2", min_freq="0.1",
                    prune_cutoff="4", threads="2", mafft="/custom/mafft", run_id="customer_run",
                    reference_id="reference", tree_mode=mode, alignment=profile)
    for name, value in settings.items():
        getattr(view, name).set(value)
    thread = Mock()
    monkeypatch.setattr("flutrees.gui.threading.Thread", thread)
    view.analyze()
    view.dialogs[1].showerror.assert_not_called()
    cfg, inputs, outdir, run_id = thread.call_args.kwargs["args"]
    assert cfg == RunConfig("/custom/mafft", 2, 85, 280, 3, 2, 0.1, 4, mode, "reference", override)
    assert outdir == tmp_path and run_id == "customer_run"
    assert inputs == view.inputs and inputs is not view.inputs
    run = Mock(return_value=tmp_path)
    monkeypatch.setattr("flutrees.pipeline.run_many", run)
    args = ["--demo", "-o", str(tmp_path), "--run-id", run_id, "--tree-mode", mode,
            "--reference-id", "reference", "--mafft", "/custom/mafft", "--threads", "2",
            "--start", "85", "--end", "280", "--max-depth", "3", "--min-split", "2",
            "--min-freq", "0.1", "--prune-cutoff", "4", *flag]
    result = CliRunner().invoke(app, args)
    assert result.exit_code == 0, result.output
    assert run.call_args.args[:4] == (cfg, inputs, outdir, run_id)
    # Later edits must never leak into the queued worker's run.
    view.min_freq.set("0.5")
    view.run_id.set("later")
    view.worker(cfg, inputs, outdir, run_id)
    assert run.call_args.args[:4] == (cfg, inputs, outdir, "customer_run")


def test_desktop_defaults_and_blank_optional_fields(view, tmp_path, monkeypatch):
    view.use_example()
    view.outdir.set(str(tmp_path))
    view.threads.set("  ")
    view.run_id.set("  ")
    view.reference_id.set("  ")
    monkeypatch.setenv("SLURM_JOB_ID", "123")
    thread = Mock()
    monkeypatch.setattr("flutrees.gui.threading.Thread", thread)
    view.analyze()
    cfg, inputs, outdir, run_id = thread.call_args.kwargs["args"]
    assert asdict(cfg) == asdict(RunConfig())
    assert run_id.startswith("run")  # Preserve the desktop's timestamp default.


@pytest.mark.parametrize("field, value, message", [
    ("start", "bad", "First residue must be a whole number"),
    ("end", "3.5", "Last residue must be a whole number"),
    ("start", "0", "Residue window"),
    ("end", "83", "Residue window"),
    ("max_depth", "", "Max depth must be a whole number"),
    ("max_depth", "21", "Maximum tree depth"),
    ("min_split", "1.5", "Min split must be a whole number"),
    ("min_split", "0", "Minimum split"),
    ("min_freq", "5%", "Min freq must be a number"),
    ("min_freq", "5", "Minimum frequency"),
    ("min_freq", "nan", "Minimum frequency"),
    ("min_freq", "inf", "Minimum frequency"),
    ("prune_cutoff", "abc", "Prune cutoff must be a whole number"),
    ("prune_cutoff", "0", "pruning counts"),
    ("threads", "1.5", "Threads must be a whole number"),
    ("threads", "0", "Threads must be at least 1"),
    ("mafft", "  ", "MAFFT executable"),
    ("run_id", "../escape", "Run ID must be a folder name"),
    ("run_id", "a:b", "Run ID must be a folder name"),
    ("run_id", "CON", "Run ID must be a portable folder name"),
    ("run_id", "a b", "Run ID must be a portable folder name"),
])
def test_invalid_settings_do_not_start_or_create_output(view, tmp_path, monkeypatch, field, value, message):
    view.use_example()
    view.outdir.set(str(tmp_path / "not_created"))
    getattr(view, field).set(value)
    thread = Mock()
    monkeypatch.setattr("flutrees.gui.threading.Thread", thread)
    view.analyze()
    assert message in view.dialogs[1].showerror.call_args.args[1]
    thread.assert_not_called()
    assert not view.running and not (tmp_path / "not_created").exists()


def test_existing_run_preserved(view, tmp_path, monkeypatch):
    existing = tmp_path / "customer_run"
    existing.mkdir()
    sentinel = existing / "data.txt"
    sentinel.write_text("retain this")
    view.use_example()
    view.outdir.set(str(tmp_path))
    view.run_id.set("customer_run")
    thread = Mock()
    monkeypatch.setattr("flutrees.gui.threading.Thread", thread)
    view.analyze()
    assert "already exists" in view.dialogs[1].showerror.call_args.args[1]
    thread.assert_not_called()
    assert sentinel.read_text() == "retain this"


def test_file_management_and_running_guards(view, tmp_path):
    first, second = tmp_path / "a.fasta", tmp_path / "b.fasta"
    view.dialogs[0].askopenfilenames.return_value = [str(first), str(second), str(first)]
    view.choose_inputs()
    assert view.inputs == [first, second]
    view.file_table.get_children.return_value = ("0", "1")
    view.file_table.selection.return_value = ("0",)
    view.remove_inputs()
    assert view.inputs == [second]
    view.file_table.delete.assert_any_call("0")
    view.clear_inputs()
    assert not view.inputs
    view.inputs = [first]
    view.running = True
    for method in (view.choose_inputs, view.remove_inputs, view.clear_inputs, view.use_example,
                   view.choose_output, view.copy_command):
        method()
    assert view.inputs == [first]
    view.root.clipboard_append.assert_not_called()


def test_settings_scroll_is_scoped_to_analysis(view):
    event = SimpleNamespace(num=4, delta=0)
    view.tabs.select.return_value = "other"
    view.scroll_settings(event)
    view.canvas.yview_scroll.assert_not_called()
    view.tabs.select.return_value = str(view.analysis_tab)
    for num, delta, direction in [(4, 0, -1), (5, 0, 1), (0, 120, -1), (0, -1, 1)]:
        view.scroll_settings(SimpleNamespace(num=num, delta=delta))
        view.canvas.yview_scroll.assert_called_with(direction, "units")
    view.canvas.yview_scroll.reset_mock()
    view.scroll_settings(SimpleNamespace(num=0, delta=0))
    view.canvas.yview_scroll.assert_not_called()


def test_copy_command_and_control_states(view, tmp_path):
    view.copy_command()
    view.dialogs[1].showerror.assert_called_once()
    view.root.clipboard_append.assert_not_called()
    view.use_example()
    view.outdir.set(str(tmp_path))
    view.run_id.set("copied_run")
    view.copy_command()
    copied = view.root.clipboard_append.call_args.args[0]
    assert "copied_run" in copied and "--min-freq" in copied
    assert not view.running and not list(tmp_path.iterdir())
    view.result = tmp_path
    view.set_running(True)
    view.progress.start.assert_called_once()
    for control, _state in view.controls:
        control.configure.assert_called_with(state="disabled")
    view.set_running(False)
    view.progress.stop.assert_called_once()
    for control, state in view.controls:
        control.configure.assert_called_with(state=state)
    view.open_button.configure.assert_called_with(state="normal")
    view.result = None
    view.set_running(False)
    view.open_button.configure.assert_called_with(state="disabled")


def test_clipboard_thread_start_and_profile_failure_recovery(view, tmp_path, monkeypatch):
    view.use_example()
    view.outdir.set(str(tmp_path))
    view.root.clipboard_append.side_effect = RuntimeError("clipboard unavailable")
    view.copy_command()
    assert "clipboard unavailable" in view.dialogs[1].showerror.call_args.args[1]
    view.alignment.set("corrupt profile")
    view.analyze()
    assert "alignment profile" in view.dialogs[1].showerror.call_args.args[1]
    view.alignment.set("Mode default")
    thread = Mock()
    thread.return_value.start.side_effect = RuntimeError("no thread available")
    monkeypatch.setattr("flutrees.gui.threading.Thread", thread)
    view.analyze()
    assert not view.running and "no thread available" in view.status.get()
    assert not list(tmp_path.iterdir())
    view.analyze_button.configure.assert_called_with(state="normal")
    view.viewer.close()
    assert not view.viewer.is_busy()


def test_gui_layout_flows_into_configuration_and_command(view, tmp_path, monkeypatch):
    view.use_example()
    view.outdir.set(str(tmp_path))
    view.threads.set("1")
    for key, value in dict(figure_width="9", figure_height="12", level_spacing="2",
                           node_spacing="3", line_width="2.5").items():
        getattr(view, key).set(value)
    request = view.collect_request()
    run = Mock(return_value=tmp_path)
    monkeypatch.setattr("flutrees.pipeline.run_many", run)
    result = CliRunner().invoke(app, shlex.split(cli_command(*request, windows=False))[1:])
    assert result.exit_code == 0, result.output
    assert run.call_args.args[0] == request[0]
    assert request[0].figure_width == 9 and request[0].node_spacing == 3


@pytest.fixture
def saved_tree(tmp_path):
    from flutrees.tree_build import to_dict
    from test_layout import branching_tree

    (tmp_path / "status.json").write_text('{"status":"complete"}')
    folder = tmp_path / "dataset/trees/frequency"
    folder.mkdir(parents=True)
    path = folder / "tree_full.json"
    path.write_text(json.dumps(to_dict(branching_tree())))
    (folder / "tree_other.json").write_text("{}")
    return tmp_path, path


def test_viewer_navigation_zoom_export_and_invalid_layout(view, saved_tree, tmp_path, monkeypatch):
    from PIL import ImageTk

    monkeypatch.setattr(ImageTk, "PhotoImage", Mock())
    viewer = view.viewer
    viewer.canvas.winfo_width.return_value = 700
    viewer.canvas.winfo_height.return_value = 400
    root, _ = saved_tree
    assert viewer.load_run(root)
    assert len(viewer.paths) == 1 and len(viewer.pages) > 1
    assert viewer.zoom == 1 and viewer.photo is not None
    assert viewer.page_image.size == (1400, 850)
    assert viewer.image.width < viewer.page_image.width
    viewer.whole_page.set(True)
    viewer.fit_page()
    assert ImageTk.PhotoImage.call_args.args[0].size == (658, 400)
    viewer.whole_page.set(False)
    viewer.fit_page()
    viewer.previous.configure.assert_called_with(state="disabled")
    viewer.change_page(-1)
    assert viewer.page == 0
    viewer.zoom_by(16)
    assert viewer.zoom == 8
    viewer.zoom_by(0.001)
    assert viewer.zoom == 0.25
    viewer.fit_page()
    assert viewer.zoom == 1
    viewer.change_page(1)
    assert viewer.page == 1 and viewer.zoom == 1
    viewer.on_resize(None)
    viewer.on_resize(None)
    viewer.redraw()
    assert viewer.resize_token is None
    viewer.on_resize(None)
    for suffix in (".png", ".svg", ".pdf"):
        target = tmp_path / ("saved" + suffix)
        view.dialogs[0].asksaveasfilename.return_value = str(target)
        viewer.save_page()
        assert target.stat().st_size > 100
        if suffix == ".svg":
            assert "<text" in target.read_text()
    view.dialogs[0].asksaveasfilename.return_value = ""
    viewer.save_page()
    view.dialogs[0].asksaveasfilename.return_value = str(tmp_path / "invalid.txt")
    viewer.save_page()
    assert "PNG, SVG, or PDF" in view.dialogs[1].showerror.call_args.args[1]
    view.figure_width.set("nan")
    viewer.change_page(1)
    assert viewer.figure is None and "Cannot apply layout" in viewer.message.get()
    viewer.save.configure.assert_called_with(state="disabled")
    viewer.save_page()
    viewer.redraw()
    view.figure_width.set("9")
    viewer.render()
    assert tuple(viewer.figure.get_size_inches()) == (9, 8.5)
    view.dialogs[0].askdirectory.return_value = ""
    viewer.open_run()
    view.dialogs[0].askdirectory.return_value = str(root)
    viewer.open_run()
    assert viewer.figure is not None
    viewer.on_resize(None)
    viewer.close()
    assert viewer.figure is None and viewer.resize_token is None


@pytest.mark.parametrize("metadata", ["[]", '{"status":"running"}', "not json", "[" * 1100 + "]" * 1100, " " * (1024 * 1024 + 1)])
def test_viewer_rejects_incomplete_or_corrupt_run(view, tmp_path, metadata):
    (tmp_path / "status.json").write_text(metadata)
    assert not view.viewer.load_run(tmp_path)
    assert "Cannot open trees" in view.viewer.message.get()


def test_viewer_rejects_missing_large_or_invalid_trees_and_busy_work(view, saved_tree, monkeypatch):
    from pathlib import Path

    root, tree = saved_tree
    viewer = view.viewer
    view.running = True
    assert not viewer.load_run(root)
    for method in (viewer.open_run, viewer.select_tree, viewer.render, viewer.save_page,
                   viewer.fit_page, lambda: viewer.zoom_by(2), lambda: viewer.change_page(1)):
        method()
    assert viewer.zoom == 1 and not viewer.paths
    view.running = False
    viewer.render()
    # Reject oversized JSON before reading or allocating its nodes.
    with tree.open("r+b") as file:
        file.truncate(64 * 1024 * 1024 + 1)
    assert not viewer.load_run(root)
    assert "64 MiB" in viewer.message.get()
    tree.write_text("[" * 1100 + "]" * 1100)
    assert not viewer.load_run(root)
    assert "Cannot display tree" in viewer.message.get()
    tree.write_text("{}")
    assert not viewer.load_run(root)
    viewer.choice.set("missing")
    viewer.select_tree()
    assert not viewer.pages
    tree.unlink()
    assert not viewer.load_run(root)
    assert "No tree JSON" in viewer.message.get()
    view.dialogs[0].askdirectory.return_value = str(root)
    viewer.open_run()
    view.dialogs[1].showerror.assert_called_once()
    original_read = Path.read_text
    monkeypatch.setattr(Path, "read_text", lambda path, **kw: original_read(path, **kw) if path.name != "status.json" else (_ for _ in ()).throw(OSError("unreadable")))
    assert not viewer.load_run(root)
    assert "unreadable" in viewer.message.get()


@pytest.mark.parametrize("profile", [None, True, False])
def test_cli_command_round_trip_and_shell_quoting(tmp_path, monkeypatch, profile):
    from pathlib import Path

    first = tmp_path / "HA sample's $(echo unsafe).fasta"
    second = tmp_path / "second.fasta"
    for path in (first, second):
        path.write_text(">a\nACDE\n")
    cfg = RunConfig(threads=2, reproducible=profile, reference_id="id'with;$characters")
    command = cli_command(cfg, [first, second], tmp_path / "results", "quoted", windows=False)
    run = Mock(return_value=tmp_path)
    monkeypatch.setattr("flutrees.pipeline.run_many", run)
    result = CliRunner().invoke(app, shlex.split(command)[1:])
    assert result.exit_code == 0, result.output
    assert run.call_args.args[:4] == (cfg, [first, second], Path(tmp_path / "results"), "quoted")
    powershell = cli_command(cfg, [first], tmp_path, "quoted", windows=True)
    assert powershell.startswith("& 'flutrees' '-i' '")
    assert "sample''s $(echo unsafe).fasta'" in powershell
    assert "'id''with;$characters'" in powershell


@pytest.mark.gui
@pytest.mark.skipif(
    sys.platform not in {"darwin", "win32"} and not os.environ.get("DISPLAY"),
    reason="Desktop integration requires a graphical session",
)
@pytest.mark.parametrize("custom", [False, True])
def test_real_desktop_runs_example(tmp_path, monkeypatch, custom):
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox

    errors = []
    monkeypatch.setattr(messagebox, "showerror", lambda title, message: errors.append(message))
    root = tk.Tk()
    gui = Launcher(root, tk, ttk, (filedialog, messagebox))
    root.update_idletasks()
    assert (
        gui.open_button.winfo_rooty() + gui.open_button.winfo_height()
        <= root.winfo_rooty() + root.winfo_height()
    )
    root.geometry("860x740")
    root.update()
    gui.canvas.yview_moveto(1.0)
    root.update()
    depth_entry = next(control for control, _state in gui.controls
                       if control.winfo_class() == "TEntry"
                       and str(control.cget("textvariable")) == str(gui.max_depth))
    assert depth_entry.winfo_rooty() >= gui.canvas.winfo_rooty()
    assert depth_entry.winfo_rooty() + depth_entry.winfo_height() <= gui.canvas.winfo_rooty() + gui.canvas.winfo_height()
    for tab in gui.tabs.tabs():
        gui.tabs.select(tab)
        root.update()
        assert gui.analyze_button.winfo_viewable()
        footer = gui.progress.master
        assert footer.winfo_rooty() + footer.winfo_height() <= root.winfo_rooty() + root.winfo_height()
    gui.tabs.select(gui.analysis_tab)
    gui.use_example()
    gui.outdir.set(str(tmp_path))
    if custom:
        for name, value in dict(max_depth="1", min_split="2", min_freq="0.25", prune_cutoff="20",
                                run_id="desktop_custom", threads="1", tree_mode="all",
                                alignment="Legacy").items():
            getattr(gui, name).set(value)
    monkeypatch.setattr("flutrees.gui.webbrowser.open", lambda url: True)
    gui.analyze()
    deadline = time.monotonic() + 60
    while gui.running and time.monotonic() < deadline:
        root.update()
        time.sleep(0.02)
    assert not gui.running and gui.result is not None, errors
    assert (gui.result / "START_HERE.html").exists()
    summary = json.loads((gui.result / "example/summary.json").read_text())
    if custom:
        assert gui.result.name == "desktop_custom"
        assert summary["config"]["max_depth"] == 1
        assert summary["config"]["min_split"] == 2
        assert summary["config"]["min_freq"] == 0.25
        assert summary["config"]["prune_cutoff"] == 20
        assert summary["resolved_threads"] == 1
        assert summary["alignment_mode"] == "legacy"
        # Compare real GUI outputs with a separate real CLI run of the same settings.
        result = CliRunner().invoke(app, ["--demo", "-o", str(tmp_path), "--run-id", "cli_custom",
                                         "--max-depth", "1", "--min-split", "2", "--min-freq", "0.25",
                                         "--prune-cutoff", "20", "--threads", "1", "--tree-mode", "all",
                                         "--legacy-alignment"])
        assert result.exit_code == 0, result.output
        for mode in ("frequency", "balanced", "diversity"):
            for artifact in ("tree_full.json", "tree_pruned.json", "group_assignments.tsv"):
                relative = f"example/trees/{mode}/{artifact}"
                assert (gui.result / relative).read_bytes() == (tmp_path / "cli_custom" / relative).read_bytes()
    else:
        assert summary["config"] == asdict(RunConfig())
    gui.tabs.select(gui.viewer_tab)
    deadline = time.monotonic() + 0.3
    while time.monotonic() < deadline:
        root.update()
        time.sleep(0.01)
    assert gui.viewer.figure is not None and gui.viewer.photo is not None
    assert gui.viewer.photo.width() <= gui.viewer.canvas.winfo_width()
    assert gui.viewer.photo.height() <= gui.viewer.canvas.winfo_height()
    gui.viewer.zoom_by(2)
    assert gui.viewer.zoom == 2
    gui.figure_width.set("6")
    gui.figure_height.set("12")
    gui.node_spacing.set("4")
    gui.viewer.render()
    deadline = time.monotonic() + 0.3
    while time.monotonic() < deadline:
        root.update()
        time.sleep(0.01)
    assert gui.viewer.zoom == 1
    assert tuple(gui.viewer.figure.get_size_inches()) == (6, 12)
    assert gui.viewer.photo.width() <= gui.viewer.canvas.winfo_width()
    assert gui.viewer.photo.height() <= gui.viewer.canvas.winfo_height()
    gui.viewer.whole_page.set(True)
    gui.viewer.fit_page()
    root.update()
    assert gui.viewer.page_image.size == (600, 1200)
    assert abs(gui.viewer.photo.width() / gui.viewer.photo.height() - 0.5) < 0.01
    gui.open_results()
    gui.close()


def test_cli_import_does_not_require_tk():
    import subprocess

    code = '''
import importlib.abc
import sys
class NoTk(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path, target=None):
        if fullname == "tkinter" or fullname.startswith("tkinter."):
            raise ModuleNotFoundError("Tk intentionally unavailable")
sys.meta_path.insert(0, NoTk())
from flutrees.cli import app
from flutrees.gui import launch
from typer.testing import CliRunner
assert CliRunner().invoke(app, ["--version"]).exit_code == 0
try:
    launch()
except SystemExit as error:
    assert "needs Tk" in str(error)
else:
    raise AssertionError("Headless launch should report missing Tk")
'''
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr

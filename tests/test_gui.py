import builtins
import os
import sys
import time
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from flutrees.gui import Launcher, launch
from flutrees.config import RunConfig


class Variable:
    def __init__(self, value=""):
        self.value = value

    def set(self, value):
        self.value = value

    def get(self):
        return self.value


@pytest.fixture
def view():
    root = Mock()
    tk = SimpleNamespace(StringVar=Variable)
    ttk = SimpleNamespace(
        **{
            name: Mock(side_effect=lambda *a, **k: Mock())
            for name in ["Frame", "Label", "Button", "Entry", "Combobox"]
        }
    )
    dialogs = (Mock(), Mock())
    return Launcher(root, tk, ttk, dialogs)


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
    view.worker(RunConfig(), [], tmp_path)
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
    view.worker(RunConfig(), [], tmp_path)
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


@pytest.mark.gui
@pytest.mark.skipif(not os.environ.get("DISPLAY"), reason="Desktop integration requires a display")
def test_real_desktop_runs_example(tmp_path, monkeypatch):
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
    gui.use_example()
    gui.outdir.set(str(tmp_path))
    monkeypatch.setattr("flutrees.gui.webbrowser.open", lambda url: True)
    gui.analyze()
    deadline = time.monotonic() + 60
    while gui.running and time.monotonic() < deadline:
        root.update()
        time.sleep(0.02)
    assert not gui.running and gui.result is not None, errors
    assert (gui.result / "START_HERE.html").exists()
    gui.open_results()
    gui.close()

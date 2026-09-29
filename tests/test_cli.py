import runpy
from unittest.mock import Mock
from typer.testing import CliRunner
from flutrees.cli import app, demo_path

runner = CliRunner()


def test_version_help_no_inputs_and_modes(monkeypatch, fasta):
    assert "0.2.2" in runner.invoke(app, ["--version"]).stdout
    assert runner.invoke(app, ["--help"]).exit_code == 0
    result = runner.invoke(app, [])
    assert result.exit_code == 2 and "--gui" in result.stdout
    assert runner.invoke(app, ["--demo", "-i", str(fasta)]).exit_code == 2
    launch = Mock()
    monkeypatch.setattr("flutrees.gui.launch", launch)
    assert runner.invoke(app, ["--gui"]).exit_code == 0
    launch.assert_called_once()
    assert demo_path().is_file()


def test_cli_paths_errors_and_browser(monkeypatch, tmp_path, fasta):
    run = Mock(return_value=tmp_path)
    monkeypatch.setattr("flutrees.pipeline.run_many", run)
    browser = Mock(return_value=False)
    monkeypatch.setattr("flutrees.cli.webbrowser.open", browser)
    monkeypatch.setenv("SLURM_JOB_ID", "123")
    result = runner.invoke(app, ["-i", str(fasta), "--open"])
    assert result.exit_code == 0 and "did not open" in result.stdout
    assert run.call_args.args[3] == "job123"
    monkeypatch.delenv("SLURM_JOB_ID")
    browser.return_value = True
    assert runner.invoke(app, ["--demo", "--open"]).exit_code == 0
    assert run.call_args.args[3].startswith("run")
    assert runner.invoke(app, ["-i", str(fasta), "--run-id", "chosen"]).exit_code == 0
    assert run.call_args.args[3] == "chosen"
    assert runner.invoke(app, ["-i", str(fasta), "--start", "0"]).exit_code == 1
    run.side_effect = OSError("Read-only destination")
    result = runner.invoke(app, ["-i", str(fasta)])
    assert result.exit_code == 1 and "Read-only" in result.output


def test_module_entry(monkeypatch):
    call = Mock()
    monkeypatch.setattr("flutrees.cli.app", call)
    runpy.run_module("flutrees.__main__", run_name="__main__")
    call.assert_called_once()
    runpy.run_module("flutrees.__main__", run_name="import_check")
    call.assert_called_once()

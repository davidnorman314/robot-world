import pytest

from robot_world import cli
from robot_world.worlds import WORLDS

pytestmark = pytest.mark.slow


@pytest.fixture
def test_world(goal_ahead_world, monkeypatch):
    monkeypatch.setitem(WORLDS, "test", lambda seed: goal_ahead_world)


@pytest.fixture
def goal_wheel(wheel_builder):
    return wheel_builder("goal_bot", "def run(robot):\n    robot.forward(10.0)\n")


def test_run_prints_outcome_and_exits_zero_on_success(goal_wheel, test_world, capsys):
    code = cli.main(["run", str(goal_wheel), "--world", "test", "--seed", "3"])
    out = capsys.readouterr().out
    assert code == 0
    assert "test seed 3: success in 3.0 s" in out


def test_run_exits_one_when_the_robot_fails(wheel_builder, test_world, capsys):
    wheel = wheel_builder("early_bot", "def run(robot):\n    robot.forward(1.0)\n")
    code = cli.main(["run", str(wheel), "--world", "test"])
    out = capsys.readouterr().out
    assert code == 1
    assert "finished" in out


def test_run_prints_the_traceback_of_a_crashing_program(wheel_builder, test_world, capsys):
    wheel = wheel_builder("bad_bot", "def run(robot):\n    raise RuntimeError('boom')\n")
    code = cli.main(["run", str(wheel), "--world", "test"])
    out = capsys.readouterr().out
    assert code == 1
    assert "RuntimeError: boom" in out


def test_run_several_episodes_prints_a_summary(goal_wheel, test_world, capsys):
    code = cli.main(["run", str(goal_wheel), "--world", "test", "--episodes", "3"])
    out = capsys.readouterr().out
    assert code == 0
    assert out.count("success") == 3
    assert "3 of 3 succeeded" in out


def test_run_with_a_missing_wheel_fails_cleanly(tmp_path, test_world, capsys):
    code = cli.main(["run", str(tmp_path / "missing.whl"), "--world", "test"])
    assert code == 1
    assert "not found" in capsys.readouterr().out


def test_run_with_an_unknown_world_fails_cleanly(goal_wheel, capsys):
    with pytest.raises(SystemExit):
        cli.main(["run", str(goal_wheel), "--world", "moon"])
    assert "moon" in capsys.readouterr().err


def test_check_reports_the_entry_point(goal_wheel, capsys):
    code = cli.main(["check", str(goal_wheel)])
    assert code == 0
    assert "goal_bot:run" in capsys.readouterr().out


def test_check_reports_a_bad_wheel(wheel_builder, capsys):
    wheel = wheel_builder("no_entry", "def run(robot):\n    pass\n", entry_points="")
    code = cli.main(["check", str(wheel)])
    assert code == 1
    assert "robot_world.robots" in capsys.readouterr().out


def test_worlds_lists_the_available_worlds(capsys):
    assert cli.main(["worlds"]) == 0
    assert "river" in capsys.readouterr().out


def test_serve_starts_the_viewer_with_the_given_wheel_and_options(monkeypatch, goal_wheel):
    calls = []
    monkeypatch.setattr(cli, "serve", lambda *args, **kwargs: calls.append((args, kwargs)))
    code = cli.main(
        ["serve", str(goal_wheel), "--world", "river", "--port", "9999", "--no-browser"]
    )
    assert code == 0
    assert calls == [((goal_wheel,), {"world": "river", "port": 9999, "open_browser": False})]


def test_serve_without_a_wheel_opens_the_browser_by_default(monkeypatch):
    calls = []
    monkeypatch.setattr(cli, "serve", lambda *args, **kwargs: calls.append((args, kwargs)))
    assert cli.main(["serve"]) == 0
    assert calls == [((None,), {"world": "river", "port": 8000, "open_browser": True})]

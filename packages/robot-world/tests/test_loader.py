import pytest

from robot_world.loader import ProgramLoadError, load_program

SOURCE = """
    def run(robot):
        robot.forward(10.0)
"""


def test_loads_run_from_the_wheel_entry_point(wheel_builder):
    program = load_program(wheel_builder("good_bot", SOURCE))
    assert callable(program)
    assert program.__name__ == "run"
    assert program.__module__ == "good_bot"


def test_missing_wheel_is_an_error(tmp_path):
    with pytest.raises(ProgramLoadError, match="not found"):
        load_program(tmp_path / "nope.whl")


def test_non_wheel_file_is_an_error(tmp_path):
    path = tmp_path / "robot.zip"
    path.write_bytes(b"")
    with pytest.raises(ProgramLoadError, match=r"\.whl"):
        load_program(path)


def test_wheel_without_entry_point_is_an_error(wheel_builder):
    path = wheel_builder("no_entry", SOURCE, entry_points="")
    with pytest.raises(ProgramLoadError, match="robot_world.robots"):
        load_program(path)


def test_wheel_with_two_entry_points_is_an_error(wheel_builder):
    entry_points = '[robot_world.robots]\na = "two_bots:run"\nb = "two_bots:run"\n'
    path = wheel_builder("two_bots", SOURCE, entry_points=entry_points)
    with pytest.raises(ProgramLoadError, match="one"):
        load_program(path)


def test_entry_point_that_does_not_import_is_an_error(wheel_builder):
    entry_points = '[robot_world.robots]\nx = "missing_module:run"\n'
    path = wheel_builder("bad_ref", SOURCE, entry_points=entry_points)
    with pytest.raises(ProgramLoadError, match="missing_module"):
        load_program(path)

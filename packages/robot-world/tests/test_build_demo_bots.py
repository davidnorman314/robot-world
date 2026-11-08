"""The test bots can be built into wheels for demos in the viewer."""

from robot_world.loader import load_program

from .bots import build


def test_builds_one_wheel_folder_per_bot_named_after_its_world(tmp_path):
    built = build.build_demo_bots(tmp_path)

    assert sorted(path.parent.name for path in built) == [
        "one-bridge",
        "simple-goal",
        "three-bridges",
    ]
    assert all(path.parent.parent == tmp_path for path in built)
    assert all(path.suffix == ".whl" for path in built)


def test_each_wheel_is_a_loadable_robot_program(tmp_path):
    for wheel in build.build_demo_bots(tmp_path):
        program = load_program(wheel)
        assert program.__name__ == "run"
        assert program.__module__ == wheel.name.split("-")[0]

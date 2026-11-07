import pytest
from fastapi.testclient import TestClient

from robot_world.server import build_app, newest_wheel
from robot_world.worlds import WORLDS

pytestmark = pytest.mark.slow


@pytest.fixture
def test_world(goal_ahead_world, monkeypatch):
    monkeypatch.setitem(WORLDS, "test", lambda seed: goal_ahead_world)


@pytest.fixture
def goal_wheel(wheel_builder):
    return wheel_builder(
        "goal_bot", "def run(robot):\n    robot.say('go')\n    robot.forward(10.0)\n"
    )


@pytest.fixture
def client(goal_wheel):
    return TestClient(build_app(default_wheel=goal_wheel))


def test_index_page_is_served(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "<title>" in response.text
    assert "app.js" in response.text


def test_vendored_three_js_is_served(client):
    assert client.get("/static/vendor/three.module.js").status_code == 200
    assert client.get("/static/vendor/OrbitControls.js").status_code == 200


def test_config_reports_worlds_and_default_wheel(client, goal_wheel, test_world):
    data = client.get("/api/config").json()
    assert "river" in data["worlds"]
    assert "test" in data["worlds"]
    assert data["wheel"] == str(goal_wheel)


def test_config_without_default_wheel():
    data = TestClient(build_app()).get("/api/config").json()
    assert data["wheel"] == ""


def test_run_returns_a_playable_episode(client, goal_wheel, test_world):
    response = client.post("/api/run", json={"wheel": str(goal_wheel), "world": "test", "seed": 1})
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["outcome"] == "success"
    assert data["time"] == pytest.approx(3.0)
    assert data["world"]["width"] == 20.0
    assert len(data["frames"]) == 61
    assert data["messages"] == [[0, "go"]]


def test_run_with_a_directory_uses_the_newest_wheel(client, goal_wheel, test_world):
    response = client.post(
        "/api/run", json={"wheel": str(goal_wheel.parent), "world": "test", "seed": 1}
    )
    assert response.status_code == 200, response.text
    assert response.json()["outcome"] == "success"


def test_run_with_a_missing_wheel_is_a_client_error(client, tmp_path, test_world):
    response = client.post(
        "/api/run", json={"wheel": str(tmp_path / "nope.whl"), "world": "test", "seed": 1}
    )
    assert response.status_code == 400
    assert "nope.whl" in response.json()["detail"]


def test_run_with_an_unknown_world_is_a_client_error(client, goal_wheel):
    response = client.post("/api/run", json={"wheel": str(goal_wheel), "world": "moon", "seed": 1})
    assert response.status_code == 400
    assert "moon" in response.json()["detail"]


def test_run_reports_program_errors_as_an_episode(client, wheel_builder, test_world):
    wheel = wheel_builder("bad_bot", "def run(robot):\n    raise RuntimeError('boom')\n")
    data = client.post("/api/run", json={"wheel": str(wheel), "world": "test", "seed": 1}).json()
    assert data["outcome"] == "error"
    assert "RuntimeError: boom" in data["error"]


def test_newest_wheel_picks_the_most_recently_modified(tmp_path):
    import os
    import time

    old = tmp_path / "bot-0.1.0-py3-none-any.whl"
    new = tmp_path / "bot-0.2.0-py3-none-any.whl"
    old.write_bytes(b"")
    new.write_bytes(b"")
    now = time.time()
    os.utime(old, (now - 100, now - 100))
    os.utime(new, (now, now))
    assert newest_wheel(tmp_path) == new
    assert newest_wheel(new) == new


def test_newest_wheel_in_an_empty_directory_is_none(tmp_path):
    assert newest_wheel(tmp_path) is None


def test_model_loader_and_rover_model_are_served(client):
    assert client.get("/static/vendor/loaders/GLTFLoader.js").status_code == 200
    assert client.get("/static/vendor/utils/BufferGeometryUtils.js").status_code == 200
    rover = client.get("/static/models/round-rover.glb")
    assert rover.status_code == 200
    assert rover.content[:4] == b"glTF"


def test_config_includes_world_descriptions(client):
    data = client.get("/api/config").json()
    assert "bridge" in data["descriptions"]["river"]

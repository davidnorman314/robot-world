from robot_api import Colors
from robot_world.world import Terrain
from robot_world.worlds import WORLDS, world_description
from robot_world.worlds.simple_goal import MIN_DISTANCE, make_simple_goal_world


def test_same_seed_gives_same_world():
    assert make_simple_goal_world(7) == make_simple_goal_world(7)


def test_different_seeds_move_the_goal_and_the_start():
    worlds = [make_simple_goal_world(seed) for seed in range(10)]
    assert len({world.goal.center for world in worlds}) > 1
    assert len({(world.start.x, world.start.y) for world in worlds}) > 1


def test_there_is_no_water_anywhere():
    world = make_simple_goal_world(3)
    for x in range(int(world.width)):
        for y in range(int(world.height)):
            assert world.terrain_at(x + 0.5, y + 0.5) in (Terrain.LAND, Terrain.GOAL)


def test_robot_starts_on_clear_land_well_away_from_the_goal():
    for seed in range(30):
        world = make_simple_goal_world(seed)
        assert world.terrain_at(world.start.x, world.start.y) is Terrain.LAND
        assert not world.is_blocked(world.start.x, world.start.y, 0.3)
        gx, gy = world.goal.center
        distance = ((gx - world.start.x) ** 2 + (gy - world.start.y) ** 2) ** 0.5
        assert distance >= MIN_DISTANCE, f"seed {seed}: goal only {distance:.1f} m away"


def test_goal_has_a_tall_post_and_the_field_is_fenced():
    world = make_simple_goal_world(1)
    posts = [box for box in world.boxes if box.color == Colors.GOAL]
    assert len(posts) == 1
    assert posts[0].height >= 1.5
    assert not posts[0].solid
    assert world.is_blocked(0.1, world.height / 2, 0.3)
    assert world.is_blocked(world.width / 2, world.height - 0.1, 0.3)


def test_simple_goal_is_the_first_world_and_has_a_description():
    assert list(WORLDS)[0] == "simple-goal"
    description = world_description("simple-goal")
    assert "goal" in description
    assert "river" not in description
    assert len(description) < 600

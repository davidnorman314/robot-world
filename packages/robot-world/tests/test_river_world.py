from robot_world.world import Terrain
from robot_world.worlds.river import make_river_world


def river_columns(world):
    """The x range that is water at the top edge of the world."""
    xs = [x / 10 for x in range(int(world.width * 10))]
    water = [x for x in xs if world.terrain_at(x, 0.5) is Terrain.WATER]
    return min(water), max(water)


def test_same_seed_gives_same_world():
    assert make_river_world(7) == make_river_world(7)


def test_different_seeds_give_different_worlds():
    worlds = {make_river_world(seed) for seed in range(10)}
    assert len(worlds) > 1


def test_river_runs_the_full_height_of_the_world():
    world = make_river_world(3)
    left, right = river_columns(world)
    for y in (0.5, world.height / 2, world.height - 0.5):
        column = world.terrain_at((left + right) / 2, y)
        assert column in (Terrain.WATER, Terrain.BRIDGE)


def test_bridge_spans_the_river():
    for seed in range(20):
        world = make_river_world(seed)
        left, right = river_columns(world)
        bridge_rows = [
            y / 10
            for y in range(int(world.height * 10))
            if world.terrain_at((left + right) / 2, y / 10) is Terrain.BRIDGE
        ]
        assert bridge_rows, f"seed {seed} has no bridge"
        y = bridge_rows[len(bridge_rows) // 2]
        assert world.terrain_at(left - 1.7, y) is Terrain.LAND  # the ramp overhangs the bank by 1.5
        assert world.terrain_at(right + 1.8, y) is Terrain.LAND
        for x in (left, (left + right) / 2, right):
            assert world.terrain_at(x, y) is Terrain.BRIDGE


def test_robot_starts_on_land_west_of_the_river_and_goal_is_east():
    for seed in range(20):
        world = make_river_world(seed)
        left, right = river_columns(world)
        assert world.terrain_at(world.start.x, world.start.y) is Terrain.LAND
        assert world.start.x < left
        assert not world.is_blocked(world.start.x, world.start.y, 0.3)
        goal = world.goal
        assert goal.center[0] > right
        assert world.terrain_at(*goal.center) is Terrain.GOAL


def test_world_is_fenced_in_by_walls():
    world = make_river_world(1)
    assert world.is_blocked(0.1, world.height / 2, 0.3)
    assert world.is_blocked(world.width - 0.1, world.height / 2, 0.3)


def test_bridge_has_railings_on_both_sides():
    world = make_river_world(1)
    bridge = next(p.rect for p in world.patches if p.terrain is Terrain.BRIDGE)
    mid_x = bridge.center[0]
    assert world.is_blocked(mid_x, bridge.y0 - 0.05, 0.1)
    assert world.is_blocked(mid_x, bridge.y1 + 0.05, 0.1)
    assert not world.is_blocked(mid_x, bridge.center[1], 0.3)


def test_ramps_on_each_bank_have_no_railings():
    world = make_river_world(1)
    bridge = next(p.rect for p in world.patches if p.terrain is Terrain.BRIDGE)
    left, right = river_columns(world)
    for x in (bridge.x0 + 0.3, left - 0.3, right + 0.4, bridge.x1 - 0.3):
        assert world.terrain_at(x, bridge.center[1]) is Terrain.BRIDGE
        assert not world.is_blocked(x, bridge.y0 + 0.3, 0.3), f"railing on the ramp at x={x}"
        assert not world.is_blocked(x, bridge.y1 - 0.3, 0.3), f"railing on the ramp at x={x}"


def test_bridge_deck_is_wide_enough_to_drive_down_the_middle_with_margin():
    world = make_river_world(1)
    bridge = next(p.rect for p in world.patches if p.terrain is Terrain.BRIDGE)
    assert bridge.height >= 3.0
    mid_x = bridge.center[0]
    for dy in (-0.8, 0.0, 0.8):
        assert not world.is_blocked(mid_x, bridge.center[1] + dy, 0.3)

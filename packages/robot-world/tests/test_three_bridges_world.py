from robot_world.world import Terrain, World
from robot_world.worlds import world_description
from robot_world.worlds.three_bridges import make_three_bridges_world


def river_bounds(world: World) -> tuple[float, float]:
    xs = [x / 10 for x in range(int(world.width * 10))]
    water = [x for x in xs if world.terrain_at(x, 0.5) is Terrain.WATER]
    return min(water), max(water)


def bridge_runs(world: World, x: float) -> list[tuple[float, float]]:
    """The y ranges that are bridge at column ``x``, as (y_start, y_end) pairs."""
    runs = []
    current = None
    for i in range(int(world.height * 20) + 1):
        y = i / 20
        on_bridge = world.terrain_at(x, y) is Terrain.BRIDGE
        if on_bridge and current is None:
            current = y
        if not on_bridge and current is not None:
            runs.append((current, y))
            current = None
    return runs


def test_same_seed_gives_same_world():
    assert make_three_bridges_world(5) == make_three_bridges_world(5)


def test_there_are_three_bridges_on_the_west_ramp_but_only_one_crosses_the_river():
    for seed in range(30):
        world = make_three_bridges_world(seed)
        left, right = river_bounds(world)
        ramps = bridge_runs(world, left - 1.0)
        assert len(ramps) == 3, f"seed {seed}: {ramps}"
        whole = bridge_runs(world, (left + right) / 2)
        assert len(whole) == 1, f"seed {seed}: {whole}"
        for start, end in ramps:
            assert end - start >= 2.9


def test_bridges_are_separated_by_clear_bank():
    for seed in range(30):
        world = make_three_bridges_world(seed)
        left, _ = river_bounds(world)
        ramps = bridge_runs(world, left - 1.0)
        for (_, end), (next_start, _) in zip(ramps, ramps[1:], strict=False):
            assert next_start - end >= 1.5, f"seed {seed}: {ramps}"


def test_broken_bridges_have_water_and_no_railing_in_the_middle():
    world = make_three_bridges_world(1)
    left, right = river_bounds(world)
    middle = (left + right) / 2
    whole = bridge_runs(world, middle)
    for start, end in bridge_runs(world, left - 1.0):
        y = (start + end) / 2
        broken = (start, end) not in [(s, e) for s, e in whole]
        middle_terrain = world.terrain_at(middle, y)
        rail_blocked = world.is_blocked(middle, start - 0.1, 0.05)
        if broken:
            assert middle_terrain is Terrain.WATER
            assert not rail_blocked
            # the deck is still there on both sides of the gap
            assert world.terrain_at(left + 0.3, y) is Terrain.BRIDGE
            assert world.terrain_at(right - 0.2, y) is Terrain.BRIDGE
        else:
            assert middle_terrain is Terrain.BRIDGE
            assert rail_blocked


def test_every_bridge_is_sometimes_the_whole_one():
    whole_positions = set()
    for seed in range(30):
        world = make_three_bridges_world(seed)
        left, right = river_bounds(world)
        ramps = bridge_runs(world, left - 1.0)
        (whole,) = bridge_runs(world, (left + right) / 2)
        whole_positions.add(ramps.index(whole))
    assert whole_positions == {0, 1, 2}


def test_start_is_west_and_goal_is_east_on_land():
    for seed in range(30):
        world = make_three_bridges_world(seed)
        left, right = river_bounds(world)
        assert world.start.x < left
        assert world.terrain_at(world.start.x, world.start.y) is Terrain.LAND
        assert world.goal.center[0] > right
        assert world.time_limit > 180.0


def test_three_bridges_is_registered_with_a_description():
    description = world_description("three-bridges")
    assert "three bridges" in description
    assert "broken" in description
    assert "goal" in description

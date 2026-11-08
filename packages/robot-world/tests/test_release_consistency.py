"""Everything that names a release tag must name the current one.

She installs from a tag and her project pins robot-api to it, so the README, the starter
template and both packages have to move together at every release.
"""

import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).parents[3]
TAGGED_FILES = (
    ROOT / "README.md",
    ROOT / "examples" / "starter-bot" / "CLAUDE.md",
    ROOT / "examples" / "starter-bot" / "README.md",
    ROOT / "examples" / "starter-bot" / "pyproject.toml",
)


def package_version(name: str) -> str:
    pyproject = ROOT / "packages" / name / "pyproject.toml"
    return tomllib.loads(pyproject.read_text(encoding="utf-8"))["project"]["version"]


def test_both_packages_have_the_same_version():
    assert package_version("robot-api") == package_version("robot-world")


def test_every_tag_reference_names_the_current_release():
    tag = f"v{package_version('robot-world')}"
    for path in TAGGED_FILES:
        text = path.read_text(encoding="utf-8")
        found = set(re.findall(r"\bv\d+\.\d+\.\d+\b", text))
        assert found, f"{path.relative_to(ROOT)} should mention the release tag"
        assert found == {tag}, f"{path.relative_to(ROOT)} mentions {sorted(found)}, expected {tag}"


def test_setup_tarball_path_names_the_current_release():
    version = package_version("robot-world")
    text = TAGGED_FILES[1].read_text(encoding="utf-8")
    assert f"/archive/refs/tags/v{version}.tar.gz" in text
    assert f"robot-world-{version}/examples/starter-bot" in text


def test_starter_template_pins_robot_api_to_the_current_tag():
    pyproject = tomllib.loads(TAGGED_FILES[3].read_text(encoding="utf-8"))
    source = pyproject["tool"]["uv"]["sources"]["robot-api"]
    assert source["tag"] == f"v{package_version('robot-api')}"
    assert source["subdirectory"] == "packages/robot-api"

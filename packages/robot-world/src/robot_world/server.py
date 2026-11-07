"""The web server behind the browser viewer.

The page is static HTML and JavaScript served from the ``static`` folder. It asks the
server to run an episode (``POST /api/run``), gets the whole recording back as JSON,
and plays it back in the browser.
"""

import threading
import webbrowser
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from robot_world.remote import run_wheel
from robot_world.serialize import episode_to_dict
from robot_world.worlds import WORLDS

STATIC = Path(__file__).parent / "static"


def newest_wheel(path: Path) -> Path | None:
    """The wheel at ``path``, or the most recently modified wheel in that directory."""
    if path.is_file():
        return path
    if path.is_dir():
        wheels = sorted(path.glob("*.whl"), key=lambda p: p.stat().st_mtime)
        return wheels[-1] if wheels else None
    return None


class RunRequest(BaseModel):
    wheel: str
    world: str
    seed: int = 1
    timeout: float = 30.0


def build_app(default_wheel: Path | None = None, default_world: str = "river") -> FastAPI:
    app = FastAPI(title="robot-world")
    app.mount("/static", StaticFiles(directory=STATIC), name="static")

    @app.get("/")
    def index() -> FileResponse:
        return FileResponse(STATIC / "index.html")

    @app.get("/api/config")
    def config() -> dict[str, Any]:
        return {
            "worlds": sorted(WORLDS),
            "world": default_world,
            "wheel": str(default_wheel) if default_wheel else "",
        }

    @app.post("/api/run")
    def run(request: RunRequest) -> dict[str, Any]:
        if request.world not in WORLDS:
            raise HTTPException(400, f"unknown world {request.world!r}")
        wheel = newest_wheel(Path(request.wheel))
        if wheel is None:
            raise HTTPException(400, f"no wheel found at {request.wheel}")
        world = WORLDS[request.world](request.seed)
        result = run_wheel(world, wheel, wall_timeout=request.timeout)
        return episode_to_dict(world, result)

    return app


def serve(
    wheel: Path | None,
    world: str = "river",
    port: int = 8035,
    open_browser: bool = True,
) -> None:
    """Run the viewer on localhost until interrupted."""
    url = f"http://127.0.0.1:{port}/"
    if open_browser:
        threading.Timer(1.0, webbrowser.open, args=[url]).start()
    print(f"robot-world viewer at {url}  (Ctrl+C to stop)")
    uvicorn.run(build_app(wheel, world), host="127.0.0.1", port=port, log_level="warning")

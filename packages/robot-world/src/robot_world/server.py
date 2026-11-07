"""The web server behind the browser viewer.

The page is static HTML and JavaScript served from the ``static`` folder. It asks the
server to run an episode (``POST /api/run``), gets the whole recording back as JSON,
and plays it back in the browser. ``POST /api/batch`` runs many seeds and streams one
summary line per finished episode, so the page can show which seeds failed.
"""

import functools
import json
import threading
import webbrowser
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from robot_world.batch import run_batch
from robot_world.remote import run_wheel
from robot_world.serialize import episode_summary, episode_to_dict
from robot_world.worlds import WORLDS, world_description

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


class BatchRequest(RunRequest):
    episodes: int = Field(default=20, ge=1, le=1000)


def build_app(default_wheel: Path | None = None, default_world: str = "one-bridge") -> FastAPI:
    app = FastAPI(title="robot-world")
    app.mount("/static", StaticFiles(directory=STATIC), name="static")

    @app.get("/")
    def index() -> FileResponse:
        return FileResponse(STATIC / "index.html")

    @app.get("/api/config")
    def config() -> dict[str, Any]:
        return {
            "worlds": sorted(WORLDS),
            "descriptions": {name: world_description(name) for name in WORLDS},
            "world": default_world,
            "wheel": str(default_wheel) if default_wheel else "",
        }

    def resolve(request: RunRequest) -> Path:
        if request.world not in WORLDS:
            raise HTTPException(400, f"unknown world {request.world!r}")
        wheel = newest_wheel(Path(request.wheel))
        if wheel is None:
            raise HTTPException(400, f"no wheel found at {request.wheel}")
        return wheel

    @app.post("/api/run")
    def run(request: RunRequest) -> dict[str, Any]:
        wheel = resolve(request)
        world = WORLDS[request.world](request.seed)
        result = run_wheel(world, wheel, wall_timeout=request.timeout)
        return episode_to_dict(world, result)

    @app.post("/api/batch")
    def batch(request: BatchRequest) -> StreamingResponse:
        """Newline-delimited JSON: one ``episode_summary`` per seed, in finishing order."""
        wheel = resolve(request)
        seeds = range(request.seed, request.seed + request.episodes)
        run_episode = functools.partial(run_wheel, wheel=wheel, wall_timeout=request.timeout)

        def lines():
            for seed, result in run_batch(WORLDS[request.world], run_episode, seeds):
                yield json.dumps(episode_summary(seed, result)) + "\n"

        return StreamingResponse(lines(), media_type="application/x-ndjson")

    return app


def serve(
    wheel: Path | None,
    world: str = "one-bridge",
    port: int = 8035,
    open_browser: bool = True,
) -> None:
    """Run the viewer on localhost until interrupted."""
    url = f"http://127.0.0.1:{port}/"
    if open_browser:
        threading.Timer(1.0, webbrowser.open, args=[url]).start()
    print(f"robot-world viewer at {url}  (Ctrl+C to stop)")
    uvicorn.run(build_app(wheel, world), host="127.0.0.1", port=port, log_level="warning")

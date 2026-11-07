// The robot-world viewer: asks the server to run an episode, then replays it in 3D.
//
// Coordinates follow the simulator: x east, y north, z up. three.js defaults to y up,
// so every camera gets its `up` set to z.

import * as THREE from "three";
import { OrbitControls } from "./vendor/OrbitControls.js";
import { GLTFLoader } from "./vendor/loaders/GLTFLoader.js";

// Display colors. Same hues as the robot's flat palette so she can relate the two views.
const TERRAIN_COLORS = {
  land: 0x60a040,
  water: 0x285ac8,
  bridge: 0x966432,
  goal: 0xe63c3c,
};
const SKY = 0x87ceeb;

// The robot model (see models/ATTRIBUTION.md). It is scaled so its longer horizontal
// side is ROBOT_LENGTH meters; the simulator's robot is a circle of radius 0.3 m.
const ROBOT_MODEL = "/static/models/round-rover.glb";
const ROBOT_LENGTH = 0.8;
// The model's own forward direction after conversion to z-up, as a rotation about z.
// Change to Math.PI if the rover turns out to drive backwards.
const ROBOT_MODEL_FORWARD = 0;

// Camera parameters that match robot_world.camera.Camera's defaults.
const EYE_HEIGHT = 0.6;
const EYE_PITCH = -10;
const EYE_FOV_H = 90;
const EYE_ASPECT = 128 / 96;

const ui = {
  wheel: document.getElementById("wheel"),
  world: document.getElementById("world"),
  seed: document.getElementById("seed"),
  run: document.getElementById("run"),
  status: document.getElementById("status"),
  banner: document.getElementById("banner"),
  play: document.getElementById("play"),
  speed: document.getElementById("speed"),
  scrubber: document.getElementById("scrubber"),
  time: document.getElementById("time"),
  eye: document.getElementById("eye"),
  eyeLabel: document.getElementById("eye-label"),
  pose: document.getElementById("pose"),
  messages: document.getElementById("messages"),
  error: document.getElementById("error"),
  view: document.getElementById("view"),
  viewButtons: Array.from(document.querySelectorAll(".view-button")),
  resetView: document.getElementById("reset-view"),
};

const state = {
  episode: null, // the JSON from /api/run
  lookImages: [], // decoded <img> per look
  time: 0, // current playback time in simulated seconds
  playing: false,
  viewMode: "top",
  lastTick: null,
};

// --- three.js setup -------------------------------------------------------------

const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
ui.view.appendChild(renderer.domElement);

const scene = new THREE.Scene();
scene.background = new THREE.Color(SKY);

const hemisphere = new THREE.HemisphereLight(0xffffff, 0x446622, 1.4);
scene.add(hemisphere);
const sun = new THREE.DirectionalLight(0xffffff, 2.4);
sun.castShadow = true;
sun.shadow.mapSize.set(2048, 2048);
scene.add(sun);
scene.add(sun.target);

let worldGroup = new THREE.Group();
scene.add(worldGroup);
const robot = buildRobot();
scene.add(robot);
loadRobotModel();

const cameras = {
  top: new THREE.PerspectiveCamera(50, 1, 0.1, 500),
  chase: new THREE.PerspectiveCamera(60, 1, 0.1, 200),
  first: new THREE.PerspectiveCamera(60, EYE_ASPECT, 0.05, 200),
};
for (const camera of Object.values(cameras)) camera.up.set(0, 0, 1);
// The overview starts looking down on the world and can be rotated, zoomed and panned.
const orbitControls = new OrbitControls(cameras.top, renderer.domElement);
orbitControls.enableDamping = true;
orbitControls.maxPolarAngle = Math.PI / 2 - 0.05; // never go below the ground

// Vertical field of view of the robot's camera, from its horizontal FOV and aspect.
cameras.first.fov = THREE.MathUtils.radToDeg(
  2 * Math.atan(Math.tan(THREE.MathUtils.degToRad(EYE_FOV_H / 2)) / EYE_ASPECT),
);
cameras.first.updateProjectionMatrix();

function resize() {
  const width = ui.view.clientWidth;
  const height = ui.view.clientHeight;
  if (width === 0 || height === 0) return;
  renderer.setSize(width, height, false);
  const aspect = width / height;
  for (const camera of [cameras.top, cameras.chase]) {
    camera.aspect = aspect;
    camera.updateProjectionMatrix();
  }
  // Letterbox the first-person view to the robot camera's aspect by adjusting fov.
  cameras.first.aspect = aspect;
  cameras.first.updateProjectionMatrix();
}
window.addEventListener("resize", resize);

function resetOverview(world) {
  // High above the middle of the world, tilted just enough that north is up on screen.
  const camera = cameras.top;
  const fov = THREE.MathUtils.degToRad(camera.fov);
  const aspect = Math.max(0.5, camera.aspect);
  const span = Math.max(world.height, world.width / aspect);
  const distance = (span / 2 / Math.tan(fov / 2)) * 1.15;
  camera.position.set(world.width / 2, world.height / 2 - distance * 0.12, distance);
  orbitControls.target.set(world.width / 2, world.height / 2, 0);
  orbitControls.update();
}

// --- building the scene from a world -------------------------------------------

function buildWorld(world) {
  scene.remove(worldGroup);
  worldGroup = new THREE.Group();
  scene.add(worldGroup);

  const ground = new THREE.Mesh(
    new THREE.PlaneGeometry(world.width, world.height),
    new THREE.MeshLambertMaterial({ color: TERRAIN_COLORS.land }),
  );
  ground.position.set(world.width / 2, world.height / 2, 0);
  ground.receiveShadow = true;
  worldGroup.add(ground);

  world.patches.forEach((patch, i) => {
    const r = patch.rect;
    const mesh = new THREE.Mesh(
      new THREE.PlaneGeometry(r.x1 - r.x0, r.y1 - r.y0),
      new THREE.MeshLambertMaterial({ color: TERRAIN_COLORS[patch.terrain] ?? 0xff00ff }),
    );
    // Later patches paint over earlier ones, so lift each a hair above the last.
    mesh.position.set((r.x0 + r.x1) / 2, (r.y0 + r.y1) / 2, 0.005 * (i + 1));
    mesh.receiveShadow = true;
    worldGroup.add(mesh);
  });

  for (const box of world.boxes) {
    const r = box.rect;
    const [cr, cg, cb] = box.color;
    const mesh = new THREE.Mesh(
      new THREE.BoxGeometry(r.x1 - r.x0, r.y1 - r.y0, box.height),
      new THREE.MeshLambertMaterial({ color: new THREE.Color(cr / 255, cg / 255, cb / 255) }),
    );
    mesh.position.set((r.x0 + r.x1) / 2, (r.y0 + r.y1) / 2, box.height / 2);
    mesh.castShadow = true;
    mesh.receiveShadow = true;
    worldGroup.add(mesh);
  }

  sun.position.set(world.width * 0.3, -world.height * 0.3, 40);
  sun.target.position.set(world.width / 2, world.height / 2, 0);
  const shadow = sun.shadow.camera;
  const extent = Math.max(world.width, world.height) * 0.75;
  shadow.left = -extent;
  shadow.right = extent;
  shadow.top = extent;
  shadow.bottom = -extent;
  shadow.near = 1;
  shadow.far = 120;
  shadow.updateProjectionMatrix();

  resetOverview(world);
}

function loadRobotModel() {
  // Replace the placeholder primitives with the glTF rover once it has loaded.
  new GLTFLoader().load(
    ROBOT_MODEL,
    (gltf) => {
      const model = gltf.scene;
      model.traverse((node) => {
        if (node.isMesh) {
          node.castShadow = true;
          node.receiveShadow = true;
        }
      });
      // glTF is y-up; the world is z-up. Wrap the model so its y becomes our z.
      const wrapper = new THREE.Group();
      wrapper.rotation.x = Math.PI / 2;
      wrapper.add(model);
      const holder = new THREE.Group();
      holder.add(wrapper);
      holder.updateMatrixWorld(true);
      const box = new THREE.Box3().setFromObject(holder);
      const size = box.getSize(new THREE.Vector3());
      const scale = ROBOT_LENGTH / Math.max(size.x, size.y);
      holder.scale.setScalar(scale);
      holder.updateMatrixWorld(true);
      box.setFromObject(holder);
      const center = box.getCenter(new THREE.Vector3());
      holder.position.set(-center.x, -center.y, -box.min.z);
      const oriented = new THREE.Group();
      oriented.rotation.z = ROBOT_MODEL_FORWARD;
      oriented.add(holder);
      robot.clear();
      robot.add(oriented);
    },
    undefined,
    (error) => console.warn("Could not load the robot model; keeping the placeholder.", error),
  );
}

function buildRobot() {
  const group = new THREE.Group();
  const body = new THREE.Mesh(
    new THREE.BoxGeometry(0.5, 0.36, 0.22),
    new THREE.MeshLambertMaterial({ color: 0xf2c14e }),
  );
  body.position.z = 0.26;
  const trackMaterial = new THREE.MeshLambertMaterial({ color: 0x2c2f36 });
  for (const side of [-1, 1]) {
    const track = new THREE.Mesh(new THREE.BoxGeometry(0.64, 0.14, 0.2), trackMaterial);
    track.position.set(0, side * 0.26, 0.1);
    track.castShadow = true;
    group.add(track);
  }
  const head = new THREE.Mesh(
    new THREE.BoxGeometry(0.2, 0.24, 0.18),
    new THREE.MeshLambertMaterial({ color: 0xdddddd }),
  );
  head.position.set(0.14, 0, 0.46);
  const lens = new THREE.Mesh(
    new THREE.CylinderGeometry(0.05, 0.05, 0.04, 16),
    new THREE.MeshLambertMaterial({ color: 0x111111 }),
  );
  lens.rotation.z = Math.PI / 2;
  lens.position.set(0.26, 0, 0.46);
  for (const part of [body, head, lens]) {
    part.castShadow = true;
    group.add(part);
  }
  return group;
}

// --- playback -------------------------------------------------------------------

function frameAt(time) {
  // Index of the last frame whose time is <= `time` (binary search).
  const frames = state.episode.frames;
  let lo = 0;
  let hi = frames.length - 1;
  while (lo < hi) {
    const mid = (lo + hi + 1) >> 1;
    if (frames[mid][0] <= time) lo = mid;
    else hi = mid - 1;
  }
  return lo;
}

function poseAt(time) {
  const frames = state.episode.frames;
  const i = frameAt(time);
  const a = frames[i];
  const b = frames[Math.min(i + 1, frames.length - 1)];
  const span = b[0] - a[0];
  const t = span > 0 ? Math.min(1, (time - a[0]) / span) : 0;
  let dh = ((b[3] - a[3] + 540) % 360) - 180; // shortest way round
  return {
    x: a[1] + (b[1] - a[1]) * t,
    y: a[2] + (b[2] - a[2]) * t,
    heading: (a[3] + dh * t + 360) % 360,
    frame: i,
  };
}

function setTime(time) {
  const episode = state.episode;
  if (!episode) return;
  const last = episode.frames[episode.frames.length - 1][0];
  state.time = Math.max(0, Math.min(last, time));
  ui.scrubber.value = state.time;
  ui.time.textContent = `${state.time.toFixed(1)} s / ${last.toFixed(1)} s`;

  const pose = poseAt(state.time);
  robot.position.set(pose.x, pose.y, 0);
  robot.rotation.z = THREE.MathUtils.degToRad(pose.heading);
  ui.pose.textContent =
    `x ${pose.x.toFixed(2)}  y ${pose.y.toFixed(2)}  heading ${pose.heading.toFixed(0)}°`;

  updateEye(pose.frame);
  updateMessages(pose.frame);
  if (state.time >= last && state.playing) setPlaying(false);
}

function updateEye(frame) {
  const looks = state.episode.looks;
  let index = -1;
  for (let i = 0; i < looks.length && looks[i].frame <= frame; i++) index = i;
  const ctx = ui.eye.getContext("2d");
  if (index < 0) {
    ctx.fillStyle = "#000";
    ctx.fillRect(0, 0, ui.eye.width, ui.eye.height);
    ui.eyeLabel.textContent = "No picture yet";
    return;
  }
  const image = state.lookImages[index];
  if (image.complete) ctx.drawImage(image, 0, 0);
  const t = state.episode.frames[looks[index].frame][0];
  ui.eyeLabel.textContent = `Picture ${index + 1} of ${looks.length}, taken at ${t.toFixed(1)} s`;
}

function updateMessages(frame) {
  const items = ui.messages.children;
  let latest = null;
  for (let i = 0; i < items.length; i++) {
    const said = Number(items[i].dataset.frame) <= frame;
    items[i].classList.toggle("said", said);
    if (said) latest = items[i];
  }
  if (latest && state.playing) latest.scrollIntoView({ block: "nearest" });
}

function setPlaying(playing) {
  if (!state.episode) return;
  const last = state.episode.frames[state.episode.frames.length - 1][0];
  if (playing && state.time >= last) setTime(0);
  state.playing = playing;
  state.lastTick = null;
  ui.play.textContent = playing ? "Pause" : "Play";
}

function setView(mode) {
  state.viewMode = mode;
  orbitControls.enabled = mode === "top";
  for (const button of ui.viewButtons) {
    button.classList.toggle("active", button.dataset.view === mode);
  }
}

function updateCamera() {
  const heading = robot.rotation.z;
  const forward = new THREE.Vector3(Math.cos(heading), Math.sin(heading), 0);
  if (state.viewMode === "chase") {
    const camera = cameras.chase;
    camera.position.copy(robot.position).addScaledVector(forward, -4).add(new THREE.Vector3(0, 0, 2.5));
    camera.lookAt(robot.position.clone().addScaledVector(forward, 2).add(new THREE.Vector3(0, 0, 0.3)));
  } else if (state.viewMode === "first") {
    const camera = cameras.first;
    camera.position.copy(robot.position).add(new THREE.Vector3(0, 0, EYE_HEIGHT));
    const pitch = THREE.MathUtils.degToRad(EYE_PITCH);
    const direction = new THREE.Vector3(
      Math.cos(heading) * Math.cos(pitch),
      Math.sin(heading) * Math.cos(pitch),
      Math.sin(pitch),
    );
    camera.lookAt(camera.position.clone().add(direction));
  } else {
    orbitControls.update();
  }
}

function animate(now) {
  requestAnimationFrame(animate);
  if (state.playing) {
    if (state.lastTick !== null) {
      const dt = (now - state.lastTick) / 1000;
      setTime(state.time + dt * Number(ui.speed.value));
    }
    state.lastTick = now;
  }
  robot.visible = state.episode !== null && state.viewMode !== "first";
  updateCamera();
  renderer.render(scene, cameras[state.viewMode]);
}

// --- talking to the server ------------------------------------------------------

async function loadConfig() {
  const config = await (await fetch("/api/config")).json();
  ui.world.innerHTML = "";
  for (const name of config.worlds) {
    const option = document.createElement("option");
    option.value = name;
    option.textContent = name;
    option.selected = name === config.world;
    ui.world.appendChild(option);
  }
  ui.wheel.value = config.wheel;
}

async function runEpisode() {
  ui.run.disabled = true;
  ui.status.textContent = "Running...";
  ui.error.style.display = "none";
  try {
    const response = await fetch("/api/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        wheel: ui.wheel.value,
        world: ui.world.value,
        seed: Number(ui.seed.value),
      }),
    });
    if (!response.ok) {
      const detail = (await response.json()).detail ?? response.statusText;
      throw new Error(detail);
    }
    showEpisode(await response.json());
    ui.status.textContent = "";
  } catch (error) {
    ui.status.textContent = `Could not run: ${error.message}`;
  } finally {
    ui.run.disabled = false;
  }
}

function showEpisode(episode) {
  state.episode = episode;
  state.lookImages = episode.looks.map((look) => {
    const image = new Image();
    image.src = `data:image/png;base64,${look.png}`;
    image.onload = () => updateEye(poseAt(state.time).frame);
    return image;
  });
  buildWorld(episode.world);

  ui.messages.innerHTML = "";
  for (const [frame, text] of episode.messages) {
    const item = document.createElement("li");
    item.dataset.frame = frame;
    const t = episode.frames[frame][0];
    item.innerHTML = `<span class="t">${t.toFixed(1)} s</span>`;
    item.appendChild(document.createTextNode(text));
    ui.messages.appendChild(item);
  }

  const last = episode.frames[episode.frames.length - 1][0];
  ui.scrubber.max = last;
  ui.scrubber.disabled = false;
  ui.play.disabled = false;

  const succeeded = episode.outcome === "success";
  ui.banner.textContent = `${episode.outcome} after ${episode.time.toFixed(1)} s`;
  ui.banner.className = succeeded ? "success" : "failure";
  if (episode.error) {
    ui.error.textContent = episode.error;
    ui.error.style.display = "block";
  }

  setTime(0);
  setPlaying(true);
}

// --- wiring ---------------------------------------------------------------------

ui.run.addEventListener("click", runEpisode);
ui.resetView.addEventListener("click", () => state.episode && resetOverview(state.episode.world));
ui.play.addEventListener("click", () => setPlaying(!state.playing));
ui.scrubber.addEventListener("input", () => {
  setPlaying(false);
  setTime(Number(ui.scrubber.value));
});
for (const button of ui.viewButtons) {
  button.addEventListener("click", () => setView(button.dataset.view));
}
window.addEventListener("keydown", (event) => {
  if (event.target.tagName === "INPUT" || event.target.tagName === "SELECT") return;
  if (event.code === "Space") {
    event.preventDefault();
    setPlaying(!state.playing);
  }
});

loadConfig();
resize();
requestAnimationFrame(animate);

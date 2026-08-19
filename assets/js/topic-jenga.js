/* A small, optional physics flourish for the homepage topic links. */
(function () {
  "use strict";

  const stage = document.querySelector("[data-topic-jenga]");
  if (!stage || !window.Matter || window.TopicStack) return;

  const nav = stage.querySelector(".topic-cloud");
  const links = Array.from(nav.querySelectorAll(".topic-tag"));
  const media = window.matchMedia(
    "(min-width: 992px) and (pointer: fine) and (prefers-reduced-motion: no-preference)"
  );
  if (links.length === 0) return;

  const { Body, Bodies, Composite, Constraint, Engine, Sleeping, Vector } = window.Matter;
  const WIDTH = 190;
  const BLOCK_HEIGHT = 28;
  const FLOOR_TOP = 620;
  const DRAG_THRESHOLD = 6;
  const ACCENTS = ["#e91e63", "#ffc107", "#00bcd4", "#06d6a0", "#ff5722", "#8e6cff"];
  const OFFSETS = [0, -8, 7, -5, 8, -4, 5];

  let engine = null;
  let entries = [];
  let frameId = 0;
  let lastFrame = 0;
  let drag = null;
  let restoreTimer = 0;
  let enabled = false;
  let visible = true;

  function topicFor(link) {
    const url = new URL(link.href, window.location.href);
    return new URLSearchParams(url.hash.slice(1)).get("category") || link.textContent.trim();
  }

  function blockWidth(link) {
    return Math.min(180, Math.max(76, 20 + topicFor(link).length * 7.1));
  }

  function initialPosition(index, width) {
    const layer = links.length - 1 - index;
    const unclampedX = WIDTH / 2 + OFFSETS[layer % OFFSETS.length];
    return {
      x: Math.max(width / 2 + 2, Math.min(WIDTH - width / 2 - 2, unclampedX)),
      y: FLOOR_TOP - BLOCK_HEIGHT / 2 - layer * BLOCK_HEIGHT,
    };
  }

  function syncEntry(entry) {
    const x = entry.body.position.x - entry.width / 2;
    const y = entry.body.position.y - BLOCK_HEIGHT / 2;
    entry.link.style.transform = `translate3d(${x}px, ${y}px, 0) rotate(${entry.body.angle}rad)`;
  }

  function syncAll() {
    entries.forEach(syncEntry);
  }

  function stopLoop() {
    if (frameId) window.cancelAnimationFrame(frameId);
    frameId = 0;
    lastFrame = 0;
  }

  function frame(now) {
    if (!enabled || !visible || document.hidden) {
      stopLoop();
      return;
    }
    const delta = lastFrame ? Math.min(now - lastFrame, 1000 / 30) : 1000 / 60;
    lastFrame = now;
    Engine.update(engine, delta);
    syncAll();

    if (drag || entries.some(({ body }) => !body.isSleeping)) {
      frameId = window.requestAnimationFrame(frame);
    } else {
      stopLoop();
    }
  }

  function startLoop() {
    if (!frameId && enabled && visible && !document.hidden) {
      frameId = window.requestAnimationFrame(frame);
    }
  }

  function releaseActiveDrag() {
    if (!drag) return;
    const active = drag;
    drag = null;
    active.link.classList.remove("is-dragging");
    if (active.link.hasPointerCapture(active.pointerId)) {
      active.link.releasePointerCapture(active.pointerId);
    }
    if (active.constraint && engine) Composite.remove(engine.world, active.constraint);
  }

  function clearWorld() {
    stopLoop();
    releaseActiveDrag();
    if (restoreTimer) window.clearTimeout(restoreTimer);
    restoreTimer = 0;
    if (engine) Composite.clear(engine.world, false, true);
    engine = null;
    entries = [];
  }

  function buildStack() {
    clearWorld();
    stage.classList.remove("is-settling");
    engine = Engine.create({ enableSleeping: true });
    engine.gravity.y = 1;
    engine.gravity.scale = 0.001;
    engine.positionIterations = 10;
    engine.velocityIterations = 7;

    const floor = Bodies.rectangle(WIDTH / 2, FLOOR_TOP + 10, WIDTH * 4, 20, {
      isStatic: true,
      friction: 1,
      restitution: 0,
    });

    entries = links.map((link, index) => {
      const width = blockWidth(link);
      const position = initialPosition(index, width);
      const body = Bodies.rectangle(position.x, position.y, width, BLOCK_HEIGHT, {
        friction: 0.9,
        frictionStatic: 1,
        frictionAir: 0.012,
        restitution: 0.02,
        density: 0.0025,
        sleepThreshold: 24,
      });

      Body.setAngle(body, ((index % 5) - 2) * 0.0014);
      Sleeping.set(body, true);
      link.style.width = `${width}px`;
      link.style.borderLeftColor = ACCENTS[index % ACCENTS.length];
      link.draggable = false;
      return { body, link, width };
    });

    Composite.add(engine.world, [floor, ...entries.map(({ body }) => body)]);
    syncAll();
  }

  function stagePoint(event) {
    const rect = stage.getBoundingClientRect();
    return {
      x: Math.max(-WIDTH, Math.min(WIDTH * 2, event.clientX - rect.left)),
      y: Math.max(BLOCK_HEIGHT / 2, Math.min(FLOOR_TOP - BLOCK_HEIGHT / 2, event.clientY - rect.top)),
    };
  }

  function beginDrag(event) {
    const point = stagePoint(event);
    const localPoint = Vector.rotate(Vector.sub(point, drag.entry.body.position), -drag.entry.body.angle);
    drag.constraint = Constraint.create({
      pointA: point,
      bodyB: drag.entry.body,
      pointB: localPoint,
      length: 0,
      stiffness: 0.16,
      damping: 0.14,
    });
    drag.active = true;
    drag.link.classList.add("is-dragging");
    entries.forEach(({ body }) => Sleeping.set(body, false));
    Composite.add(engine.world, drag.constraint);
    startLoop();
  }

  function pointerDown(event) {
    if (!enabled || drag || restoreTimer || event.button !== 0) return;
    const link = event.currentTarget;
    const entry = entries.find((candidate) => candidate.link === link);
    if (!entry) return;
    drag = {
      entry,
      link,
      pointerId: event.pointerId,
      originX: event.clientX,
      originY: event.clientY,
      baseY: entry.body.position.y,
      active: false,
      constraint: null,
    };
    link.setPointerCapture(event.pointerId);
  }

  function pointerMove(event) {
    if (!drag || drag.pointerId !== event.pointerId) return;
    const distance = Math.hypot(event.clientX - drag.originX, event.clientY - drag.originY);
    if (!drag.active && distance >= DRAG_THRESHOLD) beginDrag(event);
    if (!drag.active) return;

    event.preventDefault();
    const point = stagePoint(event);
    drag.constraint.pointA.x = point.x;
    drag.constraint.pointA.y = Math.max(
      drag.baseY - BLOCK_HEIGHT / 2,
      Math.min(drag.baseY + BLOCK_HEIGHT / 2, point.y)
    );
  }

  function pointerUp(event) {
    if (!drag || drag.pointerId !== event.pointerId) return;
    const wasDragged = drag.active;
    const link = drag.link;
    releaseActiveDrag();
    if (!wasDragged) return;

    event.preventDefault();
    link.dataset.suppressPhysicsClick = "true";
    window.setTimeout(() => delete link.dataset.suppressPhysicsClick, 0);
    stage.classList.add("is-settling");
    restoreTimer = window.setTimeout(() => {
      restoreTimer = 0;
      buildStack();
    }, 1800);
    startLoop();
  }

  function cancelPointer(event) {
    if (!drag) return;
    if (typeof event?.pointerId === "number" && event.pointerId !== drag.pointerId) return;
    buildStack();
  }

  function attachEvents() {
    links.forEach((link) => {
      link.addEventListener("pointerdown", pointerDown);
      link.addEventListener("pointermove", pointerMove);
      link.addEventListener("pointerup", pointerUp);
      link.addEventListener("pointercancel", cancelPointer);
      link.addEventListener("lostpointercapture", cancelPointer);
    });
  }

  function detachEvents() {
    links.forEach((link) => {
      link.removeEventListener("pointerdown", pointerDown);
      link.removeEventListener("pointermove", pointerMove);
      link.removeEventListener("pointerup", pointerUp);
      link.removeEventListener("pointercancel", cancelPointer);
      link.removeEventListener("lostpointercapture", cancelPointer);
      link.style.removeProperty("transform");
      link.style.removeProperty("width");
      link.style.removeProperty("border-left-color");
      link.removeAttribute("draggable");
      link.classList.remove("is-dragging");
      delete link.dataset.suppressPhysicsClick;
    });
  }

  function enable() {
    if (enabled || !media.matches) return;
    enabled = true;
    stage.classList.add("jenga-enabled");
    attachEvents();
    buildStack();
  }

  function disable() {
    if (!enabled) return;
    enabled = false;
    clearWorld();
    detachEvents();
    stage.classList.remove("jenga-enabled");
    stage.classList.remove("is-settling");
  }

  function respondToMedia() {
    if (media.matches) enable();
    else disable();
  }

  window.addEventListener("blur", cancelPointer);
  document.addEventListener("visibilitychange", () => {
    if (document.hidden) stopLoop();
    else if (enabled && (drag || entries.some(({ body }) => !body.isSleeping))) startLoop();
  });
  new IntersectionObserver(([entry]) => {
    visible = entry.isIntersecting;
    if (!visible) stopLoop();
    else if (enabled && (drag || entries.some(({ body }) => !body.isSleeping))) startLoop();
  }).observe(stage);

  media.addEventListener("change", respondToMedia);
  window.TopicStack = true;
  respondToMedia();
})();

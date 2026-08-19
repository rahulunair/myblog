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

  const { Bodies, Composite, Constraint, Engine, Sleeping, Vector } = window.Matter;
  const DRAG_THRESHOLD = 6;
  const COLLISION_GUTTER = 5;

  let engine = null;
  let entries = [];
  let frameId = 0;
  let lastFrame = 0;
  let drag = null;
  let restoreTimer = 0;
  let enabled = false;
  let visible = true;

  function syncEntry(entry) {
    const x = entry.body.position.x - entry.width / 2;
    const y = entry.body.position.y - entry.height / 2;
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
    if (!enabled || !engine || !visible || document.hidden) {
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
    if (!frameId && enabled && engine && visible && !document.hidden) {
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

  function clearPhysics() {
    stopLoop();
    releaseActiveDrag();
    if (restoreTimer) window.clearTimeout(restoreTimer);
    restoreTimer = 0;
    if (engine) Composite.clear(engine.world, false, true);
    engine = null;
    entries = [];

    stage.classList.remove("is-physical", "is-settling");
    stage.style.removeProperty("height");
    links.forEach((link) => {
      link.style.removeProperty("transform");
      link.style.removeProperty("width");
      link.style.removeProperty("height");
      link.removeAttribute("draggable");
      link.classList.remove("is-dragging");
      delete link.dataset.suppressPhysicsClick;
    });
  }

  function activatePhysics() {
    const stageRect = stage.getBoundingClientRect();
    const snapshots = links.map((link) => {
      const rect = link.getBoundingClientRect();
      return {
        link,
        width: rect.width,
        height: rect.height,
        x: rect.left - stageRect.left + rect.width / 2,
        y: rect.top - stageRect.top + rect.height / 2,
      };
    });
    const contentBottom = Math.max(...snapshots.map(({ y, height }) => y + height / 2));
    const stageHeight = Math.max(stageRect.height, contentBottom);

    stage.style.height = `${stageHeight}px`;
    stage.classList.add("is-physical");
    engine = Engine.create({ enableSleeping: true });
    engine.gravity.y = 1;
    engine.gravity.scale = 0.001;
    engine.positionIterations = 10;
    engine.velocityIterations = 7;

    const floor = Bodies.rectangle(stageRect.width / 2, stageHeight + 10, stageRect.width * 5, 20, {
      isStatic: true,
      friction: 1,
      restitution: 0,
    });

    entries = snapshots.map((snapshot) => {
      const body = Bodies.rectangle(
        snapshot.x,
        snapshot.y,
        snapshot.width + COLLISION_GUTTER,
        snapshot.height + COLLISION_GUTTER,
        {
          friction: 0.9,
          frictionStatic: 1,
          frictionAir: 0.012,
          restitution: 0.02,
          density: 0.0025,
          sleepThreshold: 24,
        }
      );
      Sleeping.set(body, true);
      snapshot.link.style.width = `${snapshot.width}px`;
      snapshot.link.style.height = `${snapshot.height}px`;
      snapshot.link.draggable = false;
      return { ...snapshot, body };
    });

    Composite.add(engine.world, [floor, ...entries.map(({ body }) => body)]);
    syncAll();
  }

  function stagePoint(event) {
    const rect = stage.getBoundingClientRect();
    return {
      x: Math.max(-64, Math.min(rect.width + 64, event.clientX - rect.left)),
      y: Math.max(0, Math.min(rect.height, event.clientY - rect.top)),
    };
  }

  function beginDrag(event) {
    activatePhysics();
    drag.entry = entries.find((entry) => entry.link === drag.link);
    if (!drag.entry) {
      clearPhysics();
      return;
    }

    drag.baseY = drag.entry.body.position.y;
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
    if (!enabled || drag || restoreTimer || event.button !== 0 || event.pointerType !== "mouse") return;
    drag = {
      link: event.currentTarget,
      pointerId: event.pointerId,
      originX: event.clientX,
      originY: event.clientY,
      active: false,
      entry: null,
      baseY: 0,
      constraint: null,
    };
    drag.link.setPointerCapture(event.pointerId);
  }

  function pointerMove(event) {
    if (!drag || drag.pointerId !== event.pointerId) return;
    const distance = Math.hypot(event.clientX - drag.originX, event.clientY - drag.originY);
    if (!drag.active && distance >= DRAG_THRESHOLD) beginDrag(event);
    if (!drag?.active) return;

    event.preventDefault();
    const point = stagePoint(event);
    drag.constraint.pointA.x = point.x;
    drag.constraint.pointA.y = Math.max(
      drag.baseY - drag.entry.height / 2,
      Math.min(drag.baseY + drag.entry.height / 2, point.y)
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
    restoreTimer = window.setTimeout(clearPhysics, 1800);
    startLoop();
  }

  function cancelPointer(event) {
    if (!drag) return;
    if (typeof event?.pointerId === "number" && event.pointerId !== drag.pointerId) return;
    clearPhysics();
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
    });
  }

  function enable() {
    if (enabled || !media.matches) return;
    enabled = true;
    stage.classList.add("jenga-enabled");
    attachEvents();
  }

  function disable() {
    if (!enabled) return;
    enabled = false;
    clearPhysics();
    detachEvents();
    stage.classList.remove("jenga-enabled");
  }

  function respondToMedia() {
    if (media.matches) enable();
    else disable();
  }

  window.addEventListener("blur", cancelPointer);
  document.addEventListener("visibilitychange", () => {
    if (document.hidden) stopLoop();
    else if (enabled && engine && (drag || entries.some(({ body }) => !body.isSleeping))) startLoop();
  });
  new IntersectionObserver(([entry]) => {
    visible = entry.isIntersecting;
    if (!visible) stopLoop();
    else if (enabled && engine && (drag || entries.some(({ body }) => !body.isSleeping))) startLoop();
  }).observe(stage);

  media.addEventListener("change", respondToMedia);
  window.TopicStack = true;
  respondToMedia();
})();

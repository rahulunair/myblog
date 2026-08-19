/* Load the physics engine only where the pointer-driven game can run. */
(function () {
  "use strict";

  const media = window.matchMedia(
    "(min-width: 992px) and (pointer: fine) and (prefers-reduced-motion: no-preference)"
  );
  const links = Array.from(document.querySelectorAll("[data-topic-jenga] .topic-tag"));
  let loading = null;

  function topicFor(link) {
    const url = new URL(link.href, window.location.href);
    return new URLSearchParams(url.hash.slice(1)).get("category") || link.textContent.trim();
  }

  function syncCurrentTopic() {
    const selected = new URLSearchParams(window.location.hash.slice(1)).get("category") || "";
    links.forEach((link) => {
      if (selected && topicFor(link) === selected) link.setAttribute("aria-current", "true");
      else link.removeAttribute("aria-current");
    });
  }

  function filterTopic(event) {
    if (event.currentTarget.dataset.suppressPhysicsClick === "true") {
      event.preventDefault();
      delete event.currentTarget.dataset.suppressPhysicsClick;
      return;
    }

    const topic = topicFor(event.currentTarget);
    if (typeof window.quartoListingCategory !== "function") return;
    event.preventDefault();
    window.quartoListingCategory(window.btoa(window.encodeURIComponent(topic)));
    syncCurrentTopic();
  }

  function loadScript(src) {
    return new Promise((resolve, reject) => {
      const script = document.createElement("script");
      script.src = src;
      script.onload = resolve;
      script.onerror = reject;
      document.head.appendChild(script);
    });
  }

  function loadGame() {
    if (!media.matches || loading || window.TopicStack) return;
    loading = loadScript("/assets/vendor/matter-js/0.20.0/matter.min.js")
      .then(() => loadScript("/assets/js/topic-jenga.js"))
      .catch(() => {
        // The server-rendered topic links remain the complete fallback.
        loading = null;
      });
  }

  media.addEventListener("change", loadGame);
  links.forEach((link) => link.addEventListener("click", filterTopic));
  window.addEventListener("hashchange", syncCurrentTopic);
  syncCurrentTopic();
  loadGame();
})();

(function () {
  const header = document.querySelector(".site-header");
  const nav = document.querySelector(".nav");
  const toggle = document.querySelector(".nav-toggle");
  if (toggle && nav) {
    toggle.addEventListener("click", function () {
      const open = nav.classList.toggle("is-open");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
    });
  }
  if (header) {
    const onScroll = function () {
      header.classList.toggle("is-scrolled", window.scrollY > 8);
    };
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
  }
  const year = document.getElementById("year");
  if (year) year.textContent = String(new Date().getFullYear());

  document.querySelectorAll("pre").forEach(function (pre) {
    if (pre.closest(".code-block")) return;
    if (pre.classList.contains("mermaid") || pre.querySelector("code.language-mermaid")) return;
    const wrap = document.createElement("div");
    wrap.className = "code-block";
    pre.parentNode.insertBefore(wrap, pre);
    wrap.appendChild(pre);
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "code-copy";
    btn.textContent = "Copy";
    btn.addEventListener("click", function () {
      const text = pre.textContent || "";
      navigator.clipboard.writeText(text).then(function () {
        btn.textContent = "Copied";
        setTimeout(function () { btn.textContent = "Copy"; }, 1600);
      });
    });
    wrap.appendChild(btn);
  });

  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  function syncHeroVideo() {
    document.querySelectorAll("video.hero-video").forEach(function (video) {
      if (reduceMotion.matches) {
        video.pause();
        video.removeAttribute("autoplay");
        try { video.currentTime = 0; } catch (err) { /* ignore */ }
      } else {
        video.setAttribute("autoplay", "");
        const play = video.play();
        if (play && typeof play.catch === "function") play.catch(function () {});
      }
    });
  }
  syncHeroVideo();
  if (typeof reduceMotion.addEventListener === "function") {
    reduceMotion.addEventListener("change", syncHeroVideo);
  }

  const mermaidNodes = document.querySelectorAll("pre code.language-mermaid, pre.mermaid, code.mermaid");
  if (mermaidNodes.length && window.mermaid) {
    window.mermaid.initialize({
      startOnLoad: false,
      theme: "base",
      themeVariables: {
        primaryColor: "#ccfbf1",
        primaryTextColor: "#0f172a",
        primaryBorderColor: "#0f766e",
        lineColor: "#64748b",
        fontFamily: "IBM Plex Sans, sans-serif",
      },
    });
    mermaidNodes.forEach(function (node) {
      const pre = node.tagName === "CODE" ? node.parentElement : node;
      const wrap = document.createElement("div");
      wrap.className = "mermaid";
      wrap.textContent = node.textContent;
      pre.replaceWith(wrap);
    });
    window.mermaid.run({ querySelector: ".mermaid" });
  }
})();

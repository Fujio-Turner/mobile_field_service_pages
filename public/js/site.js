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

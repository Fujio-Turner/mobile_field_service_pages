(function () {
  const input = document.getElementById("faq-q");
  const root = document.getElementById("faq-root");
  const empty = document.getElementById("faq-empty");
  const count = document.getElementById("faq-count");
  if (!input || !root || typeof Mark !== "function") return;

  const marker = new Mark(root);
  const items = Array.prototype.slice.call(root.querySelectorAll(".faq-item"));
  const groups = Array.prototype.slice.call(root.querySelectorAll("[data-faq-group]"));
  const jump = document.querySelector(".faq-jump");
  const total = items.length;

  function setCount(shown) {
    if (!count) return;
    if (!input.value.trim()) {
      count.textContent = total + " questions";
      return;
    }
    count.textContent = shown + " of " + total + " questions";
  }

  function run() {
    const q = input.value.trim();
    marker.unmark({
      done: function () {
        if (!q) {
          items.forEach(function (el) {
            el.hidden = false;
            el.open = false;
          });
          groups.forEach(function (g) {
            g.hidden = false;
          });
          if (jump) jump.hidden = false;
          if (empty) empty.hidden = true;
          setCount(total);
          return;
        }
        marker.mark(q, {
          element: "mark",
          className: "faq-hit",
          separateWordSearch: true,
          accuracy: "partially",
          diacritics: true,
          done: function () {
            let shown = 0;
            items.forEach(function (el) {
              const hit = el.querySelector("mark.faq-hit");
              el.hidden = !hit;
              el.open = Boolean(hit);
              if (hit) shown += 1;
            });
            groups.forEach(function (g) {
              const any = g.querySelector(".faq-item:not([hidden])");
              g.hidden = !any;
            });
            if (jump) jump.hidden = true;
            if (empty) empty.hidden = shown !== 0;
            setCount(shown);
          },
        });
      },
    });
  }

  function syncUrl(q) {
    try {
      const url = new URL(window.location.href);
      if (q) url.searchParams.set("q", q);
      else url.searchParams.delete("q");
      const next = url.pathname + url.search + url.hash;
      if (next !== window.location.pathname + window.location.search + window.location.hash) {
        history.replaceState(null, "", next);
      }
    } catch (err) {
      /* ignore */
    }
  }

  input.addEventListener("input", function () {
    run();
    syncUrl(input.value.trim());
  });
  input.addEventListener("search", function () {
    run();
    syncUrl(input.value.trim());
  });
  document.getElementById("faq-search-form").addEventListener("submit", function (e) {
    e.preventDefault();
    run();
    syncUrl(input.value.trim());
  });

  const initial = new URLSearchParams(window.location.search).get("q");
  if (initial) input.value = initial;
  setCount(total);
  if (initial) run();
})();

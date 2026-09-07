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

  initHeroSyncDemo();

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

  function initHeroSyncDemo() {
    const root = document.getElementById("sync-demo");
    if (!root) return;
    const note = root.getAttribute("data-note") || "";
    const typed = root.querySelector(".demo-text");
    const save = root.querySelector(".demo-save");
    const keys = root.querySelector(".demo-keys");
    const caption = root.querySelector(".sync-caption");
    const packets = root.querySelectorAll(".pkt");
    const nodeSt = root.querySelectorAll(".sync-node-st");
    if (!typed || !save) return;

    if (keys && !keys.childElementCount) {
      const rows = [10, 9, 1];
      rows.forEach(function (count, idx) {
        const row = document.createElement("div");
        row.className = "demo-row";
        for (let k = 0; k < count; k += 1) {
          const key = document.createElement("span");
          if (idx === 2) key.className = "wide";
          row.appendChild(key);
        }
        keys.appendChild(row);
      });
    }
    const keyEls = keys ? keys.querySelectorAll("span") : [];

    const captions = {
      idle: "A note starts empty on the phone.",
      typing: "Typing the job note.",
      aim: "Reach for Save.",
      tap: "Saved on the device.",
      push: "Pushing across the internet.",
      synced: "Saved on the phone, then across the internet.",
    };

    function setStage(name) {
      root.dataset.stage = name;
      if (caption && captions[name]) caption.textContent = captions[name];
      if (nodeSt[0] && nodeSt[1]) {
        if (name === "push") {
          nodeSt[0].textContent = "Receiving";
          nodeSt[1].textContent = "Waiting";
        } else if (name === "synced") {
          nodeSt[0].textContent = "Forwarded";
          nodeSt[1].textContent = "1 note in";
        } else {
          nodeSt[0].textContent = "On the internet";
          nodeSt[1].textContent = "Couchbase Server";
        }
      }
    }

    function hitKey() {
      if (!keyEls.length) return;
      keyEls.forEach(function (el) { el.classList.remove("is-hit"); });
      const pick = keyEls[Math.floor(Math.random() * (keyEls.length - 1))];
      pick.classList.add("is-hit");
    }

    function firePackets() {
      packets.forEach(function (pkt, i) {
        const delay = pkt.classList.contains("pkt-down") ? 900 : i * 220;
        window.setTimeout(function () {
          pkt.querySelectorAll("animate, animateMotion").forEach(function (anim) {
            if (anim.beginElement) anim.beginElement();
          });
        }, delay);
      });
    }

    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      typed.textContent = note;
      save.textContent = "Saved";
      setStage("synced");
      return;
    }

    let i = 0;
    let timer = 0;
    let running = true;

    function later(fn, ms) {
      window.clearTimeout(timer);
      timer = window.setTimeout(fn, ms);
    }

    function loop() {
      if (!running) return;
      i = 0;
      typed.textContent = "";
      save.textContent = "Save";
      setStage("idle");
      later(function () {
        setStage("typing");
        typeNext();
      }, 700);
    }

    function typeNext() {
      if (!running) return;
      if (i < note.length) {
        i += 1;
        typed.textContent = note.slice(0, i);
        hitKey();
        later(typeNext, 70 + Math.random() * 40 + (i === 14 ? 400 : 0));
        return;
      }
      keyEls.forEach(function (el) { el.classList.remove("is-hit"); });
      later(function () {
        setStage("aim");
        later(function () {
          setStage("tap");
          save.textContent = "Saved";
          later(function () {
            setStage("push");
            firePackets();
            later(function () {
              setStage("synced");
              later(loop, 3800);
            }, 2200);
          }, 380);
        }, 700);
      }, 480);
    }

    document.addEventListener("visibilitychange", function () {
      running = document.visibilityState === "visible";
      if (running) loop();
      else window.clearTimeout(timer);
    });

    loop();
  }
})();

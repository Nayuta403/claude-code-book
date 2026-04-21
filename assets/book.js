// Copy-to-clipboard buttons on every code block.
// No dependencies, ~1KB.
(function () {
  "use strict";

  function makeButton() {
    var btn = document.createElement("button");
    btn.type = "button";
    btn.className = "copy-btn";
    btn.setAttribute("aria-label", "复制代码");
    btn.textContent = "复制";
    return btn;
  }

  function onCopy(btn, pre) {
    var code = pre.querySelector("code") || pre;
    var text = code.textContent || "";
    // Strip trailing newline for cleaner paste
    if (text.charAt(text.length - 1) === "\n") text = text.slice(0, -1);

    var done = function () {
      btn.textContent = "已复制";
      btn.classList.add("copied");
      window.setTimeout(function () {
        btn.textContent = "复制";
        btn.classList.remove("copied");
      }, 1600);
    };

    var fail = function () {
      btn.textContent = "复制失败";
      window.setTimeout(function () {
        btn.textContent = "复制";
      }, 1800);
    };

    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(done, fail);
      return;
    }
    // Fallback for http: contexts
    try {
      var ta = document.createElement("textarea");
      ta.value = text;
      ta.setAttribute("readonly", "");
      ta.style.position = "absolute";
      ta.style.left = "-9999px";
      document.body.appendChild(ta);
      ta.select();
      document.execCommand("copy");
      document.body.removeChild(ta);
      done();
    } catch (e) {
      fail();
    }
  }

  function init() {
    var figs = document.querySelectorAll("figure.codeblock");
    for (var i = 0; i < figs.length; i++) {
      var fig = figs[i];
      if (fig.querySelector(".copy-btn")) continue;
      var pre = fig.querySelector("pre");
      if (!pre) continue;
      var btn = makeButton();
      (function (b, p) {
        b.addEventListener("click", function () { onCopy(b, p); });
      })(btn, pre);
      fig.appendChild(btn);
    }
    initProgressBar();
    initTopBtn();
    initKeyNav();
    initHelpOverlay();
    initOutlineSpy();
    initPrintExpand();
  }

  function initPrintExpand() {
    // Force <details> open on print so the outline becomes a static
    // Contents block in the exported PDF; restore after print.
    function openAll() {
      var dets = document.querySelectorAll("details.chap-outline");
      for (var i = 0; i < dets.length; i++) {
        if (dets[i].dataset._wasOpen == null) {
          dets[i].dataset._wasOpen = dets[i].open ? "1" : "0";
        }
        dets[i].open = true;
      }
    }
    function restore() {
      var dets = document.querySelectorAll("details.chap-outline");
      for (var i = 0; i < dets.length; i++) {
        if (dets[i].dataset._wasOpen != null) {
          dets[i].open = dets[i].dataset._wasOpen === "1";
          delete dets[i].dataset._wasOpen;
        }
      }
    }
    window.addEventListener("beforeprint", openAll);
    window.addEventListener("afterprint", restore);
    // Safari also supports MediaQueryList 'change' for print
    if (window.matchMedia) {
      var mql = window.matchMedia("print");
      if (mql.addEventListener) {
        mql.addEventListener("change", function (m) {
          if (m.matches) openAll(); else restore();
        });
      }
    }
  }

  function initOutlineSpy() {
    var outline = document.querySelector(".chap-outline");
    if (!outline || !("IntersectionObserver" in window)) return;

    var links = outline.querySelectorAll('a[href^="#"]');
    if (!links.length) return;

    var map = {};
    for (var i = 0; i < links.length; i++) {
      var href = links[i].getAttribute("href") || "";
      var id;
      try { id = decodeURIComponent(href.slice(1)); } catch (e) { id = href.slice(1); }
      if (id) map[id] = links[i];
    }

    var currentLink = null;
    function setCurrent(link) {
      if (currentLink === link) return;
      if (currentLink) currentLink.classList.remove("current");
      if (link) link.classList.add("current");
      currentLink = link;
    }

    // Choose the intersecting heading that sits highest in the viewport.
    var visible = {};  // id → intersectionRatio (or a "seen" flag)
    var io = new IntersectionObserver(function (entries) {
      for (var j = 0; j < entries.length; j++) {
        var e = entries[j];
        if (e.isIntersecting) visible[e.target.id] = e.boundingClientRect.top;
        else delete visible[e.target.id];
      }
      // pick the visible heading with the smallest top (closest to top of viewport)
      var bestId = null, bestTop = Infinity;
      for (var id in visible) {
        if (visible[id] < bestTop) { bestId = id; bestTop = visible[id]; }
      }
      setCurrent(bestId ? map[bestId] : null);
    }, {
      rootMargin: "-72px 0px -60% 0px",
      threshold: [0, 0.5, 1]
    });

    for (var id2 in map) {
      var h = document.getElementById(id2);
      if (h) io.observe(h);
    }
  }

  function initHelpOverlay() {
    if (document.querySelector(".kb-help")) return;
    var el = document.createElement("div");
    el.className = "kb-help";
    el.setAttribute("hidden", "");
    el.setAttribute("role", "dialog");
    el.setAttribute("aria-modal", "true");
    el.setAttribute("aria-label", "键盘快捷键");
    el.innerHTML =
      '<div class="kb-help-card" role="document">' +
        '<h2>键盘快捷键</h2>' +
        '<dl>' +
          '<dt><kbd>[</kbd><span class="or">/</span><kbd>←</kbd></dt><dd>上一章</dd>' +
          '<dt><kbd>]</kbd><span class="or">/</span><kbd>→</kbd></dt><dd>下一章</dd>' +
          '<dt><kbd>?</kbd></dt><dd>显示 / 隐藏此面板</dd>' +
          '<dt><kbd>Esc</kbd></dt><dd>关闭此面板</dd>' +
        '</dl>' +
        '<p class="kb-help-foot">点击外部关闭</p>' +
      '</div>';
    document.body.appendChild(el);

    function show() { el.removeAttribute("hidden"); }
    function hide() { el.setAttribute("hidden", ""); }
    function toggle() {
      if (el.hasAttribute("hidden")) show(); else hide();
    }

    document.addEventListener("keydown", function (e) {
      if (e.defaultPrevented || e.ctrlKey || e.metaKey || e.altKey) return;
      var tag = e.target && e.target.tagName;
      if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") return;
      if (e.target && e.target.isContentEditable) return;

      if (e.key === "?" || (e.key === "/" && e.shiftKey)) {
        toggle();
        e.preventDefault();
      } else if (e.key === "Escape" && !el.hasAttribute("hidden")) {
        hide();
        e.preventDefault();
      }
    });
    el.addEventListener("click", function (ev) {
      // Close when clicking on the backdrop (element itself), not on the card
      if (ev.target === el) hide();
    });
  }

  function initKeyNav() {
    var prev = document.querySelector(".chap-nav .nav-link.prev");
    var next = document.querySelector(".chap-nav .nav-link.next");
    if (!prev && !next) return;
    document.addEventListener("keydown", function (e) {
      // Ignore when user is typing in a form field or with modifier keys held.
      if (e.defaultPrevented || e.ctrlKey || e.metaKey || e.altKey) return;
      var tag = e.target && e.target.tagName;
      if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") return;
      if (e.target && e.target.isContentEditable) return;

      var k = e.key;
      if (k === "ArrowLeft" || k === "[") {
        if (prev && prev.tagName === "A") { prev.click(); e.preventDefault(); }
      } else if (k === "ArrowRight" || k === "]") {
        if (next && next.tagName === "A") { next.click(); e.preventDefault(); }
      }
    });
  }

  function initProgressBar() {
    if (document.querySelector(".read-progress")) return;
    var bar = document.createElement("div");
    bar.className = "read-progress";
    bar.setAttribute("aria-hidden", "true");
    document.body.appendChild(bar);

    var ticking = false;
    function update() {
      var max = document.documentElement.scrollHeight - window.innerHeight;
      var pct = max > 0 ? Math.min(1, Math.max(0, window.scrollY / max)) : 0;
      bar.style.transform = "scaleX(" + pct + ")";
      ticking = false;
    }
    window.addEventListener("scroll", function () {
      if (!ticking) {
        window.requestAnimationFrame(update);
        ticking = true;
      }
    }, { passive: true });
    window.addEventListener("resize", update, { passive: true });
    update();
  }

  function initTopBtn() {
    if (document.querySelector(".to-top-btn")) return;
    var btn = document.createElement("button");
    btn.type = "button";
    btn.className = "to-top-btn";
    btn.setAttribute("aria-label", "回到顶部");
    btn.innerHTML = '<span class="arr" aria-hidden="true">↑</span><span class="lbl">顶</span>';
    document.body.appendChild(btn);

    btn.addEventListener("click", function () {
      var quiet = window.matchMedia &&
        window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      window.scrollTo({ top: 0, behavior: quiet ? "auto" : "smooth" });
    });

    var visible = false;
    var ticking = false;
    function update() {
      var show = window.scrollY > 600;
      if (show !== visible) {
        visible = show;
        btn.classList.toggle("visible", show);
      }
      ticking = false;
    }
    window.addEventListener("scroll", function () {
      if (!ticking) {
        window.requestAnimationFrame(update);
        ticking = true;
      }
    }, { passive: true });
    update();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();

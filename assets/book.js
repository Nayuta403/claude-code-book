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
    initTopBtn();
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
      window.scrollTo({ top: 0, behavior: "smooth" });
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

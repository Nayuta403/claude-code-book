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
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();

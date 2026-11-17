/* Public trace page: copy buttons and print. Values come from data-copy attributes, never from innerHTML. */
(function () {
  "use strict";

  const live = document.getElementById("tr-copied");

  async function copy(text) {
    if (navigator.clipboard && window.isSecureContext) return navigator.clipboard.writeText(text);
    const t = document.createElement("textarea");
    t.value = text;
    t.setAttribute("readonly", "");
    t.style.position = "fixed";
    t.style.opacity = "0";
    document.body.append(t);
    t.select();
    try { document.execCommand("copy"); } finally { t.remove(); }
  }

  document.addEventListener("click", (e) => {
    const c = e.target.closest("[data-copy]");
    if (c) {
      copy(c.getAttribute("data-copy")).then(() => {
        c.classList.add("copied");
        if (live) live.textContent = "Copied";
        setTimeout(() => { c.classList.remove("copied"); if (live) live.textContent = ""; }, 1200);
      }).catch(() => { if (live) live.textContent = "Copy failed"; });
      return;
    }
    if (e.target.closest("[data-print]")) window.print();
  });
})();

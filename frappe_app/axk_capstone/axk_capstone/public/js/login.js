/* /login: sign-in form, demo account list, specimen strip. Server text goes in with textContent. */
(function () {
  "use strict";
  var root = document.getElementById("xl");
  if (!root) return;
  var form = document.getElementById("xl-form");
  var usr = document.getElementById("xl-usr");
  var pwd = document.getElementById("xl-pwd");
  var err = document.getElementById("xl-err");
  var go = document.getElementById("xl-go");
  var show = document.getElementById("xl-show");
  var params = new URLSearchParams(location.search);

  var CHECK = '<svg class="xt-i" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 6 9 17l-5-5"/></svg>';
  var DOT = '<svg class="xt-i" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="10"/></svg>';
  var ALERT = '<svg class="xt-i" xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="10"/><line x1="12" x2="12" y1="8" y2="12"/><line x1="12" x2="12.01" y1="16" y2="16"/></svg>';

  function csrf() {
    var t = window.frappe && window.frappe.csrf_token;
    return t && t !== "None" ? t : null;
  }
  function icon(svg) {
    var t = document.createElement("template");
    t.innerHTML = svg;
    return t.content.firstChild;
  }

  // Notches fill left to right on first load, 40ms apart.
  var reduce = window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches;
  document.querySelectorAll("#xl-specimen .xt-notch[data-fill]").forEach(function (n, i) {
    setTimeout(function () { n.classList.add("is-filled"); if (!reduce) n.classList.add("is-stamp"); }, reduce ? 0 : i * 40);
  });

  function setError(msg) {
    err.replaceChildren();
    if (msg) { err.append(icon(ALERT), document.createTextNode(msg)); }
    [usr, pwd].forEach(function (c) {
      c.classList.toggle("is-error", !!msg);
      if (msg) c.setAttribute("aria-invalid", "true"); else c.removeAttribute("aria-invalid");
    });
  }
  // Same-origin path only. The URL parser drops tabs and newlines, so "/\t/evil.com" would become "//evil.com":
  // refuse any control character, space or backslash, then confirm the resolved origin.
  function safeTarget(t) {
    if (!t || !/^\/(?![\/\\])[^\x00-\x20\x7f\\]*$/.test(t)) return null;
    // Resolving collapses dot segments ("/..//evil.com" -> "//evil.com"), so check the result's shape too.
    try {
      var u = new URL(t, location.origin), p = u.pathname + u.search + u.hash;
      return u.origin === location.origin && /^\/(?![\/\\])/.test(p) ? p : null;
    }
    catch (e) { return null; }
  }

  show.addEventListener("click", function () {
    var on = pwd.type === "password";
    pwd.type = on ? "text" : "password";
    show.textContent = on ? "Hide" : "Show";
    show.setAttribute("aria-pressed", on ? "true" : "false");
  });

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    if (!usr.value.trim() || !pwd.value) {
      setError("Enter your email and password.");
      (usr.value.trim() ? pwd : usr).focus();
      return;
    }
    setError(null);
    go.disabled = true;
    go.setAttribute("aria-busy", "true");
    go.textContent = "Signing in…";
    var headers = { Accept: "application/json", "Content-Type": "application/json" };
    if (csrf()) headers["X-Frappe-CSRF-Token"] = csrf();
    fetch("/api/method/login", { method: "POST", headers: headers, credentials: "same-origin", body: JSON.stringify({ usr: usr.value.trim(), pwd: pwd.value }) })
      .then(function (r) {
        return r.json().catch(function () { return {}; }).then(function (j) {
          if (!r.ok) throw new Error(r.status === 401 || r.status === 403 ? "Email or password is incorrect." : (j && j.message) || "Sign-in failed. Try again.");
          return j;
        });
      })
      .then(function (j) {
        location.href = safeTarget(params.get("redirect-to")) || safeTarget(j.home_page) || "/trade";
      })
      .catch(function (ex) {
        setError(ex.message || "Sign-in failed. Try again.");
        go.disabled = false;
        go.removeAttribute("aria-busy");
        go.textContent = "Sign in";
        pwd.focus();
        pwd.select();
      });
  });

  // Demo accounts: hidden when the list is empty or the call fails.
  var demo = document.getElementById("xl-demo");
  var list = document.getElementById("xl-list");
  fetch("/api/method/axk_capstone.demo.demo_accounts", { headers: { Accept: "application/json" } })
    .then(function (r) { if (!r.ok) throw new Error(); return r.json(); })
    .then(function (j) {
      var rows = (j && j.message) || [];
      if (!rows.length) return;
      var hasPw = rows.some(function (a) { return a.password; });
      document.getElementById("xl-hint").textContent = hasPw ? "Choose a role to fill the form." : "Choose a role to fill the email. Ask the organisers for the password.";
      rows.forEach(function (a) {
        var b = document.createElement("button");
        b.type = "button";
        b.className = "xl-acct";
        b.setAttribute("role", "listitem");
        b.setAttribute("aria-pressed", "false");
        var mark = document.createElement("span");
        mark.append(icon(DOT));
        var lbl = document.createElement("b");
        lbl.textContent = a.label;
        var duty = document.createElement("span");
        duty.className = "xl-duty";
        duty.textContent = a.organisation;
        var mail = document.createElement("span");
        mail.className = "xt-mono";
        mail.textContent = a.email;
        b.append(mark, lbl, duty, mail);
        b.addEventListener("click", function () {
          list.querySelectorAll(".xl-acct").forEach(function (x) {
            x.classList.remove("is-selected");
            x.setAttribute("aria-pressed", "false");
            x.firstChild.replaceChildren(icon(DOT));
          });
          b.classList.add("is-selected");
          b.setAttribute("aria-pressed", "true");
          mark.replaceChildren(icon(CHECK));
          usr.value = a.email;
          pwd.value = a.password || "";
          setError(null);
          (a.password ? go : pwd).focus();
        });
        list.append(b);
      });
      demo.hidden = false;
    })
    .catch(function () { /* demo list stays hidden */ });
})();

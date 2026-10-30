/* AXK Trade role screens: Overview, Cooperative, Inspector, Logistics, Port, Buyer, Lot detail.
 * Vanilla DOM. Everything from the server is inserted with textContent. Design contract: docs/design/DESIGN_SYSTEM.md. */
(function () {
  "use strict";

  // ---------------------------------------------------------------- icons (Lucide, ISC)
  var P = {
    "layout-grid": '<rect width="7" height="7" x="3" y="3" rx="1"/><rect width="7" height="7" x="14" y="3" rx="1"/><rect width="7" height="7" x="14" y="14" rx="1"/><rect width="7" height="7" x="3" y="14" rx="1"/>',
    sprout: '<path d="M7 20h10"/><path d="M10 20c5.5-2.5.8-6.4 3-10"/><path d="M9.5 9.4c1.1.8 1.8 2.2 2.3 3.7-2 .4-3.5.4-4.8-.3-1.2-.6-2.3-1.9-3-4.2 2.8-.5 4.4 0 5.5.8z"/><path d="M14.1 6a7 7 0 0 0-1.1 4c1.9-.1 3.3-.6 4.3-1.4 1-1 1.6-2.3 1.7-4.6-2.7.1-4 1-4.9 2z"/>',
    "clipboard-check": '<rect width="8" height="4" x="8" y="2" rx="1"/><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><path d="m9 14 2 2 4-4"/>',
    truck: '<path d="M14 18V6a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2v11a1 1 0 0 0 1 1h2"/><path d="M15 18H9"/><path d="M19 18h2a1 1 0 0 0 1-1v-3.65a1 1 0 0 0-.22-.624l-3.48-4.35A1 1 0 0 0 17.52 8H14"/><circle cx="17" cy="18" r="2"/><circle cx="7" cy="18" r="2"/>',
    anchor: '<circle cx="12" cy="5" r="3"/><path d="M12 22V8"/><path d="M5 12H2a10 10 0 0 0 20 0h-3"/>',
    wallet: '<path d="M19 7V4a1 1 0 0 0-1-1H5a2 2 0 0 0 0 4h15a1 1 0 0 1 1 1v4h-3a2 2 0 0 0 0 4h3a1 1 0 0 0 1-1v-2a1 1 0 0 0-1-1"/><path d="M3 5v14a2 2 0 0 0 2 2h15a1 1 0 0 0 1-1v-4"/>',
    "scan-line": '<path d="M3 7V5a2 2 0 0 1 2-2h2"/><path d="M17 3h2a2 2 0 0 1 2 2v2"/><path d="M21 17v2a2 2 0 0 1-2 2h-2"/><path d="M7 21H5a2 2 0 0 1-2-2v-2"/><path d="M7 12h10"/>',
    blocks: '<rect width="7" height="7" x="14" y="3" rx="1"/><path d="M10 21V8a1 1 0 0 0-1-1H4a1 1 0 0 0-1 1v12a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-5a1 1 0 0 0-1-1H3"/>',
    "circle-dashed": '<path d="M10.1 2.182a10 10 0 0 1 3.8 0"/><path d="M13.9 21.818a10 10 0 0 1-3.8 0"/><path d="M17.609 3.721a10 10 0 0 1 2.69 2.7"/><path d="M2.182 13.9a10 10 0 0 1 0-3.8"/><path d="M20.279 17.609a10 10 0 0 1-2.7 2.69"/><path d="M21.818 10.1a10 10 0 0 1 0 3.8"/><path d="M3.721 6.391a10 10 0 0 1 2.7-2.69"/><path d="M6.391 20.279a10 10 0 0 1-2.69-2.7"/>',
    "badge-check": '<path d="M3.85 8.62a4 4 0 0 1 4.78-4.77 4 4 0 0 1 6.74 0 4 4 0 0 1 4.78 4.78 4 4 0 0 1 0 6.74 4 4 0 0 1-4.77 4.78 4 4 0 0 1-6.75 0 4 4 0 0 1-4.78-4.77 4 4 0 0 1 0-6.76Z"/><path d="m9 12 2 2 4-4"/>',
    "circle-x": '<circle cx="12" cy="12" r="10"/><path d="m15 9-6 6"/><path d="m9 9 6 6"/>',
    "circle-check": '<circle cx="12" cy="12" r="10"/><path d="m9 12 2 2 4-4"/>',
    "circle-alert": '<circle cx="12" cy="12" r="10"/><line x1="12" x2="12" y1="8" y2="12"/><line x1="12" x2="12.01" y1="16" y2="16"/>',
    lock: '<rect width="18" height="11" x="3" y="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>',
    "undo-2": '<path d="M9 14 4 9l5-5"/><path d="M4 9h10.5a5.5 5.5 0 0 1 5.5 5.5a5.5 5.5 0 0 1-5.5 5.5H11"/>',
    "arrow-up-right": '<path d="M7 7h10v10"/><path d="M7 17 17 7"/>',
    "arrow-right": '<path d="M5 12h14"/><path d="m12 5 7 7-7 7"/>',
    copy: '<rect width="14" height="14" x="8" y="8" rx="2" ry="2"/><path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/>',
    check: '<path d="M20 6 9 17l-5-5"/>',
    inbox: '<polyline points="22 12 16 12 14 15 10 15 8 12 2 12"/><path d="M5.45 5.11 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"/>',
    "mouse-pointer-click": '<path d="M14 4.1 12 6"/><path d="m5.1 8-2.9-.8"/><path d="m6 12-1.9 2"/><path d="M7.2 2.2 8 5.1"/><path d="M9.037 9.69a.498.498 0 0 1 .653-.653l11 4.5a.5.5 0 0 1-.074.949l-4.349 1.041a1 1 0 0 0-.74.739l-1.04 4.35a.5.5 0 0 1-.95.074z"/>',
    shield: '<path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/>',
    "shield-check": '<path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/><path d="m9 12 2 2 4-4"/>',
    "shield-x": '<path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/><path d="m14.5 9.5-5 5"/><path d="m9.5 9.5 5 5"/>',
    download: '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" x2="12" y1="15" y2="3"/>',
    users: '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>'
  };
  var tpl = document.createElement("template");
  function icon(name, size) {
    var s = size || 16;
    tpl.innerHTML = '<svg class="xt-i" xmlns="http://www.w3.org/2000/svg" width="' + s + '" height="' + s + '" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">' + (P[name] || "") + "</svg>";
    return tpl.content.firstChild;
  }
  window.AXK_ICON = icon;

  var root = document.getElementById("xt-trade");
  if (!root) return;
  var PAGE = root.getAttribute("data-page");
  var main = document.getElementById("xt-main");
  var API = "/api/method/axk_capstone.trade_api.";
  var EXPLORER = "https://stellar.expert/explorer/testnet";
  var META = { reject_reasons: [] };
  var STEPS = ["Registered", "Inspected", "Escrow funded", "Dispatched", "At port", "Released", "Split 40/40/20", "Members paid", "Attested"];
  var ROLE_OF_PAGE = { coop: "coop", inspect: "inspector", logistics: "logistics", port: "port", buy: "buyer" };
  var ROLE_NAME = { coop: "Cooperative", inspector: "Inspector", logistics: "Logistics", port: "Port", buyer: "Buyer" };

  // ---------------------------------------------------------------- helpers
  var nf = new Intl.NumberFormat("en-US");
  var nf1 = new Intl.NumberFormat("en-US", { maximumFractionDigits: 1 });
  var NONE = "–";
  function rwf(v) { return v == null ? NONE : nf.format(Math.round(v)) + " RWF"; }
  function kg(v) { return v == null ? NONE : nf.format(Math.round(v)) + " kg"; }
  function short(h, a, b) { return h ? (h.length <= (a || 6) + (b || 6) + 1 ? h : h.slice(0, a || 6) + "…" + h.slice(-(b || 6))) : NONE; }
  function when(s) {
    if (!s || s === "None") return NONE;
    var d = new Date(String(s).replace(" ", "T"));
    return isNaN(d) ? s : d.toLocaleString("en-GB", { day: "numeric", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" });
  }

  function el(tag, props) {
    var n = document.createElement(tag);
    var kids = Array.prototype.slice.call(arguments, 2);
    Object.keys(props || {}).forEach(function (k) {
      var v = props[k];
      if (v === undefined || v === null || v === false) return;
      if (k === "class") n.className = v;
      else if (k === "text") n.textContent = v;
      else if (k === "on") Object.keys(v).forEach(function (ev) { n.addEventListener(ev, v[ev]); });
      else n.setAttribute(k, v === true ? "" : v);
    });
    (function add(list) {
      list.forEach(function (kid) {
        if (kid == null || kid === false) return;
        if (Array.isArray(kid)) add(kid);
        else n.append(kid instanceof Node ? kid : document.createTextNode(String(kid)));
      });
    })(kids);
    return n;
  }
  function withIcon(name, label, size) { return [icon(name, size), label]; }

  function csrf() {
    var t = window.frappe && window.frappe.csrf_token;
    return t && t !== "None" ? t : null;
  }

  function serverMessage(j, status) {
    try {
      if (j && j._server_messages) {
        return JSON.parse(j._server_messages).map(function (m) {
          try { return JSON.parse(m).message; } catch (e) { return m; }
        }).join(" ").replace(/<[^>]+>/g, "");
      }
      if (j && j.exception) return String(j.exception).split(":").slice(-1)[0].trim();
    } catch (e) { /* fall through */ }
    return "Request failed (" + status + ")";
  }

  function api(method, params, post) {
    var url = API + method;
    var opts = { headers: { Accept: "application/json" } };
    if (post) {
      opts.method = "POST";
      opts.headers["Content-Type"] = "application/json";
      if (csrf()) opts.headers["X-Frappe-CSRF-Token"] = csrf();
      opts.body = JSON.stringify(params || {});
    } else if (params) {
      url += "?" + new URLSearchParams(params);
    }
    return fetch(url, opts).then(function (r) {
      return r.json().catch(function () { return {}; }).then(function (j) {
        if (!r.ok) throw new Error(serverMessage(j, r.status));
        return j.message;
      });
    });
  }

  // The standalone runner (scripts/server.py) reports network "offline-simulation": nothing
  // is sent to Stellar there, so the screens must not say they are signing on-chain.
  function isSim() { return META && META.network === "offline-simulation"; }
  // In the offline simulation nothing is signed, so "on-chain" wording becomes "(simulated)".
  function chainLabel(text) { return isSim() ? text.replace(" on-chain", " (simulated)") : text; }

  var busy = document.getElementById("xt-busy");
  function withBusy(title, text, promise) {
    if (isSim()) { title = "Simulating (offline)"; text = "Offline simulation: nothing is sent to Stellar. Run make run-frappe for real testnet transactions."; }
    document.getElementById("xt-busy-title").textContent = title;
    document.getElementById("xt-busy-text").textContent = text + (isSim() ? "" : " Usually 5 to 8 seconds.");
    busy.hidden = false;
    return promise.finally(function () { busy.hidden = true; });
  }

  // A submit button in the busy state keeps its width and reads "Signing...".
  function btnBusy(btn, on) {
    if (on) {
      btn._kids = Array.prototype.slice.call(btn.childNodes);
      btn.style.minWidth = btn.offsetWidth + "px";
      btn.setAttribute("aria-busy", "true");
      btn.replaceChildren(el("span", { class: "xt-spin", "aria-hidden": "true" }), "Signing…");
    } else if (btn._kids) {
      btn.removeAttribute("aria-busy");
      btn.style.minWidth = "";
      btn.replaceChildren.apply(btn, btn._kids);
      btn._kids = null;
    }
  }

  var toastT;
  var toastEl = document.getElementById("xt-toast");
  function toast(msg, isError, link) {
    toastEl.replaceChildren(icon(isError ? "circle-alert" : "circle-check", 16), el("div", {}, msg, link ? [" ", el("a", { href: link.href, target: link.external ? "_blank" : null, rel: "noopener" }, link.text, " ", icon("arrow-up-right", 12))] : null));
    toastEl.className = "xt-toast" + (isError ? " error" : "");
    toastEl.hidden = false;
    clearTimeout(toastT);
    toastT = setTimeout(function () { toastEl.hidden = true; }, isError ? 9000 : 6000);
  }
  toastEl.addEventListener("mouseenter", function () { clearTimeout(toastT); });
  toastEl.addEventListener("mouseleave", function () { toastT = setTimeout(function () { toastEl.hidden = true; }, 3000); });

  function fail(e, box) {
    var msg = e && e.message ? e.message : String(e);
    if (box) box.replaceChildren(icon("circle-alert", 14), msg);
    toast(msg, true);
  }

  // ---------------------------------------------------------------- status tag
  var STATUS = {
    Registered: ["", "circle-dashed", "Awaiting inspection"],
    Approved: ["approved", "badge-check", "Passed inspection"],
    Rejected: ["rejected", "circle-x", "Rejected at inspection"],
    Funded: ["", "lock", "In escrow"],
    "In Transit": ["", "truck", "In transit"],
    "At Port": ["", "anchor", "At port"],
    Settled: ["settled", "circle-check", "Settled"],
    Refunded: ["refunded", "undo-2", "Refunded"]
  };
  function tag(status) {
    var s = STATUS[status] || ["", "circle-dashed", status];
    return el("span", { class: "xt-tag" + (s[0] ? " " + s[0] : "") }, icon(s[1], 14), s[2]);
  }

  // ---------------------------------------------------------------- custody strip
  // A notch is filled if and only if its step has a transaction hash.
  var SEEN = {};
  function stripState(txs, failed) {
    var out = [], nextSet = false;
    STEPS.forEach(function (_, i) {
      var has = !!(txs && txs[i]);
      if (failed && i > 1) out.push("void");
      else if (failed && i === 1) out.push("failed");
      else if (has) out.push("filled");
      else if (!nextSet) { out.push("next"); nextSet = true; }
      else out.push("pending");
    });
    return out;
  }
  function filledCount(txs) { return (txs || []).filter(Boolean).length; }
  function stampIndexes(key, txs) {
    var now = STEPS.map(function (_, i) { return !!(txs && txs[i]); });
    var prev = key ? SEEN[key] : null;
    if (key) SEEN[key] = now;
    return prev ? now.map(function (v, i) { return v && !prev[i]; }) : now.map(function () { return false; });
  }
  function notchEl(state, stamp) {
    return el("i", { class: "xt-notch" + (state === "pending" ? "" : " is-" + state) + (stamp ? " is-stamp" : "") });
  }
  function currentLabel(states) {
    var i = states.indexOf("next");
    return i >= 0 ? "Next: " + STEPS[i] : (states.indexOf("failed") >= 0 ? "Stopped at inspection" : "All steps on-chain");
  }
  function txUrl(h) { return isSim() ? null : EXPLORER + "/tx/" + h; }

  function microStrip(r) {
    if (!r.txs) return NONE;
    var failed = r.status === "Rejected";
    var st = stripState(r.txs, failed), n = filledCount(r.txs);
    var stamps = stampIndexes(r.name, r.txs);
    return el("span", { class: "xt-strip", role: "img", "aria-label": "Custody: " + n + " of 9 steps on-chain. " + currentLabel(st) + "." },
      el("span", { class: "xt-notches", "aria-hidden": "true" }, st.map(function (s, i) { return notchEl(s, stamps[i]); })),
      el("span", { class: "xt-strip-n", "aria-hidden": "true", text: n + "/9" }));
  }

  // Standard strip: labelled in the lot header, label-less with one status line in the docket.
  function bigStrip(txs, o) {
    o = o || {};
    if (!txs) return null;
    var st = stripState(txs, o.failed), n = filledCount(txs);
    var stamps = stampIndexes(o.key, txs);
    var wrap = el("div", { class: "xt-strip-lg" + (o.compact ? " is-compact" : ""), role: "group", "aria-label": "Custody: " + n + " of 9 steps on-chain. " + currentLabel(st) + "." },
      el("div", { class: "xt-notches" }, st.map(function (s, i) {
        var filled = s === "filled" || (s === "failed" && txs[i]);
        var url = (o.urls && o.urls[i]) || (txs[i] ? txUrl(txs[i]) : null);
        var label = STEPS[i];
        var inner = [notchEl(s, stamps[i]), o.compact ? null : el("span", { class: "xt-lbl", text: label })];
        if (filled && url) {
          return el("a", { class: "xt-cell is-filled", href: url, target: "_blank", rel: "noopener",
            "aria-label": label + ", transaction " + short(txs[i]) + ", opens Stellar Expert" }, inner);
        }
        return el("div", { class: "xt-cell" + (filled ? " is-filled" : "") }, inner);
      })));
    if (o.compact) {
      wrap.append(el("div", { class: "xt-strip-lbls" }, el("b", { text: currentLabel(st) }), el("span", { text: n + "/9 on-chain" })));
    }
    return wrap;
  }

  // ---------------------------------------------------------------- tx refs, ledger strip, panels
  function copyBtn(value, label) {
    var live = el("span", { class: "xt-sr", role: "status" });
    var b = el("button", { class: "xt-ic-btn", type: "button", "aria-label": "Copy " + label, title: "Copy" }, icon("copy", 14));
    b.addEventListener("click", function () {
      (navigator.clipboard ? navigator.clipboard.writeText(value) : Promise.reject()).then(function () {
        b.replaceChildren(icon("check", 14)); live.textContent = "Copied";
        setTimeout(function () { b.replaceChildren(icon("copy", 14)); live.textContent = ""; }, 1200);
      }, function () { toast("Copy is not available here. Select the value and copy it by hand.", true); });
    });
    return [b, live];
  }
  // kind: tx | account | contract. url overrides the derived explorer link.
  function txref(hash, kind, o) {
    o = o || {};
    if (!hash) return el("span", { class: "xt-muted", text: NONE });
    kind = kind || "tx";
    var url = o.url !== undefined ? o.url : (isSim() ? null : (o.explorer || EXPLORER) + "/" + kind + "/" + hash);
    var txt = kind === "tx" ? short(hash, 6, 6) : short(hash, 4, 4);
    var name = kind === "tx" ? "transaction" : kind;
    var main = url
      ? el("a", { class: "xt-mono", href: url, target: "_blank", rel: "noopener", title: hash, "aria-label": name + " " + hash + ", opens Stellar Expert" }, txt)
      : el("span", { class: "xt-mono", title: hash, text: txt + (isSim() ? " (simulated)" : "") });
    return el("span", { class: "xt-txref" }, main, url ? el("span", { class: "xt-ic-btn", "aria-hidden": "true" }, icon("arrow-up-right", 14)) : null, o.copy ? copyBtn(hash, name) : null);
  }
  function digest(h) {
    if (!h) return el("span", { class: "xt-muted", text: NONE });
    return el("div", { class: "xt-digest" }, el("span", { class: "xt-mono", text: h }), copyBtn(h, "digest"));
  }

  function ledger(cells) {
    return el("div", { class: "xt-ledger", role: "group", "aria-label": "Summary" }, cells.map(function (c) {
      return el("div", {}, el("span", { class: "xt-lbl", text: c.label }), el("span", { class: "xt-fig" }, c.value, c.unit ? el("small", { text: c.unit }) : null));
    }));
  }
  function ledgerRwf(v) { return v == null ? { value: NONE } : { value: nf.format(Math.round(v)), unit: "RWF" }; }

  function head(title, sub, right) {
    return el("div", { class: "xt-head" }, el("div", {}, el("h1", { text: title }), sub ? el("p", { text: sub }) : null), right ? el("div", { class: "xt-head-actions" }, right) : null);
  }
  function empty(iconName, title, sub, action) {
    return el("div", { class: "xt-empty" }, icon(iconName || "inbox", 20), el("b", { text: title }), sub ? el("span", { text: sub }) : null, action || null);
  }
  function setMain() { main.replaceChildren.apply(main, Array.prototype.filter.call(arguments, Boolean)); }

  function lotLink(r) { return "/trade/lot?name=" + encodeURIComponent(r.name); }
  function shareLink(r) { return location.origin + "/trace/lot?ref=" + encodeURIComponent(r.lot_ref); }
  function nextAction(r) {
    return ({ Registered: "Waiting for an inspector", Approved: "Waiting for a buyer", Rejected: r.reject_reason || "Rejected at inspection",
      Funded: "Ready to dispatch", "In Transit": "Waiting for port gate-in", "At Port": "Waiting for delivery confirmation",
      Settled: "Paid and attested", Refunded: "Refunded to the buyer" })[r.status] || "";
  }

  // ---------------------------------------------------------------- lot table
  var LOT_COLS = [
    { cls: "c-lot", label: "Lot", get: function (r) { return el("a", { class: "xt-lotref", href: lotLink(r), text: r.lot_ref }); } },
    { cls: "c-com", label: "Commodity", get: function (r) { return r.commodity; } },
    { cls: "c-qty num", label: "Qty", num: true, get: function (r) { return kg(r.inspected_quantity_kg || r.quantity_kg); } },
    { cls: "c-cus", label: "Custody", get: microStrip },
    { cls: "c-st", label: "Status", get: function (r) { return tag(r.status); } },
    { cls: "c-next", label: "Next", get: function (r) { var t = nextAction(r); return el("span", { title: t, text: t }); } }
  ];
  function lotTable(rows, o) {
    o = o || {};
    var cols = o.cols || LOT_COLS;
    return el("div", { class: "xt-tablewrap" }, el("table", { class: "xt-table" },
      el("thead", {}, el("tr", {}, cols.map(function (c) { return el("th", { class: c.num ? "num" : null, scope: "col", text: c.label }); }))),
      el("tbody", {}, rows.map(function (r) {
        var pick = function () { o.onPick(r); };
        var tr = el("tr", { class: "is-row" + (r.name === o.selected ? " is-selected" : ""), tabindex: "0", "data-name": r.name, "aria-current": r.name === o.selected ? "true" : null });
        cols.forEach(function (c) {
          var v = c.get(r);
          tr.append(el("td", { class: c.cls }, v instanceof Node ? v : (v == null ? NONE : String(v))));
        });
        tr.addEventListener("click", function (e) { if (!e.target.closest("a,button")) pick(); });
        tr.addEventListener("keydown", function (e) { if ((e.key === "Enter" || e.key === " ") && e.target === tr) { e.preventDefault(); pick(); } });
        return tr;
      }))));
  }
  function openLot(r) { location.href = lotLink(r); }

  // ---------------------------------------------------------------- form controls
  function field(label, control, hint) {
    var err = el("div", { class: "xt-err", id: (control.id || "f") + "-err", "aria-live": "polite" });
    var wrap = el("div", { class: "xt-field" }, el("label", { for: control.id || null, text: label }), control, hint ? el("small", { text: hint }) : null, err);
    wrap.setErr = function (msg) {
      err.replaceChildren.apply(err, msg ? [icon("circle-alert", 14), msg] : []);
      control.classList.toggle("is-error", !!msg);
      if (msg) { control.setAttribute("aria-invalid", "true"); control.setAttribute("aria-describedby", err.id); }
      else { control.removeAttribute("aria-invalid"); control.removeAttribute("aria-describedby"); }
    };
    wrap.control = control;
    return wrap;
  }
  function input(id, attrs) { return el("input", Object.assign({ id: id, class: "xt-input" }, attrs || {})); }
  // Validate on submit: the first empty required control gets the error and focus.
  function validate(fields) {
    var bad = null;
    fields.forEach(function (f) {
      var c = f.control, missing = c.required && !String(c.value).trim();
      f.setErr(missing ? "Required." : null);
      if (missing && !bad) bad = c;
    });
    if (bad) bad.focus();
    return !bad;
  }

  // A segmented control (radiogroup) with a .value getter/setter, so forms read it like any other control.
  function seg(name, label, options, value) {
    var group = el("fieldset", { class: "xt-seg", "aria-label": label });
    options.forEach(function (o) {
      group.append(el("label", {}, el("input", { type: "radio", name: name, value: o, checked: o === value ? true : null }), el("span", { text: o })));
    });
    Object.defineProperty(group, "value", {
      get: function () { var c = group.querySelector("input:checked"); return c ? c.value : ""; },
      set: function (v) { group.querySelectorAll("input").forEach(function (i) { i.checked = i.value === v; }); }
    });
    return group;
  }
  function segField(label, group, hint) {
    return el("div", { class: "xt-field" }, el("span", { class: "xt-field-label", text: label }), group, hint ? el("small", { text: hint }) : null);
  }
  function select(id, options, value) {
    var s = el("select", { id: id, class: "xt-input" }, options.map(function (o) { return el("option", { value: o, selected: o === value ? true : null, text: o }); }));
    return s;
  }

  function kv(rows) {
    var dl = el("dl", { class: "xt-kv" });
    rows.forEach(function (r) { if (r) dl.append(el("dt", { text: r[0] }), el("dd", {}, r[1] instanceof Node || Array.isArray(r[1]) ? r[1] : (r[1] == null ? NONE : String(r[1])))); });
    return dl;
  }

  // Confirm dialog replacing window.confirm. Resolves true on confirm.
  function confirmDialog(o) {
    return new Promise(function (resolve) {
      var dlg = el("dialog", { class: "xt-dialog", "aria-labelledby": "c-title" });
      var done = false;
      var finish = function (v) { done = true; dlg.close(); resolve(v); };
      dlg.append(el("form", { method: "dialog", on: { submit: function (e) { e.preventDefault(); finish(true); } } },
        el("h2", { id: "c-title", text: o.title }),
        el("p", { text: o.text }),
        el("div", { class: "xt-dialog-actions" },
          el("button", { class: "xt-btn secondary", type: "button", text: "Cancel", on: { click: function () { finish(false); } } }),
          el("button", { class: "xt-btn" + (o.danger ? " danger" : ""), type: "submit", text: o.confirm }))));
      dlg.addEventListener("close", function () { dlg.remove(); if (!done) resolve(false); });
      root.append(dlg);
      dlg.showModal();
    });
  }

  // ---------------------------------------------------------------- personas
  var PERSONAS = null;
  function persona(key) { return (PERSONAS || []).filter(function (p) { return p.key === key; })[0]; }
  function railPersona() {
    var key = ROLE_OF_PAGE[PAGE], p = key && persona(key);
    var name = document.getElementById("xt-persona-name"), addr = document.getElementById("xt-persona-addr");
    if (!name || !addr) return;
    if (p) {
      name.textContent = p.name + " (" + ROLE_NAME[key] + ")";
      addr.replaceChildren(p.address ? el("a", { class: "xt-persona-addr", href: EXPLORER + "/account/" + p.address, target: "_blank", rel: "noopener", title: p.address, "aria-label": "Stellar account " + p.address }, short(p.address, 4, 4), icon("arrow-up-right", 12)) : "");
    }
  }
  function signsLine(fn, where, key) {
    if (isSim()) return "Simulated: nothing is sent to Stellar.";
    var p = persona(key);
    return "Signs " + fn + " on " + where + " as " + ROLE_NAME[key] + (p && p.address ? " " + short(p.address, 4, 4) : "") + ".";
  }

  // ---------------------------------------------------------------- docket
  var LOTCACHE = {};
  function docketShell(tagName, title, bodyKids, footKids, props) {
    return el(tagName, Object.assign({ class: "xt-docket" }, props || {}),
      el("div", { class: "xt-docket-body" }, el("h2", { text: title }), bodyKids),
      footKids ? el("div", { class: "xt-docket-foot" }, footKids) : null);
  }
  function docketEmpty(text, sub) {
    return el("aside", { class: "xt-docket is-empty" }, empty("mouse-pointer-click", text, sub));
  }
  // The selected lot's ref, its standard custody strip and a two-row summary.
  function lotHeader(l) {
    return [el("div", { class: "xt-lotref-lg", text: l.lot_ref }),
      bigStrip(l.txs, { key: l.name, compact: true, failed: l.status === "Rejected" }),
      kv([["Commodity", l.commodity + " · " + kg(l.inspected_quantity_kg || l.quantity_kg)], ["Origin", l.origin]])];
  }
  function summaryDocket(l) {
    return docketShell("aside", "Lot " + l.status.toLowerCase(), [
      lotHeader(l), el("div", {}, tag(l.status)), el("p", { class: "xt-small", text: nextAction(l) })],
      [el("a", { class: "xt-btn secondary block", href: lotLink(l) }, "Open lot", icon("arrow-right", 16))]);
  }
  // Wraps an action: busy button, signing overlay, inline docket error, stamp-in on refresh.
  function sign(btn, errBox, title, text, promise, ok) {
    errBox.replaceChildren();
    btnBusy(btn, true);
    withBusy(title, text, promise).then(ok).catch(function (e) { fail(e, errBox); }).finally(function () { btnBusy(btn, false); });
  }
  function txToast(prefix, lot, stepIndex) {
    var s = lot.steps && lot.steps[stepIndex];
    toast(prefix, false, s && s.url ? { href: s.url, text: "View transaction", external: true } : null);
  }

  // ---------------------------------------------------------------- role screen engine
  // cfg: {st:{tab,sel}, title, sub, cells, tabs:[{label,rows,node?,emptyTitle,emptySub}], docket(row), idle(), auto}
  var activeScreen = null;
  function roleScreen(cfg) {
    var st = cfg.st;
    cfg.tabs.forEach(function (t, i) { t.rows = t.rows || []; t.i = i; });
    if (st.sel) {
      var hit = cfg.tabs.filter(function (t) { return t.rows.some(function (r) { return r.name === st.sel; }); })[0];
      if (hit) { if (!hit.node || st.tab !== hit.i) st.tab = hit.i; } else st.sel = null;
    }
    var tab = function () { return cfg.tabs[st.tab]; };
    if (!st.sel && cfg.auto && tab().rows.length) st.sel = tab().rows[0].name;
    var rowOf = function (n) { var f = null; cfg.tabs.forEach(function (t) { t.rows.forEach(function (r) { if (r.name === n) f = r; }); }); return f; };

    var panelBody = el("div", { class: "xt-tablewrap" });
    var docketSlot = el("div", { class: "xt-docket-slot" });
    var tabs = el("div", { class: "xt-tabs", role: "tablist" });

    function drawTabs() {
      tabs.replaceChildren.apply(tabs, cfg.tabs.map(function (t) {
        var b = el("button", { type: "button", role: "tab", "aria-selected": t.i === st.tab ? "true" : "false", tabindex: t.i === st.tab ? "0" : "-1", id: "tab-" + t.i,
          on: { click: function () { st.tab = t.i; if (cfg.auto && !t.node && t.rows.length && !t.rows.some(function (r) { return r.name === st.sel; })) st.sel = t.rows[0].name; drawTabs(); drawPanel(); drawDocket(); } } },
          t.label, t.node ? null : el("span", { class: "xt-tab-n", text: String(t.rows.length) }));
        b.addEventListener("keydown", function (e) {
          if (e.key !== "ArrowRight" && e.key !== "ArrowLeft") return;
          var n = (t.i + (e.key === "ArrowRight" ? 1 : cfg.tabs.length - 1)) % cfg.tabs.length;
          tabs.children[n].click(); tabs.children[n].focus();
        });
        return b;
      }));
      if (cfg.auto) tabs.append(el("span", { class: "xt-queue-hint" }, "Keys ", el("kbd", { text: "j" }), " ", el("kbd", { text: "k" }), cfg.keyHint || ""));
    }
    function pick(r) {
      st.sel = r.name;
      panelBody.querySelectorAll("tr.is-row").forEach(function (tr) {
        var on = tr.getAttribute("data-name") === r.name;
        tr.classList.toggle("is-selected", on);
        if (on) tr.setAttribute("aria-current", "true"); else tr.removeAttribute("aria-current");
      });
      drawDocket();
    }
    function drawPanel() {
      var t = tab(), body;
      if (t.node) body = t.node;
      else if (!t.rows.length) body = empty("inbox", t.emptyTitle || "Nothing here.", t.emptySub, t.emptyAction);
      else body = lotTable(t.rows, { selected: st.sel, onPick: pick });
      panelBody.replaceWith(body);
      panelBody = body;
      panelBody.setAttribute("role", "tabpanel");
      panelBody.setAttribute("aria-labelledby", "tab-" + st.tab);
    }
    function drawDocket() {
      var r = st.sel && rowOf(st.sel);
      var d = r ? cfg.docket(r) : (cfg.idle ? cfg.idle() : docketEmpty(cfg.idleTitle || "Select a lot.", cfg.idleSub));
      docketSlot.replaceChildren(d);
    }
    drawTabs();
    var panel = el("section", { class: "xt-panel", "aria-label": cfg.title + " queue" }, tabs, panelBody);
    var work = el("div", { class: "xt-work" }, panel, docketSlot);
    setMain(head(cfg.title, cfg.sub, cfg.right), ledger(cfg.cells), work);
    drawPanel();
    drawDocket();

    activeScreen = {
      move: function (d) {
        var t = tab(); if (!t.rows.length) return;
        var i = Math.max(0, t.rows.findIndex(function (r) { return r.name === st.sel; }));
        var n = Math.max(0, Math.min(t.rows.length - 1, i + d));
        pick(t.rows[n]);
        var tr = panelBody.querySelector('tr[data-name="' + (window.CSS && CSS.escape ? CSS.escape(t.rows[n].name) : t.rows[n].name) + '"]');
        if (tr && tr.scrollIntoView) tr.scrollIntoView({ block: "nearest" });
      },
      cfg: cfg
    };
  }
  document.addEventListener("keydown", function (e) {
    if (!activeScreen || !activeScreen.cfg.auto || e.metaKey || e.ctrlKey || e.altKey) return;
    var t = e.target;
    if (t && t.closest && t.closest("input:not([type=radio]),textarea,select,[contenteditable],dialog")) return;
    if (e.key === "j") { e.preventDefault(); activeScreen.move(1); }
    else if (e.key === "k") { e.preventDefault(); activeScreen.move(-1); }
    else if (activeScreen.cfg.keys && activeScreen.cfg.keys[e.key]) { e.preventDefault(); activeScreen.cfg.keys[e.key](); }
  });

  // ---------------------------------------------------------------- overview
  function renderOverview(data) {
    var lots = data.lots, c = data.counts;
    var settledValue = lots.filter(function (l) { return l.status === "Settled"; }).reduce(function (a, l) { return a + (l.amount_rwf || 0); }, 0);
    var stations = [
      { href: "/trade/coop", icon: "sprout", title: "Cooperative", n: c.Registered || 0, sub: "awaiting inspection" },
      { href: "/trade/inspect", icon: "clipboard-check", title: "Inspector", n: c.Registered || 0, sub: "in the queue" },
      { href: "/trade/logistics", icon: "truck", title: "Logistics", n: (c.Funded || 0) + (c.Approved || 0), sub: "ready to dispatch" },
      { href: "/trade/port", icon: "anchor", title: "Port", n: c["In Transit"] || 0, sub: "in transit to port" },
      { href: "/trade/buy", icon: "wallet", title: "Buyer", n: (c.Approved || 0) + (c["At Port"] || 0), sub: "to fund or settle" },
      { href: "/trace", icon: "scan-line", title: "Verify", n: c.Settled || 0, sub: "settled and public" }
    ];
    setMain(
      head("Overview", chainLabel("Nine steps from cooperative to buyer. Each one is a Soroban contract call."),
        el("a", { class: "xt-btn secondary", href: "/chain" }, icon("blocks", 16), "Open chain explorer")),
      ledger([
        { label: "Lots registered", value: String(lots.length) },
        { label: "Awaiting inspection", value: String(c.Registered || 0) },
        { label: "In escrow", value: String(c.Funded || 0) },
        { label: "In transit", value: String(c["In Transit"] || 0) },
        Object.assign({ label: "Settled value" }, ledgerRwf(settledValue))]),
      el("nav", { class: "xt-flow", "aria-label": "Roles" }, stations.map(function (s) {
        return el("a", { class: "xt-station", href: s.href }, icon(s.icon, 16), el("b", { text: s.title }), el("span", { class: "xt-fig", text: String(s.n) }),
          el("span", { class: "xt-sub", text: s.sub }), el("span", { class: "xt-open" }, "Open", icon("arrow-right", 14)));
      })),
      el("section", { class: "xt-panel xt-grow xt-section-gap", "aria-label": "Recent lots" },
        el("div", { class: "xt-panel-head" }, el("h2", { text: "Recent lots" }), el("p", { text: "Open a lot for its custody timeline." })),
        lots.length ? lotTable(lots.slice(0, 6), { onPick: openLot }) : empty("inbox", "No live lots yet.", "Start as the Cooperative and register one.",
          el("a", { class: "xt-btn ghost", href: "/trade/coop" }, "Go to Cooperative"))));
  }

  // ---------------------------------------------------------------- cooperative
  var coopSt = { tab: 0, sel: null };
  function renderCoop(data) {
    var lots = data.lots, me = persona("coop");
    var count = function (s) { return lots.filter(function (l) { return l.status === s; }).length; };
    var settledValue = lots.filter(function (l) { return l.status === "Settled"; }).reduce(function (a, l) { return a + (l.amount_rwf || 0); }, 0);
    roleScreen({
      st: coopSt, title: "Cooperative", sub: "Register lots and follow them through inspection and escrow.",
      cells: [{ label: "Lots registered", value: String(lots.length) }, { label: "Awaiting inspection", value: String(count("Registered")) },
        { label: "Listed for sale", value: String(count("Approved")) }, { label: "In escrow", value: String(count("Funded")) },
        Object.assign({ label: "Settled value" }, ledgerRwf(settledValue))],
      tabs: [{ label: "My lots", rows: lots, emptyTitle: "No lots yet.", emptySub: "Register your first lot with the form." }],
      docket: function (l) {
        var d = summaryDocket(l);
        d.querySelector(".xt-docket-foot").prepend(el("button", { class: "xt-btn ghost block", type: "button", text: "Register another lot", on: { click: function () { coopSt.sel = null; renderCoop(data); } } }));
        return d;
      },
      idle: function () { return registerDocket(data); }
    });
  }
  function registerDocket(data) {
    var commodity = seg("f-commodity", "Commodity", data.commodities, data.commodities[0]);
    var grade = seg("f-grade", "Declared grade", data.grades, "A");
    var qty = input("f-qty", { type: "number", min: "1", max: "100000", step: "1", value: "3850", required: true, inputmode: "numeric" });
    var variety = input("f-variety", { placeholder: "e.g. Bourbon Mayaguez 139", maxlength: "60" });
    var origin = input("f-origin", { value: "Huye, Southern Province", required: true, maxlength: "80" });
    var harvest = input("f-harvest", { type: "date", value: new Date().toISOString().slice(0, 10) });
    var fQty = field("Quantity (kg)", qty), fOrigin = field("Origin", origin);
    var err = el("div", { class: "xt-docket-err", role: "alert" });
    var submit = el("button", { class: "xt-btn block", type: "submit", text: chainLabel("Register lot on-chain") });
    return docketShell("form", "Register a lot", [
      segField("Commodity", commodity), segField("Declared grade", grade),
      el("div", { class: "xt-row" }, fQty, field("Harvest date", harvest)), fOrigin, field("Variety", variety, "Optional"),
      el("p", { class: "xt-note", text: "Only a SHA-256 digest of this record goes on-chain. The record stays here, so a buyer can check it later without the ledger holding your data." })],
      [err, submit, el("div", { class: "xt-signs", text: signsLine("register", "the lot registry", "coop") })],
      { on: { submit: function (e) {
        e.preventDefault();
        if (!validate([fQty, fOrigin])) return;
        sign(submit, err, "Registering the lot", "The cooperative signs a commitment to this lot record in the lot registry.",
          api("register_lot", { commodity: commodity.value, quantity_kg: qty.value, declared_grade: grade.value, origin: origin.value, variety: variety.value, harvest_date: harvest.value }, true),
          function (lot) { coopSt.sel = lot.name; txToast("Registered " + lot.lot_ref + ". It is now in the inspector's queue.", lot, 0); return refresh(); });
      } } });
  }

  // ---------------------------------------------------------------- inspector
  var inspSt = { tab: 0, sel: null };
  var decideHook = null;
  function renderInspect(data) {
    var queue = data.lots.filter(function (l) { return l.status === "Registered"; })
      .sort(function (a, b) { return (a.registered_at || "").localeCompare(b.registered_at || ""); });
    var done = data.lots.filter(function (l) { return l.inspected_at && l.inspected_at !== "None"; });
    var passed = done.filter(function (l) { return l.passed; }).length;
    decideHook = null;
    roleScreen({
      st: inspSt, auto: true, keyHint: el("span", {}, " move ", el("kbd", { text: "a" }), " pass ", el("kbd", { text: "r" }), " reject"),
      title: "Inspector", sub: "Examine registered lots and sign one inspection per lot. A pass lists the lot for buyers; a rejection is permanent and needs a reason.",
      cells: [{ label: "In your queue", value: String(queue.length) }, { label: "Passed", value: String(passed) }, { label: "Rejected", value: String(done.length - passed) }],
      tabs: [
        { label: "Waiting", rows: queue, emptyTitle: "Nothing waiting for inspection.", emptySub: "Lots appear here when a cooperative registers one." },
        { label: "Done", rows: done, emptyTitle: "No inspections signed yet.", emptySub: "Signed inspections are final and show here." },
        { label: "Offline import", rows: [], node: odkCard() }],
      keys: { a: function () { if (decideHook) decideHook("Pass"); }, r: function () { if (decideHook) decideHook("Reject"); } },
      docket: function (l) { return l.status === "Registered" ? inspectionDocket(l) : summaryDocket(l); },
      idleTitle: "Select a lot from the queue to inspect it."
    });
  }

  // Offline inspection (roadmap INSP-6): a submission of odk/axk_inspection.xlsx filled in ODK Collect without
  // a connection. The server signs it like a screen inspection and hashes the original submission into the report.
  function odkCard() {
    var card = el("div", { class: "xt-docket-body" }, el("h2", { text: "Import an offline inspection (ODK)" }),
      el("p", { text: "Inspected without a connection? Fill the AXK inspection form in ODK Collect, then import the submission here. It is signed once, like an inspection made on this screen, and its digest covers the original field submission." }));
    if (isSim()) {
      card.append(el("p", { class: "xt-note", text: "Not available in the offline simulation. Run make run-frappe." }));
      return card;
    }
    var file = el("input", { id: "odk-file", type: "file", accept: ".xml,application/xml,text/xml", class: "xt-input" });
    var err = el("div", { class: "xt-docket-err", role: "alert" });
    var go = el("button", { class: "xt-btn", type: "button", text: "Import and sign" });
    go.addEventListener("click", function () {
      var f = file.files && file.files[0];
      if (!f) { err.replaceChildren(icon("circle-alert", 14), "Choose the submission XML file first."); file.focus(); return; }
      var headers = { Accept: "application/json", "Content-Type": "application/xml" };
      if (csrf()) headers["X-Frappe-CSRF-Token"] = csrf();
      var send = f.text().then(function (xml) {
        return fetch("/api/method/axk_capstone.odk.import_submission", { method: "POST", headers: headers, body: xml });
      }).then(function (r) {
        return r.json().catch(function () { return {}; }).then(function (j) {
          if (!r.ok) throw new Error(serverMessage(j, r.status));
          return j.message;
        });
      });
      sign(go, err, "Signing the field inspection", "The ODK submission is checked and recorded against the lot in the registry. This can only happen once.", send,
        function (lot) { inspSt.tab = 1; inspSt.sel = lot.name; txToast(lot.lot_ref + (lot.passed ? " passed (from ODK)." : " rejected (from ODK)."), lot, 1); return refresh(); });
    });
    card.append(field("Submission file (.xml)", file), err, el("div", {}, go),
      el("p", { class: "xt-note" }, "Get the form: ", el("a", { href: "https://github.com/tejirijesse/axk-open-source-capstone/tree/main/odk", target: "_blank", rel: "noopener", text: "odk/axk_inspection.xlsx" }), ". Scan the lot's QR code to fill the reference."));
    return card;
  }

  function inspectionDocket(l) {
    var grade = seg("i-grade", "Measured grade", ["A", "B", "C"], l.declared_grade);
    var qty = input("i-qty", { type: "number", min: "1", step: "1", value: String(Math.round(l.quantity_kg)), required: true, inputmode: "numeric" });
    var moisture = input("i-moist", { type: "number", min: "0", max: "40", step: "0.1", value: "11.8", inputmode: "decimal" });
    var notes = el("textarea", { id: "i-notes", class: "xt-input", maxlength: "500", placeholder: "Sampling method, defects, anything a buyer should know" });
    var reason = select("i-reason", [""].concat(META.reject_reasons || []), "");
    var reasonField = field("Rejection reason", reason, "Structured reasons make rejections comparable across inspectors.");
    reasonField.hidden = true;
    var fQty = field("Measured quantity (kg)", qty);
    var err = el("div", { class: "xt-docket-err", role: "alert" });
    var pass = el("button", { class: "xt-btn", type: "submit", text: "Pass lot" });
    var rej = el("button", { class: "xt-btn danger", type: "button", text: "Reject lot" });
    var foot = el("div", { class: "xt-actions two" }, pass, rej);
    var run = function (ok, btn) {
      if (!validate([fQty])) return;
      reasonField.setErr(null);
      var go = function () {
        sign(btn, err, "Signing the inspection", "Your inspection is recorded against the lot in the registry. This can only happen once.",
          api("inspect_lot", { name: l.name, passed: ok ? 1 : 0, grade: grade.value, quantity_kg: qty.value, moisture_pct: moisture.value, notes: notes.value, reject_reason: ok ? null : reason.value }, true),
          function (lot) { inspSt.sel = lot.name; txToast(lot.lot_ref + (ok ? " passed. It is now listed for buyers." : " rejected."), lot, 1); return refresh(); });
      };
      if (ok) return go();
      reasonField.hidden = false;
      if (!reason.value) { reasonField.setErr("Choose a rejection reason."); reason.focus(); return; }
      confirmDialog({ title: "Reject " + l.lot_ref + "?", text: "Reason: " + reason.value + ". A rejection is permanent and stays on the ledger.", confirm: "Reject lot", danger: true })
        .then(function (yes) { if (yes) go(); });
    };
    rej.addEventListener("click", function () { run(false, rej); });
    decideHook = function (v) { if (v === "Pass") pass.focus(); else { reasonField.hidden = false; reason.focus(); } };
    return docketShell("form", "Inspect " + l.commodity, [
      lotHeader(l),
      el("div", { class: "xt-small xt-muted", text: l.cooperative_name + " · declared grade " + l.declared_grade + " · " + kg(l.quantity_kg) }),
      segField("Measured grade", grade),
      el("div", { class: "xt-row" }, fQty, field("Moisture (%)", moisture)),
      field("Notes", notes, "Hashed into the report digest; not written to the ledger in plain text."),
      reasonField],
      [err, foot, el("div", { class: "xt-signs", text: signsLine("inspect", "the lot registry", "inspector") })],
      { on: { submit: function (e) { e.preventDefault(); run(true, pass); } } });
  }

  // ---------------------------------------------------------------- logistics
  var logSt = { tab: 0, sel: null };
  function renderLogistics(data) {
    var ready = data.lots.filter(function (l) { return l.status === "Funded" || l.status === "Approved"; });
    var transit = data.lots.filter(function (l) { return l.status === "In Transit"; });
    var delivered = data.lots.filter(function (l) { return l.status === "At Port" || l.status === "Settled"; });
    roleScreen({
      st: logSt, auto: true, title: "Logistics", sub: "Take custody of verified goods, seal the container and issue a waybill. The waybill digest goes on-chain at dispatch.",
      cells: [{ label: "Ready to dispatch", value: String(ready.length) }, { label: "In transit", value: String(transit.length) }, { label: "Arrived at port", value: String(delivered.length) }],
      tabs: [
        { label: "Ready to dispatch", rows: ready, emptyTitle: "No lots ready to dispatch.", emptySub: "Lots appear here once approved or funded in escrow." },
        { label: "In custody", rows: transit.concat(delivered), emptyTitle: "No shipments dispatched yet.", emptySub: "Dispatched lots and their seals show here." }],
      docket: function (l) { return l.status === "Funded" || l.status === "Approved" ? dispatchDocket(l) : summaryDocket(l); },
      idleTitle: "Select a lot to dispatch it."
    });
  }
  function dispatchDocket(l) {
    var carrier = input("disp-carrier", { value: "Swift Freight Logistics (Rwanda)", required: true });
    var driver = input("disp-driver", { value: "Demo Driver", required: true });
    var plate = input("disp-plate", { value: "RAD 000D", required: true, maxlength: "12" });
    var seal = input("disp-seal", { value: "RW-SEAL-" + Math.floor(100000 + Math.random() * 900000), required: true, maxlength: "24" });
    var ports = ["Kigali Logistics Platform", "Goma Inland Port", "Mombasa Port Corridor", "Dar es Salaam Port Corridor"];
    var port = select("disp-port", ports, ports[0]);
    var fs = [field("Carrier company", carrier), field("Driver name", driver), field("Vehicle plate", plate), field("Tamper seal number", seal, "Applied at loading; checked against the gate seal at port.")];
    var err = el("div", { class: "xt-docket-err", role: "alert" });
    var submit = el("button", { class: "xt-btn block", type: "submit", text: chainLabel("Seal and dispatch on-chain") });
    return docketShell("form", "Dispatch", [lotHeader(l), fs[0], el("div", { class: "xt-row" }, fs[1], fs[2]), fs[3], field("Destination", port)],
      [err, submit, el("div", { class: "xt-signs", text: signsLine("dispatch", "the lot registry", "logistics") })],
      { on: { submit: function (e) {
        e.preventDefault();
        if (!validate(fs)) return;
        sign(submit, err, "Signing custody waybill", "The carrier issues a waybill and commits its digest with the seal number on-chain.",
          api("dispatch_logistics", { name: l.name, carrier_name: carrier.value, driver_name: driver.value, vehicle_plate: plate.value, seal_number: seal.value, destination_port: port.value }, true),
          function (lot) { logSt.sel = lot.name; txToast("Dispatched " + lot.lot_ref + " under seal " + seal.value + ".", lot, 3); return refresh(); });
      } } });
  }

  // ---------------------------------------------------------------- port / terminal
  var portSt = { tab: 0, sel: null };
  function renderPort(data) {
    var inbound = data.lots.filter(function (l) { return l.status === "In Transit"; });
    var atPort = data.lots.filter(function (l) { return l.status === "At Port"; });
    var settled = data.lots.filter(function (l) { return l.status === "Settled"; });
    roleScreen({
      st: portSt, auto: true, title: "Port", sub: "Receive shipments, check the container seal against the waybill and record customs clearance.",
      cells: [{ label: "Inbound", value: String(inbound.length) }, { label: "Cleared at port", value: String(atPort.length) }, { label: "Released and settled", value: String(settled.length) }],
      tabs: [
        { label: "In transit", rows: inbound, emptyTitle: "No shipments in transit.", emptySub: "Lots appear here once logistics dispatches them." },
        { label: "Cleared", rows: atPort.concat(settled), emptyTitle: "No cargo received yet.", emptySub: "Cleared shipments and their customs references show here." }],
      docket: function (l) { return l.status === "In Transit" ? portDocket(l) : summaryDocket(l); },
      idleTitle: "Select a shipment to clear it."
    });
  }
  function portDocket(l) {
    var ports = ["Kigali Logistics Platform", "Goma Inland Port", "Mombasa Port Terminal"];
    var port = select("port-name", ports, l.destination_port || ports[0]);
    var container = input("port-container", { value: "MSKU-" + Math.floor(1000000 + Math.random() * 9000000), required: true });
    var customs = input("port-customs", { value: "RW-CUST-2026-" + Math.floor(1000 + Math.random() * 9000), required: true });
    var sealInput = input("port-seal", { value: l.seal_number || "", required: true });
    var fSeal = field("Seal number at gate", sealInput, "Must match the waybill seal exactly.");
    var fs = [field("Container ID", container), field("Customs entry ref", customs), fSeal];
    var err = el("div", { class: "xt-docket-err", role: "alert" });
    var submit = el("button", { class: "xt-btn block", type: "submit", text: chainLabel("Verify seal and clear gate-in on-chain") });
    return docketShell("form", "Gate-in at port", [lotHeader(l),
      kv([["Carrier", (l.carrier_name || NONE) + (l.driver_name ? " · " + l.driver_name : "")], ["Expected seal", el("span", { class: "xt-mono", text: l.seal_number || NONE })]]),
      field("Port facility", port), fs[0], fs[1], fSeal],
      [err, submit, el("div", { class: "xt-signs", text: signsLine("receive", "the lot registry", "port") })],
      { on: { submit: function (e) {
        e.preventDefault();
        if (!validate(fs)) return;
        if (sealInput.value.trim().toLowerCase() !== (l.seal_number || "").trim().toLowerCase()) {
          fSeal.setErr("Does not match the waybill seal.");
          err.replaceChildren(icon("circle-alert", 14), "Tamper alert: seal " + sealInput.value + " does not match the waybill seal " + (l.seal_number || NONE) + ". Nothing was signed.");
          return;
        }
        sign(submit, err, "Recording port arrival", "Verifying container seal integrity and recording customs clearance.",
          api("receive_port", { name: l.name, port_name: port.value, container_id: container.value, customs_ref: customs.value, seal_number: sealInput.value }, true),
          function (lot) { portSt.sel = lot.name; txToast("Cleared " + lot.lot_ref + " at " + port.value + ". Ready for buyer delivery confirmation.", lot, 4); return refresh(); });
      } } });
  }

  // ---------------------------------------------------------------- buyer
  var buySt = { tab: 0, sel: null };
  function renderBuy(data) {
    var me = persona("buyer");
    var market = data.lots.filter(function (l) { return l.status === "Approved"; });
    var mine = data.lots.filter(function (l) { return ["Funded", "In Transit", "At Port", "Settled", "Refunded"].indexOf(l.status) >= 0; });
    var active = mine.filter(function (l) { return l.status === "Funded" || l.status === "In Transit" || l.status === "At Port"; }).length;
    var topUp = el("button", { class: "xt-btn secondary", type: "button", text: "Top up 500,000 RWF (testnet)", on: { click: function () {
      withBusy("Topping up", "The test RWF issuer pays the buyer. Testnet only; this token has no value.",
        api("top_up_buyer", { amount_rwf: 500000 }, true))
        .then(function () { toast("Added 500,000 test RWF to the buyer's wallet."); return refresh(); }).catch(fail);
    } } });
    roleScreen({
      st: buySt, title: "Buyer", right: topUp,
      sub: "Buy only what an inspector has signed off. Your payment waits in escrow and goes to the cooperative when you confirm delivery.",
      cells: [{ label: "Lots for sale", value: String(market.length) }, { label: "Active shipments", value: String(active) },
        { label: "Settled purchases", value: String(mine.filter(function (l) { return l.status === "Settled"; }).length) },
        Object.assign({ label: "Wallet balance" }, ledgerRwf(me ? me.rwf : null))],
      tabs: [
        { label: "Passed lots", rows: market, emptyTitle: "No inspected lots are for sale.", emptySub: "Uninspected and rejected lots never appear here." },
        { label: "My trades", rows: mine, emptyTitle: "No purchases yet.", emptySub: "Fund escrow on a passed lot to start one." }],
      docket: function (l) {
        if (l.status === "Approved") return fundDocket(l, me);
        if (l.status === "Funded" || l.status === "In Transit" || l.status === "At Port") return settleDocket(l);
        return doneDocket(l);
      },
      idleTitle: "Select a lot to buy or settle it."
    });
  }
  function fundDocket(l, me) {
    var perKg = l.price_rwf && (l.inspected_quantity_kg || l.quantity_kg) ? l.price_rwf / (l.inspected_quantity_kg || l.quantity_kg) : null;
    var amount = input("d-amount", { type: "number", min: "1", step: "1", value: String(l.price_rwf), required: true, inputmode: "numeric" });
    var fAmount = field("Total (RWF)", amount, "Held by the escrow contract until you confirm delivery. Refundable after 30 days if never released.");
    var err = el("div", { class: "xt-docket-err", role: "alert" });
    var submit = el("button", { class: "xt-btn block", type: "submit", text: chainLabel("Fund escrow on-chain") });
    return docketShell("form", "Fund escrow", [lotHeader(l),
      kv([["Grade", l.inspected_grade + (l.inspected_grade !== l.declared_grade ? " (declared " + l.declared_grade + ")" : "")], ["Moisture", l.moisture_pct != null ? nf1.format(l.moisture_pct) + "%" : null],
        ["Seller", l.cooperative_name], ["Inspector", l.inspector_name || "An authorised inspector"], ["Price per kg", perKg ? rwf(perKg) : null]]),
      fAmount,
      el("div", { class: "xt-small" }, el("a", { href: shareLink(l), target: "_blank", rel: "noopener" }, "Public verification page ", icon("arrow-up-right", 12)))],
      [err, submit, el("div", { class: "xt-signs", text: signsLine("fund", "the escrow contract", "buyer") })],
      { on: { submit: function (e) {
        e.preventDefault();
        if (!validate([fAmount])) return;
        if (me && me.rwf != null && Number(amount.value) > me.rwf) { fAmount.setErr("The buyer's wallet holds " + rwf(me.rwf) + ". Top up first."); amount.focus(); return; }
        sign(submit, err, "Paying into escrow", "Buyer and AXK verifier both sign. The escrow asks the lot registry who owns this inspected lot and fixes them as the payee.",
          api("fund_lot", { name: l.name, amount_rwf: amount.value }, true),
          function (lot) { buySt.tab = 1; buySt.sel = lot.name; txToast(rwf(lot.amount_rwf) + " is in escrow for " + lot.lot_ref + ".", lot, 2); return refresh(); });
      } } });
  }
  function settleDocket(l) {
    var err = el("div", { class: "xt-docket-err", role: "alert" });
    var submit = el("button", { class: "xt-btn block", type: "button", text: chainLabel("Confirm delivery and settle") });
    submit.addEventListener("click", function () {
      confirmDialog({ title: "Confirm delivery of " + l.lot_ref + "?", text: "This releases " + rwf(l.amount_rwf) + " to the cooperative and cannot be undone.", confirm: "Confirm and settle" }).then(function (yes) {
        if (!yes) return;
        sign(submit, err, "Settling the trade", "Four transactions: release escrow, record the 40/40/20 split, pay members, and attest the settled trade. About half a minute.",
          api("confirm_delivery", { name: l.name }, true),
          function (lot) { buySt.sel = lot.name; txToast("Settled " + lot.lot_ref + ". Members paid and the trade is attested.", lot, 6); return refresh(); });
      });
    });
    return docketShell("aside", "Settle", [lotHeader(l), kv([["Escrow", rwf(l.amount_rwf)], ["Status", tag(l.status)]]),
      l.status === "At Port" ? null : el("p", { class: "xt-note", text: "The goods have not reached port yet. Settle only once they have arrived." })],
      [err, submit, el("div", { class: "xt-signs", text: signsLine("release", "the escrow contract", "buyer") })]);
  }
  function doneDocket(l) {
    var d = summaryDocket(l);
    var foot = d.querySelector(".xt-docket-foot");
    foot.prepend(
      el("button", { class: "xt-btn secondary block", type: "button", on: { click: function () { downloadRecord(l.name); } } }, icon("download", 16), "Download record"),
      el("button", { class: "xt-btn ghost block", type: "button", on: { click: function () { copyShare(l); } } }, icon("copy", 16), "Copy share link"));
    return d;
  }

  // Verified record: the three committed records, their digests, the on-chain ids and
  // every transaction, in one JSON file a buyer can hand to their own compliance team.
  function downloadRecord(name) {
    api("lot", { name: name }).then(function (l) {
      var out = {
        schema: "axk.verified-record/1",
        generated_at: new Date().toISOString(),
        network: isSim() ? "offline-simulation (not on-chain)" : "stellar-testnet",
        lot_ref: l.lot_ref, status: l.status, chain_lot_id: l.chain_lot_id,
        public_verification: shareLink(l),
        lot: { record: safeJSON(l.lot_record), sha256: l.lot_digest },
        inspection: l.report_record ? { record: safeJSON(l.report_record), sha256: l.report_digest } : null,
        settlement: l.settlement_record ? { record: safeJSON(l.settlement_record), sha256: l.attest_digest } : null,
        contracts: l.contracts,
        transactions: l.steps.filter(function (s) { return s.tx; }).map(function (s) { return { step: s.label, tx: s.tx, url: s.url }; }),
        how_to_verify: "sha256 of each record's canonical JSON must equal its digest; the lot digest is checkable with the lot registry's matches(lot_id, digest), the settlement digest with the attestation registry's matches(trade_id, digest)."
      };
      var blob = new Blob([JSON.stringify(out, null, 2)], { type: "application/json" });
      var a = el("a", { href: URL.createObjectURL(blob), download: l.lot_ref + "-verified-record.json" });
      document.body.append(a); a.click(); a.remove();
      setTimeout(function () { URL.revokeObjectURL(a.href); }, 1000);
    }).catch(fail);
  }
  function safeJSON(s) { try { return JSON.parse(s); } catch (e) { return s; } }

  function copyShare(r) {
    var link = shareLink(r);
    (navigator.clipboard ? navigator.clipboard.writeText(link) : Promise.reject()).then(function () {
      toast("Share link copied. It opens a read-only verification page, no login needed.", false, { href: link, text: "Open", external: true });
    }, function () { toast("Copy is not available here. Verification link: " + link, true); });
  }

  // ---------------------------------------------------------------- lot detail
  function verdict(l) {
    var s = l.status, sim = isSim() ? " (simulated)" : "";
    var v = {
      Settled: ["is-proof", "shield-check", "An authorised inspector passed this lot on-chain, and its settlement is attested." + sim],
      "At Port": ["is-proof", "shield-check", "An authorised inspector passed this lot, and it has cleared the port." + sim],
      "In Transit": ["is-transit", "truck", "This lot passed inspection and is in transit under seal." + sim],
      Funded: ["is-proof", "shield-check", "An authorised inspector passed this lot, and the buyer's payment is held in escrow." + sim],
      Approved: ["is-proof", "shield-check", "An authorised inspector passed this lot on-chain." + sim],
      Rejected: ["is-danger", "shield-x", "An authorised inspector rejected this lot on-chain" + (l.reject_reason ? ": " + l.reject_reason + "." : ".") + sim],
      Registered: ["", "shield", "Registered on-chain, awaiting inspection." + sim],
      Refunded: ["", "shield", "The escrow was refunded to the buyer." + sim]
    }[s] || ["", "shield", s];
    return el("div", { class: "xt-verdict " + v[0], role: "status" }, icon(v[1], 20), v[2]);
  }

  function renderLot(l) {
    var failed = l.status === "Rejected";
    var txs = l.steps.map(function (s) { return s.tx || ""; });
    var urls = l.steps.map(function (s) { return s.url || null; });
    var states = stripState(txs, failed);
    var stamps = stampIndexes(l.name, txs);
    var timeline = el("ol", { class: "xt-timeline" }, l.steps.map(function (s, i) {
      var st = states[i];
      return el("li", { class: "xt-tl-row is-" + (st === "filled" ? "filled" : st === "failed" ? "failed" : st === "void" ? "void" : "pending") },
        notchEl(st, stamps[i]),
        el("div", {}, el("div", { class: "xt-tl-label", text: s.label }),
          s.tx ? el("div", { class: "xt-tl-meta" }, txref(s.tx, "tx", { url: s.url || null, copy: true }), s.at && s.at !== "None" ? el("span", { text: when(s.at) }) : null)
            : el("div", { class: "xt-tl-meta", text: st === "void" ? "Will not happen" : (st === "next" ? "Next step" : "Pending") })));
    }));

    var verifyOut = el("div", { "aria-live": "polite" });
    var verifyBtn = el("button", { class: "xt-btn secondary small", type: "button", text: isSim() ? "Check records (local hashes)" : "Check records against the chain", on: { click: function () {
      verifyBtn.disabled = true;
      Promise.all([
        hashIn(l.lot_record),
        l.waybill_record ? hashIn(l.waybill_record) : Promise.resolve(null),
        l.port_receipt_record ? hashIn(l.port_receipt_record) : Promise.resolve(null),
        l.settlement_record ? hashIn(l.settlement_record) : Promise.resolve(null),
        api("verify_lot", { name: l.name }, true)
      ]).then(function (res) {
        var lines = [check(res[0] === l.lot_digest && res[4].lot_record, isSim() ? "Lot record hashes to its stored digest" : "Lot record hashes to the digest the cooperative registered on-chain")];
        if (l.waybill_record) lines.push(check(res[1] === l.waybill_digest && res[4].waybill_record, isSim() ? "Waybill record hashes to its stored digest" : "Waybill record matches the on-chain dispatch attestation"));
        if (l.port_receipt_record) lines.push(check(res[2] === l.port_receipt_digest && res[4].port_receipt_record, isSim() ? "Port receipt hashes to its stored digest" : "Port receipt matches the on-chain clearance attestation"));
        if (l.settlement_record) lines.push(check(res[3] === l.attest_digest && res[4].settlement_record, isSim() ? "Settlement record hashes to its stored digest" : "Settlement record matches the on-chain attestation"));
        verifyOut.replaceChildren.apply(verifyOut, lines);
      }).catch(fail).finally(function () { verifyBtn.disabled = false; });
    } } });

    var contracts = Object.keys(l.contracts || {}).filter(function (k) { return l.contracts[k]; }).map(function (k) {
      return [k[0].toUpperCase() + k.slice(1) + " contract", txref(l.contracts[k], "contract", { explorer: l.explorer || EXPLORER, copy: true })];
    });
    var acct = function (a) { return a ? txref(a, "account", { copy: true }) : null; };
    var party = function (label, name, a) { return [label, [name || NONE, " ", acct(a)]]; };

    setMain(
      el("div", { class: "xt-crumb" }, el("a", { href: "/trade", text: "Overview" }), " / Lot"),
      el("div", { class: "xt-lot-head" },
        el("div", {}, el("div", { class: "xt-lot-title" }, el("h1", { class: "xt-mono-ref", text: l.lot_ref }), tag(l.status)),
          el("p", { text: l.commodity + (l.variety ? " · " + l.variety : "") + " · " + l.origin + (l.cooperative_name ? " · " + l.cooperative_name : "") })),
        el("div", { class: "xt-head-actions" },
          el("a", { class: "xt-btn secondary", href: shareLink(l), target: "_blank", rel: "noopener" }, "Public page", icon("arrow-up-right", 14)),
          el("button", { class: "xt-btn ghost", type: "button", on: { click: function () { copyShare(l); } } }, icon("copy", 16), "Copy share link"),
          el("button", { class: "xt-btn ghost", type: "button", on: { click: function () { downloadRecord(l.name); } } }, icon("download", 16), "Download record"))),
      bigStrip(txs, { key: l.name + ":hdr", urls: urls, failed: failed }),
      el("div", { class: "xt-section-gap" }, verdict(l)),
      l.last_error ? el("p", { class: "xt-note error xt-section-gap", text: "Last attempt failed: " + l.last_error }) : null,
      el("div", { class: "xt-lot-body" },
        el("div", {},
          el("section", { class: "xt-card" }, el("div", { class: "xt-card-head" }, el("div", {}, el("h2", { text: isSim() ? "Custody timeline (simulated)" : "Custody timeline" }), el("p", { text: isSim() ? "Offline simulation: these steps were not sent to Stellar." : "Each step links to its transaction on Stellar." }))), timeline),
          el("section", { class: "xt-card" },
            el("div", { class: "xt-card-head" }, el("div", {}, el("h2", { text: "Records and digests" }), el("p", { text: isSim() ? "Your browser re-hashes the records and compares them with the stored digests. Nothing is checked on-chain." : "Only digests are on-chain. Your browser re-hashes the records; the contracts confirm the match." })), verifyBtn),
            verifyOut,
            recordBlock("Lot record", l.lot_record, l.lot_digest),
            l.report_record ? recordBlock("Inspection report", l.report_record, l.report_digest) : null,
            l.waybill_record ? recordBlock("Logistics waybill", l.waybill_record, l.waybill_digest) : null,
            l.port_receipt_record ? recordBlock("Port arrival receipt", l.port_receipt_record, l.port_receipt_digest) : null,
            l.settlement_record ? recordBlock("Settlement record", l.settlement_record, l.attest_digest) : null)),
        el("div", {},
          el("section", { class: "xt-card" }, el("div", { class: "xt-card-head" }, el("h2", { text: "Lot and transport" })),
            kv([["Declared", "Grade " + l.declared_grade + " · " + kg(l.quantity_kg)],
              ["Inspected", l.inspect_tx ? "Grade " + l.inspected_grade + " · " + kg(l.inspected_quantity_kg) + (l.moisture_pct != null ? " · " + nf1.format(l.moisture_pct) + "% moisture" : "") : "Not yet"],
              l.carrier_name ? ["Carrier", l.carrier_name + (l.driver_name ? " · " + l.driver_name : "") + (l.vehicle_plate ? " (" + l.vehicle_plate + ")" : "")] : null,
              l.seal_number ? ["Seal number", el("span", {}, el("span", { class: "xt-mono", text: l.seal_number }), l.seal_verified ? [" intact ", icon("shield-check", 14)] : null)] : null,
              l.destination_port ? ["Destination", l.destination_port] : null,
              l.port_name ? ["Port terminal", l.port_name + (l.container_id ? " · " + l.container_id : "")] : null,
              l.reject_reason ? ["Rejected for", l.reject_reason] : null,
              ["Escrow", l.amount_rwf ? rwf(l.amount_rwf) : null],
              [isSim() ? "Lot id (simulated)" : "On-chain lot id", l.chain_lot_id ? el("span", { class: "xt-mono", text: l.chain_lot_id }) : null],
              l.inspection_notes ? ["Inspector notes", l.inspection_notes] : null])),
          el("section", { class: "xt-card" }, el("div", { class: "xt-card-head" }, el("h2", { text: "Accounts and contracts" })),
            kv([party("Cooperative", l.cooperative_name, l.cooperative_account), party("Inspector", l.inspector_name, l.inspector_account), party("Buyer", l.buyer_name, l.buyer_account)].concat(contracts))))));
  }
  function recordBlock(label, record, dig) {
    return el("div", { class: "xt-field xt-section-gap" }, el("span", { class: "xt-field-label", text: label }),
      el("div", { class: "xt-record", text: record || NONE }), digest(dig));
  }
  function check(ok, text) { return el("div", { class: "xt-check " + (ok ? "ok" : "bad") }, icon(ok ? "circle-check" : "circle-x", 16), text); }
  function hashIn(text) {
    return crypto.subtle.digest("SHA-256", new TextEncoder().encode(text)).then(function (b) {
      return Array.from(new Uint8Array(b)).map(function (x) { return x.toString(16).padStart(2, "0"); }).join("");
    });
  }

  // ---------------------------------------------------------------- boot
  function navCounts(data) {
    var c = data.counts;
    var badge = {
      coop: c.Registered || 0,
      inspect: c.Registered || 0,
      logistics: (c.Funded || 0) + (c.Approved || 0),
      port: c["In Transit"] || 0,
      buy: (c.Approved || 0) + (c.Funded || 0) + (c["In Transit"] || 0) + (c["At Port"] || 0)
    };
    Object.keys(badge).forEach(function (k) {
      var n = root.querySelector('.xt-rail-count[data-count="' + k + '"]');
      if (n) n.textContent = badge[k] ? String(badge[k]) : "";
    });
  }

  // Personas carry live wallet balances (a Stellar call each), so the page renders from the
  // lot data first and redraws once balances arrive.
  function refresh() {
    if (PAGE === "lot") {
      var name = new URLSearchParams(location.search).get("name");
      if (!name) { setMain(empty("inbox", "No lot chosen.", "Open a lot from the overview.", el("a", { class: "xt-btn ghost", href: "/trade" }, "Go to Overview"))); return Promise.resolve(); }
      return Promise.all([api("lot", { name: name }), api("overview")]).then(function (r) { META = r[1]; navCounts(r[1]); renderLot(r[0]); });
    }
    var draw = function (data) {
      railPersona();
      if (PAGE === "overview") renderOverview(data);
      else if (PAGE === "coop") renderCoop(data);
      else if (PAGE === "inspect") renderInspect(data);
      else if (PAGE === "logistics") renderLogistics(data);
      else if (PAGE === "port") renderPort(data);
      else if (PAGE === "buy") renderBuy(data);
    };
    var personasP = api("personas").catch(function () { return PERSONAS || []; });
    return api("overview").then(function (data) {
      META = data;
      navCounts(data);
      draw(data);
      return personasP.then(function (p) {
        PERSONAS = p;
        // Redraw only if nothing is mid-edit, so a balance update never wipes a half-typed form.
        var editing = document.activeElement && main.contains(document.activeElement) && /INPUT|TEXTAREA|SELECT/.test(document.activeElement.tagName);
        if (!editing) draw(data); else railPersona();
      });
    });
  }

  root.addEventListener("click", function (e) {
    var out = e.target.closest("[data-logout]");
    if (!out) return;
    e.preventDefault();
    var h = { Accept: "application/json" };
    if (csrf()) h["X-Frappe-CSRF-Token"] = csrf();
    fetch("/api/method/logout", { method: "POST", headers: h }).finally(function () { location.href = "/login"; });
  });

  refresh().catch(function (e) {
    if (/sign in|log in|login/i.test(e.message) || /\(40[13]\)/.test(e.message)) {
      var back = location.pathname + location.search;
      setMain(el("div", { class: "xt-signin" },
        el("h1", { text: "Sign in to use the trade screens" }),
        el("p", { text: "These screens sign real Stellar testnet transactions, so they need an account. Anyone can still verify a lot or browse the chain explorer without one." }),
        el("div", { class: "xt-signin-actions" },
          el("a", { class: "xt-btn", href: "/login?redirect-to=" + encodeURIComponent(back) }, icon("arrow-right", 16), "Sign in"),
          el("a", { class: "xt-btn ghost", href: "/trace", text: "Verify a lot" }),
          el("a", { class: "xt-btn ghost", href: "/chain", text: "Chain explorer" }))));
      return;
    }
    setMain(el("div", { class: "xt-signin" }, el("p", { class: "xt-note error", role: "alert" }, icon("circle-alert", 14), " ", e.message),
      el("button", { class: "xt-btn ghost", type: "button", text: "Try again", on: { click: function () { location.reload(); } } })));
  });
})();

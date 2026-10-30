# AXK Capstone: Design System

Version 1, 2026-10-30. This is the bar every screen is built and reviewed against. Every raw colour value lives in §3 and nowhere else. Code references are `path:line` against `frappe_app/axk_capstone/axk_capstone/`.

---

## 1. Aesthetic intent

**What it is.** It traces a lot of coffee or tea from a Rwandan cooperative to a buyer's settlement. Each step only counts if it has a Stellar transaction behind it. The product's job is to make one claim and back it up: *this lot was verified before it was paid, and here is the receipt for every step.*

**Who opens it, and how.** ALU reviewers and examiners open it once on a laptop (1280 to 1440 wide, about 800 to 900 tall) to judge it. They are sceptical, short on time, and have never seen it before. They will sign in with a demo account, click through the roles, and open a public trace page from a QR code. Inside the demo, the personas are a cooperative clerk, an inspector, logistics, port and a buyer. Because this is an occasional, first-time product, it earns guidance and clarity rather than power-user density. Each screen should answer "what is this, what's waiting, what do I do" in about five seconds.

**What it must feel like.** *Exact and accountable.* It must NOT feel like crypto hype (no neon, no gradients, no "web3" glow, no coin imagery). It must NOT feel like an aid or NGO brochure (no warm gradients, no "empowering farmers" voice). It must NOT feel like a student template (factory Frappe login, system font, card grids of equal tiles, emoji as icons).

**What would betray it.** Any mark that implies proof where there is none, such as a filled step without a transaction hash, a fake hash on the login panel, or a green tick on something that is only pending. In a verification product, a decorative checkmark is a lie.

**Where it lives.** It is desktop-first and fits one laptop viewport per screen with no page scroll at 1440x900. Only tables scroll, inside their panel. The public trace page must also work on a 390px phone, because that is where the QR code gets scanned.

### The one idea: "Nothing without its receipt"

Every lot carries a **Custody Strip**: nine notches, one for each on-chain step in `trade_api.py:151`. A notch is filled **only** when that step has a transaction hash, and every filled notch is a link to its transaction on stellar.expert. The strip appears wherever a lot appears: a micro strip in table rows, a labelled strip in the lot header, a vertical timeline on the public trace page, and a live specimen on the login panel. Green in this product means *proven on-chain*. Green is never used decoratively.

The shell is a **forest room**: a full-bleed deep-green frame (`#0c3424`, the report's colour) holds the rail and top bar, and the work sits on an inset paper sheet. The colour comes from the frame's area, not from saturated accents. This is the structure Joe has already approved on his own products (REMIS shell, AXK webapp Rev 3), carried over in the report's palette.

### Directions considered

| | Stance | Verdict |
|---|---|---|
| A **Forest room + Custody Strip** (chosen) | Deep-green frame, paper sheet, the nine-notch receipt as the signature | Brand continuity with the report, and one memorable device that *is* the thesis |
| B Paper ledger | All-light, ruled tables, serif numerals | Calm, but it reads as a document rather than a working product. Too quiet for a one-shot demo |
| C Dark terminal | Near-black, mono everywhere, bright green | Reads as crypto, which is the first betrayal in §1 |

---

## 2. Fonts

| Role | Face | Weights | Licence | Load |
|---|---|---|---|---|
| Display + UI | **Plus Jakarta Sans** (brand, matches the report) | variable 400–800 | OFL 1.1 | self-host `public/fonts/PlusJakartaSans-Var.woff2`, `<link rel="preload">` in `templates/axk_lean.html` |
| Identifiers | **JetBrains Mono** | variable 400–600 | OFL 1.1 | self-host `public/fonts/JetBrainsMono-Var.woff2` |

Self-host because the lean template exists for 3G load times (`axk_lean.html:9`), and a Google Fonts round-trip undoes that. Subset to Latin. Use `font-display: swap`. JetBrains Mono is chosen for hashes because its 0/O and 1/l/I are unambiguous and it stays narrow enough that a 64-char sha256 fits two lines in a 440px column.

Plus Jakarta Sans does both display and UI jobs. Hierarchy comes from weight and size contrast (800 display against 450 body), not from a second sans. Numbers always use `font-variant-numeric: tabular-nums`.

---

## 3. Tokens (paste into `public/css/axk.css`, replacing the current `.xt-app` block)

The dark theme block (`axk.css:37–56`) is **deleted**. There is one theme, and the frame already supplies the dark area. `--series-1: #2a78d6` (factory blue) and the chain.css pink/orange series are deleted.

```css
@font-face { font-family: "Plus Jakarta Sans"; src: url("/assets/axk_capstone/fonts/PlusJakartaSans-Var.woff2") format("woff2"); font-weight: 400 800; font-display: swap; }
@font-face { font-family: "JetBrains Mono"; src: url("/assets/axk_capstone/fonts/JetBrainsMono-Var.woff2") format("woff2"); font-weight: 400 600; font-display: swap; }

:root {
  /* frame (the forest room) */
  --frame:        #0c3424;  /* full-bleed shell, login brand panel */
  --frame-2:      #123f2d;  /* hover on frame */
  --frame-hi:     #1a4a37;  /* selected rail item fill */
  --frame-line:   #4f8a74;  /* control boundaries ON frame (3.41 vs frame) */
  --on-frame:     #eef5f1;  /* primary text on frame */
  --on-frame-2:   #a8c4b7;  /* secondary text on frame / frame-2 */
  --on-frame-3:   #86a698;  /* tertiary, ONLY on --frame (fails on frame-2: 4.46) */
  --proof-bright: #2cbf82;  /* filled notch + focus ring ON frame; text only on frame/frame-2 */

  /* sheet */
  --paper:        #fbfbf8;  /* the inset sheet */
  --sunk:         #f2f3ee;  /* table head, row hover, ledger strip */
  --field:        #ffffff;  /* inputs only */
  --line:         #e3e4dc;  /* hairlines, dividers (structural, not a control boundary) */
  --control:      #85918b;  /* input/checkbox/hollow-notch borders: 3.16 paper, 3.27 field */

  --ink:          #0f1f1a;  /* primary text */
  --ink-2:        #45534d;  /* secondary text */
  --ink-3:        #5d6b65;  /* muted / meta. The floor: nothing lighter carries text */

  /* the one accent: proof */
  --proof:        #166350;  /* filled notch, primary button, links, focus ring on paper */
  --proof-strong: #0f4f3f;  /* primary hover/pressed */
  --proof-wash:   #eaf4ef;  /* positive tag + verdict fill */

  /* semantic (never decorative) */
  --danger:       #b3261e;
  --danger-wash:  #fbefed;
  --warn:         #8a5a00;  /* Refunded only */
  --warn-wash:    #fbf3e2;
  --neutral-wash: #f0f1ec;  /* neutral tag fill */
  --danger-on-frame: #ff9b8f;

  /* charts (chain explorer): green = on-chain, graphite = everything else */
  --chart-proof:  var(--proof);
  --chart-g1:     #2b3631;
  --chart-g2:     #56635d;
  --chart-g3:     #8d9a94;
  --chart-grid:   var(--line);

  /* type */
  --font-ui:   "Plus Jakarta Sans", "Helvetica Neue", Arial, sans-serif;
  --font-mono: "JetBrains Mono", "SF Mono", Menlo, monospace;

  /* space (4-base) */
  --s-1: 4px; --s-2: 8px; --s-3: 12px; --s-4: 16px; --s-5: 20px; --s-6: 24px; --s-8: 32px; --s-10: 40px; --s-14: 56px;

  /* radii */
  --r-notch: 1px; --r-tag: 5px; --r-control: 7px; --r-panel: 10px; --r-sheet: 16px;

  /* elevation: hairline + value step. One shadow, for floating layers only */
  --shadow-float: 0 12px 32px rgba(12, 52, 36, 0.18), 0 0 0 1px var(--line);

  /* motion */
  --ease: cubic-bezier(0.2, 0.8, 0.2, 1);
  --t-fast: 140ms; --t-base: 200ms; --t-panel: 260ms; --t-stamp: 320ms;

  /* focus */
  --ring: 0 0 0 2px var(--paper), 0 0 0 4px var(--proof);
  --ring-on-frame: 0 0 0 2px var(--frame), 0 0 0 4px var(--proof-bright);
}
```

### Contrast (computed with the WCAG 2.x formula, not eyeballed)

| Pair | Ratio | Use |
|---|---|---|
| ink on paper | 16.45 | body |
| ink-2 on paper / sunk | 7.80 / 7.25 | secondary |
| ink-3 on paper / sunk / field | 5.39 / 5.01 / 5.59 | meta, labels (floor) |
| proof on paper / proof-wash / sunk | 6.90 / 6.37 / 6.42 | links, positive tag text |
| white on proof / proof-strong | 7.16 / 9.50 | primary button |
| danger on paper / danger-wash | 6.30 / 5.81 | errors, rejected tag |
| warn on warn-wash | 5.37 | refunded tag |
| ink-2 on neutral-wash | 7.12 | neutral tag |
| on-frame on frame / frame-hi | 12.38 / 9.12 | rail, top bar, login panel |
| on-frame-2 on frame / frame-2 | 7.34 / 6.34 | secondary on frame |
| on-frame-3 on frame | 5.17 | tertiary on frame **only** |
| proof-bright on frame / frame-2 | 5.80 / 5.00 | notch, live dot, focus ring on frame |
| danger-on-frame on frame | 6.75 | login error state on panel (rare) |
| control on paper / field | 3.16 / 3.27 | 1.4.11 control boundary |
| frame-line on frame | 3.41 | control boundary on frame |
| proof (ring) on paper | 6.90 | focus |

**Traps (measured):** `--control` on `--sunk` = 2.93, so **inputs never sit on sunk**. `--proof` on `--frame` = 1.92, so **never put proof green on the frame** (use proof-bright). `--line` on paper = 1.24, which is structural only and may not be the sole boundary of anything clickable. `--on-frame-3` on `--frame-2` = 4.46 fails, so hover rows on the frame use on-frame-2.

---

## 4. Type scale

| Token | Size/Line | Weight | Tracking | Use |
|---|---|---|---|---|
| `display` | 40/44 | 800 | -0.025em | login headline only |
| `h1` | 24/30 | 750 | -0.015em | page title in sheet |
| `h2` | 15/20 | 700 | -0.005em | panel heading |
| `body` | 14/20 | 450 | 0 | default |
| `small` | 13/18 | 500 | 0 | table cells, meta |
| `label` | 12/16 | 600 | 0.01em | field labels, column heads, sentence case |
| `num-lg` | 26/30 | 750 | -0.02em | ledger-strip figures, tabular |
| `num` | 14/20 | 600 | 0 | in-table numbers, tabular, right-aligned |
| `mono` | 12.5/18 | 450 | 0 | hashes, addresses, tx ids |
| `mono-ref` | 20/26 | 600 | -0.01em | lot ref as a page title (trace, lot detail) |

There are no tracked all-caps eyebrows anywhere, and letter-spacing is capped at 0.01em on positive values. Column heads are sentence case in `label` and `--ink-3`.

---

## 5. Icons

Use inline SVG from Lucide (ISC licence): 16px in UI, 14px in tags, `stroke-width: 1.75`, `stroke: currentColor`, and `aria-hidden="true"` unless it is the only content (then add an `aria-label` to the parent). Put a single `icon(name)` helper in `trade.js` and `chain.js`, plus a Jinja macro in `templates/includes/icons.html`, holding these paths. Do not use icon fonts or CDN scripts.

**Glyph sweep: every one of these is replaced (do not leave any).**

| Current | Where | Replace with |
|---|---|---|
| `○ ✓ ✕ ◷ 🚚 ⚓ ● ↩` status map | `trade.js:110–117`, `www/trace/index.html` pill macro | tag icons in §6.4 |
| `🚚` `⚓` role icons | `trade.js:224,226` | `truck`, `anchor` |
| `✓ ✕` step dots | `trade.js:758`, `www/trace/lot.html` | Custody timeline (§6.5), `check` / `x` 12px |
| `↗` after links | `trade.js:196,653,747,761,789,823`, `trace/lot.html` | `arrow-up-right` 12px |
| `✓ ✕ ○ 🚚` verdict prefixes | `trace/lot.html` verdict block | Verdict icon (§6.8) |
| `✓ / ✕` in `check()` | `trade.js:831` | `circle-check` / `circle-x` |
| `intact ✓`, `(verified intact ✓)` | `trace/lot.html`, `trade.js:807` | text "intact" + `shield-check` |
| `✓ ✕ ○ ◐ ≠` | `chain.js:160–163,172,255–269` | `circle-check`, `circle-x`, `circle-dashed`, `circle-dot`; "≠" becomes the word "differs" |
| `Open →` | `trade.js:240` | `arrow-right` |
| `·` separators | everywhere | **keep**. This is typography, not an emoji |

---

## 6. Components

### 6.1 Shell (signed-in `/trade/*`, and `/chain`)

```
+--------------------------------------------------------------+  frame #0c3424, full bleed
| [AX] AXK Trade        Stellar testnet (live dot)   (JS) Joe v|  top bar 56px, on frame
+-----------+--------------------------------------------------+
| ACTING AS |  +--------------------------------------------+  |
| [KT] Koperative...   |  sheet: --paper, r16, inset          |  |
| GAKR...4ZSN          |  margin: 0 12px 12px 0               |  |
|-----------|  |  scrolls internally if ever needed         |  |
| Overview  |  |                                            |  |
| Cooperative 1 |                                           |  |
| Inspector  2  |                                           |  |
| Logistics     |                                           |  |
| Port          |                                           |  |
| Buyer         |                                           |  |
|-----------|  |                                            |  |
| Public    |  |                                            |  |
| Verify    |  |                                            |  |
| Explorer  |  +--------------------------------------------+  |
+-----------+--------------------------------------------------+
  rail 232px
```

- **Top bar** (56px, on frame). Left: brand mark (24px square, r6, `--proof-bright` fill, `--frame` "AX" 12/800) + "AXK Trade" 15/700 `--on-frame`. Right: a network chip (1px `--frame-line` border, r-tag, 12/600 `--on-frame-2`, 6px `--proof-bright` dot; label "Stellar testnet" and, if demo, "· demo") and the user menu (28px initials avatar `--frame-hi` + name `--on-frame` + `chevron-down`; menu: "Sign out").
- **Rail = the role switcher** (232px, on frame). Group label "Roles" (12/600 `--on-frame-3`, sentence case). Items are 36px tall, r-control, padding 0 10px, 14/550 `--on-frame-2`, 16px Lucide icon (`layout-grid` Overview, `sprout` Cooperative, `clipboard-check` Inspector, `truck` Logistics, `anchor` Port, `wallet` Buyer). Count: mono 12 `--on-frame-3`, right-aligned, no bubble. Hover: `--frame-2` fill. **Selected: `--frame-hi` fill + 1px uniform `--frame-line` border + `--on-frame` text and count.** (`--proof-bright` on `--frame-hi` is 4.27, which fails as text, so the count does not turn green.) Never a left strip. Group 2 "Public": `scan-line` Verify a lot, `blocks` Chain explorer. Rail foot: "ALU Capstone 2026" 12 `--on-frame-3`.
- **Persona block** at the top of the rail (above the groups): "Acting as" label, persona name 13/650 `--on-frame`, Stellar address as TxRef-on-frame (mono 12 `--on-frame-2`, links to the account). It updates with the selected role. This replaces the in-sheet `.xt-persona` card, which frees 72px.
- **Sheet**: `--paper`, `border-radius: var(--r-sheet)`, `margin: 0 12px 12px 0`, `height: calc(100vh - 56px - 12px)`, `overflow: auto`, padding 28px 32px. The join between frame and sheet has no border; the value step is the edge.

### 6.2 Buttons

| Variant | Spec |
|---|---|
| Primary | `--proof` fill, white 14/650, h 38 (34 small), r-control, padding 0 16. Hover `--proof-strong`. Focus `--ring` (outer, never inset). |
| Secondary | `--field` fill, 1px `--control` border, `--ink` text. Hover `--sunk` fill. |
| Ghost | no border, `--proof` text, hover `--proof-wash` fill. |
| Danger | `--field` fill, 1px `--danger` border, `--danger` text (used for "Reject lot"). |
| Busy | label replaced by a 14px spinner + "Signing…"; keeps width; `aria-busy="true"`. |
| Disabled | `--sunk` fill, `--ink-3` text, `--line` border. **No `opacity`.** Primary actions are not disabled for validation; validate on submit and show the field error. |

### 6.3 Inputs, chips, form

- Input: h 38, `--field` fill, 1px `--control`, r-control, 14/450 `--ink`, placeholder `--ink-3`. Focus: border `--proof` + `--ring`. Error: border `--danger` + message 12/500 `--danger` below, with `circle-alert` 14px; the helper slot is reserved (16px) so the layout doesn't jump.
- Label above the field: `label` token `--ink-2`, 6px gap.
- Chips (commodity, grade): a **segmented control**, not floating pills. Use one row inside a 1px `--control` frame, r-control, with 32px segments. Selected segment: `--proof` fill, white text. Unselected: `--ink-2`, hover `--sunk`. This keeps `role="radiogroup"` and arrow-key navigation from `trade.js:176`. Commodities wrap to two rows max; if more, use a `<select>`.
- Field width follows the content class: quantity and moisture 140px, grade segmented, dates 160px, free text full.
- Form = **Docket panel** (§6.9).

### 6.4 Status tag (eight trade statuses, `ledger/workflow.py:3`)

h 22, padding 0 8, r-tag, 12/600, 14px icon + label, uniform 1px border. Tone comes from fill + text; the icon carries meaning for colour-blind users.

| Status | Label | Icon | Tone |
|---|---|---|---|
| Registered | Awaiting inspection | `circle-dashed` | neutral: `--neutral-wash` / `--ink-2` / border `--line` |
| Approved | Passed inspection | `badge-check` | positive: `--proof-wash` / `--proof` / border `--proof-wash` |
| Rejected | Rejected at inspection | `circle-x` | danger: `--danger-wash` / `--danger` |
| Funded | In escrow | `lock` | neutral |
| In Transit | In transit | `truck` | neutral |
| At Port | At port | `anchor` | neutral |
| Settled | Settled | `circle-check` | **solid**: `--proof` fill / white text, the only solid tag |
| Refunded | Refunded | `undo-2` | warn: `--warn-wash` / `--warn` |

In-flight states are deliberately neutral. Progress is shown by the Custody Strip, not by a rainbow of tag colours.

### 6.5 Custody Strip (the signature)

The nine steps, in order (`trade_api.py:151–161`): Registered · Inspected · Escrow funded · Dispatched · At port · Released · Split 40/40/20 · Members paid · Attested.

| Size | Where | Geometry |
|---|---|---|
| Micro | table rows | 9 segments, each 8x6px, 2px gap (88px total), r-notch. No labels. Followed by "5/9" mono 12 `--ink-3`. |
| Standard | lot header, docket | segments flex across up to 560px, 8px tall, 3px gap. Labels below each in 11/550 `--ink-3` (filled steps `--ink-2`); only the first, the current and the last labels show under 900px. |
| Timeline | `/trace/lot`, lot detail | vertical. Each row: 10x10 notch on a 1px `--line` spine, label 14/650, TxRef below, timestamp 12 `--ink-3` "30 Sep 2026, 11:06 Kigali". Row 44px; nine rows = 396px. |
| Specimen | login panel | standard geometry on frame: filled `--proof-bright`, hollow 1px `--frame-line`, labels `--on-frame-3`. |

**States per notch:**
- **Filled** (has tx): `--proof` fill (on frame: `--proof-bright`). In Standard and Timeline it is an `<a>` to the tx with `aria-label="Escrow funded, transaction 9eab5f…5bba17, opens Stellar Expert"`, and it takes focus.
- **Next** (first unfilled): hollow, 1.5px `--proof` border.
- **Pending**: hollow, 1px `--control` border.
- **Failed** (inspection rejected): `--danger` fill. The remaining notches are hollow with a 1px dashed `--line` border, meaning "will not happen".

The strip as a whole has `role="img"` (micro) with `aria-label="Custody: 5 of 9 steps on-chain. Next: Released to cooperative."`

**The rule:** a notch is filled if and only if `step.tx` is truthy. It is never filled to make a demo look complete. On the login specimen, if no settled lot exists, all notches render pending with labels and no hashes are shown.

When a step completes in-session, the new notch fills with `transform: scaleX(0→1)`, `transform-origin: left`, over `--t-stamp` `--ease`. This is the only celebratory motion in the product.

### 6.6 TxRef (transaction hash / address)

```
[ 9eab5f…5bba17  (copy) (arrow-up-right) ]
```

- Mono 12.5 `--ink`, first 6 + "…" + last 6 (addresses: first 4 + last 4). Full value in `title` and `aria-label`.
- Copy button: 24px square ghost, `copy` 14px, then `check` for 1.2s with toast-free `aria-live` text "Copied". External link: `arrow-up-right` 14px to `EXPLORER/tx/<hash>` (`/account/`, `/contract/` as appropriate), `target="_blank" rel="noopener"`.
- Inline form (in tables): no copy button, just a link with the icon.
- **Digests** (sha256) in key-value lists show in full: mono 12 `--ink-2`, `overflow-wrap: anywhere`, with a copy button at the right.

### 6.7 Lot table

- Sits in a panel (1px `--line` border, r-panel, `--paper`). Header row 36px `--sunk`, `label` `--ink-3`. Rows 44px, 1px `--line` dividers, hover `--sunk`, `cursor: pointer`; the whole row opens the lot or selects it into the docket.
- **Selected row: `--proof-wash` fill + 1px uniform `--proof` outline (`box-shadow: inset 0 0 0 1px var(--proof)`).** Never a left strip.
- Columns: Lot (mono 12.5 `--proof` link, e.g. `AXK-LIVE-CP-20260930-0001`) · Commodity · Qty (num, right) · Custody (micro strip) · Status (tag) · Next (13 `--ink-2`, truncate with title).
- `thead` is sticky. The table body scrolls inside the panel; **the page does not scroll.**
- Under 720px it becomes a stacked list: ref + tag on line 1, commodity · qty on line 2, micro strip on line 3.

### 6.8 Verdict line

This is the one sentence that states what the chain says, e.g. "An authorised inspector passed this lot on-chain, and its settlement is attested." Layout: 1px border, r-panel, padding 14px 16px, 20px icon + 16/600 `--ink` sentence.

| Verdict | Fill / border | Icon |
|---|---|---|
| Passed / settled / at port | `--proof-wash` / `--proof-wash` | `shield-check` in `--proof` |
| Rejected | `--danger-wash` / `--danger-wash` | `shield-x` in `--danger` |
| Registered, awaiting | `--neutral-wash` / `--line` | `shield` in `--ink-3` |
| In transit | `--neutral-wash` / `--line` | `truck` in `--ink-2` |

### 6.9 Docket (action panel)

This is the right-hand panel on each role screen, 380px wide, `--paper`, 1px `--line`, r-panel, padding 20. Its contents:
- Heading h2 ("Register a lot", "Inspect AXK-LIVE-…", "Fund escrow", "Dispatch", "Gate-in at port", "Settle").
- For lot actions: the selected lot's ref (mono-ref at 16px), its standard Custody Strip, and a two-row kv summary.
- Fields (§6.3).
- Footer: the primary action, full width, plus one line of `small` `--ink-3` saying what will be signed ("Signs `inspect` on the lot registry contract as Inspector GCPK…3AHJ").
- With no lot selected: the empty state (§8).

### 6.10 Ledger strip (replaces KPI tile grids)

This is one bordered row (1px `--line`, r-panel, `--sunk` fill, h 72) split by 1px `--line` vertical rules into 4–5 cells. Each cell holds a `label` in `--ink-3` and a `num-lg` in `--ink`. Money is "250,000 RWF" with "RWF" at 13/600 `--ink-3`. It must not become a card grid or icon tiles. The rightmost cell is the role's money figure (wallet balance or settled value).

### 6.11 Signing overlay, toast

- **Signing overlay** (`.xt-busy`): the sheet is dimmed with `rgba(251,251,248,0.72)`, and a centred float card (r-panel, `--shadow-float`, 320px) shows a spinner + "Signing on Stellar" 15/700 + the step name + "Usually 5–8 seconds." `role="alertdialog"` is already in place; keep it.
- **Toast**: bottom-right of the sheet, 360px, `--frame` fill, `--on-frame` text 13/550 (12.38), r-panel, `--shadow-float`. Success has a `circle-check` in `--proof-bright` + a TxRef link in `--proof-bright` (5.80). Error has `circle-alert` in `--danger-on-frame`. It auto-dismisses after 6s, stays while hovered, and uses `aria-live="polite"`.

### 6.12 QR block (trace)

This is a panel holding a 120px QR (black on white, 8px quiet zone, inside a `--field` square with 1px `--line`), with "Share or print" h2, one line of `small` `--ink-2`, and two buttons: Secondary "Copy link" and Ghost "Print". On print, use `@media print` to hide the frame and rail and print the sheet only.

---

## 7. Screens

All signed-in screens are designed at **1440x900** and must hold at **1280x800** with no page scroll.

### 7.1 Login (`/login`, overrides Frappe's)

Override by adding `www/login.html` + `www/login.py` to axk_capstone (custom-app www pages take precedence over frappe's). Extend `templates/axk_lean.html`. POST `usr`/`pwd` to `/api/method/login` with the CSRF header, then redirect to `?redirect-to=` or `/trade`. Show Frappe's error message inline. Keep "Forgot password?" pointing at `/login#forgot` only if email is configured; otherwise omit it.

```
+----------------------------+-----------------------------------+
| frame #0c3424   44% (min 440) | paper   56%                    |
|                            |                                   |
| [AX] AXK Network           |        Sign in                    |
|                            |        Use a demo account or      |
|                            |        your own credentials.      |
| Every lot verified         |                                   |
| before it is paid.         |        Email  [               ]   |
|  (display 40/800)          |        Password [          ] Show |
|                            |        [      Sign in        ]    |
| Coffee and tea from a      |                                   |
| Rwandan cooperative,       |        Demo accounts              |
| traced through nine        |        +---------------------+    |
| on-chain steps on Stellar. |        | Cooperative  coop@… |    |
|                            |        | Inspector    insp@… |    |
| [Custody Strip specimen,   |        | Logistics    …      |    |
|  9 notches + labels, from  |        | Port         …      |    |
|  the latest settled lot]   |        | Buyer        …      |    |
| AXK-LIVE-CP-…-0001  9/9    |        | Supervisor   …      |    |
|                            |        +---------------------+    |
| Stellar testnet · Soroban  |                                   |
| ALU capstone · O. Jesse    |                                   |
+----------------------------+-----------------------------------+
```

- **Brand panel**: padding 48. Wordmark top-left. Headline `display` in `--on-frame`. Sub-line 15/450 `--on-frame-2`, max 380px. The Custody Strip specimen sits near the bottom third, with the lot ref (mono 12.5 `--on-frame-2`) and "9/9 on-chain" beside it; each filled notch is a real link. Footer 12/500 `--on-frame-3`: "Stellar testnet · Soroban contracts" / "ALU capstone 2026 · Oghenetejiri Jesse". There is no illustration, no gradient and no photograph.
- **Form column**: max-width 380, vertically centred. `h1` "Sign in", sub `body` `--ink-2`. Fields per §6.3. "Show" is a Ghost text button inside the password field's right edge. Sign in is Primary, full width, h 42.
- **Demo accounts**: a ruled list, not cards. Heading `label` "Demo accounts" + `small` `--ink-3` "Click to fill. Password is the same for all." Panel 1px `--line`, r-panel. Six rows, 44px each, divided by `--line`. Each row is a `<button type="button">` with the role icon (16px, `--ink-3`) · role name 14/650 `--ink` · one-line duty 12 `--ink-3` (Cooperative "Registers lots"; Inspector "Passes or rejects"; Logistics "Dispatches with seal"; Port "Gate-in and customs"; Buyer "Funds and settles"; Supervisor "Sees every role") · email mono 12 `--ink-2` right-aligned. Hover is `--sunk`. Focus is `--ring`. Click fills both fields, then moves focus to Sign in. **Selected row** (the one just filled): `--proof-wash` fill + uniform 1px `--proof` outline + a `check` icon replacing the role icon.
- **Credentials source**: `login.py` builds `context.demo_accounts` from `frappe.conf.axk_demo_accounts` (a list of `{role, email}`) and `frappe.conf.axk_demo_password`, and only when the demo flag is on. **Never write a password literal into the repo** (block-secrets will fire, and it should). If the config is absent, the panel is not rendered.
- 390px: the brand panel collapses to a 160px frame band (wordmark + headline at 28/800 + micro specimen). The form goes below. The demo list drops the duty line.

### 7.2 Overview (`/trade`)

Sheet content:
1. Header row: `h1` "Overview" + `body` `--ink-2` "Nine steps from cooperative to buyer. Each one is a Soroban contract call." On the right: Secondary "Open chain explorer".
2. Ledger strip: Lots registered · Awaiting inspection · In escrow · In transit · Settled value.
3. **Flow row** (the dominant element): six role stations in one horizontal band (panel, h ~150) joined by a 1px `--line` connector. Each station shows the role icon, role name 14/700, the count waiting on that role (`num-lg`), and the Lucide `arrow-right` "Open". Stations are links, not cards with shadows. Hover gives a `--sunk` fill to the station.
4. Recent lots table (§6.7), 6 rows, internally scrolling.

### 7.3 Role screens (`/trade/coop`, `/inspect`, `/logistics`, `/port`, `/buy`): one template

```
| h1 Cooperative                         [persona is in rail]      |
| Register lots and follow them through inspection and escrow.     |
| [ ledger strip: 4–5 cells                                      ] |
| +-- Queue: "Waiting on you" / "My lots" ----+ +-- Docket ------+ |
| | lot table, sticky head, scrolls inside    | | form / action  | |
| |                                           | | custody strip  | |
| |                                           | | [Primary]      | |
| +-------------------------------------------+ +----------------+ |
```

Grid: `grid-template-columns: 1fr 380px; gap: 20px`. The queue panel height is `calc(100% - header - strip)`. Queue tabs (when a role has two lists, e.g. Inspector "Waiting (2)" / "Done"): an underline tab set, 2px `--proof` bottom rule on the active tab across the full tab width, `--ink` text; inactive `--ink-3`. (This is a tab indicator spanning the tab, not a selected-item side strip.)

| Role | Queue | Docket |
|---|---|---|
| Cooperative | My lots | Register a lot (commodity segmented, grade A/B/C, qty, harvest date) |
| Inspector | Waiting for inspection / Done | Inspect: inspected grade, qty, moisture %, notes; **Pass** primary + **Reject** danger (reason select) |
| Logistics | Ready to dispatch | Carrier, driver, plate, seal number |
| Port | In transit | Seal check against waybill (shows the expected seal in mono, typed value must match), container, customs ref |
| Buyer | Passed lots / My trades | Price per kg, total in RWF, Fund escrow; later Settle |

### 7.4 Lot detail (`/trade/lot?…`)

- Breadcrumb `small` `--ink-3`: "Buyer / Lot".
- Header: lot ref in `mono-ref` + status tag; sub `body` `--ink-2` "Coffee (parchment) · Huye, Southern Province · Koperative Twisungane". Right: Secondary "Public page" (`arrow-up-right`) and Ghost "Copy share link".
- The standard Custody Strip, full width.
- The verdict line.
- Two columns, `1fr 1fr`: left is the custody timeline (9 rows, 396px); right has the "Lot and transport" kv panel and the "Accounts and contracts" kv panel (TxRef for each). kv: `dt` 12/600 `--ink-3` 160px column, `dd` 13/500 `--ink`.

### 7.5 Public trace (`/trace`, `/trace/lot?ref=`), no login

The shell is the **top bar only** (no rail). Left: brand + "Verify a lot"; right: "Public record · no sign-in" 12 `--on-frame-2`. The sheet is centred, max-width 1120.

- `/trace`: `h1` "Verify a lot". A single search field (h 46, `scan-line` icon, placeholder "Lot reference, e.g. AXK-LIVE-CP-20260930-0001") + Primary "Verify". Below is a table of live lots (ref, commodity, origin district, custody micro strip, status). The privacy note `small` `--ink-3` sits at the bottom of the sheet (keep its text; it is good).
- `/trace/lot`: identical structure to §7.4, minus private fields. The verdict line is the hero, set at 18/650 here. Add the QR block (§6.12) to the right column, below "Accounts and contracts".
- **390px (the QR-scan case)**: one column. Order: ref + tag, verdict, standard strip (first/current/last labels), timeline, lot kv, accounts, QR block. Hashes wrap. Tap targets ≥ 44px. Page scroll is acceptable on phone only.

### 7.6 Chain explorer (`/chain`)

It is currently three long sections and must become **one viewport with three tabs** in the sheet header: "Settlement (live)" · "Hash chain" · "History (synthetic)". Use the underline tab set from §7.3, deep-linkable with `#live`, `#chain`, `#history`.

- **Header**: `h1` "Chain explorer" + source tags: "Live · Stellar testnet" (neutral tag with a 6px `--proof` dot) and "Synthetic · demo data" (neutral tag with `flask-conical` icon). Synthetic charts carry the synthetic tag in their panel heading as well. Live and synthetic must never be visually confusable.
- **Live tab**: ledger strip (escrowed, released, members paid, events) → two-column: "Where the money went" flow (left, 60%) + "Verified before paid" summary with the contract events table (right, 40%, scrolls inside).
- **Hash-chain tab**: the event list renders as the vertical timeline geometry. Each event shows a node (mono sequence no.), its hashes (mono 12), and a recomputed status: `circle-check` `--proof` "Recomputed, linked" / `circle-x` `--danger` "Differs from stored". The overall status line is a verdict line (§6.8). The tamper control is a Secondary button "Tamper with event…", and a broken chain turns the subsequent nodes `--danger` with a dashed spine.
- **History tab**: monthly bars and completion. **Colour rule:** anchored/on-chain = `--chart-proof`; off-chain, pending and other categories use the graphite ramp `--chart-g1/g2/g3`. There are no other hues. Read `--chart-*` via `css()` as chain.js already does (`chain.js:15`). Gridlines are `--chart-grid`, axis labels are 11/500 `--ink-3`, and values are in tooltips (float card, `--shadow-float`).

---

## 8. States

| State | Signed-in screens | Trace / login |
|---|---|---|
| **Loading** | Skeleton matches the final layout exactly: ledger strip cells, 6 table rows (micro strip as 9 grey notches), docket blocks. Fill `--sunk`, a 1.4s opacity pulse 1→0.6; static under reduced-motion. The existing `.xt-skeleton` is restyled, not removed. | Login: Sign in button goes Busy. Trace: skeleton of verdict + timeline. |
| **Empty** | Queue panel: centred inside the panel, a 20px `inbox` icon `--ink-3`, a 14/650 line that says why ("Nothing waiting for inspection."), one `small` line on what unblocks it ("Lots appear here when a cooperative registers one."), and, if the role can act, a Ghost button. The panel keeps its full height so the frame of the work stays visible. Docket with no lot: "Select a lot from the queue to inspect it." with `mouse-pointer-click` icon. | Trace no match: verdict-style neutral line "No lot with reference `XYZ`." + Ghost "Search again". |
| **Error** | Inline in the docket under the button: `circle-alert` + `--danger` message, plus the chain's refusal reason verbatim from `REFUSALS` (`ledger/workflow.py:24`), e.g. "Only inspected, approved lots can be funded." Network/RPC failure: error toast + a "Try again" Ghost. Field errors per §6.3. Never a raw traceback. | Login: inline `--danger` line under the password field, "Email or password is incorrect." Trace RPC down: neutral verdict line "The ledger could not be reached. The record below is the last confirmed copy." |
| **Success** | The signing overlay closes. The new notch stamps in (§6.5), the tag updates, and a success toast shows a TxRef link. The row stays selected so the user sees what changed. | Login: redirect. Trace: the verdict line is the success state. |

**Pending tx** is a distinct state: the next notch shows the hollow `--proof` border with a 1.2s border-opacity pulse, and the tag stays at the old status. There is never an optimistic fill.

---

## 9. Responsive

| Width | Behaviour |
|---|---|
| ≥ 1280 | full shell, rail 232 |
| 960–1279 | rail collapses to 64px icons with tooltips (the selected item keeps fill + uniform border); docket 340 |
| < 960 | rail is removed. The top bar gains a **role switcher button** ("Cooperative" + `chevron-down`, 1px `--frame-line` border) that opens a full-width float list of roles, with the persona at its top. The docket stacks under the queue. Page scroll is allowed. |
| 390 | sheet margin 0, radius 0; padding 16; ledger strip becomes a 2-column grid; tables become stacked lists (§6.7); all targets ≥ 44px; login per §7.1. |

---

## 10. Motion

- Hover and colour changes: `--t-fast` `--ease`.
- Panels, popovers and the docket swapping lots: `--t-panel`, a 4px translate + opacity fade. Settle, never bounce.
- Notch stamp: `--t-stamp` (see §6.5). Login specimen on first load: the notches fill left to right, staggered 40ms each, once.
- `@media (prefers-reduced-motion: reduce)`: all transitions are instant, and the pulse on the pending notch stays as a static `--proof` border.

---

## 11. Focus and keyboard

- Every interactive element gets a visible `:focus-visible` ring: `--ring` on paper, `--ring-on-frame` on frame. The ring is always outside the element (an outer 2-leg ring), so it survives on filled buttons.
- Rail items, table rows (`tabindex="0"`, Enter opens / selects), demo-account rows, filled notches and TxRef buttons are all keyboard-reachable.
- The `xt-main` skip target (`tabindex="-1"`) stays; add a visually hidden "Skip to content" link as the first element in the shell.

---

## 12. Prohibitions (each one is a review defect)

1. **No emoji or Unicode symbol glyphs as icons**, including ✓ ✕ ○ ● ◷ ◐ ↩ ↗ → ⚓ 🚚 ≠. Use inline Lucide SVG only. The `·` separator is allowed.
2. **No one-sided accent borders** for selected, active or status (no `border-left` strips, no top-edge highlight). Selected = fill + uniform border/outline.
3. **No filled notch, green tick or "verified" wording without a real tx hash behind it.** No fake or placeholder hashes, anywhere, including on login.
4. **No purple, no blue.** `#2a78d6`, `#3987e5` and the chain.css pink/orange series are deleted. Charts are green + graphite only.
5. **No gradients**, glows, glassmorphism or neon. The frame is a flat `--frame`.
6. **No Inter, Roboto, system-ui or Arial as a rendered face.** These appear only as fallbacks after the self-hosted fonts.
7. **No card grids of equal tiles.** KPIs are the ledger strip, roles on Overview are the flow row, and lists are tables.
8. **No page scroll on signed-in screens at 1280x800 and up.** Tables scroll inside their panel.
9. **No raw hex outside §3**, and no inline `style=` colours (`trade.js:235`'s inline grid style moves to CSS).
10. **No `opacity` for disabled or muted text.** Use the explicit tokens.
11. **No proof green (`--proof`) on the frame** (1.92), no inputs on `--sunk` (2.93), and no text lighter than `--ink-3`.
12. **No tracked uppercase eyebrows.** Labels are sentence case.
13. **No Frappe chrome** on any capstone route: no Frappe navbar, footer, "Login to Frappe" or F logo. `/login` is overridden.
14. **No dark-mode toggle.** It is one theme.
15. **No crypto iconography** (coins, rockets, chains-as-links decoration, "web3"). "Stellar" and "Soroban" are named plainly as infrastructure.

---

## 13. References (what was taken)

- **Joe's REMIS shell / AXK webapp Rev 3**: the frame + rail + inset sheet structure, with colour bought by area. Joe has approved this structure twice, so it is carried over as-is.
- **Mercury (dashboard)**: restraint. One accent, money set large in tabular figures, and hairline tables over cards.
- **Stripe dashboard**: the docket pattern (list + detail side panel), and status tags that stay neutral for in-flight states.
- **Linear**: the rail density (36px items, mono counts without bubbles), the outer focus ring and settle-not-bounce motion.
- **Superhuman**: one thing dominates each screen (here, the queue), and the keyboard reaches everything.
- **stellar.expert**: what an examiner will click through to. TxRef formatting (6…6) matches what they will see there, so the hand-off reads as continuous.
- **Anti-reference**: the current factory Frappe `/login` (rendered 2026-10-30 at capstone.axk.org, "Login to Frappe" with the F logo) and the current trade screens (`docs/screenshots/02-cooperative.jpg`: system font, five equal KPI cards, floating chip clouds, glyph icons).

---

## 14. Build order (for the implementer)

1. Fonts + §3 tokens into `axk.css`; delete the dark block; map old `--brand*`/`--text-*` names to new tokens (or rename in place).
2. Shell: `axk_nav.html` becomes top bar + rail; persona moves into the rail.
3. Icon helper + full glyph sweep (§5 table). Verify with `grep -nP '[\x{2190}-\x{2BFF}\x{1F300}-\x{1FAFF}]' -r www public/js templates` returning nothing.
4. Status tag, Custody Strip, TxRef components in `trade.js`, and the Jinja macros for trace.
5. Role screen template (queue + docket), then Overview, Lot detail.
6. `/login` override.
7. Trace pages, then chain explorer tabs + chart recolour.
8. States pass, 390px pass, keyboard pass.

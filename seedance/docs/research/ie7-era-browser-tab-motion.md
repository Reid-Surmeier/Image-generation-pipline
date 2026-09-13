# IE7-era browser tab motion (2006–2008)

Research note grounding the "open a new tab" animation for the flat Windows Live / IE7
toolbar. Compiled 2026-09-13 from Microsoft's IEBlog archive and a period screen recording.
**[OBSERVED]** = stated by a cited source or read frame by frame from footage.
**[INFERENCE]** = period-typical behavior not pinned to a citable sentence.

## 1. What IE7 actually did when a tab opened

Source footage: "Using Tabs in Internet Explorer 7", YouTube `PC6flwPVMKg`, uploaded
2008-05-28 by "Noobie", 640×480 at 15 fps, IE7 on Windows XP with the Google Toolbar.
The tab-open sequence at t = 63.6–65.6 s is cut, cropped to the tab row, and registered as
`docs/evidence/board-icons-test/references/ref-ie7-new-tab-insert.gif` / `.mp4`
(provenance in `provenance.json`).

- **[OBSERVED] The new tab appears fully formed in one frame.** Between two consecutive
  15 fps frames (≤ 67 ms) the blank New Tab stub becomes a full-width tab and a fresh stub
  appears to its right. No width tween, no slide, no fade.
- **[OBSERVED] It reads "Connecting..." first.** The inserted tab shows the page icon and
  the text "Connecting..." for 9 frames (~0.6 s) while the browser frame (title bar,
  address bar) still shows the previous tab. The previous tab keeps its close ×.
- **[OBSERVED] Then the title swaps and the row re-lays out.** In one frame the label
  becomes "Welcome to Tabbed Brow…", the close × moves to the new tab, and the neighbouring
  tab widens to fill the row ("Amazon.com: Online Sho…" → "Amazon.com: Online Shoppin…").
  Again a single-frame change.
- **[OBSERVED] The stub is a small blank tab at the right end of the row.** Hovering shows
  the tooltip "New Tab (Ctrl+T)". Its face is a lighter, shorter tab shape.
- **[OBSERVED] No loading spinner is visible in the tab** at this resolution during
  "Connecting..."; the icon is static across all nine frames.

## 2. What Microsoft said (IEBlog, primary)

- "IE7 gives you several ways to open a new tab, including clicking the small empty tab on
  the right, pressing the Ctrl key while clicking a link, clicking a link with the middle
  mouse button or pressing Alt-Enter" — described in reviews of the shipped build
  ([Computerworld review](https://www.computerworld.com/article/1643988/review-just-say-yes-to-internet-explorer-7.html)).
- New tabs open **blank by default** and put focus in the address bar: "The default is to
  open it in a blank page because this is faster, and we can predictably put focus directly
  to the address bar for blank pages. … Fast is good." — Aaron Sauve, PM,
  [Your Tab Settings…](https://learn.microsoft.com/en-us/archive/blogs/ie/your-tab-settings),
  2006-07-27. The first new tab shows the `about:Tabs` "Welcome to Tabbed Browsing" page
  until dismissed.
- "Open new tabs next to the current tab" is the default; earlier betas appended at the
  end of the row (same post).
- Quick Tabs button "appears on the left hand side of the tab band … when you have two or
  more tabs opened"; Quick Tabs thumbnails show "a loading animation" if a page has not
  finished — the only animation Microsoft mentions in the tab feature posts — Uche,
  [Quick Tabs](https://learn.microsoft.com/en-us/archive/blogs/ie/quick-tabs), 2006-02-10.
- The Beta 1 implementation post
  ([IE7 Tabbed Browsing Implementation](https://learn.microsoft.com/en-us/archive/blogs/ie/ie7-tabbed-browsing-implementation),
  2005-05-26) describes tab creation, background/foreground opening and keyboard switching.
  It never mentions animation.

## 3. Neighbours in the period

- **Firefox 2/3 (2006–2008):** no tab open/close animation. Tab animations were designed for
  Firefox 4 in 2010 ([Browser Watch, 2010-02-04](https://www.browser-watch.com/2010/02/04/tab-animations-for-firefox-4/))
  and the drag/detach animation was backed out before release
  ([Bugzilla 690227](https://bugzilla.mozilla.org/show_bug.cgi?id=690227),
  [meta 596954](https://bugzilla.mozilla.org/show_bug.cgi?id=596954)). Tab-strip tweening
  is a 2010+ idiom.
- **Chrome 1.0 (September 2008):** animated the tab strip on insert (a width tween).
  The 2008 `tab_strip.cc` constants could not be fetched during this pass (googlesource and
  the GitHub mirror both 404 on the initial-commit path); treat as **[INFERENCE]** and out
  of period for a 2006–2007 Windows Live/IE7 look.
- **Windows XP (IE7's common host):** no compositor; UI changes are immediate repaints.

## 4. The idiom, for the pipeline

| Beat | Duration | What changes | What never happens |
| --- | --- | --- | --- |
| Hold | ≥ 0.5 s | Cursor may rest on the stub; nothing moves | No hover glow, no scale |
| Insert | 1 frame | Stub becomes a full tab reading "Connecting..."; new stub appears to the right | No slide-in, no width grow, no fade |
| Connecting | ~0.6 s | Static hold with page icon + "Connecting..." | No spinner in the tab |
| Title swap | 1 frame | Label becomes the page title; close × moves to the new tab; row re-lays out | No text scroll, no crossfade |
| Settle | rest | Static | — |

Motion kind for the reference registry: **reveal** (one-shot state change; nothing travels).
Grammar for the brief: **smooth** (anti-aliased flat toolbar, not quantized pixel art).

## 5. Sourcing notes

- The reference clip is a 2 s crop of a third-party tutorial recording, kept as research
  evidence with full provenance (video id, uploader, date, source hash, crop, timestamps).
  It is not game data; the registry entry says so.
- The pasted toolbar (Muse-generated flat IE7 bar, 1706×69) is the identity authority for
  the anchors; the after-states are composited from its own tab, stub, and Page-icon pixels
  plus DejaVu Sans for the "Connecting..." / "Blank Page" labels (the source font is not on
  this machine — a known, visible difference in the anchors).

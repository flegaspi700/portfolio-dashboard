# Accessibility

The dashboard is a website (the page arrives in Phase 3). The checklists
and how to test are in the standard's `accessibility.md`; this file records
which apply and the results.

**Applies:** Apps and websites (WCAG 2.2 AA)
**Target:** NFR3 in `requirements.md`

## Project-specific notes

The site is the dashboard page (`index.html`), a page per repo
(`repos/*.html`) and the Markdown report. It has no forms, inputs, images,
video or motion. The only controls are links, the table's sort buttons and
the table's scrolling region. Checks are run on the live site in Chrome;
`tests/report/` checks the markup on every build.

### The page checklist

The standard's WCAG 2.2 AA items as they apply here, and how each is
checked. Results go in Test passes below.

| Item | What it means here | How checked |
|---|---|---|
| Keyboard | Every link, sort button and the table's scrolling region can be reached with Tab in reading order; sort buttons work with Enter and Space; no traps | Real key presses in Chrome |
| Visible focus | A 3 px `#0b57d0` outline on links, buttons and the table region | Real Tab presses, computed style |
| Contrast | Text 4.5:1, borders, health edges and the focus outline 3:1 | WCAG formula on every colour pair in `style.css` |
| Not colour alone | Health, level and scan status are words; the sort direction is ▲ or ▼; health tiles carry their name | Tests in `tests/report/test_page.py`, and a look |
| Text alternatives | No images or icons; ▲ and ▼ only repeat `aria-sort` | Page inspection |
| Labels | No inputs | n/a |
| Zoom and reflow | No horizontal scrolling at 320 CSS px (WCAG 1.4.10), apart from the data tables, which scroll inside their own labelled region | Each page in a 320 px frame |
| Motion | Nothing moves or flashes | n/a |
| Target size | Targets 24 × 24 px, or spaced so 24 px circles around them don't overlap (WCAG 2.5.8) | Measured in Chrome |
| Structure | `lang`, a title per page, one `main`, headings in order, real table headers with a caption, the scrolling region labelled | Page inspection; table markup also by tests |
| Screen reader | The summary, the attention list and the table read sensibly | Narrator or NVDA: the owner |
| Automated scan | No issues in Lighthouse's accessibility audit | Lighthouse in Chrome DevTools: the owner |

### Repo table (S4.2.1)

What the table must keep true. Tests in `tests/report/test_page.py` check
the markup; the keyboard and focus items need a browser.

- [x] A real `<table>` with a `<caption>`, a `<thead>`, column headers as
      `<th scope="col">` and each repo's name as `<th scope="row">`
- [x] Without scripts the table still lists every repo, in attention order
- [x] Sorting: the script makes each column header a `<button>`, so Tab,
      Enter and Space work as for any button; the sorted column has
      `aria-sort` (`ascending` or `descending`) and the others have none
- [x] The sort direction also shows as ▲ or ▼, not by colour
- [x] Header buttons and the scrolling table region show a visible focus
      outline, and the region can be reached by keyboard to scroll it
- [x] Every state (health, level, scan) is text; nothing is colour alone
- [x] Header buttons are at least 24 px tall (target size)

Checked 2026-11-18 (S4.2.1 on fixture data; the live page in the Phase 3
pass below).

## Test passes

| Date | Commit | Checks run | Result | Notes |
|---|---|---|---|---|
| 2026-11-18 | b18ec33 (live site, run 44342423544) | Keyboard, visible focus, contrast, not colour alone, text alternatives, zoom and reflow, target size, structure, on the dashboard page and a public repo page | Fail: B1 | **B1:** at 320 CSS px the dashboard page scrolls sideways by 13 px: the levels list's left column is as wide as its longest label ("Level 0 · Not on standard"), pushing the values past the edge. The repo page reflows cleanly. **Passed:** 29 focusable elements in reading order (the table region, 9 sort buttons, 17 repo links, 2 links), each with a visible 3 px outline, no positive tab indexes; contrast 4.54:1 to 17.40:1 on all 10 colour pairs; target size: sort buttons 24 px; repo links 21 px tall but at least 75 px wide with centres 33 px apart, and request and back links 21 px tall with no neighbouring target their 24 px circle would overlap, so all pass 2.5.8's spacing exception; `lang`, titles, one `main`, headings in order, table captions and scopes, labelled regions. **Not run yet:** screen reader and Lighthouse (the owner's). |
| 2026-11-18 | fix/B1 branch (fixture site on 127.0.0.1) | Zoom and reflow, re-check for B1 | Pass | At 320 CSS px the dashboard, a public and a private repo page have no sideways scrolling; level labels wrap in a 109 px column. At normal width the lists look as before. The live site gets the fix with the next run after the merge. |
| 2026-11-18 | 77d81c5 (live site, run 44355374079) | Zoom and reflow on the live site; Lighthouse; screen reader | Pass | The agent: at 320 CSS px the dashboard, a public and a private repo page have no sideways scrolling (B1 fixed). The owner: Lighthouse (mobile) Accessibility 100, Performance 99, Best Practices 96 (the site has no favicon, so the browser logs a 404), SEO 90 (no meta description); Narrator read the headings, the attention list, the table and the sort buttons sensibly. With the first pass, every item in the page checklist passes: NFR3 met. |

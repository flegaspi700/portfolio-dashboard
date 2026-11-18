# Accessibility

The dashboard is a website (the page arrives in Phase 3). The checklists
and how to test are in the standard's `accessibility.md`; this file records
which apply and the results.

**Applies:** Apps and websites (WCAG 2.2 AA)
**Target:** NFR3 in `requirements.md`

## Project-specific notes

The page arrives in Phase 3 (E4); the Phase 3 exit criteria include passing
these checks. The rest of the page's list is recorded before the Phase 3
accessibility pass.

### Repo table (S4.2.1)

What the table must keep true. Tests in `tests/report/test_page.py` check
the markup; the keyboard and focus items need a browser.

- [ ] A real `<table>` with a `<caption>`, a `<thead>`, column headers as
      `<th scope="col">` and each repo's name as `<th scope="row">`
- [ ] Without scripts the table still lists every repo, in attention order
- [ ] Sorting: the script makes each column header a `<button>`, so Tab,
      Enter and Space work as for any button; the sorted column has
      `aria-sort` (`ascending` or `descending`) and the others have none
- [ ] The sort direction also shows as ▲ or ▼, not by colour
- [ ] Header buttons and the scrolling table region show a visible focus
      outline, and the region can be reached by keyboard to scroll it
- [ ] Every state (health, level, scan) is text; nothing is colour alone
- [ ] Header buttons are at least 24 px tall (target size)

## Test passes

| Date | Commit | Checks run | Result | Notes |
|---|---|---|---|---|

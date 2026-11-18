# Manual tests

Checks only a person can judge: how something looks, feels or plays.
Write the steps once per feature, then record a result each run. Rules: the
standard's `testing.md` → Manual tests.

---

## F3.2 — Scheduled Action

**What to check:** a real `publish` run on GitHub works end to end, and its
public log gives nothing away. Tests can only read the workflow file; this
is the run itself (S3.2.1).

**Steps:**
1. After the F3.2 PR is merged, open the repo's **Actions** tab, choose
   **publish**, then **Run workflow** on `main` (or wait for 06:00 UTC).
2. Wait for all three jobs (`scan`, `deploy`, `result`) to finish.
3. Open https://flegaspi700.github.io/portfolio-dashboard/ and check that
   the report shows the scan time of this run and one row per in-scope repo.
4. Open the `scan` job's **Scan** step log and check:
   - it shows counts only: repos in scope, could not scan, API requests,
     seconds; no repo names, no file content;
   - the token appears only as `***`;
   - the time is under 5 minutes and the request count under 1,000 (NFR1).
5. Check the run's result: green for a complete scan; red if any repo could
   not be scanned (then the page still deployed, flagging those rows).

**Results:**

| Date | Commit | Result | Notes |
|---|---|---|---|
| 2026-11-17 | 780faee | Pass | Run 44142627009 (manual): scan, deploy, keep-alive and result all passed. The page showed this run's scan (17:57 UTC) and all 17 repos. The Scan step logged counts only, the token showed as `***` and its value was nowhere in the full log. 84 API requests, 20.6 s (NFR1). The default Pages theme loads one helper script (anchor-js) from cdnjs, with an integrity hash; Phase 3 replaces the theme. |

---

## F3.3 — Failure alert and keep-alive

**What to check:** a failed run reaches the owner as an alert, the last good
page stays up, and the keep-alive step works on a real run (S3.3.1, S3.3.2,
NFR4's forced-failure test).

**Steps:**
1. Check your GitHub notification settings send failed-workflow emails:
   github.com → Settings → Notifications → System → Actions →
   "Only notify for failed workflows" (or all), by email.
2. After a good `publish` run (F3.2's check), open **Actions** → **publish**
   → **Run workflow**, tick **force_failure**, and run it.
3. Check the run fails at the `scan` job's **Forced failure** step, the
   `deploy` job is skipped, and the page still shows the earlier scan time.
4. Check the failure email arrives.
5. On any run, check the **keep-alive** job succeeded.

**Results:**

| Date | Commit | Result | Notes |
|---|---|---|---|
| 2026-11-17 | 780faee | Pass | Run 44142953144 (manual, force_failure): scan failed at Forced failure, deploy skipped, result failed, keep-alive passed. The page kept the earlier scan (17:57 UTC). The owner received GitHub's failure email. |

---

## F4.1 — Portfolio summary

**What to check:** the page reads well in a real browser, the old-data
notice appears only when the data is old, and a first-time reader gets the
picture fast (S4.1.2, S4.1.3; F4.1's Done when). Tests check the HTML; the
notice's script and the reading need a browser and a person. The script's
logic was also run against fake clocks with Node on 2026-11-18 (hidden at
35 h 59 min, shown at 36 h 1 min).

**Steps:**
1. Build the site locally (`.venv\Scripts\python -m report`) and open
   `output/site/index.html` in a browser.
2. Check the tiles show repos, could not scan, each health value and each
   level, each with a text label, and the levels section links to the
   standard's compliance spec.
3. Old-data notice: the local scan output is less than 36 hours old, so no
   notice shows. Save a copy of the page, change the `datetime` of its
   `scanned-at` element to two days back, and open the copy: the notice
   shows. With scripts turned off, the scan time still shows and the notice
   doesn't.
4. After the merge, check the same on
   https://flegaspi700.github.io/portfolio-dashboard/.
5. First-reader test: someone who hasn't seen the page opens the link and,
   within 3 minutes and without help, names the project that needs
   attention first.

**Results:**

| Date | Commit | Result | Notes |
|---|---|---|---|

---

## F4.4 — Request links

**What to check:** a request link opens GitHub's new-issue form in that
repo, filled in, and changes nothing by itself; private repos have none
(F4.4's Done when). Tests check the links' URLs; following one needs a
signed-in browser.

**Steps:**
1. On the live page (after the merge), open a public repo that shows
   "Request a status update" or "Request standard adoption".
2. Follow each link: GitHub's new-issue form opens in that repo with the
   title and body filled in.
3. Close the tab without submitting, and check the repo's Issues tab has
   no new issue.
4. Open two private repos' pages and check they have no Requests section.

**Results:**

| Date | Commit | Result | Notes |
|---|---|---|---|

---

## F4.2 — Sortable table

**What to check:** every repo can be sorted by keyboard, and states aren't
shown by colour alone (F4.2's Done when; `accessibility.md`, Repo table).

**Steps:**
1. Open the page (built locally, or the live page after the merge).
2. Without the mouse, press Tab until a column header has focus; check the
   focus outline is visible.
3. Press Enter: the table sorts by that column, ascending, and the header
   shows ▲. Press Space: it reverses and shows ▼. Repeat for a number
   column (Risks) and Health; missing values (—) stay last both ways.
4. Check health, level and scan show as words in every row.
5. With scripts turned off, check the table shows every repo in attention
   order, with plain headers.

**Results:**

| Date | Commit | Result | Notes |
|---|---|---|---|
| 2026-11-18 | S4.2.1 branch | Pass (steps 1-4) | By the agent, in Chrome, on a site built from made-up fixture data and served on 127.0.0.1. Two Tabs reached the Repo header button; Enter sorted ascending (`aria-sort` ascending, ▲), Space reversed it (descending, ▼), focus stayed on the button with a visible outline. Clicking Risks, Health and Last activity sorted correctly, with missing values last both ways; only the sorted header had `aria-sort`. Step 5 (scripts off) is covered by the tests, not run in the browser. |

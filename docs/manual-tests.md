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

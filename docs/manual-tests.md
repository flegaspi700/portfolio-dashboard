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

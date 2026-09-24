# Project working rules

- Use Fabric names `<TYPE>_EV_<Purpose>`: workspace `WS_EV_Analytics`,
  Lakehouses `LH_EV_Bronze` and `LH_EV_Silver`, notebooks `NB_EV_<Purpose>`,
  pipelines `PL_EV_<Purpose>`.
- Prefer Fabric MCP / REST APIs. Minimize Playwright use; use it only for
  operations unavailable through the authenticated APIs.
- After each completed, verified change set, commit and push code, metadata,
  tests and documentation to the configured Azure DevOps origin. Fetch first,
  preserve upstream changes and never force-push. Report any blocked push.
- Raw CSV, generated datasets, credentials and browser artifacts stay out of Git.
  The user has authorized the four manifest CSVs to be uploaded to this project's
  Fabric Bronze Lakehouse.
- Do not conflate local validation, successful cloud upload and successful
  execution in Fabric. Record each status separately.

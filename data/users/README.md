# `data/users/`

Per-user workspace folders. Auto-populated by ExoQ when a signed-in user
runs Module 1 (or any future module). Each user gets a subfolder named
after their normalized `user_id`; each run gets a subfolder under
`runs/` named with a sortable timestamp + nonce.

```
data/users/
  <user_id>/
    runs/
      2026-04-30_022530_a1b2c3/
        metadata.json     # schema_version, tier counts, source, etc.
        survivors.csv     # the survivor DataFrame
        extras.json       # optional: original manual_text, n_stars cap, ...
```

This directory is ignored by git (see `.gitignore`) -- user data stays
local. To migrate to a cloud backend later, point
`EXOQ_WORKSPACE_BACKEND` at the new store; nothing in this folder is
load-bearing for the rest of the codebase.

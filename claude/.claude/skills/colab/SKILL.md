---
name: colab-debug
description: Debugging known Google Colab runtime issues — install failures, segfaults, kernel crashes, shell quirks. Invoke when the user reports an error or unexpected behavior in an existing Colab notebook. For interactively writing/editing a Colab notebook via the colab-mcp bridge, use the `colab-mcp` skill instead.
argument-hint: [topic]
---

# Google Colab Debugging Reference

For *interactive* editing of a Colab notebook (Claude adding/running cells in a live browser
session), see the `colab-mcp` skill. This skill is the catalog of known fixes for problems
that come up *inside* a Colab runtime.

## Debugging workflow
Gather diagnostics in the **current session** before restarting — restarting loses all
installed packages and downloaded files. Only suggest notebook edits once the fix is
confirmed from diagnostics. Then tell the user "good time to restart and apply edits"
so they restart once with the correct fix rather than iterating through multiple restarts.

## Known issues and fixes

- **`wget` silent failures**: always use `-q` for progress suppression but check file
  sizes after download (`!ls -lh`). 0-byte files mean the URL was inaccessible
  (e.g. university servers block non-campus IPs). Use Google Drive + `gdown` instead.

- **`blastn` segfault (SIGSEGV)**: usually a version mismatch between the binary and
  the database. The apt package (`ncbi-blast+`) installs 2.12.0; install the correct
  version from NCBI FTP and overwrite with `cp ... $(which blastn)`.

- **`pysam` install failure**: needs system headers before pip can compile it.
  `apt-get install libbz2-dev liblzma-dev libcurl4-openssl-dev` first, then `pip install pysam`.

- **`condacolab`**: intentionally crashes the kernel to restart — shows as an error in
  the VSCode Colab extension. Avoid; prefer NCBI binaries or pip where possible.

- **Multiline `!` commands with `\`**: unreliable in Colab. Use `%%bash` cell magic for
  multiline shell commands instead.

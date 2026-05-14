---
name: geo-ngs-submission
description: Submit RNA-seq (or other NGS) data end-to-end to NCBI GEO. Subset processed tables to the target sample columns, rename samples systematically so every token in the name is interpretable, stage raw FASTQs, fill the seq_template.xlsx metadata spreadsheet, compute MD5 sums, and (optionally) upload to GEO's FTP drop. Invoke when the user wants to submit sequencing data to GEO, prepare a GEO `seq_template.xlsx`, or stage files for a GEO/SRA upload.
---

# GEO NGS submission

## Workflow (do these in order — earlier phases set up later ones)

```
0. SCOPE + NAMING   ──>  agree on samples + a systematic naming scheme   (user input)
1. STAGE FILES      ──>  subset processed tables, copy raw FASTQs        (heavy I/O)
2. FILL METADATA    ──>  populate seq_template.xlsx + MD5 sums            (Python/openpyxl)
3. FTP UPLOAD       ──>  push raw+processed to GEO drop, verify           (curl, parallel)
```

**Stage everything in HPC scratch, not in the repo.** Submissions can be 100s of GB. Suggested location: `/scratch/midway3/$USER/GEO_submission/` (RCC Midway). Layout:

```
/scratch/midway3/$USER/GEO_submission/
├── raw/         — all raw FASTQs, renamed to systematic names
├── processed/   — gzipped TSV count/junction tables, renamed
├── metadata/    — sample_manifest.tsv, seq_template_filled.xlsx, md5sums.txt, .ftp_creds
└── scripts/     — the small set of Python/bash scripts that did the staging
```

The metadata spreadsheet should ALSO be copied to `code/scratch/seq_template_filled.xlsx` so the user can open it manually for review and final edits.

---

## Phase 0 — Scope + Naming (ASK BEFORE STAGING)

Before staging any files, get explicit user buy-in on:

1. **Which samples** — from which `samples.tsv` / project dirs, exact filter rules.
2. **Whether to combine into one GEO Series or split.** One Series is usually right unless biology is unrelated.
3. **A systematic interpretable naming scheme.** This is the most important up-front decision; renaming later means re-staging every artifact. Apply the same scheme to:
   - raw FASTQ filenames
   - processed-table column headers
   - processed-table filenames
   - sample-manifest.tsv
   - the GEO `seq_template_filled.xlsx`

   See [[feedback_systematic_sample_naming]] — every token in the name should encode metadata. Template:
   ```
   {Series/Exp}_{CellLine}_{LibraryType}_{Treatment}_{Dose}_{Rep}
   ```
   When two source projects combine, use parallel `Exp1` / `Exp2` prefixes. Drop characters that collide with the field separator (e.g., if `_` is the separator, `BPN_15477` → `BPN15477`).

4. **Lane handling** — per-lane (one row per lane in PAIRED-END EXPERIMENTS, all lane files in the same SAMPLES row as technical replicates) vs merged. Per-lane is more faithful to the raw data; GEO accepts either.

5. **Metadata fields not in samples.tsv** — ask up-front (see [[feedback_ask_for_submission_metadata]]):
   - Cell line + cell type (often missing from samples.tsv — confirm explicitly)
   - Treatment incubation time
   - RNA extraction kit
   - Library prep kit
   - Sequencer model (or detect from FASTQ header, see Reference below)
   - Series title, summary (abstract), overall design — or accept "TODO" placeholders
   - Contributor list (`First,Middle,Last` per row, depositor first)

---

## Phase 1 — Stage files

### Subset processed tables

Project-wide featureCounts / leafcutter tables get subsetted to the target sample columns. **Format quirks (important):**

**featureCounts output**: 6 leading columns are `Geneid Chr Start End Strand Length`, then one column per sample where the header is the BAM path like `rna-seq/Alignments/{sample}/Aligned.sortedByCoord.out.bam`. Rewrite headers to bare sample names.

**leafcutter `_perind_numers.counts.gz`**: SPACE-separated. The header has N sample names but data rows have N+1 columns (the unnamed first data column is the junction id `chrom:start:end:cluster_id`). **`pd.read_csv(..., sep=" ", index_col=0)` is required** — without `index_col=0`, pandas misaligns the columns and you'll silently overwrite a sample column with junction IDs.

Standard leafcutter output format must be preserved when writing back:
```python
with gzip.open(out_path, "wt") as f:
    f.write(" ".join(sub.columns) + "\n")          # header: N sample names, no leading space
    for jid, row in zip(sub.index, sub.values):
        f.write(jid + " " + " ".join(row) + "\n")  # data: junction_id + N values
```

After writing, apply the systematic rename to:
- Output filenames (e.g., `X11_GeneCounts.tsv.gz` → `Exp1_GeneCounts.tsv.gz`)
- Sample column headers within the gzipped tables

### Stage raw FASTQs

Use `rsync` (restartable, preserves checksums) into `raw/` with the renamed filenames. For 100s of GB, run in background:

```bash
chmod +x copy_fastqs.sh && ./copy_fastqs.sh   # run_in_background=true
```

The copy script should:
- Read a `fastq_rename_map.tsv` (orig_path → staged_filename) and use it to drive the copy.
- Use `rsync -t src dst.partial && mv dst.partial dst` so interrupted copies don't leave half-renamed files in the staged tree.
- Log each completion and emit a final "Finished at" marker so a waiter loop can detect completion.

Skip recopying files that already exist with the expected size (cheap restart on failure).

### Compute MD5 sums

After all raw + processed files are staged with their final filenames:
```bash
cd /scratch/midway3/$USER/GEO_submission
md5sum processed/*.gz raw/*.fastq.gz > metadata/md5sums.txt
```

---

## Phase 2 — Fill `seq_template.xlsx`

### Download the blank template

```
https://www.ncbi.nlm.nih.gov/geo/info/examples/seq_template.xlsx
```

### Structure (as of GEO template Dec 2024)

The 'Metadata' sheet has these sections; the row indices shift if you insert rows in any earlier section, so always re-locate sections by label rather than hard-coding row numbers in late-stage scripts.

| Section | Layout |
|---|---|
| **STUDY** | rows 12–22 by default. col A = label, col B = value. Labels: `*title`, `*summary (abstract)`, `*experimental design`, 7× `contributor`, `supplementary file`. If you have >7 contributors, `ws.insert_rows(idx=22, amount=extra)` to add more. |
| **SAMPLES** | header row 38 with 20 columns: `*library name`, `*title`, `*library strategy`, `*organism`, `**tissue`, `**cell line`, `**cell type`, `genotype`, `treatment`, `batch`, `*molecule`, `*single or paired-end`, `*instrument model`, `description`, `processed data file` ×2, `*raw file` ×4. Sample rows start at 39. Template reserves 14 rows; `insert_rows` to add more. |
| **PROTOCOLS** | `growth protocol`, `treatment protocol`, `*extract protocol`, `*library construction protocol`, then multiple `*data processing step` rows, `*genome build/assembly`, `*processed data files format and content`. col A = label, col B = free text. |
| **PAIRED-END EXPERIMENTS** | header `file name 1`, `file name 2`, `file name 3`, `file name 4`. One row per sequencing run (= per lane for technical replicates). `insert_rows` to add. |

The 'MD5 Checksums' sheet has section headers in row 7 (`RAW FILES` at col 1, `PROCESSED DATA FILES` at col 6), column headers in row 8, data starting row 9. Two parallel two-column blocks (file name + checksum) for raw and processed.

### Filling rules

- **One library per row** in SAMPLES — group multi-lane technical replicates onto the same row (use cols 17–20 for raw files; add more cols if needed).
- **PAIRED-END EXPERIMENTS** lists one row per lane — so 2-lane samples appear in 2 rows there.
- For each sample: set `processed data file` column to semicolon-joined list of the relevant processed tables (e.g., `Exp1_GeneCounts.tsv.gz;Exp1_leafcutter_perind_numers.counts.gz`), and `description` should call out which column the sample maps to in those tables.
- The `*processed data files format and content` row in PROTOCOLS should describe BOTH file types (gene-counts TSV + leafcutter numers) AND explicitly name the actual filenames — if you rename files later, **don't forget to update this cell**.
- Library prep kit + RNA extraction + cell-culture medium go in PROTOCOLS — these come from the user, not the code.

### Drop placeholders, not blanks

If the user opts to leave a STUDY-level field for later, insert `[TODO — user to fill] <hint>` rather than leaving the cell empty. Empty cells are easy to miss; bracketed TODOs are greppable. (Then `grep '\[TODO' /path/to/sheet` can verify nothing was forgotten.)

### Inject MD5 sums

After `md5sums.txt` is produced, parse it into two lists (raw vs processed) and write into the MD5 Checksums sheet. Sort alphabetically by filename for predictable diffs.

### Copy back for user editing

```bash
cp /scratch/midway3/$USER/GEO_submission/metadata/seq_template_filled.xlsx \
   /project2/.../code/scratch/
```

Then ask the user to review. They will typically edit:
- Series title / summary / design / contributors
- Growth-protocol medium specifics
- Any treatment / title column phrasing
After their edits, sync back: `cp code/scratch/seq_template_filled.xlsx /scratch/midway3/.../metadata/` so the upload-ready copy reflects their changes.

---

## Phase 3 — FTP upload to GEO drop

GEO provides a personalized upload space `/uploads/{user}_{token}/` with temporary credentials. Credentials look like `geoftp` / `<random>`. They expire after each submission, so cycle them carefully.

### Tooling

NCBI's drop is **plain FTP (port 21), not SFTP**. On RCC midway3, only `curl` and `sftp` are available — `sftp` won't work. Use `curl`.

### Credentials hygiene

Store in a mode-600 `.ftp_creds` (netrc format), pass via `--netrc-file`:
```
machine ftp-private.ncbi.nlm.nih.gov
login   geoftp
password <temp-password>
```
Never put the password on the command line (visible in `ps`). **Delete `.ftp_creds` with `shred -u` after upload succeeds.**

### Create the upload subfolder

GEO requires a per-submission subfolder (e.g., `MyProject_RNAseq`). Create with curl's MKD quote command:
```bash
curl --netrc-file .ftp_creds \
  -Q "MKD /uploads/${USER_TOKEN}/${SUBDIR}" \
  ftp://ftp-private.ncbi.nlm.nih.gov/uploads/${USER_TOKEN}/
```

### Parallel upload

Single-stream curl maxes ~15–20 MB/s on the GEO drop. Run 6 in parallel with `xargs -P 6` for ~90–100 MB/s aggregate (~10 min per 60 GB, ~100 min per 600 GB).

Critical curl flags:
- `--netrc-file <creds>` — auth from file, not command line
- `--upload-file <local> <remote-url-ending-with-slash>` — server uses local basename
- `--fail` — non-zero exit on FTP errors (otherwise silent)
- `--retry 3 --retry-delay 10` — auto-retry transient blips
- `--silent --show-error` — log errors but not progress bars

### Resilience

**Truncated partials persist on the server.** If a connection drops mid-upload, the server keeps the partial file with whatever bytes arrived. Re-uploading with `--upload-file` does a full replace (not append), so re-running the script after a failure recovers. The script should:
1. Pull a remote listing (`curl --silent <remote_dir>/`) at startup.
2. For each local file, look up the remote size: SKIP if it matches, otherwise (re-)upload.

This makes the upload script idempotent — safe to re-run until everything matches.

### Verify after upload

Pull a fresh remote listing, build `{filename: size}` for both local and remote, and assert:
- No missing files on remote
- No unexpected files on remote
- No size mismatches

If anything fails, re-run the upload script — it will only re-upload mismatched files.

### What NOT to upload via FTP

**Don't FTP the metadata spreadsheet.** GEO instructions are explicit: `seq_template_filled.xlsx` goes through the web "Submit Metadata" form, NOT via FTP. After FTP upload completes, the user goes to https://www.ncbi.nlm.nih.gov/geo/submitter/ and selects the upload subfolder when prompted.

---

## Reference

### FASTQ header → instrument model

The first 1–2 letters of the instrument ID (just after `@`) identify the platform:

| Prefix | Instrument |
|---|---|
| `M0xxxx`, `M1xxxx`, `M2xxxx` | Illumina MiSeq |
| `D00xxx` | Illumina HiSeq 2000/2500 |
| `K00xxx` | Illumina HiSeq 4000 |
| `J00xxx` | Illumina HiSeq 3000 |
| `E00xxx`, `ST-E00xxx` | Illumina HiSeq X |
| `N0xxxx`, `NS500xxx`, `NB5xxxxx` | Illumina NextSeq 500/550 |
| `VH00xxx` | Illumina NextSeq 1000/2000 |
| `A00xxx` | Illumina NovaSeq 6000 |
| `LH00xxx` | Illumina NovaSeq X / X Plus |
| `FS10xxx` | Illumina iSeq 100 |
| `AVxxxxxx` | **Element AVITI** (not Illumina) |

Read length comes from `zcat <fastq> | awk 'NR==2 {print length($0); exit}'`.

### Format quirks

**leafcutter `_perind_numers.counts.gz`** — space-separated. Header has N samples (no junction-id label), data rows have N+1 columns. Read with `pd.read_csv(..., sep=" ", index_col=0)`. Write with manual loop (see Phase 1).

**featureCounts output** — TAB-separated, includes a `#` comment line as the first line; use `pd.read_csv(..., sep="\t", comment="#")`. Sample columns have BAM-path headers; rewrite to bare sample names.

### Useful local resources (RCC Midway)

- `py_general` Python with `pandas` + `openpyxl`: `/project2/gilad/bjf79_project1/envs/py_general/bin/python3`
- Scratch landing zone: `/scratch/midway3/$USER/`
- Login node `midway3-login3` has `curl` (good) but no `lftp` / `ncftp`; `sftp` exists but won't work against GEO's FTP-21 drop.

### Verification checklist

Before declaring done:
- [ ] `ls raw/ | wc -l` matches expected raw file count
- [ ] `ls processed/ | wc -l == 4` (or expected number)
- [ ] `find raw processed -size 0 | wc -l == 0` (no empty files)
- [ ] `md5sum -c md5sums.txt` passes
- [ ] `zcat <fc_table> | head -1 | tr '\t' '\n' | wc -l` matches `6 + N_samples`
- [ ] `zcat <leafcutter> | head -1 | tr ' ' '\n' | wc -l` matches `N_samples` (header), and `awk 'NR==2 {print NF}'` matches `N_samples + 1` (data)
- [ ] Sample count in seq_template SAMPLES section matches manifest
- [ ] PAIRED-END EXPERIMENTS row count matches `sum(lanes_per_sample)`
- [ ] MD5 Checksums sheet: raw rows + processed rows match file counts
- [ ] `grep '\[TODO' <opened-sheet>` returns expected items only
- [ ] No `X11_`, `diverseSM`, or other stale tokens anywhere in the workbook (if you applied a rename)
- [ ] Remote listing matches local 1:1 in name AND size after FTP upload

---

## Related memories

- [[feedback_systematic_sample_naming]] — every token in the sample name must encode metadata
- [[feedback_ask_for_submission_metadata]] — actively ask for protocol fields, don't leave TODOs
- [[project_cell_lines]] — example of cell-line info not encoded in samples.tsv

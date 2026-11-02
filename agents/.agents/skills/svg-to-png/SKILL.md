---
name: svg-to-png
description: "RCC Midway HPC only. Rasterize a standalone .svg file to .png with cairosvg from the claude_svgrender conda env. Invoke whenever converting/exporting an SVG figure to PNG (e.g. hand-authored SVGs, wiki/attachments figures). Midway has no rsvg-convert/inkscape and ImageMagick has no working SVG delegate."
---

# SVG → PNG on Midway

Midway (checked Midway3, 2026-07) has **no** `rsvg-convert`, `inkscape`, or `resvg`, and
`/usr/bin/convert` (ImageMagick) has **no working SVG delegate** — do not use it for SVG, it
produces blank/garbage output. The reliable rasterizer is **cairosvg**, pre-installed in a
dedicated env.

## The command

```bash
/project2/gilad/bjf79_project1/envs/claude_svgrender/bin/cairosvg IN.svg -o OUT.png --dpi 300
```

Call the binary by absolute path — no need to `mamba activate`. `--dpi 300` is the house
default (≈ publication raster; a 6.5×4.7 in figure → ~1950×1418 px, which matches the
committed `wiki/attachments/*_combined.png` files). Alternatives: `--scale 2` (2× the SVG's
nominal px size) or `--output-width N` for an exact pixel width.

## Env facts

- Env: `claude_svgrender` at `/project2/gilad/bjf79_project1/envs/claude_svgrender` — has
  `cairosvg` 2.9.0 as both a CLI and a Python module (`from cairosvg import svg2png`).
- `py_general` does **not** have cairosvg, and per policy **do not install into py_general**.
  Use `claude_svgrender`.
- If the env is ever missing, recreate it (throwaway, safe to delete):
  ```bash
  mamba create -y -n claude_svgrender -c conda-forge cairosvg
  ```

## Gotchas

- **Fonts.** cairosvg renders text via cairo, not matplotlib. If text goes missing or falls
  back to a wrong face in the PNG, the SVG references a font cairo can't find. Fix by either
  ensuring the figure uses **Nimbus Sans** (see the `scientific-figure-fonts` preference —
  Helvetica substitute available on Midway) or exporting text as paths from the generator.
- **Matplotlib figures don't need this.** If a Python generator makes the figure, just
  `fig.savefig("out.png", dpi=300)` directly (Agg backend, no external rasterizer). cairosvg
  is only for **standalone / hand-authored `.svg` files** that must become PNG.
- Verify output dimensions with `identify -format "%wx%h\n" OUT.png` (ImageMagick `identify`
  works fine; only its SVG *reading* is broken).

## pyGenomeTracks INI approach (alternative)

For static publication-quality figures from local files (BAM, bigWig, BED, GTF):

```ini
# tracks.ini
[bigwig track]
file = path/to/signal.bw
title = My Signal
height = 3
color = blue
min_value = 0
max_value = 5

[genes]
file = path/to/annotation.gtf
title = Genes
height = 5

[spacer]

[x-axis]
```

```bash
conda run -n py_general pyGenomeTracks \
    --tracks tracks.ini \
    --region chr2:1850700-1886852 \
    --outFileName output/figure.pdf
```

Check if `pyGenomeTracks` is available: `conda run -n py_general pyGenomeTracks --version`
If not: add `- pygenometracks` to the relevant `code/envs/*.yaml`.

---

# Metric: dry-run-protect

```bash
python3 metrics/dry-run-protect/measure.py && python3 metrics/dry-run-protect/plot.py
```

Asserts `--fast` exits 2 when stamp is `mode=full`, and `--force-fast` succeeds. Restores `mode=full` afterward.

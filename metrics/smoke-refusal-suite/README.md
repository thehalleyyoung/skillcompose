# Metric: smoke_test.sh refusal suite

## Run

```bash
python3 metrics/smoke-refusal-suite/measure.py && python3 metrics/smoke-refusal-suite/plot.py
```

Asserts `scripts/smoke_test.sh` exits 0 and prints `SMOKE_OK` (includes contradictory-flags + empty-audits propose).

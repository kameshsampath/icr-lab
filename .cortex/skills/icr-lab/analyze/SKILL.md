---
name: icr-lab/analyze
description: Run ICR analysis on a task description
triggers:
  - analyze icr
  - icr score
  - token analysis
---

# ICR Analyze

Analyze a task description for its ICR characteristics across all simulation modes.

## Workflow

1. Accept a task description from the user
2. Run the simulation engine against all 5 modes
3. Compute metrics (ICR scores, token counts, amplification, cost)
4. Present a summary table + recommendations

## Implementation

```python
import sys
sys.path.insert(0, "<project_root>")

from simulations.engine import run_simulation
from examples.sample_tasks import get_operations_count
from metrics.calculator import compute_metrics, compute_savings
```

## Steps

1. Get the task description (from user input or selection)
2. Call `get_operations_count(task)` to estimate complexity
3. Call `run_simulation(task, operations)` to get results for all modes
4. Call `compute_metrics(results)` and `compute_savings(metrics)`
5. Format output as a markdown table:

```
| Mode | Tokens | ICR | Amplification | Est. Cost |
|------|--------|-----|---------------|-----------|
```

6. Highlight the best mode and quantify savings vs worst mode
7. If a live backend is available, offer to run the task through it

## Output Format

Present results as:
- Summary metrics (best ICR, token savings %, max amplification)
- Comparison table
- Recommendation: which mode the user's prompt resembles
- Suggestion: how to compress toward Intent-Optimized

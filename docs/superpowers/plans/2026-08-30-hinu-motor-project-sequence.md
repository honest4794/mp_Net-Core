# Hi-Nu Motor Project Sequence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a canonical, test-protected Project Mode motor stage manifest with a 5000 ms interval and fixed production Slave/address routing.

**Architecture:** Store the sequence as data under `slave/pixel/sequences/`, separate from the Test Kit mode registry. An integration-style unit test loads the real JSON and verifies ordered timing, routing, no-op stages, and excluded addresses without adding runtime behavior.

**Tech Stack:** JSON, Python 3 `unittest`

**Spec:** `docs/superpowers/specs/2026-08-30-hinu-motor-project-sequence-design.md`

## Global Constraints

- Run Python with `python -B`.
- Do not create `__pycache__` or `*.pyc` files.
- Preserve Test Kit modes 0–2 and their addresses.
- `motor_open_interval_ms` is `5000`.
- Stages `6`–`10` and `13`–`16` remain timed no-op stages.
- Address `35` is excluded; addresses `39` and `40` are unsequenced.

---

### Task 1: Canonical Project Sequence Manifest

**Files:**
- Create: `test/pixel/test_hinu_motor_project_sequence.py`
- Create: `slave/pixel/sequences/hi_nu_motor_project.json`

**Interfaces:**
- Consumes: the approved stage/route table in the design spec.
- Produces: JSON fields `motor_open_interval_ms: int` and `stages: list[object]`, where each stage has `sequence: str` and `targets: list[object]`.

- [ ] **Step 1: Write the failing contract test**

Create a `unittest.TestCase` that loads the real manifest. Use these literal
expectations:

```python
EXPECTED_ORDER = (
    [str(value) for value in range(1, 19)]
    + ["18A", "19", "19A", "20", "20A", "21", "21A",
       "22", "22A", "23", "23A", "24"]
)
EXPECTED_NO_OPS = {"6", "7", "8", "9", "10", "13", "14", "15", "16"}
EXPECTED_ROUTES = {
    "1": [(9, [22]), (11, [23])],
    "2": [(8, [24]), (10, [28])],
    "3": [(8, [25, 26]), (10, [29, 30])],
    "4": [(8, [27]), (10, [31])],
    "5": [(7, [32, 33, 34, 38, 36, 37])],
    "11": [(1, [41])],
    "12": [(1, [42])],
    "17": [(15, [43]), (14, [44])],
    "18": [(16, [53]), (17, [57])],
    "18A": [(16, [91]), (17, [94])],
    "19": [(16, [63]), (17, [67])],
    "19A": [(16, [101]), (17, [104])],
    "20": [(16, [54]), (17, [58])],
    "20A": [(16, [92]), (17, [95])],
    "21": [(16, [64]), (17, [68])],
    "21A": [(16, [102]), (17, [105])],
    "22": [(16, [55]), (17, [59])],
    "22A": [(16, [93]), (17, [96])],
    "23": [(16, [65]), (17, [69])],
    "23A": [(16, [103]), (17, [106])],
    "24": [(13, [45, 46, 48, 49, 60, 61, 70, 71])],
}
```

Assert that the interval is 5000, ordered stage IDs exactly match
`EXPECTED_ORDER`, no-op stages have empty targets, active routes exactly match
`EXPECTED_ROUTES`, addresses are unique, address 35 is excluded with replacement
38, and 39/40 are unsequenced and absent from targets.

- [ ] **Step 2: Run the test and verify RED**

Run:

```bash
python -B -m unittest test.pixel.test_hinu_motor_project_sequence
```

Expected: error because `slave/pixel/sequences/hi_nu_motor_project.json` does
not exist.

- [ ] **Step 3: Add the minimal JSON manifest**

Create the schema described in the spec. Populate all 30 ordered stages, using
empty `targets` arrays for `6`–`10` and `13`–`16`, and the exact literal routes
from Step 1 for all active stages.

- [ ] **Step 4: Run focused and regression tests**

Run:

```bash
python -B -m unittest test.pixel.test_hinu_motor_project_sequence
python -B -m unittest test.pixel.test_uart_motor_storymodes test.protocol.test_hinu_nc4_slave_contract
```

Expected: all tests pass.

- [ ] **Step 5: Verify repository hygiene and commit**

Run:

```bash
git diff --check
find . -type d -name __pycache__ -o -name '*.pyc'
git status --short
```

The `find` command must print nothing. Stage only the manifest and its test,
then commit:

```bash
git add slave/pixel/sequences/hi_nu_motor_project.json test/pixel/test_hinu_motor_project_sequence.py
git commit -m "feat(motor): define Hi-Nu project sequence"
```


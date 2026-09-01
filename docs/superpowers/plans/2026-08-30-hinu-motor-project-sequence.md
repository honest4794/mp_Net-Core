# Hi-Nu Motor Project Sequence v1 Plan — Superseded

This historical 30-stage implementation plan was superseded on 2026-09-02.
Do not execute its former `1–24` / `18A–23A` routing.

Current authorities:

- Design: `docs/superpowers/specs/2026-08-30-hinu-motor-project-sequence-design.md`
- Manifest: `slave/pixel/sequences/hi_nu_motor_project.json`
- Contract test: `test/pixel/test_hinu_motor_project_sequence.py`

The current schema is version `2`, contains Kai order `1–7`, and fixes:

- Close = Direction `A`, raw `0`.
- Open = Direction `B`, raw `255`.
- One `5000 ms` interval per Kai timeslot.
- Unknown chest and shield addresses remain named pending components, not UART
  targets.

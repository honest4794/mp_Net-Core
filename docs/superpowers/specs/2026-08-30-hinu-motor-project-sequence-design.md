# Hi-Nu Motor Project Sequence Design

## Goal

Define one canonical seven-timeslot Kai motor sequence for the Hi-Nu black
Slave deployment. All known motors assigned to the same Kai order start from
one shared deadline.

## Direction and timing contract

- Close: Direction `A`, raw `0` — fastest close.
- Open: Direction `B`, raw `255` — fastest open.
- Each Kai timeslot uses the global `5000 ms` interval.
- The timeline contains exactly Kai order `1` through `7`.
- Addresses within one Kai stage operate together; their list order is wiring
  documentation, not a second timing sequence.

## Canonical routes

| Kai | Components | Project targets (`slave_id: addresses`) |
|---:|---|---|
| 1 | chin; upper-backpack hammer | `1: 40`; `12: 42` |
| 2 | feet; lower-leg main, outer and inner actuators | `9: 22`; `11: 23`; `8: 24,25,26`; `10: 28,29,30` |
| 3 | knees; front, side and rear skirts | `8: 27`; `10: 31`; `7: 32,33,34,38,36,37` |
| 4 | chest; shoulder inner, outer and upper actuators | `5: 73,75,74,76,77`; `3: 83,85,84,86,87`; chest addresses pending |
| 5 | wings; left and right fuel tubes | `15: 43`; `14: 44`; `13: 45,46,48,49`; `20: 60,61,70,71` |
| 6 | all left and right funnel covers and points | `14: 53,91,63,101,54,92,64,102,55,93,65,103`; `15: 57,94,67,104,58,95,68,105,59,96,69,106` |
| 7 | shield; head top and ears | `1: 39`; shield addresses pending |

## Pending components

Unknown addresses are represented as `pending_components`, never as guessed
motor targets.

- Kai 4: chest front, both vent armours, cockpit upper, cockpit middle and
  cockpit lower.
- Kai 7: shield middle sides, shield top and shield tail sides.

## Safety metadata

- Address `35` is excluded because it short-circuited; address `38` is its
  approved replacement.
- Address `41` remains unsequenced and is not emitted as a target.
- All 63 known production addresses occur exactly once across Kai 1–7.
- Slave16 does not exist as a physical profile; its left-funnel routes are
  owned by Slave14.
- Slave17 does not exist as a physical profile; its right-funnel routes are
  owned by Slave15.

## Data interface

`slave/pixel/sequences/hi_nu_motor_project.json` schema version `2` contains:

- `motor_open_interval_ms`: global timeslot interval.
- `directions`: close/open Direction and raw endpoint contracts.
- `excluded_addresses` and `unsequenced_addresses`: safety metadata.
- `stages`: ordered Kai 1–7 records.
- `targets`: known integer `slave_id` and integer motor addresses only.
- optional `pending_components`: named parts whose Slave/address is not yet
  confirmed.

No pending component is converted into a UART target until its address is
provided and added to the correct Slave profile.

## Out of scope

- Guessing chest or shield addresses.
- Changing the existing per-Slave `config.json` address ownership.
- Loading or executing this manifest at runtime; it remains the canonical
  project sequencing contract until a runtime sequencer is implemented.

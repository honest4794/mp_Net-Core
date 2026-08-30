# Hi-Nu Motor Project Sequence Design

## Goal

Define one canonical Project Mode motor sequence before the production
configuration for Slave 1–18 is installed. Test Kit modes 0–2 remain separate.

## Decisions

- The global motor opening interval is `5000` milliseconds.
- A stage is identified by a string so `18A`–`23A` are unambiguous.
- The complete ordered timeline contains 30 stages:
  `1`–`18`, `18A`, `19`, `19A`, `20`, `20A`, `21`, `21A`, `22`,
  `22A`, `23`, `23A`, `24`.
- Stages `6`–`10` are timed chest stages assigned to Slave 1; their addresses
  remain unknown and use `{"slave_id": 1, "addresses": ["X"]}`.
- Stages `13`–`16` are timed pending stages and use
  `{"slave_id": "X", "addresses": ["X"]}` until their production routes are
  known. Every pending stage still consumes one 5000 ms interval.
- Targets in the same stage share the same stage deadline. A target contains one
  production `slave_id` and one or more local UART motor addresses.
- This file does not change or reuse Test Kit routing. Test Kit Slave1 remains
  addresses `15,19`; Test Kit Slave2 remains addresses `12,21`.

## Canonical Routes

| Stage | Project targets (`slave_id: addresses`) |
|---|---|
| 1 | `9: 22`; `11: 23` |
| 2 | `8: 24`; `10: 28` |
| 3 | `8: 25,26`; `10: 29,30` |
| 4 | `8: 27`; `10: 31` |
| 5 | `7: 32,33,34,38,36,37` |
| 6–10 | chest; pending address template `1: X` |
| 11 | `1: 41` |
| 12 | `1: 42` |
| 13 | pending template `X: X`; 肩甲 1（靠近心口），左右內側肩甲前後展開，前甲向前／後甲向後 |
| 14 | pending template `X: X`; 肩甲 2，左右外側肩甲前後展開，前甲向前／後甲向後 |
| 15 | pending template `X: X`; 前後肩甲中間結構，肩甲中央結構垂直升起 |
| 16 | pending template `X: X`; 背面中央直立組件，中央背包組件垂直升起或調整高度 |
| 17 | `15: 43`; `14: 44` |
| 18 | `16: 53`; `17: 57` |
| 18A | `16: 91`; `17: 94` |
| 19 | `16: 63`; `17: 67` |
| 19A | `16: 101`; `17: 104` |
| 20 | `16: 54`; `17: 58` |
| 20A | `16: 92`; `17: 95` |
| 21 | `16: 64`; `17: 68` |
| 21A | `16: 102`; `17: 105` |
| 22 | `16: 55`; `17: 59` |
| 22A | `16: 93`; `17: 96` |
| 23 | `16: 65`; `17: 69` |
| 23A | `16: 103`; `17: 106` |
| 24 | `13: 45,46,48,49,60,61,70,71` |

## Safety Metadata

- Address `35` is excluded because it short-circuited and was replaced by
  address `38`.
- Addresses `39` and `40` are retained as unsequenced metadata but are never
  emitted as targets.

## Data Interface

Create `slave/pixel/sequences/hi_nu_motor_project.json` with:

- `version`: integer schema version, initially `1`.
- `name`: `hi_nu_motor_project`.
- `motor_open_interval_ms`: global integer interval, initially `5000`.
- `excluded_addresses`: safety records with address, reason, and replacement.
- `unsequenced_addresses`: known addresses without a sequence.
- `stages`: ordered objects containing `sequence` and `targets`.
- known mechanism metadata uses `position`, `action_description`, and
  `motion_direction`, even when the hardware target is still pending.
- each configured target: integer `slave_id` and ordered integer `addresses`.
- each pending target uses `"X"` only for an unknown value. Stages `6`–`10`
  retain known integer `slave_id: 1` with `addresses: ["X"]`; stages `13`–`16`
  use `slave_id: "X"` and `addresses: ["X"]`. No field uses `null`.

## Out of Scope

- Creating the final hardware profiles/configuration for Slave 1–18.
- Loading or executing this sequence at runtime.
- Selecting direction, speed curve, motor run duration, or close sequence.
- Changing Test Kit mode IDs 0, 1, or 2.

---
name: project-automation-rules
description: Use when starting a FastLED project, migrating or regrouping storyMode code, mapping Excel wiring tables, choosing RGB effects, designing SpecificColorPattern Normal, Repair or Develop signal profiles, or tuning storyMode RGB/PCA brightness contrast and power budget.
---

# Project Automation Rules

Use this skill before writing or migrating storyMode code for a project.

Core rule: confirm the project's slave definition first. Do not assume slave IDs keep the same meaning across projects.

## Required routing

先讀 `references/project_automation_rules.md`。再依工作內容讀：

- 查 effect signature、參數群、完整呼叫與目前 consumer：`references/effect_function_catalog.md`
- 查元件在各正式 StoryMode 的 ON／OFF／STAGED、profile、亮度政策與完整 record ID：`references/component_storymode_matrix.md`
- 查 PGU 每個正式 source call site、非正式 mode 參考或舊專案正式 active 槍效：`references/project_call_archive.md`

`project_call_archive.md` 是 complete call-site register，不是範例集。它和
`component_storymode_matrix.md` 都由
`scripts/generate_project_call_filing.py` 從 source 重新產生；修改 storyMode
硬體／效果呼叫後必須執行 generator，不要手動只補少數範例。

This routing is required when the task involves:

- starting a new project
- importing storyMode code from another branch
- regrouping slave IDs
- distinguishing the formal `storyMode_develop` from the non-formal `storyMode_dev` test entry
- removing old project slave code
- deciding `switch (slaveId)` order
- mapping Excel / wiring table rows into code
- choosing common RGB1-RGB4 storyMode effects
- designing or changing `SpecificColorPattern` index / override color arrays
- separating Normal、Repair、Motor or other signal profiles
- sequencing GPIO17 UART motor groups with signal lead／vent timing in `storyMode_motor`
- tuning per-component RGB/PCA brightness contrast or checking the stage power budget
- summarizing functions, parameter groups, project/storyMode consumers, or component behavior

## Current project defaults

- This Hi-Nu project uses `slave 1-20`; Slave 19／20 are left／right feet, and it has no platform.
- `storyMode_develop` is formal LED mode 0. Include it when a task changes all formal StoryModes, migrates a Slave across StoryModes, or changes the Develop signal profile.
- `storyMode_dev` is a separate non-formal hardware test entry. Never treat `develop` as an abbreviation of `dev`.
- Keep only migrated PGU RGB effects. PCA, PWM, GPIO mono LED, motor and servo effects remain disabled until hardware is confirmed.
- Standard case order is `1 -> 2 -> 3/5 -> 4/6 -> 7 -> 8/10 -> 9/11 -> 12 -> 13 -> 14 -> 15 -> 16 -> 17 -> 18 -> 19/20`.
- Paired labels share exactly one code block with no `if (slaveId ...)` split:
  - `case 3: case 5:` — left/right upper arms, shared PGU Slave 4 RGB code.
  - `case 4: case 6:` — left/right lower arms, shared PGU Slave 4 RGB code.
  - `case 8: case 10:` — left/right upper legs, shared PGU Slave 7 RGB code.
  - `case 9: case 11:` — left/right lower legs, shared PGU Slave 7 RGB code.
  - `case 19: case 20:` — left/right feet, shared code with RGB1–RGB4 only.
- Funnel Gun mapping is fixed: Slave 13/14/15/16/17 use old PGU Slave 10 RGB1/2/3/4/7/8 respectively.
- Every Slave 13–17 hardware target must explicitly keep non-zero `NUM_LEDS_RGB1`,
  `RGB2`, `RGB3`, `RGB4`, `RGB7`, and `RGB8`; the fixed mapping above only selects
  the currently migrated Story Mode effect source and must not null the other pins.
- The three RGB branches are independent. A branch advances after its own previous layer completes and never waits for another branch.
- Do not migrate old PGU Slave 1/9 platform effects or old platform brightness caps.

## Editing style

- Keep storyMode calls explicit in each `case slaveId`.
- Do not add wrappers just to hide repeated calls.
- Keep paired groups only where the Hi-Nu definition says so: `3/5`, `4/6`, `8/10`, and `9/11`.
- A paired group must use one shared fall-through block. Do not add an inner `if/else` to restore different left/right source code.
- If code came from an old project, split old grouped cases first, then adjust effects with the Excel / wiring table.
- PCA hardware comments must follow the fixed field order in reference section 3.4.
- PWM mapping and complete `ch*` call examples are consolidated in the main reference; do not recreate a separate PWM mapping skill.

## RGB signal profile 隔離

- 先依 reference 的「RGB signal profile 分離 SOP」確認實際燈數、index 與 registry ID。
- 修改 `SpecificColorPattern sub-function`、registry entry 或 state 參數時，必須同步 `references/project_automation_rules.md`、`references/effect_function_catalog.md` 與專案規則文件；registry ID／名稱是 profile 合約，sub-function 是可共用的目前實作，兩者不可混為一談。
- 單閃、雙閃、維修雙脈衝與戰鬥心跳一律優先使用可調 `BlinkBurstSingleLedPattern`；以 `BlinkTwiceState` 的 `blinkTimes`、ON、gap、idle、color、brightness 調整，不新增只差次數或顏色的重複 pattern。
- Profile arrays 按 `Slave／合法 paired group／模式用途` 分組；只有硬體 grouping 與模式行為都相同時才可共用。
- Registry 可以共用；不同 Slave 或不同 Normal／Repair／Motor 設計的 index／override arrays 必須分開。
- 修改既有 array 前先搜尋所有 consumers；完成後再搜尋一次，確認未改到需求外的 story mode、motor 或其他 Slave。

## Call filing 維護

- PGU 正式 12 LED + 2 servo StoryModes 以 one record per source call site 歸檔，不合併不同 Slave、stage、target 或 source line。
- 收錄 RGB、PCA、motor、servo、GPIO、ON/OFF、fade 與 reset；排除 `millis()`、`min()`、`fill_solid()` 等一般程式工具。
- Loop call 只保留一筆 source call，不展開成每個 channel；每筆都要保留 loop context。
- 每個 call 都必須有 component description；只能採用 source 已確認的硬體註解，沒有時標記 `UNCONFIRMED COMPONENT`，不可由顏色猜部件。
- 保留原始完整 call、參數群、參數名與 definition path/line。
- Red Astray 只保存 Controller 正式啟用 modes 的 active gun calls，只能參考 gun effect，不可參考 brightness contrast。

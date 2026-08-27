---
name: uniform-coding-style
description: Use when modifying FastLED story mode, RGB/PWM/motor/GPIO effects, shared lib/patterns code, storyMode_*.cpp timing or cumulative stages, per-slave switch cases, hardware comments, or effect/state parameters in this project.
---

# Uniform Coding Style

這是本 project 唯一的 story mode coding-style skill。修改 story mode、燈效、PWM、motor、
`firmware/shared/src/lib/` 或 `firmware/shared/src/patterns/` 前，依序完整讀取：

1. `docs/storymode/storymode製作標準.md`
2. `docs/project/standards/uniform_coding_style.md`

不要再建立或引用另一份重複的 story mode coding-style skill。

## 必做流程

1. 先由 PlatformIO env、入口檔與 `STANDALONE_MODE` 確認 project 是 `master-slave`、`slave_standalone`，或同時支援兩者。
2. 先讀任務附近的既有程式碼，沿用原本結構與命名。
3. 若修改 story mode，直接在對應 `switch (slaveId)` / `case` block 內寫效果。
4. 每個 RGB / PWM / motor / GPIO 實際呼叫前，加硬體註解，寫明 slave、strip/channel/pin、部位與效果。
5. 多段時序使用累積時間門檻：`if (time >= 0)`、`if (time >= 2000)`、`if (time >= 4000)`。
6. 同一個 slave stage 內，先寫會更新 motor buffer 的呼叫，再寫 RGB / PCA base effects。
7. shared code 變更要視為同時影響 master、slave、standalone。

## Standalone Project

- 獨立 standalone project 直接使用已配置或使用者指定的 `slaveId` 執行正式 StoryMode，只保留 standalone 所需入口與硬體路徑。
- 同一 repo 同時支援 master/slave/standalone 時，用既有 compile flags 隔離，不刪除其他正式 target 的程式碼。
- Standalone 直接沿用正式 StoryMode 的累積時間門檻，不用 macro、wrapper 或第二套 timeslot 重建演出。

## 禁止模式

- 不要用 `if (time >= a && time < b)` 讓前段效果在下一段開始時自動停掉，除非需求明確要關閉或 fade out。
- 不要新增只包效果的 helper、lambda 或 macro 來隱藏 channel。
- 不要用 `renderBaseEffects`、`renderMotorBaseEffects` 或類似 wrapper 取代 per-slave 直接呼叫。
- 不要用 `renderStoryModeInternalStructure(...)` 隱藏 channel；在 story mode 內直接呼叫 `chInternalStructure(...)` 與對應 state buffer。
- 不要順手重構無關 story mode 或改動硬體設定。

## 參數與 state

- 採用 reuse-first：先調整現有 effect 參數，再擴充同一 family 的 state／函式；新檔案邊界依 `uniform_coding_style.md` 的「新燈效位置」。
- 可重用 effect 參數放在 `storyMode_parameter.h/.cpp`，並使用該 story mode 的 namespace。
- story mode 專用 state 優先放在對應 story mode `.cpp`，避免污染全域參數。
- 確定需要新增 effect 時，放入最接近的既有 `lib/` 或 `patterns/` family，並同步更新對應 header。

## 完成前

- 針對變更範圍執行最相關的 `pio run`。
- 若 shared code 有變更，至少建置 master、一個 slave 與 standalone。

# Virtual Strip Connector

核心概念：`VirtualStrip` 是「接線順序描述器」，把多條 RGB strip 當成一條連續燈帶給 effect 使用。

例子：

```text
Slave 7 RGB1 data out -> Slave 6 RGB1 data in
```

在程式裡要表達成同一個順序：

```cpp
const uint8_t rgbSeqGroup0Slaves[] = {7};
const uint8_t rgbSeqGroup1Slaves[] = {6};

const RgbVirtualSlaveGroup rgbSeqGroups[] = {
    {rgbSeqGroup0Slaves, 1, leds_RGB1, NUM_LEDS_RGB1},
    {rgbSeqGroup1Slaves, 1, leds_RGB1, NUM_LEDS_RGB1},
};
```

這個順序就是 virtual LED index 的順序。Effect 只看到一條長燈帶：

```text
virtual index 0 ... slave7 RGB1 last -> slave6 RGB1 first ... end
```

每個 slave 都會跑同一個 effect，但 `rgbVirtualStripWrite()` 只會寫入目前 `currentSlaveId` 擁有的那一段。

若多個 slave 要從同一個 virtual 起點同步開始，例如 Slave 7 與 Slave 8 同步，然後接到 Slave 6：

```cpp
const uint8_t rgbSeqGroup0Slaves[] = {7, 8};
const uint8_t rgbSeqGroup1Slaves[] = {6};

const RgbVirtualSlaveGroup rgbSeqGroups[] = {
    {rgbSeqGroup0Slaves, 2, leds_RGB1, NUM_LEDS_RGB1},
    {rgbSeqGroup1Slaves, 1, leds_RGB1, NUM_LEDS_RGB1},
};
```

這表示 Slave 7 RGB1 與 Slave 8 RGB1 畫同一段 virtual index，兩者視覺同步；下一段才是 Slave 6 RGB1。

## 目前 helper

位置：

```text
firmware/shared/include/patterns/patterns_cross_effects.h
firmware/shared/src/patterns/patterns_cross_effects.cpp
```

主要函式：

```cpp
struct RgbVirtualSlaveGroup {
    const uint8_t* slaveIds;
    size_t slaveCount;
    CRGB* leds;
    int numLeds;
};
```

不要新增 `RgbVirtualStrip` 物件。`RgbVirtualSlaveGroup` 只是接線資料，不是 wrapper；每個 cross-effect 仍可用不同 group array。

## 寫 cross-effect 的規則

Hi-Nu RGB1 共同 branching 規則：S1 頭（virtual `0-49`）→ S2 身體（`50-99`）完成後，三條 branch 由 virtual `100` 同時展開——Branch 1 手臂 `S3/S5(100,50) → S4/S6(150,50)`、Branch 2 腿部 `S7(100,20) → S8/S10(120,120) → S9/S11(240,120) → S19/S20(360,70)`、Branch 3 背包 `S12(100,30) → S13-18(130,62)` 六支 Funnel Gun 同步。不同 branch 不互相等待。S13 用 RGB1；S14-18 在各自 case 以專屬 RGB pin（RGB2/3/4/7/8）呼叫同一 cross effect。此 cross topology 只影響各 slave 被指定的那一條 RGB。

- `RgbVirtualSlaveGroup` array 的順序代表實體 data out -> data in 接線順序。
- 同一個 `RgbVirtualSlaveGroup` 裡的多個 slave 會同步畫同一段 virtual strip。
- Effect 不要知道 slave 邊界；只用 `virtualIndex` 和 `strip.totalLeds` 計算視覺。
- Effect 內先依 group 的 `numLeds` 計算 `totalLedCount`。
- 寫 LED 時只允許用一個底層 connector helper 把 `virtualIndex` 寫回目前 slave；不要再包多層 helper。
- 不要配置完整 `CRGB virtualBuffer[totalLeds]`，除非效果真的需要整幀暫存；優先用小型狀態，例如每顆 1 byte trail。
- `WLED_DIR_FORWARD` 表示照 connector 順序跑。
- `WLED_DIR_BACKWARD` 表示從 connector 末端往前跑。
- `WLED_DIR_CENTER_OUT` / `WLED_DIR_CENTER_IN` 由 helper 對 virtual index 做中心映射。
- 如果效果需要 reset，reset 應該看 `startTime`、`groupCount`、`totalLeds`、方向或參數是否改變。
- 不使用 `numLeds == 0`、空 pointer 或其他隱藏語意表達同步；同步要寫成同一個 `RgbVirtualSlaveGroup`。

## Coding style 限制

- Story mode 呼叫端不要新增 wrapper；直接宣告 group array 並呼叫 cross-effect。
- Cross-effect 實作中 helper 越少越好；只保留 virtual index mapping / current slave write 這種必要 connector 邏輯。
- 不要把 `make/total/clear/directed` 拆成多個對外 helper；呼叫端不應需要知道這些步驟。
- 不要在 effect 內用 `static` 指標保存多組效果共用狀態；需要狀態時由 caller 傳 context 或 params。
- 新 cross-effect API 以 `RgbVirtualSlaveGroup` 為標準，不再用平行陣列作為新 call site 樣式。

## RGBSeqOnV3

`RGBSeqOnV3()` 是第一個使用 `VirtualStrip` connector 的 cross-effect。

用途：

- 把多條 RGB strip 當成一條 virtual strip。
- 在 virtual strip 上播放 palette meteor。
- 用小型 `uint8_t* meteorTrail` 保存亮度 trail，不保存完整 CRGB buffer。

注意：

- `interval` 保留在 API 內是為了相容，但 V3 的核心不是逐 group 延遲啟動，而是連成一條燈帶一起跑。
- 若要表示 `Slave 7 RGB1 -> Slave 6 RGB1`，不要在 effect 裡特判 slave 7 / slave 6；只調整 connector array 順序。
- `RGBSeqOnV3()` 使用 caller-provided `RgbSeqOnV3Context`，不要在函式內用 static state，避免多組 cross-effect 同時呼叫互相干擾。
- 需要同步分裂且各分支長度不同時，使用接受 `RgbVirtualBranchSegment` 的 overload；不要拆成多個獨立 `RGBSeqOnV3()` context。
- Branch overload 與線性版本共用相同 meteor trail 演算法，只透過 `rgbVirtualBranchWrite()` 改變 virtual-to-physical mapping。

## rgbBreath_swipe_palette_v3 cross 方向

單 strip 版：

```cpp
rgbBreath_swipe_palette_v3(...)
```

跨 strip 版應使用 connector 思維：

```cpp
RGBBreathSwipePaletteV3Cross(...)
```

設計重點：

- 呼吸背景用同一個 virtual timeline，所以跨 slave 不會各自不同步呼吸。
- 掃入亮點用 virtual index 前進，所以可以自然從 Slave 7 RGB1 接到 Slave 6 RGB1。
- 每個 slave 只輸出自己那段，不需要跨 slave 傳 CRGB buffer。
- `RGBBreathSwipePaletteV3Cross()` 需要不同長度的同步分支時，使用接受 `RgbVirtualBranchSegment` 的 overload。
- Branch overload 的 swipe、breath background 與 comet 共用同一條 virtual timeline，並透過 `rgbVirtualBranchWrite()` 寫回各 Slave。

## 常見錯誤

- 錯誤：把 `VirtualStrip` 寫成 `RGBSeqOnV3` 私有 helper。
- 正確：`RgbVirtualSlaveGroup` array 是所有 future cross-effects 的 connector。
- 錯誤：在 effect 裡寫 `if (slaveId == 7) ... else if (slaveId == 6) ...` 來接燈帶。
- 正確：用 connector array 的順序描述接線。
- 錯誤：用 `numLeds == 0` 表示「跟上一段同步」。
- 正確：把同步的 slave 放在同一個 `RgbVirtualSlaveGroup`。
- 錯誤：為了跨 slave 建一整條 CRGB virtual buffer，導致記憶體暴增。
- 正確：只保存必要狀態，最後用 `rgbVirtualStripWrite()` 寫回實體 strip。
- 錯誤：每條 strip 各自跑單 strip effect，造成邊界不連續。
- 正確：effect 只看 virtual strip，slave 邊界由 connector 處理。

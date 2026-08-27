# PGU Complete Component × StoryMode Matrix

> 本矩陣與 `project_call_archive.md` 使用同一份 source-derived records。每個正式 record ID 必須在此出現；完整 call 與參數見 archive。

## Legend and authority

- `ON`：目前 mode/context 的直接持續 effect call。
- `OFF`：明確 off/clear/reset/stop；功能需要時 off is acceptable。
- `STAGED`：受 stage/condition 控制，或 fade transition。
- `candidate—not firmware authority`：未寫入目前 source 的候選值不可當現況。
- Loop 保留一筆 call 與 loop range，不展開逐 channel records。

## Controller order

- LED 0: `storyMode_develop`
- LED 1: `storyMode_signals`
- LED 2: `storyMode_0_v1`
- LED 3: `storyMode_awakening_3`
- LED 4: `storyMode_activation`
- LED 5: `storyMode_0_v2`
- LED 6: `storyMode_storing_energy`
- LED 7: `storyMode_2`
- LED 8: `storyMode_plasma`
- LED 9: `storyMode_trans_am`
- LED 10: `storyMode_3`
- LED 11: `storyMode_idle`
- SERVO 0: `storyMode_motor`
- SERVO 1: `storyMode_motor_reset`

## Slave 1

### storyMode_develop

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | GPIO '38' | Hi-Nu Slave 1 GPIO38／GPIO39：Development 開啟左／右頭 MiniMon 眼睛。 | `digitalWrite` | `pgu-storymode-develop-72-digitalwrite-8e3277b7` |
| STAGED | GPIO '39' | UNCONFIRMED COMPONENT — GPIO '39' | `digitalWrite` | `pgu-storymode-develop-73-digitalwrite-6b1fc8ef` |
| STAGED | PCA PWM0 CH channel | UNCONFIRMED COMPONENT — PCA PWM0 CH channel | `chOff`、`chOn` | `pgu-storymode-develop-81-chon-849fc726`<br>`pgu-storymode-develop-87-choff-ce795dbc` |
| STAGED | PCA PWM0 CH0 | Hi-Nu Slave 1 PWM0 CH0（0x5F，頭部綠燈）：低亮長亮。 | `chOn` | `pgu-storymode-develop-76-chon-6650811b` |
| STAGED | RGB1 | Hi-Nu Slave 1 RGB1（頭部流光 36 粒）：Development 保持關閉。 | `rgbOff` | `pgu-storymode-develop-51-rgboff-a8aa54ea` |
| STAGED | RGB2 | Hi-Nu Slave 1 RGB2（頭部散氣 45 粒）：低亮冰藍呼吸。 | `smoothSineBreath` | `pgu-storymode-develop-54-smoothsinebreath-48358d82` |
| STAGED | RGB3 | Hi-Nu Slave 1 RGB3 未接燈帶（0 粒）。 | `rgbOff` | `pgu-storymode-develop-61-rgboff-4b48d753` |
| STAGED | RGB4 | Hi-Nu Slave 1 RGB4（頭部訊號 3 粒）：科技藍 120 ms 規律閃爍。 | `SpecificColorPattern` | `pgu-storymode-develop-64-specificcolorpattern-f7a3e711` |

### storyMode_signals

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | GPIO '38' | Hi-Nu Slave 1 GPIO38／GPIO39：維修檢查時開啟左／右頭 MiniMon 眼睛。 | `digitalWrite` | `pgu-storymode-signals-72-digitalwrite-78f0b79d` |
| STAGED | GPIO '39' | UNCONFIRMED COMPONENT — GPIO '39' | `digitalWrite` | `pgu-storymode-signals-73-digitalwrite-92bb49e2` |
| STAGED | PCA PWM0 CH channel | UNCONFIRMED COMPONENT — PCA PWM0 CH channel | `chOn` | `pgu-storymode-signals-78-chon-ec324f60`<br>`pgu-storymode-signals-84-chon-cc86df05` |
| STAGED | RGB1 | Hi-Nu Slave 1 RGB1／RGB2（頭部流光／散氣）：Signals 只顯示訊號，保持關閉。 | `rgbOff` | `pgu-storymode-signals-58-rgboff-643491f8` |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `rgbOff` | `pgu-storymode-signals-59-rgboff-1b7530b1` |
| STAGED | RGB3 | Hi-Nu Slave 1 RGB3 未接燈帶（0 粒）。 | `rgbOff` | `pgu-storymode-signals-62-rgboff-82412fe1` |
| STAGED | RGB4 | Hi-Nu Slave 1 RGB4（頭部訊號 3 粒）：Maintenance 琥珀橙雙脈衝。 | `SpecificColorPattern` | `pgu-storymode-signals-65-specificcolorpattern-90a146f6` |

### storyMode_0_v1

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| ON | GPIO '38' | Hi-Nu Slave 1 GPIO38／GPIO39：亮點模式完成後關閉左／右頭 MiniMon 眼睛。 | `digitalWrite` | `pgu-storymode-0-v1-138-digitalwrite-8f001786` |
| ON | GPIO '38' | Hi-Nu Slave 1 GPIO38／GPIO39：亮點模式開啟左／右頭 MiniMon 眼睛。 | `digitalWrite` | `pgu-storymode-0-v1-113-digitalwrite-4a0d7c28` |
| ON | GPIO '39' | UNCONFIRMED COMPONENT — GPIO '39' | `digitalWrite` | `pgu-storymode-0-v1-114-digitalwrite-986bab24`<br>`pgu-storymode-0-v1-139-digitalwrite-a1146dc4` |
| STAGED | Global FastLED brightness | UNCONFIRMED COMPONENT — Global FastLED brightness | `setBrightness` | `pgu-storymode-0-v1-3124-setbrightness-9f0d6e2d` |
| OFF | PCA PWM0 CH channel | UNCONFIRMED COMPONENT — PCA PWM0 CH channel | `chOff` | `pgu-storymode-0-v1-134-choff-2ba454ee` |
| ON | PCA PWM0 CH channel | UNCONFIRMED COMPONENT — PCA PWM0 CH channel | `chOn` | `pgu-storymode-0-v1-123-chon-6345f178` |
| ON | PCA PWM0 CH0 | Hi-Nu Slave 1 PWM0 CH0（0x5F，頭部綠燈）：兩段式眼燈喚醒。 | `chGundamEyeWakeTwoStage` | `pgu-storymode-0-v1-117-chgundameyewaketwostage-2e9ae3fa` |
| STAGED | RGB1 | Hi-Nu Slave 1 RGB1（頭部流光 36 粒）：熄燈段關閉。 | `rgbOff` | `pgu-storymode-0-v1-2544-rgboff-1653bcad` |
| STAGED | RGB1 | Hi-Nu Slave 1 頭 RGB — PGU Slave 3 RGB source. | `rgbOff` | `pgu-storymode-0-v1-281-rgboff-4a2046a5`<br>`pgu-storymode-0-v1-678-rgboff-20853ea7`<br>`pgu-storymode-0-v1-1106-rgboff-462a3490`<br>`pgu-storymode-0-v1-1558-rgboff-2928e89d`<br>`pgu-storymode-0-v1-2015-rgboff-55feaf84`<br>`pgu-storymode-0-v1-2377-rgboff-f3f416bb`<br>`pgu-storymode-0-v1-2954-rgboff-06ee8c3a` |
| STAGED | RGB1 | UNCONFIRMED COMPONENT — RGB1 | `rgbOff` | `pgu-storymode-0-v1-3128-rgboff-d9529a49` |
| STAGED | RGB2 | Hi-Nu Slave 1 RGB2（頭部散氣 45 粒）：熄燈段關閉。 | `rgbOff` | `pgu-storymode-0-v1-2546-rgboff-f5b906c1` |
| STAGED | RGB2 | Hi-Nu Slave 1 頭 RGB — PGU Slave 3 RGB source. | `rgbOff` | `pgu-storymode-0-v1-202-rgboff-b7c9d552` |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `rgbOff` | `pgu-storymode-0-v1-282-rgboff-7ecb0eb5`<br>`pgu-storymode-0-v1-679-rgboff-245a351b`<br>`pgu-storymode-0-v1-1107-rgboff-55dfd140`<br>`pgu-storymode-0-v1-1559-rgboff-98a17591`<br>`pgu-storymode-0-v1-2016-rgboff-38ac6b3c`<br>`pgu-storymode-0-v1-2378-rgboff-8ec03699`<br>`pgu-storymode-0-v1-2955-rgboff-e09e8934`<br>`pgu-storymode-0-v1-3129-rgboff-95447727` |
| STAGED | RGB3 | Hi-Nu Slave 1 RGB3（未接線 0 粒）：保持關閉。 | `rgbOff` | `pgu-storymode-0-v1-2548-rgboff-769f992d` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `rgbOff` | `pgu-storymode-0-v1-203-rgboff-b6eca91d`<br>`pgu-storymode-0-v1-283-rgboff-a30bda53`<br>`pgu-storymode-0-v1-680-rgboff-21fbd182`<br>`pgu-storymode-0-v1-1108-rgboff-cc3f5adc`<br>`pgu-storymode-0-v1-1560-rgboff-064c4d93`<br>`pgu-storymode-0-v1-2017-rgboff-f4aafd24`<br>`pgu-storymode-0-v1-2379-rgboff-91b17eb6`<br>`pgu-storymode-0-v1-2956-rgboff-03591f9e`<br>`pgu-storymode-0-v1-3130-rgboff-07f73747` |
| STAGED | RGB4 | Hi-Nu Slave 1 RGB4（頭部訊號 3 粒）：熄燈段關閉。 | `rgbOff` | `pgu-storymode-0-v1-2550-rgboff-e859ce97` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `rgbOff` | `pgu-storymode-0-v1-204-rgboff-57758d1d`<br>`pgu-storymode-0-v1-284-rgboff-ecea27f3`<br>`pgu-storymode-0-v1-681-rgboff-139625b3`<br>`pgu-storymode-0-v1-1109-rgboff-9f63977e`<br>`pgu-storymode-0-v1-1561-rgboff-e8a8b8cb`<br>`pgu-storymode-0-v1-2018-rgboff-f37ad0b8`<br>`pgu-storymode-0-v1-2380-rgboff-9fb122a6`<br>`pgu-storymode-0-v1-2957-rgboff-002dae6b`<br>`pgu-storymode-0-v1-3126-rgboff-7ff302bd`<br>`pgu-storymode-0-v1-3131-rgboff-6d700ff0` |
| STAGED | RGB7 | UNCONFIRMED COMPONENT — RGB7 | `rgbOff` | `pgu-storymode-0-v1-3132-rgboff-0e127368` |
| STAGED | RGB8 | UNCONFIRMED COMPONENT — RGB8 | `rgbOff` | `pgu-storymode-0-v1-3133-rgboff-9a4b5568` |
| STAGED | RGB9 | UNCONFIRMED COMPONENT — RGB9 | `rgbOff` | `pgu-storymode-0-v1-3134-rgboff-09dd80a0` |
| ON | Runtime／group target 'PWM0' | Hi-Nu Slave 1 PWM0 CH7-9（0x5F，頭部白燈）：跟隨亮點模式隨機閃爍。 | `chRandomFlash` | `pgu-storymode-0-v1-127-chrandomflash-9f841e29` |

### storyMode_awakening_3

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | GPIO '38' | Hi-Nu Slave 1 GPIO38／GPIO39：開啟左／右頭 MiniMon 眼睛。 | `digitalWrite` | `pgu-storymode-awakening-3-212-digitalwrite-7a5d08a4` |
| STAGED | GPIO '39' | UNCONFIRMED COMPONENT — GPIO '39' | `digitalWrite` | `pgu-storymode-awakening-3-213-digitalwrite-c2fcdf6e` |
| STAGED | PCA PWM0 CH channel | UNCONFIRMED COMPONENT — PCA PWM0 CH channel | `chOff`、`chProgressiveFlash` | `pgu-storymode-awakening-3-222-chprogressiveflash-3f743586`<br>`pgu-storymode-awakening-3-231-choff-119fae9f` |
| STAGED | PCA PWM0 CH0 | Hi-Nu Slave 1 PWM0 CH0（0x5F，頭部綠燈）：兩段式眼燈喚醒。 | `chGundamEyeWakeTwoStage` | `pgu-storymode-awakening-3-216-chgundameyewaketwostage-4a15338e` |
| STAGED | RGB2 | Hi-Nu Slave 1 RGB2（頭部散氣 45 粒）：Awakening cross 前段保持關閉。 | `rgbOff` | `pgu-storymode-awakening-3-203-rgboff-b5c6d53e` |
| STAGED | RGB3 | Hi-Nu Slave 1 RGB3 未接燈帶（0 粒）。 | `rgbOff` | `pgu-storymode-awakening-3-206-rgboff-8aebf6e9` |
| STAGED | RGB4 | Hi-Nu Slave 1 RGB4（頭部訊號 3 粒）：Awakening 前段保持關閉。 | `rgbOff` | `pgu-storymode-awakening-3-209-rgboff-4cabbd3c` |

### storyMode_activation

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | GPIO '38' | Hi-Nu Slave 1 GPIO38／GPIO39：開啟左／右頭 MiniMon 眼睛。 | `digitalWrite` | `pgu-storymode-activation-250-digitalwrite-0dd2e91b` |
| STAGED | GPIO '39' | UNCONFIRMED COMPONENT — GPIO '39' | `digitalWrite` | `pgu-storymode-activation-251-digitalwrite-16cd0e3a` |
| STAGED | PCA PWM0 CH channel | UNCONFIRMED COMPONENT — PCA PWM0 CH channel | `chOn` | `pgu-storymode-activation-256-chon-731f16bd` |
| STAGED | PCA PWM0 CH5 | Hi-Nu Slave 1 PWM0 CH5-6（0x5F，左／右頭紅燈）：Normal activation 保持關閉。 | `chOff` | `pgu-storymode-activation-260-choff-f31179bf` |
| STAGED | PCA PWM0 CH6 | UNCONFIRMED COMPONENT — PCA PWM0 CH6 | `chOff` | `pgu-storymode-activation-261-choff-e4a05de2` |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `gradientVentPalette`、`randomFillAll_V2` | `pgu-storymode-activation-220-randomfillall-v2-9634bc7f`<br>`pgu-storymode-activation-223-gradientventpalette-0bf84e21` |
| STAGED | RGB3 | Hi-Nu Slave 1 RGB3 未接燈帶（0 粒）。 | `rgbOff` | `pgu-storymode-activation-240-rgboff-1bbda790` |
| STAGED | RGB4 | Hi-Nu Slave 1 RGB4（頭部訊號 3 粒）：Normal 機械綠慢呼吸。 | `SpecificColorPattern` | `pgu-storymode-activation-243-specificcolorpattern-b3643905` |

### storyMode_0_v2

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| ON | GPIO '38' | Hi-Nu Slave 1 GPIO38／GPIO39：亮點模式完成後關閉左／右頭 MiniMon 眼睛。 | `digitalWrite` | `pgu-storymode-0-v2-102-digitalwrite-ae629215` |
| ON | GPIO '38' | Hi-Nu Slave 1 GPIO38／GPIO39：亮點模式開啟左／右頭 MiniMon 眼睛。 | `digitalWrite` | `pgu-storymode-0-v2-77-digitalwrite-9a64f464` |
| ON | GPIO '39' | UNCONFIRMED COMPONENT — GPIO '39' | `digitalWrite` | `pgu-storymode-0-v2-78-digitalwrite-a237004f`<br>`pgu-storymode-0-v2-103-digitalwrite-c9ddc309` |
| STAGED | Global FastLED brightness | UNCONFIRMED COMPONENT — Global FastLED brightness | `setBrightness` | `pgu-storymode-0-v2-2238-setbrightness-e1a25664` |
| OFF | PCA PWM0 CH channel | UNCONFIRMED COMPONENT — PCA PWM0 CH channel | `chOff` | `pgu-storymode-0-v2-98-choff-bc1d3e73` |
| ON | PCA PWM0 CH channel | UNCONFIRMED COMPONENT — PCA PWM0 CH channel | `chOn` | `pgu-storymode-0-v2-87-chon-558c5ab4` |
| ON | PCA PWM0 CH0 | Hi-Nu Slave 1 PWM0 CH0（0x5F，頭部綠燈）：兩段式眼燈喚醒。 | `chGundamEyeWakeTwoStage` | `pgu-storymode-0-v2-81-chgundameyewaketwostage-35ed6b51` |
| STAGED | RGB1 | Hi-Nu Slave 1 頭 RGB — PGU Slave 3 RGB source. | `rgbOff` | `pgu-storymode-0-v2-379-rgboff-7eca7227`<br>`pgu-storymode-0-v2-829-rgboff-b9053b3f`<br>`pgu-storymode-0-v2-1210-rgboff-ed77caaf`<br>`pgu-storymode-0-v2-1596-rgboff-3e0c3ca4`<br>`pgu-storymode-0-v2-1881-rgboff-05122f29`<br>`pgu-storymode-0-v2-2067-rgboff-293d4e10` |
| STAGED | RGB1 | UNCONFIRMED COMPONENT — RGB1 | `rgbOff` | `pgu-storymode-0-v2-2242-rgboff-93e1d141` |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `rgbOff` | `pgu-storymode-0-v2-380-rgboff-2495d08b`<br>`pgu-storymode-0-v2-830-rgboff-2ddbefa0`<br>`pgu-storymode-0-v2-1211-rgboff-c45c3314`<br>`pgu-storymode-0-v2-1597-rgboff-ee838719`<br>`pgu-storymode-0-v2-1882-rgboff-6dc32c8f`<br>`pgu-storymode-0-v2-2068-rgboff-94746d27`<br>`pgu-storymode-0-v2-2243-rgboff-21732039` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `rgbOff` | `pgu-storymode-0-v2-381-rgboff-6bc9056b`<br>`pgu-storymode-0-v2-831-rgboff-88cba708`<br>`pgu-storymode-0-v2-1212-rgboff-b713036c`<br>`pgu-storymode-0-v2-1598-rgboff-e97916c9`<br>`pgu-storymode-0-v2-1883-rgboff-2271ae51`<br>`pgu-storymode-0-v2-2069-rgboff-3e02e426`<br>`pgu-storymode-0-v2-2244-rgboff-1cc80b17` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `rgbOff` | `pgu-storymode-0-v2-382-rgboff-b3fe3e56`<br>`pgu-storymode-0-v2-832-rgboff-93d64d4f`<br>`pgu-storymode-0-v2-1213-rgboff-69b3c20c`<br>`pgu-storymode-0-v2-1599-rgboff-47758029`<br>`pgu-storymode-0-v2-1884-rgboff-7f196a8e`<br>`pgu-storymode-0-v2-2070-rgboff-3c643fd6`<br>`pgu-storymode-0-v2-2240-rgboff-6bece9e2`<br>`pgu-storymode-0-v2-2245-rgboff-1cc21afd` |
| STAGED | RGB7 | UNCONFIRMED COMPONENT — RGB7 | `rgbOff` | `pgu-storymode-0-v2-2246-rgboff-0a790ea5` |
| STAGED | RGB8 | UNCONFIRMED COMPONENT — RGB8 | `rgbOff` | `pgu-storymode-0-v2-2247-rgboff-9bc3b5a0` |
| STAGED | RGB9 | UNCONFIRMED COMPONENT — RGB9 | `rgbOff` | `pgu-storymode-0-v2-2248-rgboff-f4012464` |
| ON | Runtime／group target 'PWM0' | Hi-Nu Slave 1 PWM0 CH7-9（0x5F，頭部白燈）：跟隨亮點模式隨機閃爍。 | `chRandomFlash` | `pgu-storymode-0-v2-91-chrandomflash-f854107e` |
| STAGED | Runtime／group target 'strips' | UNCONFIRMED COMPONENT — Runtime／group target 'strips' | `randomFlashFixedCount_multiple` | `pgu-storymode-0-v2-162-randomflashfixedcount-multiple-b76ec8e8` |

### storyMode_storing_energy

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | GPIO '38' | Hi-Nu Slave 1 GPIO38／GPIO39：儲能開始時開啟左／右頭 MiniMon 眼睛。 | `digitalWrite` | `pgu-storymode-storing-energy-357-digitalwrite-c36e29d4` |
| STAGED | GPIO '39' | UNCONFIRMED COMPONENT — GPIO '39' | `digitalWrite` | `pgu-storymode-storing-energy-358-digitalwrite-635ddc85` |
| STAGED | PCA PWM0 CH channel | UNCONFIRMED COMPONENT — PCA PWM0 CH channel | `chOn`、`chProgressiveFlash` | `pgu-storymode-storing-energy-934-chprogressiveflash-3d360c98`<br>`pgu-storymode-storing-energy-1318-chon-d249b522` |
| STAGED | PCA PWM0 CH channel (loop 1..12 inclusive) | Hi-Nu Slave 1 PWM0 CH1-12（0x5F）：儲能前段先保持關閉。 | `chOff` | `pgu-storymode-storing-energy-366-choff-59486193` |
| STAGED | PCA PWM0 CH channel (loop 7..9 inclusive) | Hi-Nu Slave 1 PWM0 CH7-9（0x5F，頭部白燈）：1 秒後開始漸進閃爍。 | `chProgressiveFlash` | `pgu-storymode-storing-energy-1033-chprogressiveflash-11424d25` |
| STAGED | PCA PWM0 CH channel (loop 7..9 inclusive) | Hi-Nu Slave 1 PWM0 CH7-9（0x5F，頭部白燈）：3 秒後低亮長亮。 | `chOn` | `pgu-storymode-storing-energy-986-chon-cd45dd73` |
| STAGED | PCA PWM0 CH0 | Hi-Nu Slave 1 PWM0 CH0（0x5F，頭部綠燈）：4 秒後穩定呼吸。 | `chSmoothBeatsin16` | `pgu-storymode-storing-energy-1087-chsmoothbeatsin16-c6603fd8` |
| STAGED | PCA PWM0 CH0 | Hi-Nu Slave 1 PWM0 CH0（0x5F，頭部綠燈）：兩段式眼燈喚醒。 | `chGundamEyeWakeTwoStage` | `pgu-storymode-storing-energy-361-chgundameyewaketwostage-9a581b17` |
| STAGED | PCA PWM0 CH11 | Hi-Nu Slave 1 PWM0 CH11-12（0x5F，左／右頭黃二極管）：5 秒後漸進閃爍。 | `chProgressiveFlash` | `pgu-storymode-storing-energy-1186-chprogressiveflash-587a4bba` |
| STAGED | PCA PWM0 CH12 | UNCONFIRMED COMPONENT — PCA PWM0 CH12 | `chProgressiveFlash` | `pgu-storymode-storing-energy-1189-chprogressiveflash-0450bd34` |
| STAGED | PCA PWM0 CH5 | Hi-Nu Slave 1 PWM0 CH5-6（0x5F，左／右頭紅燈）：儲能期間保持關閉。 | `chOff` | `pgu-storymode-storing-energy-1134-choff-6fca58ee` |
| STAGED | PCA PWM0 CH5 | Hi-Nu Slave 1 PWM0 CH5-6（0x5F，左／右頭紅燈）：滿能量仍保持關閉。 | `chOff` | `pgu-storymode-storing-energy-1322-choff-a9f5bf89` |
| STAGED | PCA PWM0 CH6 | UNCONFIRMED COMPONENT — PCA PWM0 CH6 | `chOff` | `pgu-storymode-storing-energy-1135-choff-f6579bf2`<br>`pgu-storymode-storing-energy-1323-choff-5f27b2e7` |
| STAGED | RGB1 | Hi-Nu Slave 1 RGB1（頭部流光 36 粒）：儲能波由 80% 填充向前推進。 | `paletteWave_80Percent_SpecialWave` | `pgu-storymode-storing-energy-595-palettewave-80percent-specialwave-8b15420c` |
| STAGED | RGB2 | Hi-Nu Slave 1 RGB2（頭部散氣 45 粒）：儲能散氣持續運行。 | `VentEffect` | `pgu-storymode-storing-energy-605-venteffect-ccb307e3` |
| STAGED | RGB2 | Hi-Nu Slave 1 RGB2（頭部散氣 45 粒）：滿能量維持散氣效果。 | `VentEffect` | `pgu-storymode-storing-energy-1294-venteffect-65c60851` |
| STAGED | RGB2 | Hi-Nu Slave 1 RGB2／RGB3／RGB4：儲能 Stage 1 先保持關閉，RGB1 由共用 cross 控制。 | `rgbOff` | `pgu-storymode-storing-energy-352-rgboff-1b8be55d` |
| STAGED | RGB3 | Hi-Nu Slave 1 RGB3 未接燈帶（0 粒）。 | `rgbOff` | `pgu-storymode-storing-energy-617-rgboff-1717699f`<br>`pgu-storymode-storing-energy-1306-rgboff-1d8b5049` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `rgbOff` | `pgu-storymode-storing-energy-353-rgboff-c1a07033` |
| STAGED | RGB4 | Hi-Nu Slave 1 RGB4（頭部訊號 3 粒）：Normal 機械綠慢呼吸。 | `SpecificColorPattern` | `pgu-storymode-storing-energy-620-specificcolorpattern-4234e5ef` |
| STAGED | RGB4 | Hi-Nu Slave 1 RGB4（頭部訊號 3 粒）：滿能量維持 Normal 機械綠呼吸。 | `SpecificColorPattern` | `pgu-storymode-storing-energy-1309-specificcolorpattern-9702a63c` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `rgbOff` | `pgu-storymode-storing-energy-354-rgboff-738e6a71` |

### storyMode_2

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | GPIO '38' | Hi-Nu Slave 1 GPIO38／GPIO39：Mode 2 開啟左／右頭 MiniMon 眼睛。 | `digitalWrite` | `pgu-storymode-2-267-digitalwrite-a2373708` |
| STAGED | GPIO '39' | UNCONFIRMED COMPONENT — GPIO '39' | `digitalWrite` | `pgu-storymode-2-268-digitalwrite-8cbaf69a` |
| STAGED | PCA PWM0 CH channel | UNCONFIRMED COMPONENT — PCA PWM0 CH channel | `chOn` | `pgu-storymode-2-932-chon-906bc0cb` |
| STAGED | PCA PWM0 CH0 | Hi-Nu Slave 1 PWM0 CH0（0x5F，頭部綠燈）：兩段式眼燈喚醒。 | `chGundamEyeWakeTwoStage` | `pgu-storymode-2-271-chgundameyewaketwostage-85d4383f` |
| STAGED | PCA PWM0 CH10 | Hi-Nu Slave 1 PWM0 CH10（0x5F，頭部暖白）：8 秒後用漸進閃爍作最後啟動點綴。 | `chProgressiveFlash` | `pgu-storymode-2-1103-chprogressiveflash-f04707de` |
| STAGED | PCA PWM0 CH11 | Hi-Nu Slave 1 PWM0 CH11-12（0x5F，左／右頭黃二極管）：4 秒後低亮長亮。 | `chOn` | `pgu-storymode-2-989-chon-3bcd6017` |
| STAGED | PCA PWM0 CH12 | UNCONFIRMED COMPONENT — PCA PWM0 CH12 | `chOn` | `pgu-storymode-2-990-chon-fce47c07` |
| STAGED | PCA PWM0 CH5 | Hi-Nu Slave 1 PWM0 CH5-6（0x5F，左／右頭紅燈）：Normal 模式保持關閉。 | `chOff` | `pgu-storymode-2-1046-choff-a850729e` |
| STAGED | PCA PWM0 CH6 | UNCONFIRMED COMPONENT — PCA PWM0 CH6 | `chOff` | `pgu-storymode-2-1047-choff-eee0fbd9` |
| STAGED | RGB2 | Hi-Nu Slave 1 RGB2（頭部散氣 45 粒）：Mode 2 持續散氣。 | `VentEffect` | `pgu-storymode-2-247-venteffect-8227827a` |
| STAGED | RGB3 | Hi-Nu Slave 1 RGB3 未接燈帶（0 粒）。 | `rgbOff` | `pgu-storymode-2-259-rgboff-ad97e300` |
| STAGED | RGB4 | Hi-Nu Slave 1 RGB4（頭部訊號 3 粒）：Normal 機械綠慢呼吸。 | `SpecificColorPattern` | `pgu-storymode-2-262-specificcolorpattern-cf5a43f6` |

### storyMode_plasma

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| ON | GPIO '38' | Hi-Nu Slave 1 GPIO38／GPIO39：Plasma 全程開啟左／右頭 MiniMon 眼睛。 | `digitalWrite` | `pgu-storymode-plasma-42-digitalwrite-cfa29888` |
| ON | GPIO '39' | UNCONFIRMED COMPONENT — GPIO '39' | `digitalWrite` | `pgu-storymode-plasma-43-digitalwrite-345db8a4` |
| ON | PCA PWM0 CH channel | UNCONFIRMED COMPONENT — PCA PWM0 CH channel | `chOn` | `pgu-storymode-plasma-48-chon-81f86fd6` |
| OFF | PCA PWM0 CH5 | Hi-Nu Slave 1 PWM0 CH5-6（0x5F，左／右頭紅燈）：Plasma 保持關閉。 | `chOff` | `pgu-storymode-plasma-52-choff-88592e6e` |
| OFF | PCA PWM0 CH6 | UNCONFIRMED COMPONENT — PCA PWM0 CH6 | `chOff` | `pgu-storymode-plasma-53-choff-6e398d46` |
| STAGED | RGB3 | Hi-Nu Slave 1 RGB3 未接燈帶（0 粒）。 | `rgbOff` | `pgu-storymode-plasma-591-rgboff-8e8bd0fc` |
| STAGED | RGB4 | Hi-Nu Slave 1 RGB4（頭部訊號 3 粒）：Plasma Stage 4 使用 Normal 機械綠呼吸。 | `SpecificColorPattern` | `pgu-storymode-plasma-594-specificcolorpattern-45e8e979` |

### storyMode_trans_am

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | GPIO '38' | Hi-Nu Slave 1 GPIO38／GPIO39：開啟左／右頭 MiniMon 眼睛。 | `digitalWrite` | `pgu-storymode-trans-am-101-digitalwrite-be1cffe3` |
| STAGED | GPIO '39' | UNCONFIRMED COMPONENT — GPIO '39' | `digitalWrite` | `pgu-storymode-trans-am-102-digitalwrite-7b6f10fa` |
| STAGED | PCA PWM0 CH channel | UNCONFIRMED COMPONENT — PCA PWM0 CH channel | `chOn` | `pgu-storymode-trans-am-107-chon-de22a566` |
| STAGED | PCA PWM0 CH0 | Hi-Nu Slave 1 PWM0 CH0（0x5F，頭部綠燈）：Trans-Am 讓位給紅色戰鬥狀態。 | `chOff` | `pgu-storymode-trans-am-115-choff-a755a714` |
| STAGED | PCA PWM0 CH5 | Hi-Nu Slave 1 PWM0 CH5-6（0x5F，左／右頭紅燈）：戰鬥模式高亮長亮。 | `chOn` | `pgu-storymode-trans-am-111-chon-b4e871f8` |
| STAGED | PCA PWM0 CH6 | UNCONFIRMED COMPONENT — PCA PWM0 CH6 | `chOn` | `pgu-storymode-trans-am-112-chon-4903c741` |
| STAGED | RGB1 | Hi-Nu Slave 1 RGB1（頭部流光 36 粒）：Trans-Am 高功率紅色流動。 | `GN_Drive_Running` | `pgu-storymode-trans-am-63-gn-drive-running-28f6c2c5` |
| STAGED | RGB2 | Hi-Nu Slave 1 RGB2（頭部散氣 45 粒）：高功率散氣。 | `VentEffect` | `pgu-storymode-trans-am-75-venteffect-42adadc6` |
| STAGED | RGB3 | Hi-Nu Slave 1 RGB3 未接燈帶（0 粒）。 | `rgbOff` | `pgu-storymode-trans-am-87-rgboff-5e268325` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `SpecificColorPattern` | `pgu-storymode-trans-am-94-specificcolorpattern-8845f86b` |

### storyMode_3

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | GPIO '38' | Hi-Nu Slave 1 GPIO38／GPIO39：Mode 3 前段先開啟左／右頭 MiniMon 眼睛。 | `digitalWrite` | `pgu-storymode-3-189-digitalwrite-3cfb3732` |
| STAGED | GPIO '39' | UNCONFIRMED COMPONENT — GPIO '39' | `digitalWrite` | `pgu-storymode-3-190-digitalwrite-c343cc8b` |
| STAGED | PCA PWM0 CH channel | UNCONFIRMED COMPONENT — PCA PWM0 CH channel | `chOn` | `pgu-storymode-3-280-chon-70d98e10` |
| STAGED | PCA PWM0 CH0 | Hi-Nu Slave 1 PWM0 CH0（0x5F，頭部綠燈）：兩段式眼燈喚醒。 | `chGundamEyeWakeTwoStage` | `pgu-storymode-3-193-chgundameyewaketwostage-d2eeea1a` |
| STAGED | PCA PWM0 CH5 | Hi-Nu Slave 1 PWM0 CH5-6（0x5F，左／右頭紅燈）：Normal 保持關閉。 | `chOff` | `pgu-storymode-3-284-choff-ead64b4b` |
| STAGED | PCA PWM0 CH6 | UNCONFIRMED COMPONENT — PCA PWM0 CH6 | `chOff` | `pgu-storymode-3-285-choff-70f411b9` |
| STAGED | RGB2 | Hi-Nu Slave 1 RGB2（頭部散氣 45 粒）：Mode 3 散氣。 | `VentEffect` | `pgu-storymode-3-256-venteffect-3725269e` |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `rgb_fadeOut` | `pgu-storymode-3-738-rgb-fadeout-4522157f` |
| STAGED | RGB3 | Hi-Nu Slave 1 RGB3 未接燈帶（0 粒）。 | `rgbOff` | `pgu-storymode-3-268-rgboff-feb4199e` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `rgb_fadeOut` | `pgu-storymode-3-739-rgb-fadeout-7a0d180b` |
| STAGED | RGB4 | Hi-Nu Slave 1 RGB4（頭部訊號 3 粒）：Normal 機械綠慢呼吸。 | `SpecificColorPattern` | `pgu-storymode-3-271-specificcolorpattern-4c8172c8` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `rgb_fadeOut` | `pgu-storymode-3-740-rgb-fadeout-7b1986fd` |

### storyMode_idle

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | GPIO '38' | Hi-Nu Slave 1 GPIO38／GPIO39：Idle 關閉左／右頭 MiniMon 眼睛。 | `digitalWrite` | `pgu-storymode-idle-121-digitalwrite-cea6443a` |
| STAGED | GPIO '39' | UNCONFIRMED COMPONENT — GPIO '39' | `digitalWrite` | `pgu-storymode-idle-122-digitalwrite-8cb4b7d7` |
| STAGED | PCA PWM0 CH channel (loop 0..16 exclusive) | Hi-Nu Slave 1 PWM0 CH0-15（0x5F）：Idle 全部關閉。 | `chOff` | `pgu-storymode-idle-126-choff-ac99fe2e` |

### storyMode_motor

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | GPIO '38' | Hi-Nu Slave 1 GPIO38／GPIO39：Prelude 開啟左／右頭 MiniMon 眼睛。 | `digitalWrite` | `pgu-storymode-motor-151-digitalwrite-e369dfa1` |
| STAGED | GPIO '38' | Hi-Nu Slave 1 GPIO38／GPIO39：開甲期間保持左／右頭 MiniMon 眼睛開啟。 | `digitalWrite` | `pgu-storymode-motor-254-digitalwrite-c44032d5` |
| STAGED | GPIO '38' | UNCONFIRMED COMPONENT — GPIO '38' | `digitalWrite` | `pgu-storymode-motor-101-digitalwrite-c12346a9`<br>`pgu-storymode-motor-287-digitalwrite-44f0c971` |
| STAGED | GPIO '39' | UNCONFIRMED COMPONENT — GPIO '39' | `digitalWrite` | `pgu-storymode-motor-102-digitalwrite-4e1f3c48`<br>`pgu-storymode-motor-152-digitalwrite-26e4f3f4`<br>`pgu-storymode-motor-255-digitalwrite-d824e5fa`<br>`pgu-storymode-motor-288-digitalwrite-f5802331` |
| STAGED | PCA PWM0 CH channel | UNCONFIRMED COMPONENT — PCA PWM0 CH channel | `chOff`、`chOn` | `pgu-storymode-motor-157-chon-273fe22e`<br>`pgu-storymode-motor-164-choff-4fb05488`<br>`pgu-storymode-motor-260-chon-7b02dfb7` |
| STAGED | PCA PWM0 CH5 | Hi-Nu Slave 1 PWM0 CH5-6（0x5F，左／右頭紅燈）：與 RGB4 預警同步。 | `chOn` | `pgu-storymode-motor-265-chon-a97ad736` |
| STAGED | PCA PWM0 CH5 | UNCONFIRMED COMPONENT — PCA PWM0 CH5 | `chOff` | `pgu-storymode-motor-268-choff-bcbd82b4` |
| STAGED | PCA PWM0 CH6 | UNCONFIRMED COMPONENT — PCA PWM0 CH6 | `chOff`、`chOn` | `pgu-storymode-motor-266-chon-ecc62d10`<br>`pgu-storymode-motor-269-choff-7e733e4b` |
| STAGED | RGB1 | UNCONFIRMED COMPONENT — RGB1 | `rgbOff` | `pgu-storymode-motor-93-rgboff-9c06f1c8`<br>`pgu-storymode-motor-283-rgboff-b99df348` |
| STAGED | RGB2 | Hi-Nu Slave 1 RGB2（頭部散氣 45 粒）：第一支推桿啟動後模擬氣流排出。 | `VentEffect` | `pgu-storymode-motor-220-venteffect-a4aef56a` |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `rgbOff` | `pgu-storymode-motor-94-rgboff-f641b3ac`<br>`pgu-storymode-motor-284-rgboff-82201df2` |
| STAGED | RGB3 | Hi-Nu Slave 1 RGB3 未接燈帶（0 粒）。 | `rgbOff` | `pgu-storymode-motor-136-rgboff-d983ef17`<br>`pgu-storymode-motor-233-rgboff-97179d64` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `rgbOff` | `pgu-storymode-motor-95-rgboff-b8868afb`<br>`pgu-storymode-motor-285-rgboff-c2b75c71` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `SpecificColorPattern`、`rgbOff` | `pgu-storymode-motor-96-rgboff-a84a831d`<br>`pgu-storymode-motor-142-specificcolorpattern-c9349511`<br>`pgu-storymode-motor-244-specificcolorpattern-727700eb`<br>`pgu-storymode-motor-286-rgboff-b08069ed` |
| STAGED | Runtime／group target 'slaveId' | UNCONFIRMED COMPONENT — Runtime／group target 'slaveId' | `RGBActivationCometCross` | `pgu-storymode-motor-122-rgbactivationcometcross-7ee3131e` |

### storyMode_motor_reset

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | GPIO '38' | Hi-Nu Slave 1 GPIO38／GPIO39：reset 期間保持左／右頭 MiniMon 眼睛開啟。 | `digitalWrite` | `pgu-storymode-motor-reset-97-digitalwrite-9dd2fb2e` |
| STAGED | GPIO '38' | UNCONFIRMED COMPONENT — GPIO '38' | `digitalWrite` | `pgu-storymode-motor-reset-39-digitalwrite-0cc23fc8`<br>`pgu-storymode-motor-reset-124-digitalwrite-92704daf` |
| STAGED | GPIO '39' | UNCONFIRMED COMPONENT — GPIO '39' | `digitalWrite` | `pgu-storymode-motor-reset-40-digitalwrite-0c9f6216`<br>`pgu-storymode-motor-reset-98-digitalwrite-aa79faa6`<br>`pgu-storymode-motor-reset-125-digitalwrite-0a701c38` |
| STAGED | PCA PWM0 CH channel | UNCONFIRMED COMPONENT — PCA PWM0 CH channel | `chOn` | `pgu-storymode-motor-reset-103-chon-2fa3be23` |
| STAGED | PCA PWM0 CH5 | Hi-Nu Slave 1 PWM0 CH5-6（0x5F，左／右頭紅燈）：reset 期間低亮警示。 | `chOn` | `pgu-storymode-motor-reset-107-chon-e086d2bc` |
| STAGED | PCA PWM0 CH6 | UNCONFIRMED COMPONENT — PCA PWM0 CH6 | `chOn` | `pgu-storymode-motor-reset-108-chon-c72e8759` |
| STAGED | RGB1 | Hi-Nu Slave 1 RGB1／RGB2／RGB3：reset 只保留訊號，不播放流光或散氣。 | `rgbOff` | `pgu-storymode-motor-reset-84-rgboff-a43c4373` |
| STAGED | RGB1 | UNCONFIRMED COMPONENT — RGB1 | `rgbOff` | `pgu-storymode-motor-reset-35-rgboff-54a9ca76`<br>`pgu-storymode-motor-reset-120-rgboff-7afd03fc` |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `rgbOff` | `pgu-storymode-motor-reset-36-rgboff-8dae615c`<br>`pgu-storymode-motor-reset-85-rgboff-28f5b89e`<br>`pgu-storymode-motor-reset-121-rgboff-5ca3e342` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `rgbOff` | `pgu-storymode-motor-reset-37-rgboff-8f37ba7d`<br>`pgu-storymode-motor-reset-86-rgboff-27d39bb5`<br>`pgu-storymode-motor-reset-122-rgboff-a641f6d9` |
| STAGED | RGB4 | Hi-Nu Slave 1 RGB4（頭部訊號 3 粒）：Maintenance 琥珀橙雙脈衝。 | `SpecificColorPattern` | `pgu-storymode-motor-reset-89-specificcolorpattern-2e00044b` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `rgbOff` | `pgu-storymode-motor-reset-38-rgboff-bef38d04`<br>`pgu-storymode-motor-reset-123-rgboff-3c0429bd` |

## Slave 2

### storyMode_develop

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB1 | Hi-Nu Slave 2 身體 RGB — PGU Slave 3 RGB source. | `rgbOff` | `pgu-storymode-develop-93-rgboff-13b671f3` |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `smoothSineBreath` | `pgu-storymode-develop-95-smoothsinebreath-8fcd7c52` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `rgbOff` | `pgu-storymode-develop-101-rgboff-bea00f31` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `SpecificColorPattern` | `pgu-storymode-develop-103-specificcolorpattern-f548c99e` |

### storyMode_signals

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB4 | Hi-Nu Slave 2 身體 RGB — PGU Slave 3 RGB source. | `SpecificColorPattern` | `pgu-storymode-signals-90-specificcolorpattern-1d5d719f` |

### storyMode_0_v1

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB1 | Hi-Nu Slave 2 身體 RGB — PGU Slave 3 RGB source. | `rgbOff` | `pgu-storymode-0-v1-289-rgboff-d8a6ce8e`<br>`pgu-storymode-0-v1-686-rgboff-6b2b53a6`<br>`pgu-storymode-0-v1-1114-rgboff-f895dad1`<br>`pgu-storymode-0-v1-1566-rgboff-97d3dd4e`<br>`pgu-storymode-0-v1-2023-rgboff-2c16b493`<br>`pgu-storymode-0-v1-2385-rgboff-74c30581`<br>`pgu-storymode-0-v1-2962-rgboff-5ef7bdcd` |
| STAGED | RGB2 | Hi-Nu Slave 2 身體 RGB — PGU Slave 3 RGB source. | `rgbOff` | `pgu-storymode-0-v1-211-rgboff-4cd577a3` |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `rgbOff` | `pgu-storymode-0-v1-290-rgboff-1f544cd6`<br>`pgu-storymode-0-v1-687-rgboff-0f76ffe7`<br>`pgu-storymode-0-v1-1115-rgboff-4b249361`<br>`pgu-storymode-0-v1-1567-rgboff-753dc066`<br>`pgu-storymode-0-v1-2024-rgboff-fcba6218`<br>`pgu-storymode-0-v1-2386-rgboff-6d953a0e`<br>`pgu-storymode-0-v1-2963-rgboff-3f4abc69` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `rgbOff` | `pgu-storymode-0-v1-212-rgboff-a77826c9`<br>`pgu-storymode-0-v1-291-rgboff-29bc9052`<br>`pgu-storymode-0-v1-688-rgboff-9a8953c1`<br>`pgu-storymode-0-v1-1116-rgboff-33d78624`<br>`pgu-storymode-0-v1-1568-rgboff-fc864e71`<br>`pgu-storymode-0-v1-2025-rgboff-74d62a4b`<br>`pgu-storymode-0-v1-2387-rgboff-3e4f00fe`<br>`pgu-storymode-0-v1-2964-rgboff-ea532b27` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `rgbOff` | `pgu-storymode-0-v1-213-rgboff-339fe4f2`<br>`pgu-storymode-0-v1-292-rgboff-1b127a71`<br>`pgu-storymode-0-v1-689-rgboff-d1bab6dd`<br>`pgu-storymode-0-v1-1117-rgboff-c66df0ab`<br>`pgu-storymode-0-v1-1569-rgboff-7a2c038c`<br>`pgu-storymode-0-v1-2026-rgboff-827380fb`<br>`pgu-storymode-0-v1-2388-rgboff-aab0b2b1`<br>`pgu-storymode-0-v1-2965-rgboff-833497a0` |

### storyMode_awakening_3

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB2 | Hi-Nu Slave 2 身體 RGB — PGU Slave 3 RGB source. | `rgbOff` | `pgu-storymode-awakening-3-237-rgboff-4f84f3a8` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `rgbOff` | `pgu-storymode-awakening-3-239-rgboff-f8659d5a` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `rgbOff` | `pgu-storymode-awakening-3-241-rgboff-4eb645e9` |

### storyMode_activation

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `gradientVentPalette`、`randomFillAll_V2` | `pgu-storymode-activation-268-randomfillall-v2-ba188e4f`<br>`pgu-storymode-activation-271-gradientventpalette-bb27255f` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `GN_Drive_Normal` | `pgu-storymode-activation-286-gn-drive-normal-57d19d7f` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `renderSlave3Rgb4SpecificColor` | `pgu-storymode-activation-297-renderslave3rgb4specificcolor-9f98afc9` |

### storyMode_0_v2

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB1 | Hi-Nu Slave 2 身體 RGB — PGU Slave 3 RGB source. | `rgbOff` | `pgu-storymode-0-v2-387-rgboff-bcb6a428`<br>`pgu-storymode-0-v2-837-rgboff-601ddf74`<br>`pgu-storymode-0-v2-1218-rgboff-9154eed9`<br>`pgu-storymode-0-v2-1604-rgboff-4f1c20d2`<br>`pgu-storymode-0-v2-1889-rgboff-0adfbffd`<br>`pgu-storymode-0-v2-2075-rgboff-e81bd884` |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `rgbOff` | `pgu-storymode-0-v2-388-rgboff-b3ad96d8`<br>`pgu-storymode-0-v2-838-rgboff-590b1430`<br>`pgu-storymode-0-v2-1219-rgboff-d78ab356`<br>`pgu-storymode-0-v2-1605-rgboff-a7c2276b`<br>`pgu-storymode-0-v2-1890-rgboff-740f64b8`<br>`pgu-storymode-0-v2-2076-rgboff-74083eef` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `rgbOff` | `pgu-storymode-0-v2-389-rgboff-d238f6d1`<br>`pgu-storymode-0-v2-839-rgboff-95f4062c`<br>`pgu-storymode-0-v2-1220-rgboff-21a8586f`<br>`pgu-storymode-0-v2-1606-rgboff-4bfe9afc`<br>`pgu-storymode-0-v2-1891-rgboff-389ee08d`<br>`pgu-storymode-0-v2-2077-rgboff-22c0f7a8` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `rgbOff` | `pgu-storymode-0-v2-390-rgboff-08fbd4c3`<br>`pgu-storymode-0-v2-840-rgboff-74e2ae5e`<br>`pgu-storymode-0-v2-1221-rgboff-0011bdd5`<br>`pgu-storymode-0-v2-1607-rgboff-b56149bf`<br>`pgu-storymode-0-v2-1892-rgboff-0a70ac2c`<br>`pgu-storymode-0-v2-2078-rgboff-f5eedad4` |
| STAGED | RGB9 | Slave 2 RGB9 (3粒) 背包中間拖尾：重複亮燈輪與首輪一致。 | `rgbOn` | `pgu-storymode-0-v2-2061-rgbon-7c7f0a09` |
| STAGED | Runtime／group target 'strips' | UNCONFIRMED COMPONENT — Runtime／group target 'strips' | `randomFlashFixedCount_multiple` | `pgu-storymode-0-v2-184-randomflashfixedcount-multiple-b9adefb7` |

### storyMode_storing_energy

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB1 | Hi-Nu Slave 2 身體 RGB — PGU Slave 3 RGB source. | `paletteWave_80Percent_SpecialWave` | `pgu-storymode-storing-energy-629-palettewave-80percent-specialwave-1a4ad7d6` |
| STAGED | RGB2 | Hi-Nu Slave 2 身體 RGB — PGU Slave 3 RGB source. | `GN_Wire_Normal`、`rgbOff` | `pgu-storymode-storing-energy-372-rgboff-faad7d5a`<br>`pgu-storymode-storing-energy-1330-gn-wire-normal-e1867ac6` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `GN_Capacitor_Normal`、`rgbOff` | `pgu-storymode-storing-energy-373-rgboff-34f15e9a`<br>`pgu-storymode-storing-energy-1341-gn-capacitor-normal-4470fc40` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `renderSlave3Rgb4SpecificColor`、`rgbOff` | `pgu-storymode-storing-energy-374-rgboff-73b31824`<br>`pgu-storymode-storing-energy-638-renderslave3rgb4specificcolor-8a875b6c` |

### storyMode_2

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB2 | Hi-Nu Slave 2 身體 RGB — PGU Slave 3 RGB source. | `VentEffect` | `pgu-storymode-2-278-venteffect-008538ff` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `turbine_v3` | `pgu-storymode-2-289-turbine-v3-23cd5e30` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `SpecificColorPattern` | `pgu-storymode-2-309-specificcolorpattern-8f6efe36` |

### storyMode_plasma

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB4 | Hi-Nu Slave 2 身體 RGB — PGU Slave 3 RGB source. | `SpecificColorPattern` | `pgu-storymode-plasma-603-specificcolorpattern-d8281fb3` |

### storyMode_trans_am

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB1 | Hi-Nu Slave 2 身體 RGB — PGU Slave 3 RGB source. | `GN_Drive_Running` | `pgu-storymode-trans-am-120-gn-drive-running-ee8e3eef` |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `VentEffect` | `pgu-storymode-trans-am-131-venteffect-4ac01d68` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `turbine_v3` | `pgu-storymode-trans-am-142-turbine-v3-89213336` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `SpecificColorPattern` | `pgu-storymode-trans-am-153-specificcolorpattern-d2efb3d5` |

### storyMode_3

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB2 | Hi-Nu Slave 2 身體 RGB — PGU Slave 3 RGB source. | `VentEffect` | `pgu-storymode-3-290-venteffect-dac830b8` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `GN_Capacitor_Normal` | `pgu-storymode-3-301-gn-capacitor-normal-4b962702` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `SpecificColorPattern` | `pgu-storymode-3-313-specificcolorpattern-9d69dee4` |

### storyMode_idle

OFF／no direct call in this Slave context。

### storyMode_motor

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | Motor／servo channel '0' | UNCONFIRMED COMPONENT — Motor／servo channel '0' | `chFadeIn`、`chServoHold` | `pgu-storymode-motor-1432-chfadein-7e266397`<br>`pgu-storymode-motor-1442-chservohold-7f717eb1`<br>`pgu-storymode-motor-2101-chservohold-349ca145` |
| STAGED | Motor／servo channel '1' | UNCONFIRMED COMPONENT — Motor／servo channel '1' | `chFadeOut`、`chServoHold` | `pgu-storymode-motor-1433-chfadeout-2530f712`<br>`pgu-storymode-motor-1443-chservohold-652e2247`<br>`pgu-storymode-motor-2102-chservohold-7ea595cf` |
| STAGED | Motor／servo channel '2' | UNCONFIRMED COMPONENT — Motor／servo channel '2' | `chFadeIn`、`chServoHold` | `pgu-storymode-motor-1430-chfadein-51794ea1`<br>`pgu-storymode-motor-1444-chservohold-290f7d6f`<br>`pgu-storymode-motor-2103-chservohold-fa3638c6` |
| STAGED | Motor／servo channel '3' | UNCONFIRMED COMPONENT — Motor／servo channel '3' | `chFadeOut`、`chServoHold` | `pgu-storymode-motor-1431-chfadeout-94017f0b`<br>`pgu-storymode-motor-1445-chservohold-a182e716`<br>`pgu-storymode-motor-2104-chservohold-83d0392e` |
| STAGED | Motor／servo channel '4' | UNCONFIRMED COMPONENT — Motor／servo channel '4' | `chFadeIn`、`chServoHold` | `pgu-storymode-motor-1428-chfadein-f1c40093`<br>`pgu-storymode-motor-1446-chservohold-bb9cc10b`<br>`pgu-storymode-motor-2105-chservohold-55078b13` |
| STAGED | Motor／servo channel '5' | UNCONFIRMED COMPONENT — Motor／servo channel '5' | `chFadeOut`、`chServoHold` | `pgu-storymode-motor-1429-chfadeout-53dba5de`<br>`pgu-storymode-motor-1447-chservohold-2ce971e6`<br>`pgu-storymode-motor-2106-chservohold-183a3a20` |
| STAGED | PCA PWM1 CH i (loop 0..8 inclusive) | 0s: body white PCA + eyes — Slave 3 chest/skirt pure white PCA. | `chOn` | `pgu-storymode-motor-660-chon-c49b432e` |
| STAGED | RGB10 | UNCONFIRMED COMPONENT — RGB10 | `SpecificColorPattern` | `pgu-storymode-motor-1338-specificcolorpattern-65d34506`<br>`pgu-storymode-motor-1396-specificcolorpattern-5a6673fe`<br>`pgu-storymode-motor-2065-specificcolorpattern-b02a2172` |
| STAGED | RGB11 | UNCONFIRMED COMPONENT — RGB11 | `GN_Drive_Running` | `pgu-storymode-motor-1507-gn-drive-running-b153a3d5` |
| STAGED | RGB12 | UNCONFIRMED COMPONENT — RGB12 | `SpecificColorPattern` | `pgu-storymode-motor-1342-specificcolorpattern-5c6f7c87`<br>`pgu-storymode-motor-1371-specificcolorpattern-5cd4add6`<br>`pgu-storymode-motor-2040-specificcolorpattern-42d30bbd` |
| STAGED | RGB2 | Slave 2 backpack RGB2 — vent effect. | `VentEffect` | `pgu-storymode-motor-1451-venteffect-210f90b0` |
| STAGED | RGB3 | Slave 2 backpack RGB3 — turbine vortex. | `turbine_v3_sound` | `pgu-storymode-motor-1462-turbine-v3-sound-22d65c55` |
| STAGED | RGB4 | Slave 2 RGB4 (15粒) 背包武器流光：3秒後啟用琥珀橙黃同色系儲能漸層。 | `gunStoringEnergy` | `pgu-storymode-motor-646-gunstoringenergy-5e61ea88` |
| STAGED | RGB4 | Slave 2 RGB4 (15粒) 背包武器流光：琥珀橙黃同色系儲能漸層。 | `gunStoringEnergy` | `pgu-storymode-motor-1475-gunstoringenergy-1983ae78` |
| STAGED | RGB7 | Slave 2 backpack RGB7/RGB9/RGB11 — GN drive running. | `GN_Drive_Running` | `pgu-storymode-motor-1487-gn-drive-running-1e4f62b8` |
| STAGED | RGB8 | UNCONFIRMED COMPONENT — RGB8 | `SpecificColorPattern` | `pgu-storymode-motor-1334-specificcolorpattern-2a05c0c8`<br>`pgu-storymode-motor-1421-specificcolorpattern-6d394611`<br>`pgu-storymode-motor-2090-specificcolorpattern-5bdafab7` |
| STAGED | RGB9 | UNCONFIRMED COMPONENT — RGB9 | `GN_Drive_Running` | `pgu-storymode-motor-1497-gn-drive-running-607d0dcc` |

### storyMode_motor_reset

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | Motor／servo channel '0' | UNCONFIRMED COMPONENT — Motor／servo channel '0' | `chFadeOut`、`chServoHold` | `pgu-storymode-motor-reset-272-chfadeout-8ec7952f`<br>`pgu-storymode-motor-reset-281-chservohold-e3b397f3`<br>`pgu-storymode-motor-reset-631-chservohold-657b24c5`<br>`pgu-storymode-motor-reset-828-chservohold-d25420fb`<br>`pgu-storymode-motor-reset-999-chservohold-f2ce1394` |
| STAGED | Motor／servo channel '1' | UNCONFIRMED COMPONENT — Motor／servo channel '1' | `chFadeIn`、`chServoHold` | `pgu-storymode-motor-reset-273-chfadein-b5607e6b`<br>`pgu-storymode-motor-reset-282-chservohold-1d010dec`<br>`pgu-storymode-motor-reset-632-chservohold-d24d1509`<br>`pgu-storymode-motor-reset-829-chservohold-d00646a5`<br>`pgu-storymode-motor-reset-1000-chservohold-7ddd1490` |
| STAGED | Motor／servo channel '2' | UNCONFIRMED COMPONENT — Motor／servo channel '2' | `chFadeOut`、`chServoHold` | `pgu-storymode-motor-reset-270-chfadeout-26c6de39`<br>`pgu-storymode-motor-reset-283-chservohold-a63b3682`<br>`pgu-storymode-motor-reset-633-chservohold-2a9156b4`<br>`pgu-storymode-motor-reset-830-chservohold-1d0a089e`<br>`pgu-storymode-motor-reset-1001-chservohold-b6476b9b` |
| STAGED | Motor／servo channel '3' | UNCONFIRMED COMPONENT — Motor／servo channel '3' | `chFadeIn`、`chServoHold` | `pgu-storymode-motor-reset-271-chfadein-a5139207`<br>`pgu-storymode-motor-reset-284-chservohold-557a6a4f`<br>`pgu-storymode-motor-reset-634-chservohold-827616d4`<br>`pgu-storymode-motor-reset-831-chservohold-92be9f4c`<br>`pgu-storymode-motor-reset-1002-chservohold-f0baff53` |
| STAGED | Motor／servo channel '4' | UNCONFIRMED COMPONENT — Motor／servo channel '4' | `chFadeOut`、`chServoHold` | `pgu-storymode-motor-reset-268-chfadeout-c0ff3b87`<br>`pgu-storymode-motor-reset-285-chservohold-6618a6e7`<br>`pgu-storymode-motor-reset-635-chservohold-66e8997e`<br>`pgu-storymode-motor-reset-832-chservohold-88384eaf`<br>`pgu-storymode-motor-reset-1003-chservohold-d789b45c` |
| STAGED | Motor／servo channel '5' | UNCONFIRMED COMPONENT — Motor／servo channel '5' | `chFadeIn`、`chServoHold` | `pgu-storymode-motor-reset-269-chfadein-f675a320`<br>`pgu-storymode-motor-reset-286-chservohold-f62904aa`<br>`pgu-storymode-motor-reset-636-chservohold-b8e95d67`<br>`pgu-storymode-motor-reset-833-chservohold-fc228dfc`<br>`pgu-storymode-motor-reset-1004-chservohold-2ea63031` |
| STAGED | RGB10 | UNCONFIRMED COMPONENT — RGB10 | `SpecificColorPattern`、`rgbOff` | `pgu-storymode-motor-reset-236-specificcolorpattern-be3c5703`<br>`pgu-storymode-motor-reset-623-rgboff-6f2c99ee`<br>`pgu-storymode-motor-reset-820-rgboff-998917e1`<br>`pgu-storymode-motor-reset-991-rgboff-d75ff52d` |
| STAGED | RGB12 | UNCONFIRMED COMPONENT — RGB12 | `SpecificColorPattern`、`rgbOff` | `pgu-storymode-motor-reset-210-specificcolorpattern-788de56d`<br>`pgu-storymode-motor-reset-624-rgboff-d8147f18`<br>`pgu-storymode-motor-reset-821-rgboff-966b67a4`<br>`pgu-storymode-motor-reset-992-rgboff-46605bc5` |
| STAGED | RGB8 | UNCONFIRMED COMPONENT — RGB8 | `SpecificColorPattern`、`rgbOff` | `pgu-storymode-motor-reset-262-specificcolorpattern-644e74e9`<br>`pgu-storymode-motor-reset-622-rgboff-22ffb00b`<br>`pgu-storymode-motor-reset-819-rgboff-8ed344e1`<br>`pgu-storymode-motor-reset-990-rgboff-40e96962` |

## Slave 3

### storyMode_develop

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB1 | Hi-Nu Slave 3/5 左右手上段 RGB — shared PGU Slave 4 RGB source. | `rgbOff` | `pgu-storymode-develop-122-rgboff-bfeb2c5b` |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `rgbOff` | `pgu-storymode-develop-123-rgboff-d4a0077e` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `rgbOff` | `pgu-storymode-develop-124-rgboff-c656e65f` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `SpecificColorPattern` | `pgu-storymode-develop-126-specificcolorpattern-a89be655` |

### storyMode_signals

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB4 | Hi-Nu Slave 3/5 左右手上段 RGB — shared PGU Slave 4 RGB source. | `SpecificColorPattern` | `pgu-storymode-signals-112-specificcolorpattern-6a08c2d1` |

### storyMode_0_v1

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB1 | Hi-Nu Slave 3/5 左右手上段 RGB — shared PGU Slave 4 RGB source. | `randomFlashWithGap_multiple`、`randomLightUp` | `pgu-storymode-0-v1-298-randomflashwithgap-multiple-6bce3ee0`<br>`pgu-storymode-0-v1-2032-randomlightup-951392c3` |
| STAGED | RGB1 | UNCONFIRMED COMPONENT — RGB1 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v1-699-randomflashwithgap-multiple-e2222f52`<br>`pgu-storymode-0-v1-1135-randomlightup-ec3770c2`<br>`pgu-storymode-0-v1-1598-randomlightup-6bb5d2c2`<br>`pgu-storymode-0-v1-2398-rgbon-45029b8a`<br>`pgu-storymode-0-v1-2975-rgbon-cdc34964` |
| STAGED | RGB10 | UNCONFIRMED COMPONENT — RGB10 | `randomFlashWithGap_multiple` | `pgu-storymode-0-v1-347-randomflashwithgap-multiple-8391b8e7` |
| STAGED | RGB11 | UNCONFIRMED COMPONENT — RGB11 | `randomFlashWithGap_multiple` | `pgu-storymode-0-v1-354-randomflashwithgap-multiple-0ccfbede` |
| STAGED | RGB12 | UNCONFIRMED COMPONENT — RGB12 | `randomFlashWithGap_multiple` | `pgu-storymode-0-v1-361-randomflashwithgap-multiple-faec005e` |
| STAGED | RGB13 | UNCONFIRMED COMPONENT — RGB13 | `randomFlashWithGap_multiple` | `pgu-storymode-0-v1-368-randomflashwithgap-multiple-daeb1bb7` |
| STAGED | RGB16 | UNCONFIRMED COMPONENT — RGB16 | `randomFlashWithGap_multiple` | `pgu-storymode-0-v1-375-randomflashwithgap-multiple-a9d2e2e4` |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v1-305-randomflashwithgap-multiple-456d3505`<br>`pgu-storymode-0-v1-706-randomflashwithgap-multiple-a9e35944`<br>`pgu-storymode-0-v1-1142-randomlightup-afd92ea9`<br>`pgu-storymode-0-v1-1605-randomlightup-ff05026c`<br>`pgu-storymode-0-v1-2039-randomlightup-2a9f2647`<br>`pgu-storymode-0-v1-2400-rgbon-c5d527bf`<br>`pgu-storymode-0-v1-2977-rgbon-6759bd9e` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v1-312-randomflashwithgap-multiple-43c556d1`<br>`pgu-storymode-0-v1-713-randomflashwithgap-multiple-f9e90c47`<br>`pgu-storymode-0-v1-1149-randomlightup-eb22ee16`<br>`pgu-storymode-0-v1-1612-randomlightup-1c80d27c`<br>`pgu-storymode-0-v1-2046-randomlightup-3ced3297`<br>`pgu-storymode-0-v1-2402-rgbon-94f82500`<br>`pgu-storymode-0-v1-2979-rgbon-c22eea66` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v1-319-randomflashwithgap-multiple-4b5e601b`<br>`pgu-storymode-0-v1-720-randomflashwithgap-multiple-e75038a1`<br>`pgu-storymode-0-v1-1127-randomlightup-19cabc52`<br>`pgu-storymode-0-v1-1157-randomlightup-9f2c8e70`<br>`pgu-storymode-0-v1-1620-randomlightup-827e1894`<br>`pgu-storymode-0-v1-2053-randomlightup-c8dd8f5c`<br>`pgu-storymode-0-v1-2404-rgbon-18c00769`<br>`pgu-storymode-0-v1-2981-rgbon-4361b8c7` |
| STAGED | RGB7 | Hi-Nu Slave 3/5 左右手上段 RGB — shared PGU Slave 4 RGB source. | `GN_Sword_Pulse_Color` | `pgu-storymode-0-v1-1577-gn-sword-pulse-color-c4622d74` |
| STAGED | RGB7 | UNCONFIRMED COMPONENT — RGB7 | `GN_Sword_Pulse_Color`、`randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v1-326-randomflashwithgap-multiple-96f81d17`<br>`pgu-storymode-0-v1-1173-randomlightup-54894fa5`<br>`pgu-storymode-0-v1-1589-randomlightup-027bf6ef`<br>`pgu-storymode-0-v1-2061-gn-sword-pulse-color-c66ff0a1`<br>`pgu-storymode-0-v1-2073-randomlightup-bf6a107d`<br>`pgu-storymode-0-v1-2406-rgbon-e340c77b`<br>`pgu-storymode-0-v1-2983-rgbon-44d0d621` |
| STAGED | RGB8 | UNCONFIRMED COMPONENT — RGB8 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v1-333-randomflashwithgap-multiple-6d79cb2b`<br>`pgu-storymode-0-v1-727-randomflashwithgap-multiple-4caf6259`<br>`pgu-storymode-0-v1-1180-randomlightup-290eb087`<br>`pgu-storymode-0-v1-1636-randomlightup-5642c1b2`<br>`pgu-storymode-0-v1-2081-randomlightup-dfc3ced8`<br>`pgu-storymode-0-v1-2408-rgbon-583d7b24`<br>`pgu-storymode-0-v1-2985-rgbon-664a8c41` |
| STAGED | RGB9 | UNCONFIRMED COMPONENT — RGB9 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v1-340-randomflashwithgap-multiple-5dedbe22`<br>`pgu-storymode-0-v1-734-randomflashwithgap-multiple-6782aae4`<br>`pgu-storymode-0-v1-1165-randomlightup-284a6b45`<br>`pgu-storymode-0-v1-1187-randomlightup-59cfd1ee`<br>`pgu-storymode-0-v1-1628-randomlightup-b1c4bc23`<br>`pgu-storymode-0-v1-1643-randomlightup-95e8e19e`<br>`pgu-storymode-0-v1-2088-randomlightup-b799184d`<br>`pgu-storymode-0-v1-2410-rgbon-28cd0d95`<br>`pgu-storymode-0-v1-2987-rgbon-08c15269` |

### storyMode_awakening_3

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB2 | Hi-Nu Slave 3/5 左右手上段 RGB — shared PGU Slave 4 RGB source. | `rgbOff` | `pgu-storymode-awakening-3-247-rgboff-959952a3` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `rgbOff` | `pgu-storymode-awakening-3-249-rgboff-34694bef` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `rgbOff` | `pgu-storymode-awakening-3-252-rgboff-83cf3eca`<br>`pgu-storymode-awakening-3-257-rgboff-3fa9d9e3` |
| STAGED | RGB7 | UNCONFIRMED COMPONENT — RGB7 | `rgbOff` | `pgu-storymode-awakening-3-254-rgboff-e39c7992` |

### storyMode_activation

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `gradientVentPalette`、`randomFillAll_V2` | `pgu-storymode-activation-317-randomfillall-v2-bc624f37`<br>`pgu-storymode-activation-320-gradientventpalette-426cac24` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `VentEffect`、`turbine_v3` | `pgu-storymode-activation-336-venteffect-7ab7982c`<br>`pgu-storymode-activation-347-turbine-v3-ebef0019` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `SpecificColorPattern` | `pgu-storymode-activation-360-specificcolorpattern-d0b36ae1`<br>`pgu-storymode-activation-368-specificcolorpattern-41cf367f` |

### storyMode_0_v2

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB1 | Hi-Nu Slave 3/5 左右手上段 RGB — shared PGU Slave 4 RGB source. | `randomLightUp` | `pgu-storymode-0-v2-1613-randomlightup-24a00213` |
| STAGED | RGB1 | UNCONFIRMED COMPONENT — RGB1 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v2-401-randomflashwithgap-multiple-3add7303`<br>`pgu-storymode-0-v2-850-randomlightup-e593927b`<br>`pgu-storymode-0-v2-1250-randomlightup-e4dc1bc2`<br>`pgu-storymode-0-v2-1902-rgbon-1fd3daf0`<br>`pgu-storymode-0-v2-2088-rgbon-cdb9d0bf` |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v2-408-randomflashwithgap-multiple-05e649e1`<br>`pgu-storymode-0-v2-857-randomlightup-99506465`<br>`pgu-storymode-0-v2-1257-randomlightup-81775a00`<br>`pgu-storymode-0-v2-1620-randomlightup-aad872aa`<br>`pgu-storymode-0-v2-1904-rgbon-65c9c5ef`<br>`pgu-storymode-0-v2-2090-rgbon-7c6c0a03` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v2-415-randomflashwithgap-multiple-29addb43`<br>`pgu-storymode-0-v2-864-randomlightup-aeb56491`<br>`pgu-storymode-0-v2-1264-randomlightup-5e4a3ef4`<br>`pgu-storymode-0-v2-1627-randomlightup-2558bc4e`<br>`pgu-storymode-0-v2-1906-rgbon-c4e62a56`<br>`pgu-storymode-0-v2-2092-rgbon-b3eeb579` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v2-422-randomflashwithgap-multiple-d0b50e67`<br>`pgu-storymode-0-v2-872-randomlightup-5e9847fb`<br>`pgu-storymode-0-v2-1271-randomlightup-6dd55b35`<br>`pgu-storymode-0-v2-1634-randomlightup-875f0c05`<br>`pgu-storymode-0-v2-1908-rgbon-838cfe47`<br>`pgu-storymode-0-v2-2094-rgbon-f676eeb7` |
| STAGED | RGB7 | Hi-Nu Slave 3/5 左右手上段 RGB — shared PGU Slave 4 RGB source. | `GN_Sword_Pulse_Color` | `pgu-storymode-0-v2-1229-gn-sword-pulse-color-55ecf825` |
| STAGED | RGB7 | UNCONFIRMED COMPONENT — RGB7 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOff`、`rgbOn` | `pgu-storymode-0-v2-429-randomflashwithgap-multiple-3e5a41f0`<br>`pgu-storymode-0-v2-453-rgboff-408e0ebf`<br>`pgu-storymode-0-v2-888-randomlightup-e511e28b`<br>`pgu-storymode-0-v2-1241-randomlightup-7d3cf370`<br>`pgu-storymode-0-v2-1642-randomlightup-20708adf`<br>`pgu-storymode-0-v2-1910-rgbon-a2518330`<br>`pgu-storymode-0-v2-2096-rgbon-5634ec78` |
| STAGED | RGB8 | UNCONFIRMED COMPONENT — RGB8 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v2-436-randomflashwithgap-multiple-44681506`<br>`pgu-storymode-0-v2-895-randomlightup-eb0d4b45`<br>`pgu-storymode-0-v2-1278-randomlightup-4ae1f2b4`<br>`pgu-storymode-0-v2-1650-randomlightup-a4dabd5b`<br>`pgu-storymode-0-v2-1912-rgbon-4a4fe977`<br>`pgu-storymode-0-v2-2098-rgbon-271388a9` |
| STAGED | RGB9 | UNCONFIRMED COMPONENT — RGB9 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v2-443-randomflashwithgap-multiple-e3f48e5a`<br>`pgu-storymode-0-v2-880-randomlightup-512c7a46`<br>`pgu-storymode-0-v2-902-randomlightup-f2d0d200`<br>`pgu-storymode-0-v2-1285-randomlightup-f81ba1ad`<br>`pgu-storymode-0-v2-1657-randomlightup-a6656afd`<br>`pgu-storymode-0-v2-1914-rgbon-6a5254ec`<br>`pgu-storymode-0-v2-2100-rgbon-e60afc2f` |
| STAGED | Runtime／group target 'strips' | UNCONFIRMED COMPONENT — Runtime／group target 'strips' | `randomFlashFixedCount_multiple` | `pgu-storymode-0-v2-209-randomflashfixedcount-multiple-bef3d0cb` |

### storyMode_storing_energy

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB1 | Hi-Nu Slave 3/5 左右手上段 RGB — shared PGU Slave 4 RGB source. | `paletteWave_80Percent_SpecialWave` | `pgu-storymode-storing-energy-644-palettewave-80percent-specialwave-112b3e49` |
| STAGED | RGB2 | Hi-Nu Slave 3/5 左右手上段 RGB — shared PGU Slave 4 RGB source. | `rgbOff` | `pgu-storymode-storing-energy-380-rgboff-ad631d82` |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `gradientVentPalette`、`rgbOff` | `pgu-storymode-storing-energy-654-gradientventpalette-9268881e`<br>`pgu-storymode-storing-energy-673-rgboff-c56cf59c` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `rgbOff` | `pgu-storymode-storing-energy-381-rgboff-da8d0948`<br>`pgu-storymode-storing-energy-676-rgboff-71bbebae` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `SpecificColorPattern`、`rgbOff` | `pgu-storymode-storing-energy-382-rgboff-4cd42119`<br>`pgu-storymode-storing-energy-678-specificcolorpattern-7a44aeb9` |

### storyMode_2

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB2 | Hi-Nu Slave 3/5 左右手上段 RGB — shared PGU Slave 4 RGB source. | `gradientVentPalette` | `pgu-storymode-2-318-gradientventpalette-42187153` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `turbine_v3` | `pgu-storymode-2-338-turbine-v3-b94ec230` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `SpecificColorPattern` | `pgu-storymode-2-351-specificcolorpattern-c8af8eff` |

### storyMode_plasma

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB4 | Hi-Nu Slave 3/5 左右手上段 RGB — shared PGU Slave 4 RGB source. | `SpecificColorPattern` | `pgu-storymode-plasma-613-specificcolorpattern-a355adc9` |

### storyMode_trans_am

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB1 | Hi-Nu Slave 3/5 左右手上段 RGB — shared PGU Slave 4 RGB source. | `GN_Drive_Running` | `pgu-storymode-trans-am-163-gn-drive-running-cfe38193` |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `gradientVentPalette` | `pgu-storymode-trans-am-174-gradientventpalette-8f1e46bb` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `turbine_v3` | `pgu-storymode-trans-am-194-turbine-v3-032f68d4` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `SpecificColorPattern` | `pgu-storymode-trans-am-207-specificcolorpattern-4b92c72e` |

### storyMode_3

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `gradientVentPalette` | `pgu-storymode-3-336-gradientventpalette-ac663d1d` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `turbine_v3` | `pgu-storymode-3-356-turbine-v3-49f36c91` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `SpecificColorPattern` | `pgu-storymode-3-370-specificcolorpattern-9a587c61`<br>`pgu-storymode-3-378-specificcolorpattern-244c844b` |

### storyMode_idle

OFF／no direct call in this Slave context。

### storyMode_motor

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | Motor／servo channel '0' | UNCONFIRMED COMPONENT — Motor／servo channel '0' | `chServoHold`、`chServoStop` | `pgu-storymode-motor-942-chservostop-24c8ff09`<br>`pgu-storymode-motor-1072-chservostop-4bdf4745`<br>`pgu-storymode-motor-1537-chservohold-5877ee3b`<br>`pgu-storymode-motor-1540-chservostop-63f89bdf`<br>`pgu-storymode-motor-2113-chservohold-906b46c0` |
| STAGED | Motor／servo channel '1' | UNCONFIRMED COMPONENT — Motor／servo channel '1' | `chFadeIn`、`chServoStop` | `pgu-storymode-motor-943-chservostop-b9b85250`<br>`pgu-storymode-motor-1067-chfadein-b6ab65c2`<br>`pgu-storymode-motor-1070-chservostop-1f92562b` |
| STAGED | Motor／servo channel '2' | UNCONFIRMED COMPONENT — Motor／servo channel '2' | `chFadeIn`、`chServoHold`、`chServoStop` | `pgu-storymode-motor-931-chfadein-6f223dcf`<br>`pgu-storymode-motor-937-chservostop-f884d7eb`<br>`pgu-storymode-motor-1073-chservohold-2fbb7204` |
| STAGED | Motor／servo channel '3' | UNCONFIRMED COMPONENT — Motor／servo channel '3' | `chFadeIn`、`chServoHold`、`chServoStop` | `pgu-storymode-motor-932-chfadein-24775ec4`<br>`pgu-storymode-motor-938-chservostop-c071f3b9`<br>`pgu-storymode-motor-1074-chservohold-872870f1` |
| STAGED | Motor／servo channel '4' | UNCONFIRMED COMPONENT — Motor／servo channel '4' | `chFadeIn`、`chServoHold`、`chServoStop` | `pgu-storymode-motor-933-chfadein-25ab4fc0`<br>`pgu-storymode-motor-939-chservostop-b54642f7`<br>`pgu-storymode-motor-1075-chservohold-8cf26b02` |
| STAGED | Motor／servo channel '5' | UNCONFIRMED COMPONENT — Motor／servo channel '5' | `chFadeIn`、`chServoHold`、`chServoStop` | `pgu-storymode-motor-934-chfadein-a0bfa45c`<br>`pgu-storymode-motor-940-chservostop-06980562`<br>`pgu-storymode-motor-1076-chservohold-dc2e998e` |
| STAGED | Motor／servo channel 'i' | UNCONFIRMED COMPONENT — Motor／servo channel 'i' | `chServoHold` | `pgu-storymode-motor-1542-chservohold-2b1a5a06`<br>`pgu-storymode-motor-2115-chservohold-814b83c6` |
| STAGED | PCA PWM0 CH 0 | Slave 3 PWM0 CH0 (0x51) 頭眼，綠，2粒。 | `chSmoothBeatsin16` | `pgu-storymode-motor-986-chsmoothbeatsin16-174e54c3` |
| STAGED | PCA PWM0 CH 0 | UNCONFIRMED COMPONENT — PCA PWM0 CH 0 | `chSmoothBeatsin16` | `pgu-storymode-motor-1005-chsmoothbeatsin16-497a755a` |
| STAGED | PCA PWM0 CH 1 | UNCONFIRMED COMPONENT — PCA PWM0 CH 1 | `chOn` | `pgu-storymode-motor-1544-chon-594239c0`<br>`pgu-storymode-motor-2117-chon-797160a8` |
| STAGED | PCA PWM0 CH i (loop 1..6 inclusive) | Slave 3 PWM0 CH1-6 (0x51) 左頭火神炮，橙，1粒；右頭火神炮，橙，1粒；左／右頭耳，暖白，6粒；頭嘴，白，2粒；左／右頭，暖白，2粒；頭額頭，綠，1粒。 | `chInternalStructure` | `pgu-storymode-motor-991-chinternalstructure-44138dff` |
| STAGED | PCA PWM0 CH i (loop 7..15 inclusive) | Slave 3 PWM0 CH7-15 (0x51) 頭後額，綠，1粒；左／右頭，冰藍，8粒；左／右頭，暖白，4粒；左／右頭後頸，冰藍，2粒；左／右頭後腦，暖白，40粒；左／右頭後腦，白，2粒。 | `chOn` | `pgu-storymode-motor-1003-chon-edb38a29` |
| ON | PCA PWM0 CH0 | Slave 3 PWM0 CH0 (0x51) 頭眼，綠，2粒。 | `chGundamEyeWakeTwoStage` | `pgu-storymode-motor-581-chgundameyewaketwostage-21a01939` |
| ON | PCA PWM0 CH6 | Slave 3 PWM0 CH6 (0x51) 頭額頭，綠，1粒。 | `chGundamEyeWakeTwoStage` | `pgu-storymode-motor-583-chgundameyewaketwostage-efe2a643` |
| STAGED | PCA PWM1 CH 0 | Slave 3 PWM1 CH0-2,9,14-15 (0x5B) 右胸上圓圈燈，燈，1粒；右胸下金長方框，紅，1粒；左／右胸駕駛艙，冰藍，2粒；右胸，白，1粒；左胸後，紅，2粒；右胸後，紅，2粒。 | `chOn` | `pgu-storymode-motor-1011-chon-4ac66820` |
| STAGED | PCA PWM1 CH 0 | UNCONFIRMED COMPONENT — PCA PWM1 CH 0 | `chOn` | `pgu-storymode-motor-944-chon-24d9959a`<br>`pgu-storymode-motor-1077-chon-07f083b1`<br>`pgu-storymode-motor-1546-chon-8dcd9b39`<br>`pgu-storymode-motor-2118-chon-9e8b46a0` |
| STAGED | PCA PWM1 CH 1 | UNCONFIRMED COMPONENT — PCA PWM1 CH 1 | `chOn` | `pgu-storymode-motor-945-chon-0ad3bfe6`<br>`pgu-storymode-motor-1012-chon-f56268e9`<br>`pgu-storymode-motor-1078-chon-2eaee55c`<br>`pgu-storymode-motor-1547-chon-942660a4`<br>`pgu-storymode-motor-2119-chon-0d468273` |
| STAGED | PCA PWM1 CH 12 | Slave 3 PWM1 CH12-13 (0x5B) 左胸前，紅，2粒；右胸前，紅，2粒。 | `chProgressiveFlash` | `pgu-storymode-motor-1036-chprogressiveflash-340a4039` |
| STAGED | PCA PWM1 CH 13 | UNCONFIRMED COMPONENT — PCA PWM1 CH 13 | `chProgressiveFlash` | `pgu-storymode-motor-1040-chprogressiveflash-8829bac3` |
| STAGED | PCA PWM1 CH 2 | UNCONFIRMED COMPONENT — PCA PWM1 CH 2 | `chOn` | `pgu-storymode-motor-946-chon-e64ae446`<br>`pgu-storymode-motor-1013-chon-9a8170c0`<br>`pgu-storymode-motor-1079-chon-d66da8b2`<br>`pgu-storymode-motor-1548-chon-3fd26639`<br>`pgu-storymode-motor-2120-chon-2073d0a4` |
| STAGED | PCA PWM1 CH 4 | Slave 3 PWM1 CH4-5,7 (0x5B) 左胸前頸，綠，1粒；右胸前頸，綠，1粒；胸，白，1粒。 | `chSmoothBeatsin16` | `pgu-storymode-motor-1026-chsmoothbeatsin16-9042c465` |
| STAGED | PCA PWM1 CH 5 | UNCONFIRMED COMPONENT — PCA PWM1 CH 5 | `chSmoothBeatsin16` | `pgu-storymode-motor-1029-chsmoothbeatsin16-e373e629` |
| STAGED | PCA PWM1 CH 7 | UNCONFIRMED COMPONENT — PCA PWM1 CH 7 | `chOn`、`chSmoothBeatsin16` | `pgu-storymode-motor-947-chon-aa129e70`<br>`pgu-storymode-motor-1032-chsmoothbeatsin16-7ac4b77f`<br>`pgu-storymode-motor-1080-chon-031e94fe`<br>`pgu-storymode-motor-1549-chon-5ac37f1a`<br>`pgu-storymode-motor-2121-chon-c268ed66` |
| STAGED | PCA PWM1 CH 8 | UNCONFIRMED COMPONENT — PCA PWM1 CH 8 | `chOn` | `pgu-storymode-motor-948-chon-7acea167`<br>`pgu-storymode-motor-1081-chon-2ab49e51`<br>`pgu-storymode-motor-1550-chon-d36e2c6c`<br>`pgu-storymode-motor-2122-chon-859a6ac5` |
| STAGED | PCA PWM1 CH 9 | UNCONFIRMED COMPONENT — PCA PWM1 CH 9 | `chOn` | `pgu-storymode-motor-1014-chon-69232c85` |
| STAGED | PCA PWM1 CH i (loop 0..8 inclusive) | 0s: body white PCA + eyes — Slave 3 chest/skirt pure white PCA. | `chOn` | `pgu-storymode-motor-674-chon-4da78bfa` |
| STAGED | PCA PWM1 CH i (loop 14..15 inclusive) | UNCONFIRMED COMPONENT — PCA PWM1 CH i (loop 14..15 inclusive) | `chOn` | `pgu-storymode-motor-1016-chon-515d8ee6` |
| STAGED | PCA PWM1 CH3 | Slave 3 PWM1 CH3,6,10-11 (0x5B) 胸後頸，暖白，5粒；胸，綠，1粒；左胸，白，1粒；右胸，白，1粒。 | `chFlashAlternative` | `pgu-storymode-motor-1019-chflashalternative-43540349` |
| STAGED | PCA PWM1 CH6 | UNCONFIRMED COMPONENT — PCA PWM1 CH6 | `chFlashAlternative` | `pgu-storymode-motor-1022-chflashalternative-b7e9df5b` |
| STAGED | RGB1 | Slave 3 RGB1 — GN drive running. | `GN_Drive_Running` | `pgu-storymode-motor-951-gn-drive-running-bb203ba0` |
| STAGED | RGB2 | Slave 3 RGB2 — chest/skirt vent effect. | `VentEffect` | `pgu-storymode-motor-962-venteffect-1a709b78` |
| STAGED | RGB3 | Slave 3 RGB3 — rear-skirt turbine vortex. | `turbine_v3_sound` | `pgu-storymode-motor-973-turbine-v3-sound-e26dcc1d` |
| STAGED | RGB4 | 3s: all signals green — Slave 3 RGB4 signal LEDs. | `SpecificColorPattern` | `pgu-storymode-motor-666-specificcolorpattern-75ec790b` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `SpecificColorPattern` | `pgu-storymode-motor-919-specificcolorpattern-de3a914e`<br>`pgu-storymode-motor-925-specificcolorpattern-543503b0`<br>`pgu-storymode-motor-1055-specificcolorpattern-a0ab9ee0`<br>`pgu-storymode-motor-1061-specificcolorpattern-e7034e72`<br>`pgu-storymode-motor-1521-specificcolorpattern-c87edebe`<br>`pgu-storymode-motor-1527-specificcolorpattern-a380f0d7`<br>`pgu-storymode-motor-2109-specificcolorpattern-f265fc92` |

### storyMode_motor_reset

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | Motor／servo channel '0' | UNCONFIRMED COMPONENT — Motor／servo channel '0' | `chFadeOut`、`chServoHold`、`chServoStop` | `pgu-storymode-motor-reset-297-chfadeout-b8b6f7e5`<br>`pgu-storymode-motor-reset-300-chservohold-1db85706`<br>`pgu-storymode-motor-reset-649-chservostop-7e85fe19`<br>`pgu-storymode-motor-reset-848-chservostop-f420bb55` |
| STAGED | Motor／servo channel '1' | UNCONFIRMED COMPONENT — Motor／servo channel '1' | `chFadeOut`、`chServoHold`、`chServoStop` | `pgu-storymode-motor-reset-645-chfadeout-b52fcc97`<br>`pgu-storymode-motor-reset-647-chservohold-d0fd326f`<br>`pgu-storymode-motor-reset-849-chservostop-75f816bf` |
| STAGED | Motor／servo channel '2' | UNCONFIRMED COMPONENT — Motor／servo channel '2' | `chFadeOut`、`chServoHold` | `pgu-storymode-motor-reset-842-chfadeout-b639e56f`<br>`pgu-storymode-motor-reset-845-chservohold-03bbc514` |
| STAGED | Motor／servo channel '3' | UNCONFIRMED COMPONENT — Motor／servo channel '3' | `chFadeOut`、`chServoHold` | `pgu-storymode-motor-reset-843-chfadeout-65981089`<br>`pgu-storymode-motor-reset-846-chservohold-db7025de` |
| STAGED | Motor／servo channel '4' | UNCONFIRMED COMPONENT — Motor／servo channel '4' | `chFadeOut`、`chServoHold` | `pgu-storymode-motor-reset-851-chservohold-83601935`<br>`pgu-storymode-motor-reset-1014-chfadeout-0b91f7e6`<br>`pgu-storymode-motor-reset-1017-chservohold-ee992115` |
| STAGED | Motor／servo channel '5' | UNCONFIRMED COMPONENT — Motor／servo channel '5' | `chFadeOut`、`chServoHold` | `pgu-storymode-motor-reset-852-chservohold-98cef8c2`<br>`pgu-storymode-motor-reset-1015-chfadeout-385cd2ef`<br>`pgu-storymode-motor-reset-1018-chservohold-b10b5c1a` |
| STAGED | Motor／servo channel 'i' | Chest + skirts still deployed. | `chServoHold` | `pgu-storymode-motor-reset-303-chservohold-fce84e19` |
| STAGED | Motor／servo channel 'i' | UNCONFIRMED COMPONENT — Motor／servo channel 'i' | `chServoHold`、`chServoStop` | `pgu-storymode-motor-reset-651-chservohold-d276d0c0`<br>`pgu-storymode-motor-reset-1020-chservostop-3fd6b346` |
| ON | PCA PWM0 CH0 | Slave 3 PWM0 CH0 (0x51) 頭眼，綠，2粒。 | `chGundamEyeWakeTwoStage` | `pgu-storymode-motor-reset-140-chgundameyewaketwostage-e7d43986` |
| ON | PCA PWM0 CH6 | Slave 3 PWM0 CH6 (0x51) 頭額頭，綠，1粒。 | `chGundamEyeWakeTwoStage` | `pgu-storymode-motor-reset-142-chgundameyewaketwostage-ef37e703` |
| STAGED | PCA PWM1 CH 0 | Chest + skirts still deployed. | `chOn` | `pgu-storymode-motor-reset-304-chon-7ead1ec5` |
| STAGED | PCA PWM1 CH 0 | UNCONFIRMED COMPONENT — PCA PWM1 CH 0 | `chOn` | `pgu-storymode-motor-reset-652-chon-279cb0d9`<br>`pgu-storymode-motor-reset-853-chon-2d6be631`<br>`pgu-storymode-motor-reset-1021-chon-2d638f36` |
| STAGED | PCA PWM1 CH 1 | UNCONFIRMED COMPONENT — PCA PWM1 CH 1 | `chOn` | `pgu-storymode-motor-reset-305-chon-c346cf29`<br>`pgu-storymode-motor-reset-653-chon-87de8224`<br>`pgu-storymode-motor-reset-854-chon-7696a05a`<br>`pgu-storymode-motor-reset-1022-chon-61137510` |
| STAGED | PCA PWM1 CH 2 | UNCONFIRMED COMPONENT — PCA PWM1 CH 2 | `chOn` | `pgu-storymode-motor-reset-306-chon-8bb1c965`<br>`pgu-storymode-motor-reset-654-chon-405e2148`<br>`pgu-storymode-motor-reset-855-chon-b95c51e6`<br>`pgu-storymode-motor-reset-1023-chon-bbc570ba` |
| STAGED | PCA PWM1 CH 7 | UNCONFIRMED COMPONENT — PCA PWM1 CH 7 | `chOn` | `pgu-storymode-motor-reset-307-chon-61a4502a`<br>`pgu-storymode-motor-reset-655-chon-a911336c`<br>`pgu-storymode-motor-reset-856-chon-5deb36c0`<br>`pgu-storymode-motor-reset-1024-chon-6137fec9` |
| STAGED | PCA PWM1 CH 8 | UNCONFIRMED COMPONENT — PCA PWM1 CH 8 | `chOn` | `pgu-storymode-motor-reset-308-chon-c7c997d6`<br>`pgu-storymode-motor-reset-656-chon-4644c03b`<br>`pgu-storymode-motor-reset-857-chon-64382339`<br>`pgu-storymode-motor-reset-1025-chon-65072eb5` |
| STAGED | RGB4 | All other slave-3 servos already at MIN; no corner accents. | `SpecificColorPattern` | `pgu-storymode-motor-reset-1009-specificcolorpattern-fd09df0a` |
| STAGED | RGB4 | Case-3 CLOSE_MID: Chest closes. Drop chest corners; keep front-skirt only. | `SpecificColorPattern` | `pgu-storymode-motor-reset-640-specificcolorpattern-c0d18594` |
| STAGED | RGB4 | Drop head corners; keep chest + front-skirt corners on. | `SpecificColorPattern` | `pgu-storymode-motor-reset-292-specificcolorpattern-f601ee55` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `SpecificColorPattern` | `pgu-storymode-motor-reset-837-specificcolorpattern-47971f60` |

## Slave 4

### storyMode_develop

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB1 | Hi-Nu Slave 4/6 左右手下段 RGB — shared PGU Slave 4 RGB source. | `rgbOff` | `pgu-storymode-develop-143-rgboff-f56448fd` |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `rgbOff` | `pgu-storymode-develop-144-rgboff-51a36b63` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `rgbOff` | `pgu-storymode-develop-145-rgboff-cfa75bc3` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `SpecificColorPattern` | `pgu-storymode-develop-147-specificcolorpattern-f790e36e` |

### storyMode_signals

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB4 | Hi-Nu Slave 4/6 左右手下段 RGB — shared PGU Slave 4 RGB source. | `SpecificColorPattern` | `pgu-storymode-signals-128-specificcolorpattern-3ec0d687` |

### storyMode_0_v1

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB1 | Hi-Nu Slave 4/6 左右手下段 RGB — shared PGU Slave 4 RGB source. | `randomFlashWithGap_multiple`、`randomLightUp` | `pgu-storymode-0-v1-387-randomflashwithgap-multiple-768dfea5`<br>`pgu-storymode-0-v1-2100-randomlightup-889249bf` |
| STAGED | RGB1 | UNCONFIRMED COMPONENT — RGB1 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v1-750-randomflashwithgap-multiple-0eabe8d6`<br>`pgu-storymode-0-v1-1211-randomlightup-99c60575`<br>`pgu-storymode-0-v1-1678-randomlightup-b71a7517`<br>`pgu-storymode-0-v1-2421-rgbon-1ef41320`<br>`pgu-storymode-0-v1-2998-rgbon-1f9476a1` |
| STAGED | RGB10 | UNCONFIRMED COMPONENT — RGB10 | `randomFlashWithGap_multiple` | `pgu-storymode-0-v1-436-randomflashwithgap-multiple-68485935` |
| STAGED | RGB11 | UNCONFIRMED COMPONENT — RGB11 | `randomFlashWithGap_multiple` | `pgu-storymode-0-v1-443-randomflashwithgap-multiple-18424735` |
| STAGED | RGB12 | UNCONFIRMED COMPONENT — RGB12 | `randomFlashWithGap_multiple` | `pgu-storymode-0-v1-450-randomflashwithgap-multiple-652634d7` |
| STAGED | RGB13 | UNCONFIRMED COMPONENT — RGB13 | `randomFlashWithGap_multiple` | `pgu-storymode-0-v1-457-randomflashwithgap-multiple-8612f089` |
| STAGED | RGB16 | UNCONFIRMED COMPONENT — RGB16 | `randomFlashWithGap_multiple` | `pgu-storymode-0-v1-464-randomflashwithgap-multiple-f088d166` |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v1-394-randomflashwithgap-multiple-8e2726a1`<br>`pgu-storymode-0-v1-757-randomflashwithgap-multiple-3e7fb057`<br>`pgu-storymode-0-v1-1218-randomlightup-64cbf239`<br>`pgu-storymode-0-v1-1685-randomlightup-142a09fb`<br>`pgu-storymode-0-v1-2107-randomlightup-eb26aa2f`<br>`pgu-storymode-0-v1-2423-rgbon-98949eac`<br>`pgu-storymode-0-v1-3000-rgbon-4c31fdfe` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v1-401-randomflashwithgap-multiple-934d0c6d`<br>`pgu-storymode-0-v1-764-randomflashwithgap-multiple-1026ee46`<br>`pgu-storymode-0-v1-1225-randomlightup-4526bc1b`<br>`pgu-storymode-0-v1-1692-randomlightup-ec9fb954`<br>`pgu-storymode-0-v1-2114-randomlightup-8eb48b00`<br>`pgu-storymode-0-v1-2425-rgbon-437d1682`<br>`pgu-storymode-0-v1-3002-rgbon-f4bbb893` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v1-408-randomflashwithgap-multiple-2895973d`<br>`pgu-storymode-0-v1-771-randomflashwithgap-multiple-a597ff25`<br>`pgu-storymode-0-v1-1203-randomlightup-27c688d5`<br>`pgu-storymode-0-v1-1233-randomlightup-c5bab036`<br>`pgu-storymode-0-v1-1700-randomlightup-dcb8ef61`<br>`pgu-storymode-0-v1-2121-randomlightup-eaeb2613`<br>`pgu-storymode-0-v1-2427-rgbon-3880858b`<br>`pgu-storymode-0-v1-3004-rgbon-dc441f25` |
| STAGED | RGB7 | Hi-Nu Slave 4/6 左右手下段 RGB — shared PGU Slave 4 RGB source. | `GN_Sword_Pulse_Color` | `pgu-storymode-0-v1-1657-gn-sword-pulse-color-0eaff14b` |
| STAGED | RGB7 | UNCONFIRMED COMPONENT — RGB7 | `GN_Sword_Pulse_Color`、`randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v1-415-randomflashwithgap-multiple-1c0b4897`<br>`pgu-storymode-0-v1-1249-randomlightup-47068cf5`<br>`pgu-storymode-0-v1-1669-randomlightup-be5e5a66`<br>`pgu-storymode-0-v1-2129-gn-sword-pulse-color-fccbdfd1`<br>`pgu-storymode-0-v1-2141-randomlightup-58f7413d`<br>`pgu-storymode-0-v1-2429-rgbon-d4f19fbf`<br>`pgu-storymode-0-v1-3006-rgbon-b2136f0b` |
| STAGED | RGB8 | UNCONFIRMED COMPONENT — RGB8 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v1-422-randomflashwithgap-multiple-1550ca22`<br>`pgu-storymode-0-v1-778-randomflashwithgap-multiple-8bdb7645`<br>`pgu-storymode-0-v1-1256-randomlightup-30916f03`<br>`pgu-storymode-0-v1-1716-randomlightup-c3f44783`<br>`pgu-storymode-0-v1-2149-randomlightup-d7231f70`<br>`pgu-storymode-0-v1-2431-rgbon-19c228d7`<br>`pgu-storymode-0-v1-3008-rgbon-43e61481` |
| STAGED | RGB9 | UNCONFIRMED COMPONENT — RGB9 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v1-429-randomflashwithgap-multiple-5c78e339`<br>`pgu-storymode-0-v1-785-randomflashwithgap-multiple-b8bd4913`<br>`pgu-storymode-0-v1-1241-randomlightup-bc8b941b`<br>`pgu-storymode-0-v1-1263-randomlightup-83bd5ede`<br>`pgu-storymode-0-v1-1708-randomlightup-87aa4c6e`<br>`pgu-storymode-0-v1-1723-randomlightup-00fa4674`<br>`pgu-storymode-0-v1-2156-randomlightup-ae18eb6b`<br>`pgu-storymode-0-v1-2433-rgbon-412a43d1`<br>`pgu-storymode-0-v1-3010-rgbon-72ccf345` |

### storyMode_awakening_3

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB2 | Hi-Nu Slave 4/6 左右手下段 RGB — shared PGU Slave 4 RGB source. | `rgbOff` | `pgu-storymode-awakening-3-268-rgboff-ed919fdc` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `rgbOff` | `pgu-storymode-awakening-3-270-rgboff-4a93eb65` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `rgbOff` | `pgu-storymode-awakening-3-273-rgboff-e1ea3971`<br>`pgu-storymode-awakening-3-278-rgboff-bf6c6b25` |
| STAGED | RGB7 | UNCONFIRMED COMPONENT — RGB7 | `rgbOff` | `pgu-storymode-awakening-3-275-rgboff-4828a086` |

### storyMode_activation

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `gradientVentPalette`、`randomFillAll_V2` | `pgu-storymode-activation-386-randomfillall-v2-5095a4f8`<br>`pgu-storymode-activation-389-gradientventpalette-57237bbb` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `VentEffect`、`turbine_v3` | `pgu-storymode-activation-405-venteffect-7937484d`<br>`pgu-storymode-activation-416-turbine-v3-be8f6f22` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `SpecificColorPattern` | `pgu-storymode-activation-429-specificcolorpattern-1e751b9a`<br>`pgu-storymode-activation-437-specificcolorpattern-1d7a7a38` |

### storyMode_0_v2

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB1 | Hi-Nu Slave 4/6 左右手下段 RGB — shared PGU Slave 4 RGB source. | `randomLightUp` | `pgu-storymode-0-v2-1669-randomlightup-e43fa9c5` |
| STAGED | RGB1 | UNCONFIRMED COMPONENT — RGB1 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v2-465-randomflashwithgap-multiple-4edb2dbd`<br>`pgu-storymode-0-v2-918-randomlightup-8991bc36`<br>`pgu-storymode-0-v2-1320-randomlightup-650477a0`<br>`pgu-storymode-0-v2-1925-rgbon-cff2a153`<br>`pgu-storymode-0-v2-2111-rgbon-33dff60c` |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v2-472-randomflashwithgap-multiple-2cc1f93c`<br>`pgu-storymode-0-v2-925-randomlightup-8aac7e1a`<br>`pgu-storymode-0-v2-1327-randomlightup-30976e04`<br>`pgu-storymode-0-v2-1676-randomlightup-8ddea020`<br>`pgu-storymode-0-v2-1927-rgbon-51fb21be`<br>`pgu-storymode-0-v2-2113-rgbon-cf84c791` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v2-479-randomflashwithgap-multiple-2597d1c6`<br>`pgu-storymode-0-v2-932-randomlightup-a21a139c`<br>`pgu-storymode-0-v2-1334-randomlightup-662762f5`<br>`pgu-storymode-0-v2-1683-randomlightup-5ab893b7`<br>`pgu-storymode-0-v2-1929-rgbon-7e27e0eb`<br>`pgu-storymode-0-v2-2115-rgbon-ff84568a` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v2-486-randomflashwithgap-multiple-a8082533`<br>`pgu-storymode-0-v2-940-randomlightup-5ffa9b97`<br>`pgu-storymode-0-v2-1341-randomlightup-4031e910`<br>`pgu-storymode-0-v2-1690-randomlightup-a59fdc60`<br>`pgu-storymode-0-v2-1931-rgbon-dee9bd2e`<br>`pgu-storymode-0-v2-2117-rgbon-53843fe1` |
| STAGED | RGB7 | Hi-Nu Slave 4/6 左右手下段 RGB — shared PGU Slave 4 RGB source. | `GN_Sword_Pulse_Color` | `pgu-storymode-0-v2-1299-gn-sword-pulse-color-1a3032c3` |
| STAGED | RGB7 | UNCONFIRMED COMPONENT — RGB7 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOff`、`rgbOn` | `pgu-storymode-0-v2-493-randomflashwithgap-multiple-e5bd649d`<br>`pgu-storymode-0-v2-517-rgboff-10cf1ce9`<br>`pgu-storymode-0-v2-956-randomlightup-5de25ab1`<br>`pgu-storymode-0-v2-1311-randomlightup-ba938e02`<br>`pgu-storymode-0-v2-1698-randomlightup-09d7f710`<br>`pgu-storymode-0-v2-1933-rgbon-989a8b97`<br>`pgu-storymode-0-v2-2119-rgbon-25fec7e3` |
| STAGED | RGB8 | UNCONFIRMED COMPONENT — RGB8 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v2-500-randomflashwithgap-multiple-b2f45527`<br>`pgu-storymode-0-v2-963-randomlightup-cda0983a`<br>`pgu-storymode-0-v2-1348-randomlightup-cca79417`<br>`pgu-storymode-0-v2-1706-randomlightup-c4cd792f`<br>`pgu-storymode-0-v2-1935-rgbon-5697c047`<br>`pgu-storymode-0-v2-2121-rgbon-bcc73a7c` |
| STAGED | RGB9 | UNCONFIRMED COMPONENT — RGB9 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v2-507-randomflashwithgap-multiple-e27942ad`<br>`pgu-storymode-0-v2-948-randomlightup-3d34cff5`<br>`pgu-storymode-0-v2-970-randomlightup-c6209fe0`<br>`pgu-storymode-0-v2-1355-randomlightup-c840adad`<br>`pgu-storymode-0-v2-1713-randomlightup-3e033e95`<br>`pgu-storymode-0-v2-1937-rgbon-bc36bde5`<br>`pgu-storymode-0-v2-2123-rgbon-e584a101` |
| STAGED | Runtime／group target 'strips' | UNCONFIRMED COMPONENT — Runtime／group target 'strips' | `randomFlashFixedCount_multiple` | `pgu-storymode-0-v2-234-randomflashfixedcount-multiple-08a643a2` |

### storyMode_storing_energy

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB1 | Hi-Nu Slave 4/6 左右手下段 RGB — shared PGU Slave 4 RGB source. | `paletteWave_80Percent_SpecialWave` | `pgu-storymode-storing-energy-690-palettewave-80percent-specialwave-190ea77c` |
| STAGED | RGB2 | Hi-Nu Slave 4/6 左右手下段 RGB — shared PGU Slave 4 RGB source. | `rgbOff` | `pgu-storymode-storing-energy-393-rgboff-8f5ea9b1` |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `gradientVentPalette`、`rgbOff` | `pgu-storymode-storing-energy-700-gradientventpalette-d5726643`<br>`pgu-storymode-storing-energy-719-rgboff-10fb6879` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `rgbOff` | `pgu-storymode-storing-energy-394-rgboff-2527d93a`<br>`pgu-storymode-storing-energy-722-rgboff-23830595` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `SpecificColorPattern`、`rgbOff` | `pgu-storymode-storing-energy-395-rgboff-53bc58a5`<br>`pgu-storymode-storing-energy-724-specificcolorpattern-bd9dc0cb` |

### storyMode_2

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB2 | Hi-Nu Slave 4/6 左右手下段 RGB — shared PGU Slave 4 RGB source. | `gradientVentPalette` | `pgu-storymode-2-362-gradientventpalette-fd4dfb18` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `turbine_v3` | `pgu-storymode-2-382-turbine-v3-17dc6070` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `SpecificColorPattern` | `pgu-storymode-2-395-specificcolorpattern-8d5adf14` |

### storyMode_plasma

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB4 | Hi-Nu Slave 4/6 左右手下段 RGB — shared PGU Slave 4 RGB source. | `SpecificColorPattern` | `pgu-storymode-plasma-623-specificcolorpattern-df7513e3` |

### storyMode_trans_am

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB1 | Hi-Nu Slave 4/6 左右手下段 RGB — shared PGU Slave 4 RGB source. | `GN_Drive_Running` | `pgu-storymode-trans-am-217-gn-drive-running-701d4305` |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `gradientVentPalette` | `pgu-storymode-trans-am-228-gradientventpalette-9aa763d1` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `turbine_v3` | `pgu-storymode-trans-am-248-turbine-v3-b42f0952` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `SpecificColorPattern` | `pgu-storymode-trans-am-261-specificcolorpattern-074cd999` |

### storyMode_3

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `gradientVentPalette` | `pgu-storymode-3-397-gradientventpalette-91d7c442` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `turbine_v3` | `pgu-storymode-3-417-turbine-v3-7181826d` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `SpecificColorPattern` | `pgu-storymode-3-431-specificcolorpattern-f23dd8e7`<br>`pgu-storymode-3-439-specificcolorpattern-0b3dce03` |

### storyMode_idle

OFF／no direct call in this Slave context。

### storyMode_motor

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | Motor／servo channel '2' | UNCONFIRMED COMPONENT — Motor／servo channel '2' | `chFadeIn`、`chServoHold` | `pgu-storymode-motor-1097-chfadein-86e8ee9f`<br>`pgu-storymode-motor-1107-chservohold-0c935bde`<br>`pgu-storymode-motor-1572-chservohold-ab41cbb9`<br>`pgu-storymode-motor-2144-chservohold-01b51e0b` |
| STAGED | Motor／servo channel '3' | UNCONFIRMED COMPONENT — Motor／servo channel '3' | `chFadeIn`、`chServoHold` | `pgu-storymode-motor-1098-chfadein-f3af2bbc`<br>`pgu-storymode-motor-1108-chservohold-d4a2955e`<br>`pgu-storymode-motor-1573-chservohold-6afff00f`<br>`pgu-storymode-motor-2145-chservohold-186f98b7` |
| STAGED | Motor／servo channel '4' | UNCONFIRMED COMPONENT — Motor／servo channel '4' | `chFadeIn`、`chServoHold` | `pgu-storymode-motor-1099-chfadein-451c4be6`<br>`pgu-storymode-motor-1109-chservohold-1e08a306`<br>`pgu-storymode-motor-1574-chservohold-7834ca9b`<br>`pgu-storymode-motor-2146-chservohold-c5ed7668` |
| STAGED | Motor／servo channel '5' | UNCONFIRMED COMPONENT — Motor／servo channel '5' | `chFadeIn`、`chServoHold` | `pgu-storymode-motor-1100-chfadein-8c9f4368`<br>`pgu-storymode-motor-1110-chservohold-fd146c3b`<br>`pgu-storymode-motor-1575-chservohold-703f109b`<br>`pgu-storymode-motor-2147-chservohold-4bfff701` |
| STAGED | PCA PWM0 CH 0 | Slave 4/5 PWM0 — body white/signal channels. | `chOn` | `pgu-storymode-motor-1167-chon-fb512a2e` |
| STAGED | PCA PWM0 CH 1 | UNCONFIRMED COMPONENT — PCA PWM0 CH 1 | `chOn` | `pgu-storymode-motor-1168-chon-8db321ae` |
| STAGED | PCA PWM0 CH 12 | UNCONFIRMED COMPONENT — PCA PWM0 CH 12 | `chOff` | `pgu-storymode-motor-1118-choff-f19be9b7`<br>`pgu-storymode-motor-1172-choff-5332f967`<br>`pgu-storymode-motor-1563-choff-42632d7d`<br>`pgu-storymode-motor-2135-choff-813850cf` |
| STAGED | PCA PWM0 CH 13 | UNCONFIRMED COMPONENT — PCA PWM0 CH 13 | `chOff` | `pgu-storymode-motor-1119-choff-e562d3e1`<br>`pgu-storymode-motor-1173-choff-f7a330b0`<br>`pgu-storymode-motor-1564-choff-6453a87b`<br>`pgu-storymode-motor-2136-choff-644eab39` |
| STAGED | PCA PWM0 CH 14 | UNCONFIRMED COMPONENT — PCA PWM0 CH 14 | `chOn`、`chValcanGun` | `pgu-storymode-motor-1120-chvalcangun-1e8ad476`<br>`pgu-storymode-motor-1174-chon-e673f3d1`<br>`pgu-storymode-motor-1565-chvalcangun-c215153a`<br>`pgu-storymode-motor-2137-chvalcangun-feb8743e` |
| STAGED | PCA PWM0 CH 15 | UNCONFIRMED COMPONENT — PCA PWM0 CH 15 | `chFlashAlternativeV2`、`chOn` | `pgu-storymode-motor-1122-chflashalternativev2-9e24a604`<br>`pgu-storymode-motor-1175-chon-cd8fa451`<br>`pgu-storymode-motor-1567-chflashalternativev2-5b057038`<br>`pgu-storymode-motor-2139-chflashalternativev2-460bf09b` |
| STAGED | PCA PWM0 CH i (loop 12..15 inclusive) | Slave 4 PWM0 CH12-15 (0x5A) 左前臂（僅左手），白，1粒；左前臂（僅左手），暖白，6粒；未接燈。 | `chOn` | `pgu-storymode-motor-689-chon-b935d1df` |
| STAGED | PCA PWM0 CH i (loop 2..7 inclusive) | UNCONFIRMED COMPONENT — PCA PWM0 CH i (loop 2..7 inclusive) | `chOff` | `pgu-storymode-motor-1113-choff-dab5c774`<br>`pgu-storymode-motor-1558-choff-d2b73e48`<br>`pgu-storymode-motor-2130-choff-d2639c35` |
| STAGED | PCA PWM0 CH i (loop 4..8 inclusive) | UNCONFIRMED COMPONENT — PCA PWM0 CH i (loop 4..8 inclusive) | `chOn` | `pgu-storymode-motor-1170-chon-9ecaf31f` |
| STAGED | PCA PWM0 CH i (loop 9..11 inclusive) | UNCONFIRMED COMPONENT — PCA PWM0 CH i (loop 9..11 inclusive) | `chOn` | `pgu-storymode-motor-1116-chon-c9e99b9f`<br>`pgu-storymode-motor-1561-chon-d220040c`<br>`pgu-storymode-motor-2133-chon-732a85d9` |
| STAGED | RGB1 | Slave 4/5 RGB1 — GN drive running. | `GN_Drive_Running` | `pgu-storymode-motor-1125-gn-drive-running-a230bb47` |
| STAGED | RGB2 | Slave 4/5 RGB2/RGB3 — vent effects. | `VentEffect` | `pgu-storymode-motor-1136-venteffect-c84d5932` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `VentEffect` | `pgu-storymode-motor-1146-venteffect-6dff14b0` |
| STAGED | RGB4 | 3s: all signals green — Slave 4/5 RGB4 signal LEDs. | `SpecificColorPattern` | `pgu-storymode-motor-681-specificcolorpattern-0cbedd8a` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `SpecificColorPattern` | `pgu-storymode-motor-1085-specificcolorpattern-ee1bcb8b`<br>`pgu-storymode-motor-1091-specificcolorpattern-26b19497`<br>`pgu-storymode-motor-1553-specificcolorpattern-1166034f`<br>`pgu-storymode-motor-2125-specificcolorpattern-f564dadd` |
| STAGED | RGB8 | UNCONFIRMED COMPONENT — RGB8 | `footplatev2` | `pgu-storymode-motor-1156-footplatev2-e273b4fc` |

### storyMode_motor_reset

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | Motor／servo channel '2' | UNCONFIRMED COMPONENT — Motor／servo channel '2' | `chFadeOut`、`chServoHold` | `pgu-storymode-motor-reset-330-chservohold-20f6dcd7`<br>`pgu-storymode-motor-reset-675-chfadeout-b75315ff`<br>`pgu-storymode-motor-reset-684-chservohold-7ceab492`<br>`pgu-storymode-motor-reset-868-chservohold-d45e8ee2`<br>`pgu-storymode-motor-reset-1036-chservohold-fda9c74c` |
| STAGED | Motor／servo channel '3' | UNCONFIRMED COMPONENT — Motor／servo channel '3' | `chFadeOut`、`chServoHold` | `pgu-storymode-motor-reset-331-chservohold-4fd95440`<br>`pgu-storymode-motor-reset-676-chfadeout-c67056e6`<br>`pgu-storymode-motor-reset-685-chservohold-637666bd`<br>`pgu-storymode-motor-reset-869-chservohold-ccc9f8e2`<br>`pgu-storymode-motor-reset-1037-chservohold-e3a8d640` |
| STAGED | Motor／servo channel '4' | UNCONFIRMED COMPONENT — Motor／servo channel '4' | `chFadeOut`、`chServoHold` | `pgu-storymode-motor-reset-332-chservohold-8f6d244c`<br>`pgu-storymode-motor-reset-677-chfadeout-3bd9bcef`<br>`pgu-storymode-motor-reset-686-chservohold-d6f2148d`<br>`pgu-storymode-motor-reset-870-chservohold-5dc22a01`<br>`pgu-storymode-motor-reset-1038-chservohold-f963b3c0` |
| STAGED | Motor／servo channel '5' | UNCONFIRMED COMPONENT — Motor／servo channel '5' | `chFadeOut`、`chServoHold` | `pgu-storymode-motor-reset-333-chservohold-ecd50c8d`<br>`pgu-storymode-motor-reset-678-chfadeout-3b304897`<br>`pgu-storymode-motor-reset-687-chservohold-335571ab`<br>`pgu-storymode-motor-reset-871-chservohold-1d74e73d`<br>`pgu-storymode-motor-reset-1039-chservohold-6a2555ec` |
| STAGED | PCA PWM0 CH 12 | UNCONFIRMED COMPONENT — PCA PWM0 CH 12 | `chOff` | `pgu-storymode-motor-reset-321-choff-ed944535`<br>`pgu-storymode-motor-reset-669-choff-90e8f8ed` |
| STAGED | PCA PWM0 CH 13 | UNCONFIRMED COMPONENT — PCA PWM0 CH 13 | `chOff` | `pgu-storymode-motor-reset-322-choff-c1466eb1`<br>`pgu-storymode-motor-reset-670-choff-4dfd5267` |
| STAGED | PCA PWM0 CH 14 | UNCONFIRMED COMPONENT — PCA PWM0 CH 14 | `chValcanGun` | `pgu-storymode-motor-reset-323-chvalcangun-7b31ff11`<br>`pgu-storymode-motor-reset-671-chvalcangun-3175f7ce` |
| STAGED | PCA PWM0 CH 15 | UNCONFIRMED COMPONENT — PCA PWM0 CH 15 | `chFlashAlternativeV2` | `pgu-storymode-motor-reset-325-chflashalternativev2-41ee57f2`<br>`pgu-storymode-motor-reset-673-chflashalternativev2-6c24d057` |
| STAGED | PCA PWM0 CH i (loop 2..7 inclusive) | UNCONFIRMED COMPONENT — PCA PWM0 CH i (loop 2..7 inclusive) | `chOff` | `pgu-storymode-motor-reset-316-choff-96334b3f`<br>`pgu-storymode-motor-reset-664-choff-75dc84a0` |
| STAGED | PCA PWM0 CH i (loop 9..11 inclusive) | UNCONFIRMED COMPONENT — PCA PWM0 CH i (loop 9..11 inclusive) | `chOn` | `pgu-storymode-motor-reset-319-chon-964cf4c2`<br>`pgu-storymode-motor-reset-667-chon-d9885628` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `SpecificColorPattern` | `pgu-storymode-motor-reset-311-specificcolorpattern-93c33af7`<br>`pgu-storymode-motor-reset-659-specificcolorpattern-efd55945`<br>`pgu-storymode-motor-reset-860-specificcolorpattern-4005177d`<br>`pgu-storymode-motor-reset-1028-specificcolorpattern-0a59e8e9` |

## Slave 5

### storyMode_develop

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB1 | Hi-Nu Slave 3/5 左右手上段 RGB — shared PGU Slave 4 RGB source. | `rgbOff` | `pgu-storymode-develop-122-rgboff-bfeb2c5b` |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `rgbOff` | `pgu-storymode-develop-123-rgboff-d4a0077e` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `rgbOff` | `pgu-storymode-develop-124-rgboff-c656e65f` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `SpecificColorPattern` | `pgu-storymode-develop-126-specificcolorpattern-a89be655` |

### storyMode_signals

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB4 | Hi-Nu Slave 3/5 左右手上段 RGB — shared PGU Slave 4 RGB source. | `SpecificColorPattern` | `pgu-storymode-signals-112-specificcolorpattern-6a08c2d1` |

### storyMode_0_v1

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB1 | Hi-Nu Slave 3/5 左右手上段 RGB — shared PGU Slave 4 RGB source. | `randomFlashWithGap_multiple`、`randomLightUp` | `pgu-storymode-0-v1-298-randomflashwithgap-multiple-6bce3ee0`<br>`pgu-storymode-0-v1-2032-randomlightup-951392c3` |
| STAGED | RGB1 | UNCONFIRMED COMPONENT — RGB1 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v1-699-randomflashwithgap-multiple-e2222f52`<br>`pgu-storymode-0-v1-1135-randomlightup-ec3770c2`<br>`pgu-storymode-0-v1-1598-randomlightup-6bb5d2c2`<br>`pgu-storymode-0-v1-2398-rgbon-45029b8a`<br>`pgu-storymode-0-v1-2975-rgbon-cdc34964` |
| STAGED | RGB10 | UNCONFIRMED COMPONENT — RGB10 | `randomFlashWithGap_multiple` | `pgu-storymode-0-v1-347-randomflashwithgap-multiple-8391b8e7` |
| STAGED | RGB11 | UNCONFIRMED COMPONENT — RGB11 | `randomFlashWithGap_multiple` | `pgu-storymode-0-v1-354-randomflashwithgap-multiple-0ccfbede` |
| STAGED | RGB12 | UNCONFIRMED COMPONENT — RGB12 | `randomFlashWithGap_multiple` | `pgu-storymode-0-v1-361-randomflashwithgap-multiple-faec005e` |
| STAGED | RGB13 | UNCONFIRMED COMPONENT — RGB13 | `randomFlashWithGap_multiple` | `pgu-storymode-0-v1-368-randomflashwithgap-multiple-daeb1bb7` |
| STAGED | RGB16 | UNCONFIRMED COMPONENT — RGB16 | `randomFlashWithGap_multiple` | `pgu-storymode-0-v1-375-randomflashwithgap-multiple-a9d2e2e4` |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v1-305-randomflashwithgap-multiple-456d3505`<br>`pgu-storymode-0-v1-706-randomflashwithgap-multiple-a9e35944`<br>`pgu-storymode-0-v1-1142-randomlightup-afd92ea9`<br>`pgu-storymode-0-v1-1605-randomlightup-ff05026c`<br>`pgu-storymode-0-v1-2039-randomlightup-2a9f2647`<br>`pgu-storymode-0-v1-2400-rgbon-c5d527bf`<br>`pgu-storymode-0-v1-2977-rgbon-6759bd9e` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v1-312-randomflashwithgap-multiple-43c556d1`<br>`pgu-storymode-0-v1-713-randomflashwithgap-multiple-f9e90c47`<br>`pgu-storymode-0-v1-1149-randomlightup-eb22ee16`<br>`pgu-storymode-0-v1-1612-randomlightup-1c80d27c`<br>`pgu-storymode-0-v1-2046-randomlightup-3ced3297`<br>`pgu-storymode-0-v1-2402-rgbon-94f82500`<br>`pgu-storymode-0-v1-2979-rgbon-c22eea66` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v1-319-randomflashwithgap-multiple-4b5e601b`<br>`pgu-storymode-0-v1-720-randomflashwithgap-multiple-e75038a1`<br>`pgu-storymode-0-v1-1127-randomlightup-19cabc52`<br>`pgu-storymode-0-v1-1157-randomlightup-9f2c8e70`<br>`pgu-storymode-0-v1-1620-randomlightup-827e1894`<br>`pgu-storymode-0-v1-2053-randomlightup-c8dd8f5c`<br>`pgu-storymode-0-v1-2404-rgbon-18c00769`<br>`pgu-storymode-0-v1-2981-rgbon-4361b8c7` |
| STAGED | RGB7 | Hi-Nu Slave 3/5 左右手上段 RGB — shared PGU Slave 4 RGB source. | `GN_Sword_Pulse_Color` | `pgu-storymode-0-v1-1577-gn-sword-pulse-color-c4622d74` |
| STAGED | RGB7 | UNCONFIRMED COMPONENT — RGB7 | `GN_Sword_Pulse_Color`、`randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v1-326-randomflashwithgap-multiple-96f81d17`<br>`pgu-storymode-0-v1-1173-randomlightup-54894fa5`<br>`pgu-storymode-0-v1-1589-randomlightup-027bf6ef`<br>`pgu-storymode-0-v1-2061-gn-sword-pulse-color-c66ff0a1`<br>`pgu-storymode-0-v1-2073-randomlightup-bf6a107d`<br>`pgu-storymode-0-v1-2406-rgbon-e340c77b`<br>`pgu-storymode-0-v1-2983-rgbon-44d0d621` |
| STAGED | RGB8 | UNCONFIRMED COMPONENT — RGB8 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v1-333-randomflashwithgap-multiple-6d79cb2b`<br>`pgu-storymode-0-v1-727-randomflashwithgap-multiple-4caf6259`<br>`pgu-storymode-0-v1-1180-randomlightup-290eb087`<br>`pgu-storymode-0-v1-1636-randomlightup-5642c1b2`<br>`pgu-storymode-0-v1-2081-randomlightup-dfc3ced8`<br>`pgu-storymode-0-v1-2408-rgbon-583d7b24`<br>`pgu-storymode-0-v1-2985-rgbon-664a8c41` |
| STAGED | RGB9 | UNCONFIRMED COMPONENT — RGB9 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v1-340-randomflashwithgap-multiple-5dedbe22`<br>`pgu-storymode-0-v1-734-randomflashwithgap-multiple-6782aae4`<br>`pgu-storymode-0-v1-1165-randomlightup-284a6b45`<br>`pgu-storymode-0-v1-1187-randomlightup-59cfd1ee`<br>`pgu-storymode-0-v1-1628-randomlightup-b1c4bc23`<br>`pgu-storymode-0-v1-1643-randomlightup-95e8e19e`<br>`pgu-storymode-0-v1-2088-randomlightup-b799184d`<br>`pgu-storymode-0-v1-2410-rgbon-28cd0d95`<br>`pgu-storymode-0-v1-2987-rgbon-08c15269` |

### storyMode_awakening_3

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB2 | Hi-Nu Slave 3/5 左右手上段 RGB — shared PGU Slave 4 RGB source. | `rgbOff` | `pgu-storymode-awakening-3-247-rgboff-959952a3` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `rgbOff` | `pgu-storymode-awakening-3-249-rgboff-34694bef` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `rgbOff` | `pgu-storymode-awakening-3-252-rgboff-83cf3eca`<br>`pgu-storymode-awakening-3-257-rgboff-3fa9d9e3` |
| STAGED | RGB7 | UNCONFIRMED COMPONENT — RGB7 | `rgbOff` | `pgu-storymode-awakening-3-254-rgboff-e39c7992` |

### storyMode_activation

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `gradientVentPalette`、`randomFillAll_V2` | `pgu-storymode-activation-317-randomfillall-v2-bc624f37`<br>`pgu-storymode-activation-320-gradientventpalette-426cac24` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `VentEffect`、`turbine_v3` | `pgu-storymode-activation-336-venteffect-7ab7982c`<br>`pgu-storymode-activation-347-turbine-v3-ebef0019` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `SpecificColorPattern` | `pgu-storymode-activation-360-specificcolorpattern-d0b36ae1`<br>`pgu-storymode-activation-368-specificcolorpattern-41cf367f` |

### storyMode_0_v2

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB1 | Hi-Nu Slave 3/5 左右手上段 RGB — shared PGU Slave 4 RGB source. | `randomLightUp` | `pgu-storymode-0-v2-1613-randomlightup-24a00213` |
| STAGED | RGB1 | UNCONFIRMED COMPONENT — RGB1 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v2-401-randomflashwithgap-multiple-3add7303`<br>`pgu-storymode-0-v2-850-randomlightup-e593927b`<br>`pgu-storymode-0-v2-1250-randomlightup-e4dc1bc2`<br>`pgu-storymode-0-v2-1902-rgbon-1fd3daf0`<br>`pgu-storymode-0-v2-2088-rgbon-cdb9d0bf` |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v2-408-randomflashwithgap-multiple-05e649e1`<br>`pgu-storymode-0-v2-857-randomlightup-99506465`<br>`pgu-storymode-0-v2-1257-randomlightup-81775a00`<br>`pgu-storymode-0-v2-1620-randomlightup-aad872aa`<br>`pgu-storymode-0-v2-1904-rgbon-65c9c5ef`<br>`pgu-storymode-0-v2-2090-rgbon-7c6c0a03` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v2-415-randomflashwithgap-multiple-29addb43`<br>`pgu-storymode-0-v2-864-randomlightup-aeb56491`<br>`pgu-storymode-0-v2-1264-randomlightup-5e4a3ef4`<br>`pgu-storymode-0-v2-1627-randomlightup-2558bc4e`<br>`pgu-storymode-0-v2-1906-rgbon-c4e62a56`<br>`pgu-storymode-0-v2-2092-rgbon-b3eeb579` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v2-422-randomflashwithgap-multiple-d0b50e67`<br>`pgu-storymode-0-v2-872-randomlightup-5e9847fb`<br>`pgu-storymode-0-v2-1271-randomlightup-6dd55b35`<br>`pgu-storymode-0-v2-1634-randomlightup-875f0c05`<br>`pgu-storymode-0-v2-1908-rgbon-838cfe47`<br>`pgu-storymode-0-v2-2094-rgbon-f676eeb7` |
| STAGED | RGB7 | Hi-Nu Slave 3/5 左右手上段 RGB — shared PGU Slave 4 RGB source. | `GN_Sword_Pulse_Color` | `pgu-storymode-0-v2-1229-gn-sword-pulse-color-55ecf825` |
| STAGED | RGB7 | UNCONFIRMED COMPONENT — RGB7 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOff`、`rgbOn` | `pgu-storymode-0-v2-429-randomflashwithgap-multiple-3e5a41f0`<br>`pgu-storymode-0-v2-453-rgboff-408e0ebf`<br>`pgu-storymode-0-v2-888-randomlightup-e511e28b`<br>`pgu-storymode-0-v2-1241-randomlightup-7d3cf370`<br>`pgu-storymode-0-v2-1642-randomlightup-20708adf`<br>`pgu-storymode-0-v2-1910-rgbon-a2518330`<br>`pgu-storymode-0-v2-2096-rgbon-5634ec78` |
| STAGED | RGB8 | UNCONFIRMED COMPONENT — RGB8 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v2-436-randomflashwithgap-multiple-44681506`<br>`pgu-storymode-0-v2-895-randomlightup-eb0d4b45`<br>`pgu-storymode-0-v2-1278-randomlightup-4ae1f2b4`<br>`pgu-storymode-0-v2-1650-randomlightup-a4dabd5b`<br>`pgu-storymode-0-v2-1912-rgbon-4a4fe977`<br>`pgu-storymode-0-v2-2098-rgbon-271388a9` |
| STAGED | RGB9 | UNCONFIRMED COMPONENT — RGB9 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v2-443-randomflashwithgap-multiple-e3f48e5a`<br>`pgu-storymode-0-v2-880-randomlightup-512c7a46`<br>`pgu-storymode-0-v2-902-randomlightup-f2d0d200`<br>`pgu-storymode-0-v2-1285-randomlightup-f81ba1ad`<br>`pgu-storymode-0-v2-1657-randomlightup-a6656afd`<br>`pgu-storymode-0-v2-1914-rgbon-6a5254ec`<br>`pgu-storymode-0-v2-2100-rgbon-e60afc2f` |
| STAGED | Runtime／group target 'strips' | UNCONFIRMED COMPONENT — Runtime／group target 'strips' | `randomFlashFixedCount_multiple` | `pgu-storymode-0-v2-209-randomflashfixedcount-multiple-bef3d0cb` |

### storyMode_storing_energy

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB1 | Hi-Nu Slave 3/5 左右手上段 RGB — shared PGU Slave 4 RGB source. | `paletteWave_80Percent_SpecialWave` | `pgu-storymode-storing-energy-644-palettewave-80percent-specialwave-112b3e49` |
| STAGED | RGB2 | Hi-Nu Slave 3/5 左右手上段 RGB — shared PGU Slave 4 RGB source. | `rgbOff` | `pgu-storymode-storing-energy-380-rgboff-ad631d82` |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `gradientVentPalette`、`rgbOff` | `pgu-storymode-storing-energy-654-gradientventpalette-9268881e`<br>`pgu-storymode-storing-energy-673-rgboff-c56cf59c` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `rgbOff` | `pgu-storymode-storing-energy-381-rgboff-da8d0948`<br>`pgu-storymode-storing-energy-676-rgboff-71bbebae` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `SpecificColorPattern`、`rgbOff` | `pgu-storymode-storing-energy-382-rgboff-4cd42119`<br>`pgu-storymode-storing-energy-678-specificcolorpattern-7a44aeb9` |

### storyMode_2

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB2 | Hi-Nu Slave 3/5 左右手上段 RGB — shared PGU Slave 4 RGB source. | `gradientVentPalette` | `pgu-storymode-2-318-gradientventpalette-42187153` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `turbine_v3` | `pgu-storymode-2-338-turbine-v3-b94ec230` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `SpecificColorPattern` | `pgu-storymode-2-351-specificcolorpattern-c8af8eff` |

### storyMode_plasma

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB4 | Hi-Nu Slave 3/5 左右手上段 RGB — shared PGU Slave 4 RGB source. | `SpecificColorPattern` | `pgu-storymode-plasma-613-specificcolorpattern-a355adc9` |

### storyMode_trans_am

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB1 | Hi-Nu Slave 3/5 左右手上段 RGB — shared PGU Slave 4 RGB source. | `GN_Drive_Running` | `pgu-storymode-trans-am-163-gn-drive-running-cfe38193` |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `gradientVentPalette` | `pgu-storymode-trans-am-174-gradientventpalette-8f1e46bb` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `turbine_v3` | `pgu-storymode-trans-am-194-turbine-v3-032f68d4` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `SpecificColorPattern` | `pgu-storymode-trans-am-207-specificcolorpattern-4b92c72e` |

### storyMode_3

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `gradientVentPalette` | `pgu-storymode-3-336-gradientventpalette-ac663d1d` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `turbine_v3` | `pgu-storymode-3-356-turbine-v3-49f36c91` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `SpecificColorPattern` | `pgu-storymode-3-370-specificcolorpattern-9a587c61`<br>`pgu-storymode-3-378-specificcolorpattern-244c844b` |

### storyMode_idle

OFF／no direct call in this Slave context。

### storyMode_motor

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | Motor／servo channel '2' | UNCONFIRMED COMPONENT — Motor／servo channel '2' | `chFadeIn`、`chServoHold` | `pgu-storymode-motor-1192-chfadein-b742ebf3`<br>`pgu-storymode-motor-1202-chservohold-448e6f62`<br>`pgu-storymode-motor-1597-chservohold-f0e5a3df`<br>`pgu-storymode-motor-2169-chservohold-3975334a` |
| STAGED | Motor／servo channel '3' | UNCONFIRMED COMPONENT — Motor／servo channel '3' | `chFadeIn`、`chServoHold` | `pgu-storymode-motor-1193-chfadein-c18df73b`<br>`pgu-storymode-motor-1203-chservohold-e18388ad`<br>`pgu-storymode-motor-1598-chservohold-133be456`<br>`pgu-storymode-motor-2170-chservohold-7e1345b8` |
| STAGED | Motor／servo channel '4' | UNCONFIRMED COMPONENT — Motor／servo channel '4' | `chFadeIn`、`chServoHold` | `pgu-storymode-motor-1194-chfadein-62a33c93`<br>`pgu-storymode-motor-1204-chservohold-438e4029`<br>`pgu-storymode-motor-1599-chservohold-53323927`<br>`pgu-storymode-motor-2171-chservohold-31cc3098` |
| STAGED | Motor／servo channel '5' | UNCONFIRMED COMPONENT — Motor／servo channel '5' | `chFadeIn`、`chServoHold` | `pgu-storymode-motor-1195-chfadein-54735e59`<br>`pgu-storymode-motor-1205-chservohold-dbc39564`<br>`pgu-storymode-motor-1600-chservohold-f3dce59f`<br>`pgu-storymode-motor-2172-chservohold-f62f183d` |
| STAGED | PCA PWM0 CH 0 | Slave 4/5 PWM0 — body white/signal channels. | `chOn` | `pgu-storymode-motor-1273-chon-4e60a678` |
| STAGED | PCA PWM0 CH 1 | UNCONFIRMED COMPONENT — PCA PWM0 CH 1 | `chOn` | `pgu-storymode-motor-1274-chon-7a1e0847` |
| STAGED | PCA PWM0 CH 12 | UNCONFIRMED COMPONENT — PCA PWM0 CH 12 | `chOff` | `pgu-storymode-motor-1213-choff-ae3221b7`<br>`pgu-storymode-motor-1278-choff-8dcf6bfe`<br>`pgu-storymode-motor-1588-choff-1f76ceec`<br>`pgu-storymode-motor-2160-choff-b00e49c5` |
| STAGED | PCA PWM0 CH 13 | UNCONFIRMED COMPONENT — PCA PWM0 CH 13 | `chOff` | `pgu-storymode-motor-1214-choff-8476e3ae`<br>`pgu-storymode-motor-1279-choff-607797a2`<br>`pgu-storymode-motor-1589-choff-ef59d716`<br>`pgu-storymode-motor-2161-choff-fa9726de` |
| STAGED | PCA PWM0 CH 14 | UNCONFIRMED COMPONENT — PCA PWM0 CH 14 | `chOn`、`chValcanGun` | `pgu-storymode-motor-1215-chvalcangun-e5737ebc`<br>`pgu-storymode-motor-1280-chon-01b5c9e9`<br>`pgu-storymode-motor-1590-chvalcangun-e6e86a8c`<br>`pgu-storymode-motor-2162-chvalcangun-df8e9cf0` |
| STAGED | PCA PWM0 CH 15 | UNCONFIRMED COMPONENT — PCA PWM0 CH 15 | `chFlashAlternativeV2`、`chOn` | `pgu-storymode-motor-1217-chflashalternativev2-00690840`<br>`pgu-storymode-motor-1281-chon-7bf2500c`<br>`pgu-storymode-motor-1592-chflashalternativev2-140889c6`<br>`pgu-storymode-motor-2164-chflashalternativev2-d66f71f4` |
| STAGED | PCA PWM0 CH i (loop 12..15 inclusive) | Slave 4 PWM0 CH12-15 (0x5A) 左前臂（僅左手），白，1粒；左前臂（僅左手），暖白，6粒；未接燈。 | `chOn` | `pgu-storymode-motor-689-chon-b935d1df` |
| STAGED | PCA PWM0 CH i (loop 2..7 inclusive) | UNCONFIRMED COMPONENT — PCA PWM0 CH i (loop 2..7 inclusive) | `chOff` | `pgu-storymode-motor-1208-choff-491cfa15`<br>`pgu-storymode-motor-1583-choff-2dd4039f`<br>`pgu-storymode-motor-2155-choff-5ccdabe7` |
| STAGED | PCA PWM0 CH i (loop 4..8 inclusive) | UNCONFIRMED COMPONENT — PCA PWM0 CH i (loop 4..8 inclusive) | `chOn` | `pgu-storymode-motor-1276-chon-b60c81c6` |
| STAGED | PCA PWM0 CH i (loop 9..11 inclusive) | UNCONFIRMED COMPONENT — PCA PWM0 CH i (loop 9..11 inclusive) | `chOn` | `pgu-storymode-motor-1211-chon-9bc8a30f`<br>`pgu-storymode-motor-1586-chon-f6009386`<br>`pgu-storymode-motor-2158-chon-835a3f9f` |
| STAGED | RGB1 | Slave 4/5 RGB1 — GN drive running. | `GN_Drive_Running` | `pgu-storymode-motor-1220-gn-drive-running-7f35fa13` |
| STAGED | RGB2 | Slave 4/5 RGB2/RGB3 — vent effects. | `VentEffect` | `pgu-storymode-motor-1231-venteffect-e0d6b869` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `VentEffect` | `pgu-storymode-motor-1241-venteffect-c373f39e` |
| STAGED | RGB4 | 3s: all signals green — Slave 4/5 RGB4 signal LEDs. | `SpecificColorPattern` | `pgu-storymode-motor-681-specificcolorpattern-0cbedd8a` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `SpecificColorPattern` | `pgu-storymode-motor-1180-specificcolorpattern-311f072b`<br>`pgu-storymode-motor-1186-specificcolorpattern-95fda9de`<br>`pgu-storymode-motor-1578-specificcolorpattern-86b623fb`<br>`pgu-storymode-motor-2150-specificcolorpattern-fd0f521c` |
| STAGED | RGB7 | Slave 4/5 RGB7/RGB8 — footplate effect. | `footplatev2` | `pgu-storymode-motor-1252-footplatev2-60148fa4` |
| STAGED | RGB8 | UNCONFIRMED COMPONENT — RGB8 | `footplatev2` | `pgu-storymode-motor-1262-footplatev2-b065ad87` |

### storyMode_motor_reset

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | Motor／servo channel '2' | UNCONFIRMED COMPONENT — Motor／servo channel '2' | `chFadeOut`、`chServoHold` | `pgu-storymode-motor-reset-355-chservohold-ae0ff398`<br>`pgu-storymode-motor-reset-707-chfadeout-c6059683`<br>`pgu-storymode-motor-reset-716-chservohold-4ebf691e`<br>`pgu-storymode-motor-reset-882-chservohold-7aa6fe47`<br>`pgu-storymode-motor-reset-1050-chservohold-dc857b95` |
| STAGED | Motor／servo channel '3' | UNCONFIRMED COMPONENT — Motor／servo channel '3' | `chFadeOut`、`chServoHold` | `pgu-storymode-motor-reset-356-chservohold-9d81b248`<br>`pgu-storymode-motor-reset-708-chfadeout-d72adf1f`<br>`pgu-storymode-motor-reset-717-chservohold-97df2326`<br>`pgu-storymode-motor-reset-883-chservohold-92e64c3d`<br>`pgu-storymode-motor-reset-1051-chservohold-cba06780` |
| STAGED | Motor／servo channel '4' | UNCONFIRMED COMPONENT — Motor／servo channel '4' | `chFadeOut`、`chServoHold` | `pgu-storymode-motor-reset-357-chservohold-232d5343`<br>`pgu-storymode-motor-reset-709-chfadeout-1a94ac82`<br>`pgu-storymode-motor-reset-718-chservohold-64f44022`<br>`pgu-storymode-motor-reset-884-chservohold-e09ff6dc`<br>`pgu-storymode-motor-reset-1052-chservohold-97376b22` |
| STAGED | Motor／servo channel '5' | UNCONFIRMED COMPONENT — Motor／servo channel '5' | `chFadeOut`、`chServoHold` | `pgu-storymode-motor-reset-358-chservohold-65c51a04`<br>`pgu-storymode-motor-reset-710-chfadeout-38dc11bd`<br>`pgu-storymode-motor-reset-719-chservohold-8dbedcdf`<br>`pgu-storymode-motor-reset-885-chservohold-8333a5c9`<br>`pgu-storymode-motor-reset-1053-chservohold-22aa02e3` |
| STAGED | PCA PWM0 CH 12 | UNCONFIRMED COMPONENT — PCA PWM0 CH 12 | `chOff` | `pgu-storymode-motor-reset-346-choff-ff11e637`<br>`pgu-storymode-motor-reset-701-choff-cc1eb03e` |
| STAGED | PCA PWM0 CH 13 | UNCONFIRMED COMPONENT — PCA PWM0 CH 13 | `chOff` | `pgu-storymode-motor-reset-347-choff-1f73efa3`<br>`pgu-storymode-motor-reset-702-choff-3de02c10` |
| STAGED | PCA PWM0 CH 14 | UNCONFIRMED COMPONENT — PCA PWM0 CH 14 | `chValcanGun` | `pgu-storymode-motor-reset-348-chvalcangun-dc402899`<br>`pgu-storymode-motor-reset-703-chvalcangun-9f57315f` |
| STAGED | PCA PWM0 CH 15 | UNCONFIRMED COMPONENT — PCA PWM0 CH 15 | `chFlashAlternativeV2` | `pgu-storymode-motor-reset-350-chflashalternativev2-30b11415`<br>`pgu-storymode-motor-reset-705-chflashalternativev2-de7b1e80` |
| STAGED | PCA PWM0 CH i (loop 2..7 inclusive) | UNCONFIRMED COMPONENT — PCA PWM0 CH i (loop 2..7 inclusive) | `chOff` | `pgu-storymode-motor-reset-341-choff-db1eebf6`<br>`pgu-storymode-motor-reset-696-choff-bc534bb0` |
| STAGED | PCA PWM0 CH i (loop 9..11 inclusive) | UNCONFIRMED COMPONENT — PCA PWM0 CH i (loop 9..11 inclusive) | `chOn` | `pgu-storymode-motor-reset-344-chon-f95a8fac`<br>`pgu-storymode-motor-reset-699-chon-fe5c8747` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `SpecificColorPattern` | `pgu-storymode-motor-reset-336-specificcolorpattern-a872da24`<br>`pgu-storymode-motor-reset-691-specificcolorpattern-d7fc9c62`<br>`pgu-storymode-motor-reset-874-specificcolorpattern-85533b1e`<br>`pgu-storymode-motor-reset-1042-specificcolorpattern-acb2c141` |

## Slave 6

### storyMode_develop

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB1 | Hi-Nu Slave 4/6 左右手下段 RGB — shared PGU Slave 4 RGB source. | `rgbOff` | `pgu-storymode-develop-143-rgboff-f56448fd` |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `rgbOff` | `pgu-storymode-develop-144-rgboff-51a36b63` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `rgbOff` | `pgu-storymode-develop-145-rgboff-cfa75bc3` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `SpecificColorPattern` | `pgu-storymode-develop-147-specificcolorpattern-f790e36e` |

### storyMode_signals

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB4 | Hi-Nu Slave 4/6 左右手下段 RGB — shared PGU Slave 4 RGB source. | `SpecificColorPattern` | `pgu-storymode-signals-128-specificcolorpattern-3ec0d687` |

### storyMode_0_v1

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB1 | Hi-Nu Slave 4/6 左右手下段 RGB — shared PGU Slave 4 RGB source. | `randomFlashWithGap_multiple`、`randomLightUp` | `pgu-storymode-0-v1-387-randomflashwithgap-multiple-768dfea5`<br>`pgu-storymode-0-v1-2100-randomlightup-889249bf` |
| STAGED | RGB1 | Slave 6 RGB1-4、RGB7-9 腰部／裙甲燈：重複亮燈輪與首輪一致。 | `rgbOn` | `pgu-storymode-0-v1-2936-rgbon-f9fb609e` |
| STAGED | RGB1 | UNCONFIRMED COMPONENT — RGB1 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v1-750-randomflashwithgap-multiple-0eabe8d6`<br>`pgu-storymode-0-v1-1211-randomlightup-99c60575`<br>`pgu-storymode-0-v1-1678-randomlightup-b71a7517`<br>`pgu-storymode-0-v1-2421-rgbon-1ef41320`<br>`pgu-storymode-0-v1-2998-rgbon-1f9476a1` |
| STAGED | RGB10 | UNCONFIRMED COMPONENT — RGB10 | `randomFlashWithGap_multiple` | `pgu-storymode-0-v1-436-randomflashwithgap-multiple-68485935` |
| STAGED | RGB11 | UNCONFIRMED COMPONENT — RGB11 | `randomFlashWithGap_multiple` | `pgu-storymode-0-v1-443-randomflashwithgap-multiple-18424735` |
| STAGED | RGB12 | UNCONFIRMED COMPONENT — RGB12 | `randomFlashWithGap_multiple` | `pgu-storymode-0-v1-450-randomflashwithgap-multiple-652634d7` |
| STAGED | RGB13 | UNCONFIRMED COMPONENT — RGB13 | `randomFlashWithGap_multiple` | `pgu-storymode-0-v1-457-randomflashwithgap-multiple-8612f089` |
| STAGED | RGB16 | UNCONFIRMED COMPONENT — RGB16 | `randomFlashWithGap_multiple` | `pgu-storymode-0-v1-464-randomflashwithgap-multiple-f088d166` |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v1-394-randomflashwithgap-multiple-8e2726a1`<br>`pgu-storymode-0-v1-757-randomflashwithgap-multiple-3e7fb057`<br>`pgu-storymode-0-v1-1218-randomlightup-64cbf239`<br>`pgu-storymode-0-v1-1685-randomlightup-142a09fb`<br>`pgu-storymode-0-v1-2107-randomlightup-eb26aa2f`<br>`pgu-storymode-0-v1-2423-rgbon-98949eac`<br>`pgu-storymode-0-v1-2938-rgbon-0cc5228d`<br>`pgu-storymode-0-v1-3000-rgbon-4c31fdfe` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v1-401-randomflashwithgap-multiple-934d0c6d`<br>`pgu-storymode-0-v1-764-randomflashwithgap-multiple-1026ee46`<br>`pgu-storymode-0-v1-1225-randomlightup-4526bc1b`<br>`pgu-storymode-0-v1-1692-randomlightup-ec9fb954`<br>`pgu-storymode-0-v1-2114-randomlightup-8eb48b00`<br>`pgu-storymode-0-v1-2425-rgbon-437d1682`<br>`pgu-storymode-0-v1-2940-rgbon-809b6928`<br>`pgu-storymode-0-v1-3002-rgbon-f4bbb893` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v1-408-randomflashwithgap-multiple-2895973d`<br>`pgu-storymode-0-v1-771-randomflashwithgap-multiple-a597ff25`<br>`pgu-storymode-0-v1-1203-randomlightup-27c688d5`<br>`pgu-storymode-0-v1-1233-randomlightup-c5bab036`<br>`pgu-storymode-0-v1-1700-randomlightup-dcb8ef61`<br>`pgu-storymode-0-v1-2121-randomlightup-eaeb2613`<br>`pgu-storymode-0-v1-2427-rgbon-3880858b`<br>`pgu-storymode-0-v1-2942-rgbon-fbe2c3f6`<br>`pgu-storymode-0-v1-3004-rgbon-dc441f25` |
| STAGED | RGB7 | Hi-Nu Slave 4/6 左右手下段 RGB — shared PGU Slave 4 RGB source. | `GN_Sword_Pulse_Color` | `pgu-storymode-0-v1-1657-gn-sword-pulse-color-0eaff14b` |
| STAGED | RGB7 | UNCONFIRMED COMPONENT — RGB7 | `GN_Sword_Pulse_Color`、`randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v1-415-randomflashwithgap-multiple-1c0b4897`<br>`pgu-storymode-0-v1-1249-randomlightup-47068cf5`<br>`pgu-storymode-0-v1-1669-randomlightup-be5e5a66`<br>`pgu-storymode-0-v1-2129-gn-sword-pulse-color-fccbdfd1`<br>`pgu-storymode-0-v1-2141-randomlightup-58f7413d`<br>`pgu-storymode-0-v1-2429-rgbon-d4f19fbf`<br>`pgu-storymode-0-v1-2944-rgbon-e841f870`<br>`pgu-storymode-0-v1-3006-rgbon-b2136f0b` |
| STAGED | RGB8 | UNCONFIRMED COMPONENT — RGB8 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v1-422-randomflashwithgap-multiple-1550ca22`<br>`pgu-storymode-0-v1-778-randomflashwithgap-multiple-8bdb7645`<br>`pgu-storymode-0-v1-1256-randomlightup-30916f03`<br>`pgu-storymode-0-v1-1716-randomlightup-c3f44783`<br>`pgu-storymode-0-v1-2149-randomlightup-d7231f70`<br>`pgu-storymode-0-v1-2431-rgbon-19c228d7`<br>`pgu-storymode-0-v1-2946-rgbon-89b10970`<br>`pgu-storymode-0-v1-3008-rgbon-43e61481` |
| STAGED | RGB9 | UNCONFIRMED COMPONENT — RGB9 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v1-429-randomflashwithgap-multiple-5c78e339`<br>`pgu-storymode-0-v1-785-randomflashwithgap-multiple-b8bd4913`<br>`pgu-storymode-0-v1-1241-randomlightup-bc8b941b`<br>`pgu-storymode-0-v1-1263-randomlightup-83bd5ede`<br>`pgu-storymode-0-v1-1708-randomlightup-87aa4c6e`<br>`pgu-storymode-0-v1-1723-randomlightup-00fa4674`<br>`pgu-storymode-0-v1-2156-randomlightup-ae18eb6b`<br>`pgu-storymode-0-v1-2433-rgbon-412a43d1`<br>`pgu-storymode-0-v1-2948-rgbon-ff910a9a`<br>`pgu-storymode-0-v1-3010-rgbon-72ccf345` |

### storyMode_awakening_3

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB2 | Hi-Nu Slave 4/6 左右手下段 RGB — shared PGU Slave 4 RGB source. | `rgbOff` | `pgu-storymode-awakening-3-268-rgboff-ed919fdc` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `rgbOff` | `pgu-storymode-awakening-3-270-rgboff-4a93eb65` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `rgbOff` | `pgu-storymode-awakening-3-273-rgboff-e1ea3971`<br>`pgu-storymode-awakening-3-278-rgboff-bf6c6b25` |
| STAGED | RGB7 | UNCONFIRMED COMPONENT — RGB7 | `rgbOff` | `pgu-storymode-awakening-3-275-rgboff-4828a086` |

### storyMode_activation

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `gradientVentPalette`、`randomFillAll_V2` | `pgu-storymode-activation-386-randomfillall-v2-5095a4f8`<br>`pgu-storymode-activation-389-gradientventpalette-57237bbb` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `VentEffect`、`turbine_v3` | `pgu-storymode-activation-405-venteffect-7937484d`<br>`pgu-storymode-activation-416-turbine-v3-be8f6f22` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `SpecificColorPattern` | `pgu-storymode-activation-429-specificcolorpattern-1e751b9a`<br>`pgu-storymode-activation-437-specificcolorpattern-1d7a7a38` |

### storyMode_0_v2

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB1 | Hi-Nu Slave 4/6 左右手下段 RGB — shared PGU Slave 4 RGB source. | `randomLightUp` | `pgu-storymode-0-v2-1669-randomlightup-e43fa9c5` |
| STAGED | RGB1 | UNCONFIRMED COMPONENT — RGB1 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v2-465-randomflashwithgap-multiple-4edb2dbd`<br>`pgu-storymode-0-v2-918-randomlightup-8991bc36`<br>`pgu-storymode-0-v2-1320-randomlightup-650477a0`<br>`pgu-storymode-0-v2-1925-rgbon-cff2a153`<br>`pgu-storymode-0-v2-2111-rgbon-33dff60c` |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v2-472-randomflashwithgap-multiple-2cc1f93c`<br>`pgu-storymode-0-v2-925-randomlightup-8aac7e1a`<br>`pgu-storymode-0-v2-1327-randomlightup-30976e04`<br>`pgu-storymode-0-v2-1676-randomlightup-8ddea020`<br>`pgu-storymode-0-v2-1927-rgbon-51fb21be`<br>`pgu-storymode-0-v2-2113-rgbon-cf84c791` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v2-479-randomflashwithgap-multiple-2597d1c6`<br>`pgu-storymode-0-v2-932-randomlightup-a21a139c`<br>`pgu-storymode-0-v2-1334-randomlightup-662762f5`<br>`pgu-storymode-0-v2-1683-randomlightup-5ab893b7`<br>`pgu-storymode-0-v2-1929-rgbon-7e27e0eb`<br>`pgu-storymode-0-v2-2115-rgbon-ff84568a` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v2-486-randomflashwithgap-multiple-a8082533`<br>`pgu-storymode-0-v2-940-randomlightup-5ffa9b97`<br>`pgu-storymode-0-v2-1341-randomlightup-4031e910`<br>`pgu-storymode-0-v2-1690-randomlightup-a59fdc60`<br>`pgu-storymode-0-v2-1931-rgbon-dee9bd2e`<br>`pgu-storymode-0-v2-2117-rgbon-53843fe1` |
| STAGED | RGB7 | Hi-Nu Slave 4/6 左右手下段 RGB — shared PGU Slave 4 RGB source. | `GN_Sword_Pulse_Color` | `pgu-storymode-0-v2-1299-gn-sword-pulse-color-1a3032c3` |
| STAGED | RGB7 | UNCONFIRMED COMPONENT — RGB7 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOff`、`rgbOn` | `pgu-storymode-0-v2-493-randomflashwithgap-multiple-e5bd649d`<br>`pgu-storymode-0-v2-517-rgboff-10cf1ce9`<br>`pgu-storymode-0-v2-956-randomlightup-5de25ab1`<br>`pgu-storymode-0-v2-1311-randomlightup-ba938e02`<br>`pgu-storymode-0-v2-1698-randomlightup-09d7f710`<br>`pgu-storymode-0-v2-1933-rgbon-989a8b97`<br>`pgu-storymode-0-v2-2119-rgbon-25fec7e3` |
| STAGED | RGB8 | UNCONFIRMED COMPONENT — RGB8 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v2-500-randomflashwithgap-multiple-b2f45527`<br>`pgu-storymode-0-v2-963-randomlightup-cda0983a`<br>`pgu-storymode-0-v2-1348-randomlightup-cca79417`<br>`pgu-storymode-0-v2-1706-randomlightup-c4cd792f`<br>`pgu-storymode-0-v2-1935-rgbon-5697c047`<br>`pgu-storymode-0-v2-2121-rgbon-bcc73a7c` |
| STAGED | RGB9 | UNCONFIRMED COMPONENT — RGB9 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v2-507-randomflashwithgap-multiple-e27942ad`<br>`pgu-storymode-0-v2-948-randomlightup-3d34cff5`<br>`pgu-storymode-0-v2-970-randomlightup-c6209fe0`<br>`pgu-storymode-0-v2-1355-randomlightup-c840adad`<br>`pgu-storymode-0-v2-1713-randomlightup-3e033e95`<br>`pgu-storymode-0-v2-1937-rgbon-bc36bde5`<br>`pgu-storymode-0-v2-2123-rgbon-e584a101` |
| STAGED | Runtime／group target 'strips' | UNCONFIRMED COMPONENT — Runtime／group target 'strips' | `randomFlashFixedCount_multiple` | `pgu-storymode-0-v2-234-randomflashfixedcount-multiple-08a643a2` |

### storyMode_storing_energy

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB1 | Hi-Nu Slave 4/6 左右手下段 RGB — shared PGU Slave 4 RGB source. | `paletteWave_80Percent_SpecialWave` | `pgu-storymode-storing-energy-690-palettewave-80percent-specialwave-190ea77c` |
| STAGED | RGB2 | Hi-Nu Slave 4/6 左右手下段 RGB — shared PGU Slave 4 RGB source. | `rgbOff` | `pgu-storymode-storing-energy-393-rgboff-8f5ea9b1` |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `gradientVentPalette`、`rgbOff` | `pgu-storymode-storing-energy-700-gradientventpalette-d5726643`<br>`pgu-storymode-storing-energy-719-rgboff-10fb6879` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `rgbOff` | `pgu-storymode-storing-energy-394-rgboff-2527d93a`<br>`pgu-storymode-storing-energy-722-rgboff-23830595` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `SpecificColorPattern`、`rgbOff` | `pgu-storymode-storing-energy-395-rgboff-53bc58a5`<br>`pgu-storymode-storing-energy-724-specificcolorpattern-bd9dc0cb` |

### storyMode_2

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB2 | Hi-Nu Slave 4/6 左右手下段 RGB — shared PGU Slave 4 RGB source. | `gradientVentPalette` | `pgu-storymode-2-362-gradientventpalette-fd4dfb18` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `turbine_v3` | `pgu-storymode-2-382-turbine-v3-17dc6070` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `SpecificColorPattern` | `pgu-storymode-2-395-specificcolorpattern-8d5adf14` |

### storyMode_plasma

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB4 | Hi-Nu Slave 4/6 左右手下段 RGB — shared PGU Slave 4 RGB source. | `SpecificColorPattern` | `pgu-storymode-plasma-623-specificcolorpattern-df7513e3` |

### storyMode_trans_am

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB1 | Hi-Nu Slave 4/6 左右手下段 RGB — shared PGU Slave 4 RGB source. | `GN_Drive_Running` | `pgu-storymode-trans-am-217-gn-drive-running-701d4305` |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `gradientVentPalette` | `pgu-storymode-trans-am-228-gradientventpalette-9aa763d1` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `turbine_v3` | `pgu-storymode-trans-am-248-turbine-v3-b42f0952` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `SpecificColorPattern` | `pgu-storymode-trans-am-261-specificcolorpattern-074cd999` |

### storyMode_3

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `gradientVentPalette` | `pgu-storymode-3-397-gradientventpalette-91d7c442` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `turbine_v3` | `pgu-storymode-3-417-turbine-v3-7181826d` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `SpecificColorPattern` | `pgu-storymode-3-431-specificcolorpattern-f23dd8e7`<br>`pgu-storymode-3-439-specificcolorpattern-0b3dce03` |

### storyMode_idle

OFF／no direct call in this Slave context。

### storyMode_motor

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | Motor／servo channel '0' | UNCONFIRMED COMPONENT — Motor／servo channel '0' | `chFadeIn`、`chServoHold` | `pgu-storymode-motor-1702-chfadein-496c01d9`<br>`pgu-storymode-motor-1712-chservohold-2a9e9063`<br>`pgu-storymode-motor-2259-chservohold-1e4b05aa` |
| STAGED | Motor／servo channel '1' | UNCONFIRMED COMPONENT — Motor／servo channel '1' | `chFadeOut`、`chServoHold` | `pgu-storymode-motor-1703-chfadeout-068bd369`<br>`pgu-storymode-motor-1713-chservohold-d9c5d8cc`<br>`pgu-storymode-motor-2260-chservohold-128e908e` |
| STAGED | Motor／servo channel '2' | UNCONFIRMED COMPONENT — Motor／servo channel '2' | `chFadeIn`、`chServoHold` | `pgu-storymode-motor-1700-chfadein-cb8cf8f8`<br>`pgu-storymode-motor-1714-chservohold-8b437855`<br>`pgu-storymode-motor-2261-chservohold-5caf855e` |
| STAGED | Motor／servo channel '3' | UNCONFIRMED COMPONENT — Motor／servo channel '3' | `chFadeOut`、`chServoHold` | `pgu-storymode-motor-1701-chfadeout-f7050618`<br>`pgu-storymode-motor-1715-chservohold-fcd52d90`<br>`pgu-storymode-motor-2262-chservohold-f66132f5` |
| STAGED | Motor／servo channel '4' | UNCONFIRMED COMPONENT — Motor／servo channel '4' | `chFadeIn`、`chServoHold` | `pgu-storymode-motor-1698-chfadein-b40af610`<br>`pgu-storymode-motor-1716-chservohold-92f79966`<br>`pgu-storymode-motor-2263-chservohold-5acd99f1` |
| STAGED | Motor／servo channel '5' | UNCONFIRMED COMPONENT — Motor／servo channel '5' | `chFadeOut`、`chServoHold` | `pgu-storymode-motor-1699-chfadeout-4179838d`<br>`pgu-storymode-motor-1717-chservohold-9749e526`<br>`pgu-storymode-motor-2264-chservohold-c19ca8cc` |
| STAGED | PCA PWM1 CH i (loop 0..8 inclusive) | 0s: body white PCA + eyes — Slave 3 chest/skirt pure white PCA. | `chOn` | `pgu-storymode-motor-703-chon-7b4483f3` |
| STAGED | RGB1 | Slave 6 waist RGB1 — GN drive running. | `GN_Drive_Running` | `pgu-storymode-motor-1721-gn-drive-running-65d7d5cd` |
| STAGED | RGB10 | UNCONFIRMED COMPONENT — RGB10 | `SpecificColorPattern` | `pgu-storymode-motor-1608-specificcolorpattern-38c2fde6`<br>`pgu-storymode-motor-1666-specificcolorpattern-cf9187ab`<br>`pgu-storymode-motor-2223-specificcolorpattern-5cd65ff2` |
| STAGED | RGB11 | UNCONFIRMED COMPONENT — RGB11 | `GN_Drive_Running` | `pgu-storymode-motor-1787-gn-drive-running-6ca9dcbe` |
| STAGED | RGB12 | UNCONFIRMED COMPONENT — RGB12 | `SpecificColorPattern` | `pgu-storymode-motor-1612-specificcolorpattern-7c2e424c`<br>`pgu-storymode-motor-1641-specificcolorpattern-4f09edad`<br>`pgu-storymode-motor-2198-specificcolorpattern-f8ff6004` |
| STAGED | RGB2 | Slave 6 waist RGB2 — vent effect. | `VentEffect` | `pgu-storymode-motor-1732-venteffect-a7d9e310` |
| STAGED | RGB3 | Slave 6 waist RGB3 — turbine vortex. | `turbine_v3_sound` | `pgu-storymode-motor-1743-turbine-v3-sound-76d91b30` |
| STAGED | RGB4 | 3s: all signals green — Slave 3 RGB4 signal LEDs. | `SpecificColorPattern` | `pgu-storymode-motor-695-specificcolorpattern-007dd120` |
| STAGED | RGB4 | Slave 6 waist RGB4 — footplate effect. | `footplatev2` | `pgu-storymode-motor-1756-footplatev2-05a29530` |
| STAGED | RGB7 | Slave 6 waist RGB7/RGB9/RGB11 — GN drive running. | `GN_Drive_Running` | `pgu-storymode-motor-1767-gn-drive-running-cd36b591` |
| STAGED | RGB8 | UNCONFIRMED COMPONENT — RGB8 | `SpecificColorPattern` | `pgu-storymode-motor-1604-specificcolorpattern-da8a328d`<br>`pgu-storymode-motor-1691-specificcolorpattern-0907411f`<br>`pgu-storymode-motor-2248-specificcolorpattern-36c4316d` |
| STAGED | RGB9 | UNCONFIRMED COMPONENT — RGB9 | `GN_Drive_Running` | `pgu-storymode-motor-1777-gn-drive-running-dc5e1015` |

### storyMode_motor_reset

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | Motor／servo channel '0' | UNCONFIRMED COMPONENT — Motor／servo channel '0' | `chFadeOut`、`chServoHold` | `pgu-storymode-motor-reset-444-chfadeout-5d4f60f3`<br>`pgu-storymode-motor-reset-453-chservohold-676da94c`<br>`pgu-storymode-motor-reset-733-chservohold-20c6ed82`<br>`pgu-storymode-motor-reset-897-chservohold-e1a77db5`<br>`pgu-storymode-motor-reset-1065-chservohold-a9ecf7dd` |
| STAGED | Motor／servo channel '1' | UNCONFIRMED COMPONENT — Motor／servo channel '1' | `chFadeIn`、`chServoHold` | `pgu-storymode-motor-reset-445-chfadein-34f6ac35`<br>`pgu-storymode-motor-reset-454-chservohold-2c48b4f6`<br>`pgu-storymode-motor-reset-734-chservohold-d699867d`<br>`pgu-storymode-motor-reset-898-chservohold-033f554c`<br>`pgu-storymode-motor-reset-1066-chservohold-e51ce507` |
| STAGED | Motor／servo channel '2' | UNCONFIRMED COMPONENT — Motor／servo channel '2' | `chFadeOut`、`chServoHold` | `pgu-storymode-motor-reset-442-chfadeout-d97c586c`<br>`pgu-storymode-motor-reset-455-chservohold-2ccb35dc`<br>`pgu-storymode-motor-reset-735-chservohold-e575145a`<br>`pgu-storymode-motor-reset-899-chservohold-0b7a520a`<br>`pgu-storymode-motor-reset-1067-chservohold-a913c386` |
| STAGED | Motor／servo channel '3' | UNCONFIRMED COMPONENT — Motor／servo channel '3' | `chFadeIn`、`chServoHold` | `pgu-storymode-motor-reset-443-chfadein-42d929e5`<br>`pgu-storymode-motor-reset-456-chservohold-c9393ce7`<br>`pgu-storymode-motor-reset-736-chservohold-916d2c15`<br>`pgu-storymode-motor-reset-900-chservohold-f149ac4a`<br>`pgu-storymode-motor-reset-1068-chservohold-eabe53a1` |
| STAGED | Motor／servo channel '4' | UNCONFIRMED COMPONENT — Motor／servo channel '4' | `chFadeOut`、`chServoHold` | `pgu-storymode-motor-reset-440-chfadeout-b5383dd9`<br>`pgu-storymode-motor-reset-457-chservohold-a64fb5a3`<br>`pgu-storymode-motor-reset-737-chservohold-18a36266`<br>`pgu-storymode-motor-reset-901-chservohold-012325b5`<br>`pgu-storymode-motor-reset-1069-chservohold-9f5fde5f` |
| STAGED | Motor／servo channel '5' | UNCONFIRMED COMPONENT — Motor／servo channel '5' | `chFadeIn`、`chServoHold` | `pgu-storymode-motor-reset-441-chfadein-73e710c8`<br>`pgu-storymode-motor-reset-458-chservohold-d53fc0c3`<br>`pgu-storymode-motor-reset-738-chservohold-5def5a03`<br>`pgu-storymode-motor-reset-902-chservohold-d007aca4`<br>`pgu-storymode-motor-reset-1070-chservohold-287838e0` |
| STAGED | RGB10 | UNCONFIRMED COMPONENT — RGB10 | `SpecificColorPattern`、`rgbOff` | `pgu-storymode-motor-reset-408-specificcolorpattern-da1f4d26`<br>`pgu-storymode-motor-reset-725-rgboff-1f323a28`<br>`pgu-storymode-motor-reset-889-rgboff-e6c3df56`<br>`pgu-storymode-motor-reset-1057-rgboff-395e723a` |
| STAGED | RGB12 | UNCONFIRMED COMPONENT — RGB12 | `SpecificColorPattern`、`rgbOff` | `pgu-storymode-motor-reset-382-specificcolorpattern-48239a15`<br>`pgu-storymode-motor-reset-726-rgboff-09b777c3`<br>`pgu-storymode-motor-reset-890-rgboff-87c76e7e`<br>`pgu-storymode-motor-reset-1058-rgboff-d78a84fd` |
| STAGED | RGB8 | UNCONFIRMED COMPONENT — RGB8 | `SpecificColorPattern`、`rgbOff` | `pgu-storymode-motor-reset-434-specificcolorpattern-7ec2d727`<br>`pgu-storymode-motor-reset-724-rgboff-a94fd5ba`<br>`pgu-storymode-motor-reset-888-rgboff-14861f84`<br>`pgu-storymode-motor-reset-1056-rgboff-a7a21892` |

## Slave 7

### storyMode_develop

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB1 | Hi-Nu Slave 7 腰甲 RGB — PGU Slave 6 RGB source. | `rgbOff` | `pgu-storymode-develop-163-rgboff-0680114a` |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `rgbOff` | `pgu-storymode-develop-164-rgboff-1e0baf77` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `rgbOff` | `pgu-storymode-develop-165-rgboff-6d063957` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `SpecificColorPattern` | `pgu-storymode-develop-168-specificcolorpattern-611046cd` |
| STAGED | RGB7 | UNCONFIRMED COMPONENT — RGB7 | `SpecificColorPattern` | `pgu-storymode-develop-175-specificcolorpattern-6fab3e42` |
| STAGED | RGB8 | UNCONFIRMED COMPONENT — RGB8 | `SpecificColorPattern` | `pgu-storymode-develop-182-specificcolorpattern-426c0060` |
| STAGED | RGB9 | UNCONFIRMED COMPONENT — RGB9 | `rgbOff` | `pgu-storymode-develop-166-rgboff-6cea22b6` |

### storyMode_signals

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | PCA PWM0 CH channel (loop 0..5 inclusive) | Hi-Nu Slave 7 PWM0 CH0-5 (0x50) 左／右前裙甲白燈：低亮長亮。 | `chOn` | `pgu-storymode-signals-164-chon-0b9233fa` |
| STAGED | PCA PWM0 CH channel (loop 6..7 inclusive) | Hi-Nu Slave 7 PWM0 CH6-7 (0x50) 左／右前裙甲暖白燈：Signals 保持關閉。 | `chOff` | `pgu-storymode-signals-169-choff-84fcec48` |
| STAGED | RGB2 | Hi-Nu Slave 7 腰甲 RGB — PGU Slave 6 RGB source. ／ Hi-Nu Slave 7 RGB2 (左/右後裙甲; 散氣) 快插 藍線 18 粒：Signals 模式關閉。 | `rgbOff` | `pgu-storymode-signals-144-rgboff-fc469448` |
| STAGED | RGB3 | Hi-Nu Slave 7 RGB3 未接燈帶（-1 粒），保持關閉。 | `rgbOff` | `pgu-storymode-signals-147-rgboff-b91b837f` |
| STAGED | RGB4 | Hi-Nu Slave 7 RGB4 未接燈帶（-1 粒），保持關閉。 | `rgbOff` | `pgu-storymode-signals-150-rgboff-7f0bbd27` |
| STAGED | RGB7 | Hi-Nu Slave 7 RGB7 (3 粒) 腰甲訊號燈。 | `SpecificColorPattern` | `pgu-storymode-signals-153-specificcolorpattern-ff99e0ea` |
| STAGED | RGB8 | Hi-Nu Slave 7 RGB8 (右後裙甲; 腳底燈) 快插 白線 2020 燈帶 42 粒：Signals 模式關閉。 | `rgbOff` | `pgu-storymode-signals-160-rgboff-2a77bdb1` |

### storyMode_0_v1

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB1 | UNCONFIRMED COMPONENT — RGB1 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v1-801-randomflashwithgap-multiple-1361c470`<br>`pgu-storymode-0-v1-1279-randomlightup-87da5129`<br>`pgu-storymode-0-v1-1739-randomlightup-9c3dafed`<br>`pgu-storymode-0-v1-2172-randomlightup-bdd870b6`<br>`pgu-storymode-0-v1-2444-rgbon-b7964771` |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v1-809-randomflashwithgap-multiple-0676a187`<br>`pgu-storymode-0-v1-1287-randomlightup-3417587e`<br>`pgu-storymode-0-v1-1747-randomlightup-ac18ceb7`<br>`pgu-storymode-0-v1-2180-randomlightup-420e4d92`<br>`pgu-storymode-0-v1-2447-rgbon-bed9d6d1` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v1-817-randomflashwithgap-multiple-dd36f151`<br>`pgu-storymode-0-v1-1295-randomlightup-cb4a0087`<br>`pgu-storymode-0-v1-1755-randomlightup-75e24ece`<br>`pgu-storymode-0-v1-2188-randomlightup-e4aaedbd`<br>`pgu-storymode-0-v1-2450-rgbon-d54edcfe` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v1-825-randomflashwithgap-multiple-0bc12d10`<br>`pgu-storymode-0-v1-1303-randomlightup-703f9067`<br>`pgu-storymode-0-v1-1763-randomlightup-888e4558`<br>`pgu-storymode-0-v1-2196-randomlightup-fd5fc355`<br>`pgu-storymode-0-v1-2453-rgbon-efb8d257` |
| STAGED | RGB7 | UNCONFIRMED COMPONENT — RGB7 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v1-833-randomflashwithgap-multiple-30430427`<br>`pgu-storymode-0-v1-1311-randomlightup-a6a897f4`<br>`pgu-storymode-0-v1-1771-randomlightup-7aad1bd7`<br>`pgu-storymode-0-v1-2204-randomlightup-6c5e5b10`<br>`pgu-storymode-0-v1-2456-rgbon-59c66e34` |
| STAGED | RGB8 | UNCONFIRMED COMPONENT — RGB8 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v1-841-randomflashwithgap-multiple-f4ed4cc1`<br>`pgu-storymode-0-v1-1319-randomlightup-ad10ea7c`<br>`pgu-storymode-0-v1-1779-randomlightup-5dcec600`<br>`pgu-storymode-0-v1-2212-randomlightup-2f61606e`<br>`pgu-storymode-0-v1-2459-rgbon-2a4b781d` |
| STAGED | RGB9 | UNCONFIRMED COMPONENT — RGB9 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v1-849-randomflashwithgap-multiple-cf95d01f`<br>`pgu-storymode-0-v1-1327-randomlightup-740caa58`<br>`pgu-storymode-0-v1-1787-randomlightup-e99b4b3a`<br>`pgu-storymode-0-v1-2220-randomlightup-6817f702`<br>`pgu-storymode-0-v1-2462-rgbon-8ac5ecd1` |
| STAGED | Runtime／group target 'PWM0' | Hi-Nu Slave 7 腰甲 RGB — PGU Slave 6 RGB source. ／ Hi-Nu Slave 7 PWM0 CH0-7 (0x50) 左／右前裙甲白／暖白燈：選中的閃爍通道保持長亮。 | `chSelectedOn` | `pgu-storymode-0-v1-3017-chselectedon-4e90ef91` |
| STAGED | Runtime／group target 'PWM0' | Hi-Nu Slave 7 腰甲 RGB — PGU Slave 6 RGB source. ／ Hi-Nu Slave 7 PWM0 CH0-7 (0x50) 左／右前裙甲白／暖白燈：隨機閃爍。 | `chRandomFlash` | `pgu-storymode-0-v1-797-chrandomflash-71f0e3ba`<br>`pgu-storymode-0-v1-1275-chrandomflash-4a620bcb`<br>`pgu-storymode-0-v1-1735-chrandomflash-12b797c8`<br>`pgu-storymode-0-v1-2168-chrandomflash-3df1fffd`<br>`pgu-storymode-0-v1-2440-chrandomflash-c85209f7` |

### storyMode_awakening_3

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | PCA PWM0 CH channel (loop 0..5 inclusive) | Hi-Nu Slave 7 PWM0 CH0-2 (0x50) 左前裙甲、CH3-5 右前裙甲白燈：低亮長亮。 | `chOn` | `pgu-storymode-awakening-3-315-chon-6398f964` |
| STAGED | PCA PWM0 CH channel (loop 6..7 inclusive) | Hi-Nu Slave 7 PWM0 CH6-7 (0x50) 左／右前裙甲暖白燈：漸進閃爍。 | `chProgressiveFlash` | `pgu-storymode-awakening-3-320-chprogressiveflash-25fd6ffb` |
| STAGED | RGB2 | Hi-Nu Slave 7 腰甲 RGB — PGU Slave 6 RGB source. ／ Hi-Nu Slave 7 RGB2 (左/右後裙甲; 散氣) 快插 藍線 18 粒：Awakening 3 保持關閉。 | `rgbOff` | `pgu-storymode-awakening-3-289-rgboff-f21722e1` |
| STAGED | RGB3 | Hi-Nu Slave 7 RGB3 未接燈帶（-1 粒），保持關閉。 | `rgbOff` | `pgu-storymode-awakening-3-292-rgboff-b929151a` |
| STAGED | RGB4 | Hi-Nu Slave 7 RGB4 未接燈帶（-1 粒），保持關閉。 | `rgbOff` | `pgu-storymode-awakening-3-295-rgboff-f3761d27` |
| STAGED | RGB7 | UNCONFIRMED COMPONENT — RGB7 | `rgbOff` | `pgu-storymode-awakening-3-297-rgboff-981e17d4` |
| STAGED | RGB8 | Hi-Nu Slave 7 RGB8 (右後裙甲; 腳底燈) 快插 白線 2020 燈帶 42 粒。 | `footplatev2` | `pgu-storymode-awakening-3-300-footplatev2-d8ab7ec8` |
| STAGED | RGB9 | UNCONFIRMED COMPONENT — RGB9 | `rgbOff` | `pgu-storymode-awakening-3-311-rgboff-144db133` |

### storyMode_activation

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | PCA PWM0 CH channel (loop 0..5 inclusive) | Hi-Nu Slave 7 PWM0 CH0-5 (0x50) 左／右前裙甲白燈：低亮長亮。 | `chOn` | `pgu-storymode-activation-501-chon-b51129f6` |
| STAGED | PCA PWM0 CH channel (loop 6..7 inclusive) | Hi-Nu Slave 7 PWM0 CH6-7 (0x50) 左／右前裙甲暖白燈：漸進閃爍。 | `chProgressiveFlash` | `pgu-storymode-activation-506-chprogressiveflash-8597d783` |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `gradientVentPalette`、`randomFillAll_V2` | `pgu-storymode-activation-455-randomfillall-v2-5b1d39fb`<br>`pgu-storymode-activation-458-gradientventpalette-066786c6` |
| STAGED | RGB3 | Hi-Nu Slave 7 RGB3 未接燈帶（-1 粒），保持關閉。 | `rgbOff` | `pgu-storymode-activation-475-rgboff-7fd10670` |
| STAGED | RGB4 | Hi-Nu Slave 7 RGB4 未接燈帶（-1 粒），保持關閉。 | `rgbOff` | `pgu-storymode-activation-478-rgboff-0edbe355` |
| STAGED | RGB7 | Hi-Nu Slave 7 RGB7 (3 粒) 腰甲訊號燈。 | `SpecificColorPattern` | `pgu-storymode-activation-481-specificcolorpattern-33b0c32c` |
| STAGED | RGB8 | Hi-Nu Slave 7 RGB8 (右後裙甲; 腳底燈) 快插 白線 2020 燈帶 42 粒。 | `footplatev2` | `pgu-storymode-activation-488-footplatev2-29d18b4f` |

### storyMode_0_v2

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB1 | UNCONFIRMED COMPONENT — RGB1 | `randomFlashWithGap_multiple` | `pgu-storymode-0-v2-530-randomflashwithgap-multiple-f0253f38` |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `randomFlashWithGap_multiple` | `pgu-storymode-0-v2-538-randomflashwithgap-multiple-3df44ed6` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `randomFlashWithGap_multiple` | `pgu-storymode-0-v2-546-randomflashwithgap-multiple-cc001902` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `randomFlashWithGap_multiple` | `pgu-storymode-0-v2-554-randomflashwithgap-multiple-9e1844f3` |
| STAGED | RGB7 | UNCONFIRMED COMPONENT — RGB7 | `randomFlashWithGap_multiple` | `pgu-storymode-0-v2-562-randomflashwithgap-multiple-2cf34a5d` |
| STAGED | RGB8 | UNCONFIRMED COMPONENT — RGB8 | `randomFlashWithGap_multiple` | `pgu-storymode-0-v2-570-randomflashwithgap-multiple-9b3f3e2d` |
| STAGED | RGB9 | UNCONFIRMED COMPONENT — RGB9 | `randomFlashWithGap_multiple` | `pgu-storymode-0-v2-578-randomflashwithgap-multiple-95bc0f70` |
| STAGED | Runtime／group target 'PWM0' | Hi-Nu Slave 7 腰甲 RGB — PGU Slave 6 RGB source. ／ Hi-Nu Slave 7 PWM0 CH0-7 (0x50) 左／右前裙甲白／暖白燈：選中的閃爍通道保持長亮。 | `chSelectedOn` | `pgu-storymode-0-v2-1944-chselectedon-a22ec90b`<br>`pgu-storymode-0-v2-2130-chselectedon-d6bac0db` |
| STAGED | Runtime／group target 'PWM0' | Hi-Nu Slave 7 腰甲 RGB — PGU Slave 6 RGB source. ／ Hi-Nu Slave 7 PWM0 CH0-7 (0x50) 左／右前裙甲白／暖白燈：隨機閃爍。 | `chRandomFlash` | `pgu-storymode-0-v2-524-chrandomflash-fc7c94d3`<br>`pgu-storymode-0-v2-982-chrandomflash-ecbdfb1c`<br>`pgu-storymode-0-v2-1367-chrandomflash-303a31b2`<br>`pgu-storymode-0-v2-1725-chrandomflash-44879123` |

### storyMode_storing_energy

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | PCA PWM0 CH channel (loop 0..5 inclusive) | Hi-Nu Slave 7 PWM0 CH0-5 (0x50) 左／右前裙甲白燈：低亮長亮。 | `chOn` | `pgu-storymode-storing-energy-424-chon-48c39896`<br>`pgu-storymode-storing-energy-764-chon-39a77490`<br>`pgu-storymode-storing-energy-1402-chon-cb457d4e` |
| STAGED | PCA PWM0 CH channel (loop 6..7 inclusive) | Hi-Nu Slave 7 PWM0 CH6-7 (0x50) 左／右前裙甲暖白燈：漸進閃爍。 | `chProgressiveFlash` | `pgu-storymode-storing-energy-429-chprogressiveflash-04af2ef5`<br>`pgu-storymode-storing-energy-769-chprogressiveflash-28dec457`<br>`pgu-storymode-storing-energy-1407-chprogressiveflash-80be386a` |
| STAGED | RGB1 | Hi-Nu Slave 7 腰甲 RGB — PGU Slave 6 RGB source. | `paletteWave_80Percent_SpecialWave` | `pgu-storymode-storing-energy-735-palettewave-80percent-specialwave-ab6003ec` |
| STAGED | RGB2 | Hi-Nu Slave 7 腰甲 RGB — PGU Slave 6 RGB source. ／ Hi-Nu Slave 7 RGB2 (左/右後裙甲; 散氣) 快插 藍線 18 粒：Full power 矩陣流動。 | `runPattern` | `pgu-storymode-storing-energy-1369-runpattern-4c11f4e8` |
| STAGED | RGB3 | Hi-Nu Slave 7 RGB3 未接燈帶（-1 粒），保持關閉。 | `rgbOff` | `pgu-storymode-storing-energy-745-rgboff-267721a6`<br>`pgu-storymode-storing-energy-1372-rgboff-b8de7293` |
| STAGED | RGB3 | Hi-Nu Slave 7 腰甲 RGB — PGU Slave 6 RGB source. ／ Hi-Nu Slave 7 RGB3 未接燈帶（-1 粒），保持關閉。 | `rgbOff` | `pgu-storymode-storing-energy-406-rgboff-abdeede5` |
| STAGED | RGB4 | Hi-Nu Slave 7 RGB4 未接燈帶（-1 粒），保持關閉。 | `rgbOff` | `pgu-storymode-storing-energy-409-rgboff-dd8cdc15`<br>`pgu-storymode-storing-energy-748-rgboff-2fe6156e`<br>`pgu-storymode-storing-energy-1375-rgboff-05d7ee0e` |
| STAGED | RGB7 | Hi-Nu Slave 7 RGB7 (3 粒) 腰甲訊號燈。 | `SpecificColorPattern` | `pgu-storymode-storing-energy-1378-specificcolorpattern-e4f4d1ab` |
| STAGED | RGB8 | Hi-Nu Slave 7 RGB8 (右後裙甲; 腳底燈) 快插 白線 2020 燈帶 42 粒。 | `footplatev2` | `pgu-storymode-storing-energy-412-footplatev2-25a43014`<br>`pgu-storymode-storing-energy-751-footplatev2-1086ed6f`<br>`pgu-storymode-storing-energy-1385-footplatev2-2e4e8f01` |

### storyMode_2

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | PCA PWM0 CH channel (loop 0..5 inclusive) | Hi-Nu Slave 7 腰甲 RGB — PGU Slave 6 RGB source. ／ Hi-Nu Slave 7 PWM0 CH0-5 (0x50) 左／右前裙甲白燈：低亮長亮。 | `chOn` | `pgu-storymode-2-407-chon-028b04c2`<br>`pgu-storymode-2-954-chon-05e1bcdb`<br>`pgu-storymode-2-1011-chon-ef256b52`<br>`pgu-storymode-2-1068-chon-05785dba`<br>`pgu-storymode-2-1126-chon-58944df7` |
| STAGED | PCA PWM0 CH channel (loop 6..7 inclusive) | Hi-Nu Slave 7 PWM0 CH6-7 (0x50) 左／右前裙甲暖白燈：漸進閃爍。 | `chProgressiveFlash` | `pgu-storymode-2-412-chprogressiveflash-73091e72`<br>`pgu-storymode-2-959-chprogressiveflash-b8fd85d9`<br>`pgu-storymode-2-1016-chprogressiveflash-4f3ae464`<br>`pgu-storymode-2-1073-chprogressiveflash-4de12128`<br>`pgu-storymode-2-1131-chprogressiveflash-443c868a` |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `gradientVentPalette` | `pgu-storymode-2-417-gradientventpalette-4e54b991` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `gradientVentPalette` | `pgu-storymode-2-459-gradientventpalette-75bcbbaf` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `SpecificColorPattern` | `pgu-storymode-2-437-specificcolorpattern-aa9709aa` |
| STAGED | RGB7 | UNCONFIRMED COMPONENT — RGB7 | `SpecificColorPattern` | `pgu-storymode-2-442-specificcolorpattern-a298e40e` |
| STAGED | RGB8 | Hi-Nu Slave 7 RGB8 (右後裙甲; 腳底燈) 快插 白線 2020 燈帶 42 粒。 | `footplatev2` | `pgu-storymode-2-448-footplatev2-cf1345f8` |

### storyMode_plasma

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | PCA PWM0 CH channel (loop 0..5 inclusive) | Hi-Nu Slave 7 PWM0 CH0-5 (0x50) 左／右前裙甲白燈：低亮長亮。 | `chOn` | `pgu-storymode-plasma-202-chon-f253e8d7`<br>`pgu-storymode-plasma-316-chon-1d69dfda`<br>`pgu-storymode-plasma-431-chon-91dbd515`<br>`pgu-storymode-plasma-658-chon-b07be8a1`<br>`pgu-storymode-plasma-774-chon-19ce4f17` |
| STAGED | PCA PWM0 CH channel (loop 6..7 inclusive) | Hi-Nu Slave 7 PWM0 CH6-7 (0x50) 左／右前裙甲暖白燈：漸進閃爍。 | `chProgressiveFlash` | `pgu-storymode-plasma-207-chprogressiveflash-9af37a38`<br>`pgu-storymode-plasma-321-chprogressiveflash-b5af0f87`<br>`pgu-storymode-plasma-436-chprogressiveflash-f623be9f`<br>`pgu-storymode-plasma-663-chprogressiveflash-41662028`<br>`pgu-storymode-plasma-779-chprogressiveflash-bf262286` |
| STAGED | RGB3 | Hi-Nu Slave 7 腰甲 RGB — PGU Slave 6 RGB source. ／ Hi-Nu Slave 7 RGB3 未接燈帶（-1 粒），保持關閉。 | `rgbOff` | `pgu-storymode-plasma-633-rgboff-c457afba` |
| STAGED | RGB4 | Hi-Nu Slave 7 RGB4 未接燈帶（-1 粒），保持關閉。 | `rgbOff` | `pgu-storymode-plasma-636-rgboff-401d5eef` |
| STAGED | RGB7 | Hi-Nu Slave 7 RGB7 (3 粒) 腰甲訊號燈。 | `SpecificColorPattern` | `pgu-storymode-plasma-639-specificcolorpattern-1bfbefed` |
| STAGED | RGB8 | Hi-Nu Slave 7 RGB8 (右後裙甲; 腳底燈) 快插 白線 2020 燈帶 42 粒。 | `footplatev2` | `pgu-storymode-plasma-646-footplatev2-bfd522b0` |
| STAGED | RGB8 | Hi-Nu Slave 7 腰甲 RGB — PGU Slave 6 RGB source. ／ Hi-Nu Slave 7 RGB8 (右後裙甲; 腳底燈) 快插 白線 2020 燈帶 42 粒。 | `footplatev2` | `pgu-storymode-plasma-190-footplatev2-16c23544`<br>`pgu-storymode-plasma-304-footplatev2-3521fb58`<br>`pgu-storymode-plasma-419-footplatev2-1eec526a`<br>`pgu-storymode-plasma-762-footplatev2-d5085486` |

### storyMode_trans_am

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | PCA PWM0 CH channel (loop 0..5 inclusive) | Hi-Nu Slave 7 PWM0 CH0-5 (0x50) 左／右前裙甲白燈：低亮長亮。 | `chOn` | `pgu-storymode-trans-am-346-chon-0fef02fc` |
| STAGED | PCA PWM0 CH channel (loop 6..7 inclusive) | Hi-Nu Slave 7 PWM0 CH6-7 (0x50) 左／右前裙甲暖白燈：漸進閃爍。 | `chProgressiveFlash` | `pgu-storymode-trans-am-351-chprogressiveflash-46532838` |
| STAGED | RGB1 | Hi-Nu Slave 7 腰甲 RGB — PGU Slave 6 RGB source. | `GN_Drive_Running` | `pgu-storymode-trans-am-270-gn-drive-running-5f2006ec` |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `gradientVentPalette`、`randomFillAll_V2` | `pgu-storymode-trans-am-286-randomfillall-v2-3848566b`<br>`pgu-storymode-trans-am-295-gradientventpalette-34975398` |
| STAGED | RGB3 | Hi-Nu Slave 7 RGB3 未接燈帶（-1 粒），保持關閉。 | `rgbOff` | `pgu-storymode-trans-am-320-rgboff-775f2eb4` |
| STAGED | RGB4 | Hi-Nu Slave 7 RGB4 未接燈帶（-1 粒），保持關閉。 | `rgbOff` | `pgu-storymode-trans-am-323-rgboff-c29e155a` |
| STAGED | RGB7 | Hi-Nu Slave 7 RGB7 (3 粒) 腰甲訊號燈。 | `SpecificColorPattern` | `pgu-storymode-trans-am-326-specificcolorpattern-59f00dab` |
| STAGED | RGB8 | Hi-Nu Slave 7 RGB8 (右後裙甲; 腳底燈) 快插 白線 2020 燈帶 42 粒。 | `footplatev2` | `pgu-storymode-trans-am-333-footplatev2-14fefcf0` |

### storyMode_3

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | PCA PWM0 CH channel (loop 0..5 inclusive) | Hi-Nu Slave 7 PWM0 CH0-5 (0x50) 左／右前裙甲白燈：低亮長亮。 | `chOn` | `pgu-storymode-3-499-chon-dd672744` |
| STAGED | PCA PWM0 CH channel (loop 6..7 inclusive) | Hi-Nu Slave 7 PWM0 CH6-7 (0x50) 左／右前裙甲暖白燈：漸進閃爍。 | `chProgressiveFlash` | `pgu-storymode-3-504-chprogressiveflash-ffe7c909` |
| STAGED | RGB2 | Hi-Nu Slave 7 腰甲 RGB — PGU Slave 6 RGB source. ／ Hi-Nu Slave 7 RGB2 (左/右後裙甲; 散氣) 快插 藍線 18 粒：共用腰甲 vent slot 3。 | `gradientVentPalette` | `pgu-storymode-3-452-gradientventpalette-35584fa0` |
| STAGED | RGB3 | Hi-Nu Slave 7 RGB3 未接燈帶（-1 粒），保持關閉。 | `rgbOff` | `pgu-storymode-3-473-rgboff-2b4abab1` |
| STAGED | RGB4 | Hi-Nu Slave 7 RGB4 未接燈帶（-1 粒），保持關閉。 | `rgbOff` | `pgu-storymode-3-476-rgboff-c8c6f901` |
| STAGED | RGB7 | Hi-Nu Slave 7 RGB7 (3 粒) 腰甲訊號燈。 | `SpecificColorPattern` | `pgu-storymode-3-479-specificcolorpattern-012e2b2d` |
| STAGED | RGB8 | Hi-Nu Slave 7 RGB8 (右後裙甲; 腳底燈) 快插 白線 2020 燈帶 42 粒。 | `footplatev2` | `pgu-storymode-3-486-footplatev2-5079d51f` |

### storyMode_idle

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | PCA PWM0 CH channel (loop 0..5 inclusive) | Hi-Nu Slave 7 PWM0 CH0-5 (0x50) 左／右前裙甲白燈：Idle 低亮長亮。 | `chOn` | `pgu-storymode-idle-133-chon-ea5ca92e` |
| STAGED | PCA PWM0 CH channel (loop 6..7 inclusive) | Hi-Nu Slave 7 PWM0 CH6-7 (0x50) 左／右前裙甲暖白燈：Idle 漸進閃爍。 | `chProgressiveFlash` | `pgu-storymode-idle-139-chprogressiveflash-7e9540df` |

### storyMode_motor

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | Motor／servo channel '0' | UNCONFIRMED COMPONENT — Motor／servo channel '0' | `chServoHold`、`chServoStop` | `pgu-storymode-motor-810-chservostop-13e4fc14`<br>`pgu-storymode-motor-821-chservohold-6a34a8e4`<br>`pgu-storymode-motor-830-chservohold-0a8c5a73` |
| STAGED | Motor／servo channel '1' | UNCONFIRMED COMPONENT — Motor／servo channel '1' | `chServoStop` | `pgu-storymode-motor-795-chservostop-74dd9687` |
| STAGED | Motor／servo channel 'i' | UNCONFIRMED COMPONENT — Motor／servo channel 'i' | `chServoHold` | `pgu-storymode-motor-1812-chservohold-c0aba602`<br>`pgu-storymode-motor-2279-chservohold-ccee32e3` |
| STAGED | PCA PWM0 CH 0 | 0s: body white PCA + eyes — Slave 7/8 PCA white markers. | `chOn` | `pgu-storymode-motor-719-chon-c1109568` |
| STAGED | PCA PWM0 CH 0 | UNCONFIRMED COMPONENT — PCA PWM0 CH 0 | `chOn` | `pgu-storymode-motor-813-chon-1490ac28`<br>`pgu-storymode-motor-824-chon-f3ae8be7`<br>`pgu-storymode-motor-1806-chon-cff67cbf`<br>`pgu-storymode-motor-2273-chon-bb3649d8` |
| STAGED | PCA PWM0 CH 1 | UNCONFIRMED COMPONENT — PCA PWM0 CH 1 | `chOn` | `pgu-storymode-motor-720-chon-2402ae4f`<br>`pgu-storymode-motor-814-chon-6de10107`<br>`pgu-storymode-motor-825-chon-d816c83b`<br>`pgu-storymode-motor-1807-chon-bdba57d9`<br>`pgu-storymode-motor-2274-chon-71a18e08` |
| STAGED | PCA PWM0 CH 15 | Slave 7 PWM0 CH15 (0x56) 未接燈。 | `chBoosterFade` | `pgu-storymode-motor-902-chboosterfade-5c73a21d` |
| STAGED | PCA PWM0 CH 4 | UNCONFIRMED COMPONENT — PCA PWM0 CH 4 | `chOn` | `pgu-storymode-motor-721-chon-5c3f2baf`<br>`pgu-storymode-motor-815-chon-8e8a3e6f`<br>`pgu-storymode-motor-826-chon-2791601a`<br>`pgu-storymode-motor-1808-chon-a0619a71`<br>`pgu-storymode-motor-2275-chon-2560789d` |
| STAGED | PCA PWM0 CH 5 | UNCONFIRMED COMPONENT — PCA PWM0 CH 5 | `chOn` | `pgu-storymode-motor-722-chon-dbd0c461`<br>`pgu-storymode-motor-816-chon-88550335`<br>`pgu-storymode-motor-827-chon-d0790a4b`<br>`pgu-storymode-motor-1809-chon-85a4a247`<br>`pgu-storymode-motor-2276-chon-071cd349` |
| STAGED | PCA PWM0 CH 7 | UNCONFIRMED COMPONENT — PCA PWM0 CH 7 | `chOn` | `pgu-storymode-motor-723-chon-201e1ce3`<br>`pgu-storymode-motor-817-chon-82e35056`<br>`pgu-storymode-motor-828-chon-8239723a`<br>`pgu-storymode-motor-1810-chon-9e5b09ab`<br>`pgu-storymode-motor-2277-chon-105dfcb2` |
| STAGED | PCA PWM0 CH 8 | UNCONFIRMED COMPONENT — PCA PWM0 CH 8 | `chOn` | `pgu-storymode-motor-724-chon-a69e72ed`<br>`pgu-storymode-motor-818-chon-0039beb0`<br>`pgu-storymode-motor-829-chon-87134908`<br>`pgu-storymode-motor-1811-chon-a2cfd940`<br>`pgu-storymode-motor-2278-chon-ffbe69e8` |
| STAGED | PCA PWM0 CH i (loop 0..12 inclusive) | Slave 7 PWM0 CH0-12 (0x56) 左腳掌，白，2粒；左腳掌腳跟，紅，2粒；左腳掌後跟，紅，3粒；左腳掌偽漩渦，黃，8粒。 | `chOn` | `pgu-storymode-motor-899-chon-5172bbcc` |
| STAGED | RGB runtime target 'selectedRgb4' | 3s: all signals green — Slave 7/8 RGB4 signal LEDs. | `SpecificColorPattern` | `pgu-storymode-motor-712-specificcolorpattern-75617f09` |
| STAGED | RGB runtime target 'selectedRgb4' | UNCONFIRMED COMPONENT — RGB runtime target 'selectedRgb4' | `SpecificColorPattern` | `pgu-storymode-motor-797-specificcolorpattern-a80fef81`<br>`pgu-storymode-motor-803-specificcolorpattern-296ea49b`<br>`pgu-storymode-motor-1802-specificcolorpattern-41aa8407`<br>`pgu-storymode-motor-2269-specificcolorpattern-ccdb69b3` |
| STAGED | RGB1 | UNCONFIRMED COMPONENT — RGB1 | `whiteSwipe` | `pgu-storymode-motor-836-whiteswipe-2be99eea` |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `VentEffect`、`randomFillAll_V2` | `pgu-storymode-motor-848-randomfillall-v2-158477c3`<br>`pgu-storymode-motor-852-venteffect-1be7873c` |
| STAGED | RGB3 | Slave 7/8 RGB3 — foot turbine. | `turbine_v3_sound` | `pgu-storymode-motor-864-turbine-v3-sound-71c3bd4a` |
| STAGED | RGB7 | Slave 7/8 RGB7/RGB8 — footplate effect. | `footplatev2` | `pgu-storymode-motor-877-footplatev2-7989e6ae` |
| STAGED | RGB8 | UNCONFIRMED COMPONENT — RGB8 | `footplatev2` | `pgu-storymode-motor-887-footplatev2-06b5a33a` |

### storyMode_motor_reset

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | Motor／servo channel '0' | UNCONFIRMED COMPONENT — Motor／servo channel '0' | `chServoHold`、`chServoStop` | `pgu-storymode-motor-reset-751-chservohold-35c3811e`<br>`pgu-storymode-motor-reset-915-chservohold-f3df6fa1`<br>`pgu-storymode-motor-reset-1085-chservohold-697a6f63`<br>`pgu-storymode-motor-reset-1089-chservohold-04c1ddad`<br>`pgu-storymode-motor-reset-1091-chservostop-35cc3ebf` |
| STAGED | Motor／servo channel '1' | UNCONFIRMED COMPONENT — Motor／servo channel '1' | `chServoStop` | `pgu-storymode-motor-reset-752-chservostop-33574f8e`<br>`pgu-storymode-motor-reset-916-chservostop-39bf1dd1`<br>`pgu-storymode-motor-reset-1083-chservostop-cc49e144` |
| STAGED | Motor／servo channel 'i' | UNCONFIRMED COMPONENT — Motor／servo channel 'i' | `chServoHold` | `pgu-storymode-motor-reset-472-chservohold-d4cd8c0d` |
| STAGED | PCA PWM0 CH 0 | UNCONFIRMED COMPONENT — PCA PWM0 CH 0 | `chOn` | `pgu-storymode-motor-reset-466-chon-cfaf433a`<br>`pgu-storymode-motor-reset-745-chon-a110993b`<br>`pgu-storymode-motor-reset-909-chon-e9a9f480`<br>`pgu-storymode-motor-reset-1077-chon-924bf56a` |
| STAGED | PCA PWM0 CH 1 | UNCONFIRMED COMPONENT — PCA PWM0 CH 1 | `chOn` | `pgu-storymode-motor-reset-467-chon-4a7b88bd`<br>`pgu-storymode-motor-reset-746-chon-aad8dc04`<br>`pgu-storymode-motor-reset-910-chon-b3c082e8`<br>`pgu-storymode-motor-reset-1078-chon-8fc53683` |
| STAGED | PCA PWM0 CH 4 | UNCONFIRMED COMPONENT — PCA PWM0 CH 4 | `chOn` | `pgu-storymode-motor-reset-468-chon-d51e79dd`<br>`pgu-storymode-motor-reset-747-chon-9d939445`<br>`pgu-storymode-motor-reset-911-chon-9cc8f9a1`<br>`pgu-storymode-motor-reset-1079-chon-e7fc4e2a` |
| STAGED | PCA PWM0 CH 5 | UNCONFIRMED COMPONENT — PCA PWM0 CH 5 | `chOn` | `pgu-storymode-motor-reset-469-chon-8960558a`<br>`pgu-storymode-motor-reset-748-chon-dc9f9db7`<br>`pgu-storymode-motor-reset-912-chon-b99ca3ce`<br>`pgu-storymode-motor-reset-1080-chon-b627b797` |
| STAGED | PCA PWM0 CH 7 | UNCONFIRMED COMPONENT — PCA PWM0 CH 7 | `chOn` | `pgu-storymode-motor-reset-470-chon-3c8514ea`<br>`pgu-storymode-motor-reset-749-chon-9706b244`<br>`pgu-storymode-motor-reset-913-chon-cee2e4da`<br>`pgu-storymode-motor-reset-1081-chon-b0cef13a` |
| STAGED | PCA PWM0 CH 8 | UNCONFIRMED COMPONENT — PCA PWM0 CH 8 | `chOn` | `pgu-storymode-motor-reset-471-chon-020cb377`<br>`pgu-storymode-motor-reset-750-chon-13441f77`<br>`pgu-storymode-motor-reset-914-chon-dae91714`<br>`pgu-storymode-motor-reset-1082-chon-df48bf97` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `SpecificColorPattern` | `pgu-storymode-motor-reset-462-specificcolorpattern-eb3018e9`<br>`pgu-storymode-motor-reset-741-specificcolorpattern-2c747dc5`<br>`pgu-storymode-motor-reset-905-specificcolorpattern-2cdc2d28`<br>`pgu-storymode-motor-reset-1073-specificcolorpattern-94357ef4` |

## Slave 8

### storyMode_develop

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB1 | Hi-Nu Slave 8/10 RGB1/2/7/8：Develop 模式只保留 42 粒訊號燈。 | `rgbOff` | `pgu-storymode-develop-194-rgboff-2d3f0b2c` |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `rgbOff` | `pgu-storymode-develop-195-rgboff-dfa78c9c` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `rgbOff` | `pgu-storymode-develop-196-rgboff-53c1c290` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `SpecificColorPattern` | `pgu-storymode-develop-200-specificcolorpattern-c57094f5` |
| STAGED | RGB7 | UNCONFIRMED COMPONENT — RGB7 | `rgbOff` | `pgu-storymode-develop-197-rgboff-ee54a117` |
| STAGED | RGB8 | UNCONFIRMED COMPONENT — RGB8 | `rgbOff` | `pgu-storymode-develop-198-rgboff-ceab810f` |
| STAGED | Runtime／group target 'espLed[channel]' | GPIO48 白燈 4 粒；GPIO47／45／42 紅燈：Develop 模式低亮長亮。 | `chOn` | `pgu-storymode-develop-209-chon-5d047c79` |

### storyMode_signals

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB4 | Hi-Nu Slave 8/10 RGB4：42 粒訊號燈共用完整 Repair profile。 | `SpecificColorPattern` | `pgu-storymode-signals-176-specificcolorpattern-d94838a9` |
| STAGED | Runtime／group target 'espLed[channel]' | Hi-Nu Slave 8/10 GPIO48 白燈 4 粒；GPIO47／45／42 紅燈：進入 Signals 立即關閉。 | `chOff` | `pgu-storymode-signals-35-choff-6de79856` |

### storyMode_0_v1

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB1 | Hi-Nu Slave 8/10 左右腿 RGB：兩側固定使用相同 RGB pin。 | `randomLightUp`、`rgbOn` | `pgu-storymode-0-v1-1339-randomlightup-000ae4ad`<br>`pgu-storymode-0-v1-1800-randomlightup-95b36afc`<br>`pgu-storymode-0-v1-2470-rgbon-2c67ef52`<br>`pgu-storymode-0-v1-3026-rgbon-4954e367` |
| STAGED | RGB1 | Hi-Nu Slave 8/10 左右腿上段 RGB — shared PGU Slave 7 RGB source. | `randomFlashWithGap_multiple`、`randomLightUp` | `pgu-storymode-0-v1-480-randomflashwithgap-multiple-5cee67bb`<br>`pgu-storymode-0-v1-862-randomflashwithgap-multiple-c796a33e`<br>`pgu-storymode-0-v1-2232-randomlightup-897fa487` |
| STAGED | RGB10 | UNCONFIRMED COMPONENT — RGB10 | `randomFlashWithGap_multiple` | `pgu-storymode-0-v1-529-randomflashwithgap-multiple-35f38906` |
| STAGED | RGB11 | UNCONFIRMED COMPONENT — RGB11 | `randomFlashWithGap_multiple` | `pgu-storymode-0-v1-536-randomflashwithgap-multiple-6e452c5a` |
| STAGED | RGB12 | UNCONFIRMED COMPONENT — RGB12 | `randomFlashWithGap_multiple` | `pgu-storymode-0-v1-543-randomflashwithgap-multiple-9b5fec0d` |
| STAGED | RGB13 | UNCONFIRMED COMPONENT — RGB13 | `randomFlashWithGap_multiple` | `pgu-storymode-0-v1-550-randomflashwithgap-multiple-5cc38ea4` |
| STAGED | RGB16 | UNCONFIRMED COMPONENT — RGB16 | `randomFlashWithGap_multiple` | `pgu-storymode-0-v1-557-randomflashwithgap-multiple-02d938ff` |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v1-487-randomflashwithgap-multiple-bf13acc6`<br>`pgu-storymode-0-v1-869-randomflashwithgap-multiple-9b996d1b`<br>`pgu-storymode-0-v1-1346-randomlightup-640de706`<br>`pgu-storymode-0-v1-1807-randomlightup-9ff938bb`<br>`pgu-storymode-0-v1-2239-randomlightup-747ca70f`<br>`pgu-storymode-0-v1-2472-rgbon-9629c27a`<br>`pgu-storymode-0-v1-3028-rgbon-4a618cff` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v1-494-randomflashwithgap-multiple-53640921`<br>`pgu-storymode-0-v1-876-randomflashwithgap-multiple-b1de5839`<br>`pgu-storymode-0-v1-1353-randomlightup-1cdc2a0f`<br>`pgu-storymode-0-v1-1814-randomlightup-118b8350`<br>`pgu-storymode-0-v1-2246-randomlightup-c57aa0be`<br>`pgu-storymode-0-v1-2474-rgbon-486c859d`<br>`pgu-storymode-0-v1-3030-rgbon-36d0ad85` |
| STAGED | RGB4 | Hi-Nu Slave 8/10 RGB4 (42 粒) 腿部訊號：與其他腿部 RGB 同步長亮。 | `rgbOn` | `pgu-storymode-0-v1-2477-rgbon-97ce6031`<br>`pgu-storymode-0-v1-3033-rgbon-4a915a05` |
| STAGED | RGB4 | Hi-Nu Slave 8/10 RGB4 (42 粒) 腿部訊號：與其他腿部 RGB 同步隨機亮起。 | `randomLightUp` | `pgu-storymode-0-v1-1361-randomlightup-d4f3fe3c` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `randomFlashWithGap_multiple`、`randomLightUp` | `pgu-storymode-0-v1-501-randomflashwithgap-multiple-c3de7391`<br>`pgu-storymode-0-v1-883-randomflashwithgap-multiple-815c841c`<br>`pgu-storymode-0-v1-1821-randomlightup-24128e52`<br>`pgu-storymode-0-v1-2253-randomlightup-b9277b73` |
| STAGED | RGB7 | UNCONFIRMED COMPONENT — RGB7 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v1-508-randomflashwithgap-multiple-ada694bc`<br>`pgu-storymode-0-v1-890-randomflashwithgap-multiple-bad51f9c`<br>`pgu-storymode-0-v1-1368-randomlightup-dcced8b6`<br>`pgu-storymode-0-v1-1828-randomlightup-2d158799`<br>`pgu-storymode-0-v1-2260-randomlightup-17782b3b`<br>`pgu-storymode-0-v1-2479-rgbon-5bc4823d`<br>`pgu-storymode-0-v1-3035-rgbon-1803500b` |
| STAGED | RGB8 | UNCONFIRMED COMPONENT — RGB8 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v1-515-randomflashwithgap-multiple-2a4fae3a`<br>`pgu-storymode-0-v1-897-randomflashwithgap-multiple-079dc7ab`<br>`pgu-storymode-0-v1-1375-randomlightup-06678456`<br>`pgu-storymode-0-v1-1835-randomlightup-7b140595`<br>`pgu-storymode-0-v1-2267-randomlightup-141ac05a`<br>`pgu-storymode-0-v1-2481-rgbon-ca78834a`<br>`pgu-storymode-0-v1-3037-rgbon-1f41bba2` |
| STAGED | RGB9 | UNCONFIRMED COMPONENT — RGB9 | `randomFlashWithGap_multiple`、`randomLightUp` | `pgu-storymode-0-v1-522-randomflashwithgap-multiple-3770009e`<br>`pgu-storymode-0-v1-904-randomflashwithgap-multiple-31ad0ebc`<br>`pgu-storymode-0-v1-1382-randomlightup-aaa8ff31`<br>`pgu-storymode-0-v1-1842-randomlightup-b70358c9` |

### storyMode_awakening_3

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB2 | Hi-Nu Slave 8/10 左右腿上段 RGB — shared PGU Slave 7 RGB source. | `rgbOff` | `pgu-storymode-awakening-3-330-rgboff-9a3bb44d` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `rgbOff` | `pgu-storymode-awakening-3-332-rgboff-4b1eacd1` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `rgbOff` | `pgu-storymode-awakening-3-334-rgboff-1c1faa31` |
| STAGED | RGB7 | UNCONFIRMED COMPONENT — RGB7 | `rgbOff` | `pgu-storymode-awakening-3-336-rgboff-19e7c65f` |
| STAGED | RGB8 | UNCONFIRMED COMPONENT — RGB8 | `rgbOff` | `pgu-storymode-awakening-3-338-rgboff-3d951ed3` |
| STAGED | Runtime／group target 'espLed[0]' | (左／右小腿) 白、紅及大腿後甲燈：espLed[0-3] 與 RGB1 同週期呼吸。 | `chBreath` | `pgu-storymode-awakening-3-341-chbreath-b6ab97d9` |
| STAGED | Runtime／group target 'espLed[1]' | UNCONFIRMED COMPONENT — Runtime／group target 'espLed[1]' | `chBreath` | `pgu-storymode-awakening-3-342-chbreath-8c002e46` |
| STAGED | Runtime／group target 'espLed[2]' | UNCONFIRMED COMPONENT — Runtime／group target 'espLed[2]' | `chBreath` | `pgu-storymode-awakening-3-343-chbreath-ef44fd2c` |
| STAGED | Runtime／group target 'espLed[3]' | UNCONFIRMED COMPONENT — Runtime／group target 'espLed[3]' | `chBreath` | `pgu-storymode-awakening-3-344-chbreath-c84fbad8` |

### storyMode_activation

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `gradientVentPalette`、`randomFillAll_V2` | `pgu-storymode-activation-524-randomfillall-v2-760ba794`<br>`pgu-storymode-activation-527-gradientventpalette-f8d3c801` |
| STAGED | RGB4 | Hi-Nu Slave 8/10 RGB4：共用 42 粒腿部訊號 Normal profile。 | `SpecificColorPattern` | `pgu-storymode-activation-516-specificcolorpattern-a5ab43e3` |
| STAGED | RGB7 | Slave 8 RGB7 (63粒) 左膝關節／大漩渦：覺醒渦輪。 | `turbine_v3` | `pgu-storymode-activation-544-turbine-v3-0c653df2` |
| STAGED | RGB8 | Slave 8 RGB8 (49粒) 左腳腳底燈：覺醒 footplate。 | `footplatev2` | `pgu-storymode-activation-556-footplatev2-79125c7f` |
| STAGED | Runtime／group target 'espLed[channel]' | GPIO48 白燈 4 粒；GPIO47／45／42 紅燈：Activation 模式低亮長亮。 | `chOn` | `pgu-storymode-activation-572-chon-98ce9bfb` |

### storyMode_0_v2

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB1 | Hi-Nu Slave 8/10 左右腿 RGB：兩側固定使用相同 RGB pin。 | `randomLightUp`、`rgbOn` | `pgu-storymode-0-v2-991-randomlightup-52b7b564`<br>`pgu-storymode-0-v2-1377-randomlightup-938d2f38`<br>`pgu-storymode-0-v2-1734-randomlightup-7b203f2a`<br>`pgu-storymode-0-v2-1953-rgbon-a143406d`<br>`pgu-storymode-0-v2-2139-rgbon-a38e1e6b` |
| STAGED | RGB1 | UNCONFIRMED COMPONENT — RGB1 | `randomFlashWithGap_multiple` | `pgu-storymode-0-v2-592-randomflashwithgap-multiple-dd79f85e` |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v2-599-randomflashwithgap-multiple-e2563ca8`<br>`pgu-storymode-0-v2-998-randomlightup-8414e177`<br>`pgu-storymode-0-v2-1384-randomlightup-800162a9`<br>`pgu-storymode-0-v2-1741-randomlightup-024630b9`<br>`pgu-storymode-0-v2-1955-rgbon-54a31a5d`<br>`pgu-storymode-0-v2-2141-rgbon-9d2ca258` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v2-606-randomflashwithgap-multiple-92dd43b6`<br>`pgu-storymode-0-v2-1005-randomlightup-fc9cbd8b`<br>`pgu-storymode-0-v2-1391-randomlightup-9bc0195a`<br>`pgu-storymode-0-v2-1748-randomlightup-ff17367b`<br>`pgu-storymode-0-v2-1957-rgbon-8ff82eec`<br>`pgu-storymode-0-v2-2143-rgbon-7ca171ed` |
| STAGED | RGB4 | Hi-Nu Slave 8/10 RGB4 (42 粒) 腿部訊號：與其他腿部 RGB 同步長亮。 | `rgbOn` | `pgu-storymode-0-v2-1960-rgbon-83f8d002`<br>`pgu-storymode-0-v2-2146-rgbon-4bc2ff28` |
| STAGED | RGB4 | Hi-Nu Slave 8/10 RGB4 (42 粒) 腿部訊號：與其他腿部 RGB 同步隨機亮起。 | `randomLightUp` | `pgu-storymode-0-v2-1013-randomlightup-674b8fd0`<br>`pgu-storymode-0-v2-1399-randomlightup-bda9756e`<br>`pgu-storymode-0-v2-1756-randomlightup-9f09258d` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `randomFlashWithGap_multiple` | `pgu-storymode-0-v2-613-randomflashwithgap-multiple-e28cee9c` |
| STAGED | RGB7 | UNCONFIRMED COMPONENT — RGB7 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v2-620-randomflashwithgap-multiple-32ba20d7`<br>`pgu-storymode-0-v2-1020-randomlightup-a7451ee3`<br>`pgu-storymode-0-v2-1406-randomlightup-c7519570`<br>`pgu-storymode-0-v2-1763-randomlightup-e94aaf65`<br>`pgu-storymode-0-v2-1962-rgbon-880b74c3`<br>`pgu-storymode-0-v2-2148-rgbon-216fa10d` |
| STAGED | RGB8 | UNCONFIRMED COMPONENT — RGB8 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v2-627-randomflashwithgap-multiple-2c3b0208`<br>`pgu-storymode-0-v2-1027-randomlightup-5fad5866`<br>`pgu-storymode-0-v2-1413-randomlightup-f27f6561`<br>`pgu-storymode-0-v2-1770-randomlightup-11702929`<br>`pgu-storymode-0-v2-1964-rgbon-a1751b28`<br>`pgu-storymode-0-v2-2150-rgbon-a648b183` |
| STAGED | RGB9 | UNCONFIRMED COMPONENT — RGB9 | `randomLightUp` | `pgu-storymode-0-v2-1034-randomlightup-6bac79d3`<br>`pgu-storymode-0-v2-1420-randomlightup-18782fa3` |
| STAGED | Runtime／group target 'strips' | UNCONFIRMED COMPONENT — Runtime／group target 'strips' | `randomFlashFixedCount_multiple` | `pgu-storymode-0-v2-262-randomflashfixedcount-multiple-290d18b8` |

### storyMode_storing_energy

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB1 | Hi-Nu Slave 8/10 左右腿 RGB：滿能量時共用同一套效果與接線。 | `renderSlave78Rgb1StorySpecificColor` | `pgu-storymode-storing-energy-1417-renderslave78rgb1storyspecificcolor-ed28ee22` |
| STAGED | RGB1 | Hi-Nu Slave 8/10 左右腿上段 RGB — shared PGU Slave 7 RGB source. | `paletteWave_80Percent_SpecialWave` | `pgu-storymode-storing-energy-779-palettewave-80percent-specialwave-08e4d8a1` |
| STAGED | RGB2 | Hi-Nu Slave 8/10 RGB2/3/4：儲能初始化時保持關閉。 | `rgbOff` | `pgu-storymode-storing-energy-439-rgboff-18c69cf1` |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `GN_Wire_Normal`、`paletteWave_80Percent_SpecialWave` | `pgu-storymode-storing-energy-788-palettewave-80percent-specialwave-0f4b3ddc`<br>`pgu-storymode-storing-energy-1419-gn-wire-normal-1e63e9b7` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `rgbOff` | `pgu-storymode-storing-energy-440-rgboff-620e3b63` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `SpecificColorPattern`、`rgbOff` | `pgu-storymode-storing-energy-442-rgboff-7b05a8ed`<br>`pgu-storymode-storing-energy-809-rgboff-09b587c3`<br>`pgu-storymode-storing-energy-1442-specificcolorpattern-0baaf235` |
| STAGED | RGB7 | Slave 8 RGB7 (63粒) 左膝關節／大漩渦：儲能渦輪。 | `turbine_v3` | `pgu-storymode-storing-energy-798-turbine-v3-f56b6625` |
| STAGED | RGB7 | Slave 8 RGB7 (63粒) 左膝關節／大漩渦：滿能量渦輪。 | `turbine_v3` | `pgu-storymode-storing-energy-1431-turbine-v3-d6177cec` |
| STAGED | RGB8 | Slave 8 RGB8 (49粒) 左腳腳底燈：滿能量 footplate。 | `footplatev2` | `pgu-storymode-storing-energy-1449-footplatev2-a9907858` |
| ON | Runtime／group target 'espLed[channel]' | Hi-Nu Slave 8/10 GPIO48 白燈 4 粒；GPIO47／45／42 紅燈：儲能全程每幀低亮長亮。 | `chOn` | `pgu-storymode-storing-energy-305-chon-e22625cf` |

### storyMode_2

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `gradientVentPalette`、`randomFillAll_V2` | `pgu-storymode-2-486-randomfillall-v2-ee59ebb1`<br>`pgu-storymode-2-495-gradientventpalette-945968f1` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `SpecificColorPattern` | `pgu-storymode-2-543-specificcolorpattern-8a4df028` |
| STAGED | RGB7 | Slave 8 RGB7 (63粒) 左膝關節／大漩渦：長著模式渦輪。 | `turbine_v3` | `pgu-storymode-2-516-turbine-v3-a54a0ccb` |
| STAGED | RGB8 | Slave 8 RGB8 (49粒) 左腳腳底燈：長著模式 footplate。 | `footplatev2` | `pgu-storymode-2-529-footplatev2-42349674` |
| STAGED | Runtime／group target 'espLed[channel]' | GPIO48 白燈 4 粒；GPIO47／45／42 紅燈：Normal 模式低亮長亮。 | `chOn` | `pgu-storymode-2-550-chon-06ce96d3` |

### storyMode_plasma

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB4 | Hi-Nu Slave 8/10 RGB4：共用 42 粒腿部訊號 Normal profile。 | `SpecificColorPattern` | `pgu-storymode-plasma-673-specificcolorpattern-bbbb180d` |
| ON | Runtime／group target 'espLed[channel]' | Hi-Nu Slave 8/10 GPIO48 白燈 4 粒；GPIO47／45／42 紅燈：Plasma 全程每幀低亮長亮。 | `chOn` | `pgu-storymode-plasma-62-chon-77ce5cc1` |

### storyMode_trans_am

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB1 | Hi-Nu Slave 8/10 左右腿 RGB：兩側共用同一套效果與接線。 | `GN_Drive_Running` | `pgu-storymode-trans-am-361-gn-drive-running-a1c9c2d3` |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `GN_Wire_TransAM` | `pgu-storymode-trans-am-372-gn-wire-transam-fad757a0` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `SpecificColorPattern` | `pgu-storymode-trans-am-412-specificcolorpattern-54da8473` |
| STAGED | RGB7 | Slave 8 RGB7 (63粒) 左膝關節／大漩渦：Trans-Am 渦輪。 | `turbine_v3` | `pgu-storymode-trans-am-385-turbine-v3-18ef4d66` |
| STAGED | RGB8 | Slave 8 RGB8 (49粒) 左腳腳底燈：Trans-Am footplate。 | `footplatev2` | `pgu-storymode-trans-am-398-footplatev2-4324bcfd` |
| STAGED | Runtime／group target 'espLed[channel]' | GPIO48 白燈 4 粒；GPIO47／45／42 紅燈：Trans-Am 模式低亮長亮。 | `chOn` | `pgu-storymode-trans-am-420-chon-add4fee6` |

### storyMode_3

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB2 | Hi-Nu Slave 8/10 左右腿上段 RGB — shared PGU Slave 7 RGB source. | `gradientVentPalette` | `pgu-storymode-3-514-gradientventpalette-11629449` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `SpecificColorPattern` | `pgu-storymode-3-562-specificcolorpattern-567c9d50` |
| STAGED | RGB7 | Slave 8 RGB7 (63粒) 左膝關節／大漩渦：呼吸模式渦輪。 | `turbine_v3` | `pgu-storymode-3-535-turbine-v3-053276bf` |
| STAGED | RGB8 | Slave 8 RGB8 (49粒) 左腳腳底燈：呼吸模式 footplate。 | `footplatev2` | `pgu-storymode-3-548-footplatev2-88571b47` |
| STAGED | Runtime／group target 'espLed[channel]' | GPIO48 白燈 4 粒；GPIO47／45／42 紅燈：呼吸模式低亮長亮。 | `chOn` | `pgu-storymode-3-570-chon-b5fd1004` |

### storyMode_idle

OFF／no direct call in this Slave context。

### storyMode_motor

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | All PCA／channel output | Slave 8 GPIO48／47／45／42 單色燈：保持 20%。 | `chOnAll` | `pgu-storymode-motor-551-chonall-56d52b7c` |
| STAGED | All PCA／channel output | Slave 8 GPIO48／47／45／42 單色燈：同步淡入至 20%。 | `chOnAll` | `pgu-storymode-motor-357-chonall-bb7c807b` |
| STAGED | Motor／servo channel '0' | UNCONFIRMED COMPONENT — Motor／servo channel '0' | `chServoHold`、`chServoStop` | `pgu-storymode-motor-810-chservostop-13e4fc14`<br>`pgu-storymode-motor-821-chservohold-6a34a8e4`<br>`pgu-storymode-motor-830-chservohold-0a8c5a73` |
| STAGED | Motor／servo channel '1' | UNCONFIRMED COMPONENT — Motor／servo channel '1' | `chServoStop` | `pgu-storymode-motor-795-chservostop-74dd9687` |
| STAGED | Motor／servo channel 'i' | UNCONFIRMED COMPONENT — Motor／servo channel 'i' | `chServoHold` | `pgu-storymode-motor-1812-chservohold-c0aba602`<br>`pgu-storymode-motor-2279-chservohold-ccee32e3` |
| STAGED | PCA PWM0 CH 0 | 0s: body white PCA + eyes — Slave 7/8 PCA white markers. | `chOn` | `pgu-storymode-motor-719-chon-c1109568` |
| STAGED | PCA PWM0 CH 0 | UNCONFIRMED COMPONENT — PCA PWM0 CH 0 | `chOn` | `pgu-storymode-motor-813-chon-1490ac28`<br>`pgu-storymode-motor-824-chon-f3ae8be7`<br>`pgu-storymode-motor-1806-chon-cff67cbf`<br>`pgu-storymode-motor-2273-chon-bb3649d8` |
| STAGED | PCA PWM0 CH 1 | UNCONFIRMED COMPONENT — PCA PWM0 CH 1 | `chOn` | `pgu-storymode-motor-720-chon-2402ae4f`<br>`pgu-storymode-motor-814-chon-6de10107`<br>`pgu-storymode-motor-825-chon-d816c83b`<br>`pgu-storymode-motor-1807-chon-bdba57d9`<br>`pgu-storymode-motor-2274-chon-71a18e08` |
| STAGED | PCA PWM0 CH 15 | Slave 7 PWM0 CH15 (0x56) 未接燈。 | `chBoosterFade` | `pgu-storymode-motor-902-chboosterfade-5c73a21d` |
| STAGED | PCA PWM0 CH 4 | UNCONFIRMED COMPONENT — PCA PWM0 CH 4 | `chOn` | `pgu-storymode-motor-721-chon-5c3f2baf`<br>`pgu-storymode-motor-815-chon-8e8a3e6f`<br>`pgu-storymode-motor-826-chon-2791601a`<br>`pgu-storymode-motor-1808-chon-a0619a71`<br>`pgu-storymode-motor-2275-chon-2560789d` |
| STAGED | PCA PWM0 CH 5 | UNCONFIRMED COMPONENT — PCA PWM0 CH 5 | `chOn` | `pgu-storymode-motor-722-chon-dbd0c461`<br>`pgu-storymode-motor-816-chon-88550335`<br>`pgu-storymode-motor-827-chon-d0790a4b`<br>`pgu-storymode-motor-1809-chon-85a4a247`<br>`pgu-storymode-motor-2276-chon-071cd349` |
| STAGED | PCA PWM0 CH 7 | UNCONFIRMED COMPONENT — PCA PWM0 CH 7 | `chOn` | `pgu-storymode-motor-723-chon-201e1ce3`<br>`pgu-storymode-motor-817-chon-82e35056`<br>`pgu-storymode-motor-828-chon-8239723a`<br>`pgu-storymode-motor-1810-chon-9e5b09ab`<br>`pgu-storymode-motor-2277-chon-105dfcb2` |
| STAGED | PCA PWM0 CH 8 | UNCONFIRMED COMPONENT — PCA PWM0 CH 8 | `chOn` | `pgu-storymode-motor-724-chon-a69e72ed`<br>`pgu-storymode-motor-818-chon-0039beb0`<br>`pgu-storymode-motor-829-chon-87134908`<br>`pgu-storymode-motor-1811-chon-a2cfd940`<br>`pgu-storymode-motor-2278-chon-ffbe69e8` |
| STAGED | PCA PWM0 CH i (loop 0..12 inclusive) | Slave 7 PWM0 CH0-12 (0x56) 左腳掌，白，2粒；左腳掌腳跟，紅，2粒；左腳掌後跟，紅，3粒；左腳掌偽漩渦，黃，8粒。 | `chOn` | `pgu-storymode-motor-899-chon-5172bbcc` |
| STAGED | RGB runtime target 'selectedRgb4' | 3s: all signals green — Slave 7/8 RGB4 signal LEDs. | `SpecificColorPattern` | `pgu-storymode-motor-712-specificcolorpattern-75617f09` |
| STAGED | RGB runtime target 'selectedRgb4' | UNCONFIRMED COMPONENT — RGB runtime target 'selectedRgb4' | `SpecificColorPattern` | `pgu-storymode-motor-797-specificcolorpattern-a80fef81`<br>`pgu-storymode-motor-803-specificcolorpattern-296ea49b`<br>`pgu-storymode-motor-1802-specificcolorpattern-41aa8407`<br>`pgu-storymode-motor-2269-specificcolorpattern-ccdb69b3` |
| STAGED | RGB1 | UNCONFIRMED COMPONENT — RGB1 | `rgbOff`、`whiteSwipe` | `pgu-storymode-motor-304-rgboff-caa38919`<br>`pgu-storymode-motor-563-rgboff-75625402`<br>`pgu-storymode-motor-836-whiteswipe-2be99eea` |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `VentEffect`、`randomFillAll_V2`、`rgbOff` | `pgu-storymode-motor-305-rgboff-88ca7a64`<br>`pgu-storymode-motor-500-venteffect-e8ee854e`<br>`pgu-storymode-motor-520-rgboff-259eccb7`<br>`pgu-storymode-motor-564-rgboff-254d7d12`<br>`pgu-storymode-motor-848-randomfillall-v2-158477c3`<br>`pgu-storymode-motor-852-venteffect-1be7873c` |
| STAGED | RGB3 | Slave 7/8 RGB3 — foot turbine. | `turbine_v3_sound` | `pgu-storymode-motor-864-turbine-v3-sound-71c3bd4a` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `rgbOff` | `pgu-storymode-motor-306-rgboff-96a1c0cf`<br>`pgu-storymode-motor-565-rgboff-343ea7db` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `SpecificColorPattern`、`rgbOff` | `pgu-storymode-motor-307-rgboff-cdd4677a`<br>`pgu-storymode-motor-346-specificcolorpattern-aca35478`<br>`pgu-storymode-motor-468-specificcolorpattern-1ad863a1`<br>`pgu-storymode-motor-475-specificcolorpattern-299ff24e`<br>`pgu-storymode-motor-566-rgboff-8e7fbb41` |
| STAGED | RGB7 | Slave 7/8 RGB7/RGB8 — footplate effect. | `footplatev2` | `pgu-storymode-motor-877-footplatev2-7989e6ae` |
| STAGED | RGB7 | Slave 8 RGB7 (63粒) 左膝關節／大漩渦：20% 上限渦輪效果。 | `turbine_v3_sound` | `pgu-storymode-motor-524-turbine-v3-sound-7a70bd98` |
| STAGED | RGB7 | UNCONFIRMED COMPONENT — RGB7 | `rgbOff` | `pgu-storymode-motor-308-rgboff-568a59bf`<br>`pgu-storymode-motor-567-rgboff-670e0cf1` |
| STAGED | RGB8 | Slave 8 RGB8 (49粒) 左腳腳底燈：20% 上限 footplate 效果。 | `footplatev2` | `pgu-storymode-motor-537-footplatev2-8fda3de5` |
| STAGED | RGB8 | UNCONFIRMED COMPONENT — RGB8 | `footplatev2`、`rgbOff` | `pgu-storymode-motor-309-rgboff-42cc6e9f`<br>`pgu-storymode-motor-568-rgboff-a6f4055f`<br>`pgu-storymode-motor-887-footplatev2-06b5a33a` |
| STAGED | Runtime／group target 'slaveId' | UNCONFIRMED COMPONENT — Runtime／group target 'slaveId' | `RGBActivationCometCross` | `pgu-storymode-motor-361-rgbactivationcometcross-1112c67a` |

### storyMode_motor_reset

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | Motor／servo channel '0' | UNCONFIRMED COMPONENT — Motor／servo channel '0' | `chServoHold`、`chServoStop` | `pgu-storymode-motor-reset-765-chservohold-278f82af`<br>`pgu-storymode-motor-reset-931-chservohold-c0d9b0a4`<br>`pgu-storymode-motor-reset-935-chservohold-086a53b6`<br>`pgu-storymode-motor-reset-937-chservostop-467e7dc7`<br>`pgu-storymode-motor-reset-1107-chservohold-b8bc7afc`<br>`pgu-storymode-motor-reset-1111-chservohold-b8e5fc05`<br>`pgu-storymode-motor-reset-1113-chservostop-1b69680b` |
| STAGED | Motor／servo channel '1' | UNCONFIRMED COMPONENT — Motor／servo channel '1' | `chServoStop` | `pgu-storymode-motor-reset-766-chservostop-5e565497`<br>`pgu-storymode-motor-reset-929-chservostop-4102fb62`<br>`pgu-storymode-motor-reset-1105-chservostop-ed29f383` |
| STAGED | Motor／servo channel 'i' | UNCONFIRMED COMPONENT — Motor／servo channel 'i' | `chServoHold` | `pgu-storymode-motor-reset-485-chservohold-fcfa759d` |
| STAGED | PCA PWM0 CH 0 | UNCONFIRMED COMPONENT — PCA PWM0 CH 0 | `chOn` | `pgu-storymode-motor-reset-479-chon-bccd1081`<br>`pgu-storymode-motor-reset-759-chon-d152dbbf`<br>`pgu-storymode-motor-reset-923-chon-9e5556fb`<br>`pgu-storymode-motor-reset-1099-chon-e7d761e3` |
| STAGED | PCA PWM0 CH 1 | UNCONFIRMED COMPONENT — PCA PWM0 CH 1 | `chOn` | `pgu-storymode-motor-reset-480-chon-2ec065c2`<br>`pgu-storymode-motor-reset-760-chon-6d503456`<br>`pgu-storymode-motor-reset-924-chon-7b1cbd7e`<br>`pgu-storymode-motor-reset-1100-chon-d7d3366e` |
| STAGED | PCA PWM0 CH 4 | UNCONFIRMED COMPONENT — PCA PWM0 CH 4 | `chOn` | `pgu-storymode-motor-reset-481-chon-3fc7710c`<br>`pgu-storymode-motor-reset-761-chon-30f0ffde`<br>`pgu-storymode-motor-reset-925-chon-cd633c59`<br>`pgu-storymode-motor-reset-1101-chon-cb3af538` |
| STAGED | PCA PWM0 CH 5 | UNCONFIRMED COMPONENT — PCA PWM0 CH 5 | `chOn` | `pgu-storymode-motor-reset-482-chon-a3bad36c`<br>`pgu-storymode-motor-reset-762-chon-c926623d`<br>`pgu-storymode-motor-reset-926-chon-a2020585`<br>`pgu-storymode-motor-reset-1102-chon-ebc13e7f` |
| STAGED | PCA PWM0 CH 7 | UNCONFIRMED COMPONENT — PCA PWM0 CH 7 | `chOn` | `pgu-storymode-motor-reset-483-chon-b1e2a9ce`<br>`pgu-storymode-motor-reset-763-chon-79a8dd09`<br>`pgu-storymode-motor-reset-927-chon-43a685f2`<br>`pgu-storymode-motor-reset-1103-chon-76da58a4` |
| STAGED | PCA PWM0 CH 8 | UNCONFIRMED COMPONENT — PCA PWM0 CH 8 | `chOn` | `pgu-storymode-motor-reset-484-chon-df11e765`<br>`pgu-storymode-motor-reset-764-chon-636fe5c9`<br>`pgu-storymode-motor-reset-928-chon-8302a68c`<br>`pgu-storymode-motor-reset-1104-chon-5babc1bd` |
| STAGED | RGB9 | UNCONFIRMED COMPONENT — RGB9 | `SpecificColorPattern` | `pgu-storymode-motor-reset-475-specificcolorpattern-a1e5ab32`<br>`pgu-storymode-motor-reset-755-specificcolorpattern-d969d70c`<br>`pgu-storymode-motor-reset-919-specificcolorpattern-c7c61f51`<br>`pgu-storymode-motor-reset-1095-specificcolorpattern-882155fa` |

## Slave 9

### storyMode_develop

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB1 | Hi-Nu Slave 19/20 左右腳掌 RGB — shared PGU Slave 7 RGB source. | `rgbOff` | `pgu-storymode-develop-232-rgboff-cd9c19be` |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `rgbOff` | `pgu-storymode-develop-233-rgboff-b222cedb` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `rgbOff` | `pgu-storymode-develop-234-rgboff-fb9fcc55` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `SpecificColorPattern` | `pgu-storymode-develop-235-specificcolorpattern-9ec0269b` |

### storyMode_signals

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB4 | Hi-Nu Slave 19/20 左右腳掌 RGB — shared PGU Slave 7 RGB source. | `SpecificColorPattern` | `pgu-storymode-signals-187-specificcolorpattern-40e9ed43` |

### storyMode_0_v1

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB1 | Hi-Nu Slave 19/20 左右腳掌 RGB — shared PGU Slave 7 RGB source. | `randomFlashWithGap_multiple`、`randomLightUp` | `pgu-storymode-0-v1-569-randomflashwithgap-multiple-6e1ce021`<br>`pgu-storymode-0-v1-2279-randomlightup-3e9945d1` |
| STAGED | RGB1 | UNCONFIRMED COMPONENT — RGB1 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v1-922-randomflashwithgap-multiple-7a837a14`<br>`pgu-storymode-0-v1-1399-randomlightup-46f159ad`<br>`pgu-storymode-0-v1-1860-randomlightup-71795bb8`<br>`pgu-storymode-0-v1-2494-rgbon-9534d053`<br>`pgu-storymode-0-v1-3050-rgbon-27c680ae` |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v1-576-randomflashwithgap-multiple-d38a0466`<br>`pgu-storymode-0-v1-929-randomflashwithgap-multiple-3864e3ce`<br>`pgu-storymode-0-v1-1406-randomlightup-eeaa9563`<br>`pgu-storymode-0-v1-1867-randomlightup-2e8d3d42`<br>`pgu-storymode-0-v1-2286-randomlightup-43d01ff8`<br>`pgu-storymode-0-v1-2496-rgbon-2c226342`<br>`pgu-storymode-0-v1-3052-rgbon-462411d1` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v1-583-randomflashwithgap-multiple-e4e814fe`<br>`pgu-storymode-0-v1-936-randomflashwithgap-multiple-9ab206d9`<br>`pgu-storymode-0-v1-1413-randomlightup-f801d52e`<br>`pgu-storymode-0-v1-1874-randomlightup-255732f2`<br>`pgu-storymode-0-v1-2293-randomlightup-1a979921`<br>`pgu-storymode-0-v1-2498-rgbon-3fab67c8`<br>`pgu-storymode-0-v1-3054-rgbon-cb844724` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v1-590-randomflashwithgap-multiple-dadbbf6a`<br>`pgu-storymode-0-v1-943-randomflashwithgap-multiple-03c667ba`<br>`pgu-storymode-0-v1-1421-randomlightup-3520cdf0`<br>`pgu-storymode-0-v1-1881-randomlightup-55a0c4d9`<br>`pgu-storymode-0-v1-2300-randomlightup-ce156ffa`<br>`pgu-storymode-0-v1-2501-rgbon-5e21ac60`<br>`pgu-storymode-0-v1-3057-rgbon-16e8bfd6` |

### storyMode_awakening_3

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB2 | Hi-Nu Slave 19/20 左右腳掌 RGB — shared PGU Slave 7 RGB source. | `rgbOff` | `pgu-storymode-awakening-3-351-rgboff-aec52258` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `rgbOff` | `pgu-storymode-awakening-3-353-rgboff-054b6761` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `rgbOff` | `pgu-storymode-awakening-3-355-rgboff-0b886234` |
| STAGED | Runtime／group target 'espLed[0]' | (左／右腳掌) 後腳踭紅燈及腳掌白燈：espLed[0-3] 與 RGB1 同週期呼吸。 | `chBreath` | `pgu-storymode-awakening-3-358-chbreath-6c2a7e9a` |
| STAGED | Runtime／group target 'espLed[1]' | UNCONFIRMED COMPONENT — Runtime／group target 'espLed[1]' | `chBreath` | `pgu-storymode-awakening-3-359-chbreath-26e237ad` |
| STAGED | Runtime／group target 'espLed[2]' | UNCONFIRMED COMPONENT — Runtime／group target 'espLed[2]' | `chBreath` | `pgu-storymode-awakening-3-360-chbreath-f31355bc` |
| STAGED | Runtime／group target 'espLed[3]' | UNCONFIRMED COMPONENT — Runtime／group target 'espLed[3]' | `chBreath` | `pgu-storymode-awakening-3-361-chbreath-d27db3aa` |

### storyMode_activation

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `gradientVentPalette`、`randomFillAll_V2` | `pgu-storymode-activation-603-randomfillall-v2-43b9819d`<br>`pgu-storymode-activation-606-gradientventpalette-69f93047` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `turbine_v3` | `pgu-storymode-activation-622-turbine-v3-011e8747` |
| STAGED | RGB4 | Hi-Nu Slave 19/20 左右腳掌 RGB — shared PGU Slave 7 RGB source. | `SpecificColorPattern` | `pgu-storymode-activation-595-specificcolorpattern-f210bb16` |

### storyMode_0_v2

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB1 | Hi-Nu Slave 19/20 左右腳掌 RGB — shared PGU Slave 7 RGB source. | `randomLightUp` | `pgu-storymode-0-v2-1782-randomlightup-e7d0c4af` |
| STAGED | RGB1 | UNCONFIRMED COMPONENT — RGB1 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v2-646-randomflashwithgap-multiple-1d73a958`<br>`pgu-storymode-0-v2-1051-randomlightup-d6865cfd`<br>`pgu-storymode-0-v2-1438-randomlightup-f21ef008`<br>`pgu-storymode-0-v2-1977-rgbon-a97241a2`<br>`pgu-storymode-0-v2-2163-rgbon-cf5daa50` |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v2-653-randomflashwithgap-multiple-c183fb6f`<br>`pgu-storymode-0-v2-1058-randomlightup-762e453a`<br>`pgu-storymode-0-v2-1445-randomlightup-349341d3`<br>`pgu-storymode-0-v2-1789-randomlightup-e166e14d`<br>`pgu-storymode-0-v2-1979-rgbon-d123171f`<br>`pgu-storymode-0-v2-2165-rgbon-1a3447c9` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v2-660-randomflashwithgap-multiple-16bff609`<br>`pgu-storymode-0-v2-1065-randomlightup-d7294d5c`<br>`pgu-storymode-0-v2-1452-randomlightup-9407d3f7`<br>`pgu-storymode-0-v2-1796-randomlightup-abcf061a`<br>`pgu-storymode-0-v2-1981-rgbon-c54e2357`<br>`pgu-storymode-0-v2-2167-rgbon-a3fc1ed5` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v2-667-randomflashwithgap-multiple-e57728bf`<br>`pgu-storymode-0-v2-1073-randomlightup-f3428508`<br>`pgu-storymode-0-v2-1459-randomlightup-edc73f29`<br>`pgu-storymode-0-v2-1804-randomlightup-cb8ac12a`<br>`pgu-storymode-0-v2-1984-rgbon-f1131ca9`<br>`pgu-storymode-0-v2-2170-rgbon-c1668c0d` |
| STAGED | Runtime／group target 'strips' | UNCONFIRMED COMPONENT — Runtime／group target 'strips' | `randomFlashFixedCount_multiple` | `pgu-storymode-0-v2-285-randomflashfixedcount-multiple-d8f707cd` |

### storyMode_storing_energy

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB1 | Hi-Nu Slave 19/20 左右腳掌 RGB — shared PGU Slave 7 RGB source. | `paletteWave_80Percent_SpecialWave`、`renderSlave78Rgb1StorySpecificColor` | `pgu-storymode-storing-energy-815-palettewave-80percent-specialwave-7b2f89e4`<br>`pgu-storymode-storing-energy-1464-renderslave78rgb1storyspecificcolor-105ae191` |
| STAGED | RGB2 | Hi-Nu Slave 19/20 左右腳掌 RGB — shared PGU Slave 7 RGB source. | `rgbOff` | `pgu-storymode-storing-energy-448-rgboff-895ab9e1` |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `GN_Wire_Normal`、`paletteWave_80Percent_SpecialWave` | `pgu-storymode-storing-energy-824-palettewave-80percent-specialwave-b02ffc06`<br>`pgu-storymode-storing-energy-1466-gn-wire-normal-72e0a923` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `rgbOff`、`turbine_v3` | `pgu-storymode-storing-energy-449-rgboff-7cf852ac`<br>`pgu-storymode-storing-energy-833-turbine-v3-0ffe89f3`<br>`pgu-storymode-storing-energy-1477-turbine-v3-b4b255a8` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `SpecificColorPattern`、`rgbOff` | `pgu-storymode-storing-energy-451-rgboff-72712967`<br>`pgu-storymode-storing-energy-844-rgboff-70071ea6`<br>`pgu-storymode-storing-energy-1488-specificcolorpattern-baf42f24` |

### storyMode_2

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `gradientVentPalette`、`randomFillAll_V2` | `pgu-storymode-2-566-randomfillall-v2-e1218298`<br>`pgu-storymode-2-575-gradientventpalette-fcf76e9f` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `turbine_v3` | `pgu-storymode-2-595-turbine-v3-38966b7a` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `SpecificColorPattern` | `pgu-storymode-2-607-specificcolorpattern-8261079a` |

### storyMode_plasma

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB4 | Hi-Nu Slave 9/11 左右腳掌 RGB — shared PGU Slave 7 RGB source. | `SpecificColorPattern` | `pgu-storymode-plasma-683-specificcolorpattern-0cb64a28` |

### storyMode_trans_am

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB1 | Hi-Nu Slave 19/20 左右腳掌 RGB — shared PGU Slave 7 RGB source. | `GN_Drive_Running` | `pgu-storymode-trans-am-433-gn-drive-running-558dd4be` |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `GN_Wire_TransAM` | `pgu-storymode-trans-am-444-gn-wire-transam-a760d0c4` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `turbine_v3` | `pgu-storymode-trans-am-456-turbine-v3-be937ee7` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `SpecificColorPattern` | `pgu-storymode-trans-am-468-specificcolorpattern-a8bc8918` |

### storyMode_3

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB2 | Hi-Nu Slave 19/20 左右腳掌 RGB — shared PGU Slave 7 RGB source. | `gradientVentPalette` | `pgu-storymode-3-583-gradientventpalette-b96aedc7` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `turbine_v3` | `pgu-storymode-3-603-turbine-v3-6530d150` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `SpecificColorPattern` | `pgu-storymode-3-615-specificcolorpattern-ffae20b5` |

### storyMode_idle

OFF／no direct call in this Slave context。

### storyMode_motor

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | Motor／servo channel '0' | UNCONFIRMED COMPONENT — Motor／servo channel '0' | `chFadeIn`、`chServoHold` | `pgu-storymode-motor-1914-chfadein-5e6e2780`<br>`pgu-storymode-motor-1924-chservohold-4bfa42e9`<br>`pgu-storymode-motor-2366-chservohold-b5b92ab5` |
| STAGED | Motor／servo channel '1' | UNCONFIRMED COMPONENT — Motor／servo channel '1' | `chFadeOut`、`chServoHold` | `pgu-storymode-motor-1915-chfadeout-b0aa0131`<br>`pgu-storymode-motor-1925-chservohold-d425fda8`<br>`pgu-storymode-motor-2367-chservohold-1eaa81da` |
| STAGED | Motor／servo channel '2' | UNCONFIRMED COMPONENT — Motor／servo channel '2' | `chFadeIn`、`chServoHold` | `pgu-storymode-motor-1912-chfadein-6f1900d3`<br>`pgu-storymode-motor-1926-chservohold-ff883f2d`<br>`pgu-storymode-motor-2368-chservohold-48b28178` |
| STAGED | Motor／servo channel '3' | UNCONFIRMED COMPONENT — Motor／servo channel '3' | `chFadeOut`、`chServoHold` | `pgu-storymode-motor-1913-chfadeout-63a2e0bc`<br>`pgu-storymode-motor-1927-chservohold-696ac959`<br>`pgu-storymode-motor-2369-chservohold-841bd085` |
| STAGED | Motor／servo channel '4' | UNCONFIRMED COMPONENT — Motor／servo channel '4' | `chFadeIn`、`chServoHold` | `pgu-storymode-motor-1910-chfadein-eac3a959`<br>`pgu-storymode-motor-1928-chservohold-b2412fbe`<br>`pgu-storymode-motor-2370-chservohold-17d6a6ff` |
| STAGED | Motor／servo channel '5' | UNCONFIRMED COMPONENT — Motor／servo channel '5' | `chFadeOut`、`chServoHold` | `pgu-storymode-motor-1911-chfadeout-4a433775`<br>`pgu-storymode-motor-1929-chservohold-21ee03d2`<br>`pgu-storymode-motor-2371-chservohold-6cb0745b` |
| STAGED | PCA PWM1 CH i (loop 0..8 inclusive) | 0s: body white PCA + eyes — Slave 3 chest/skirt pure white PCA. | `chOn` | `pgu-storymode-motor-737-chon-bc56755d` |
| STAGED | RGB1 | Slave 9 platform RGB1 — GN drive running. | `GN_Drive_Running` | `pgu-storymode-motor-1933-gn-drive-running-19399c9f` |
| STAGED | RGB10 | UNCONFIRMED COMPONENT — RGB10 | `SpecificColorPattern` | `pgu-storymode-motor-1820-specificcolorpattern-989ee53d`<br>`pgu-storymode-motor-1878-specificcolorpattern-78c167f8`<br>`pgu-storymode-motor-2330-specificcolorpattern-c6f8c13a` |
| STAGED | RGB11 | UNCONFIRMED COMPONENT — RGB11 | `GN_Drive_Running` | `pgu-storymode-motor-1999-gn-drive-running-6315981e` |
| STAGED | RGB12 | UNCONFIRMED COMPONENT — RGB12 | `SpecificColorPattern` | `pgu-storymode-motor-1824-specificcolorpattern-4f5f0612`<br>`pgu-storymode-motor-1853-specificcolorpattern-6fb0fbe7`<br>`pgu-storymode-motor-2305-specificcolorpattern-75a93d09` |
| STAGED | RGB2 | Slave 9 platform RGB2 — vent effect. | `VentEffect` | `pgu-storymode-motor-1944-venteffect-89ed3de6` |
| STAGED | RGB3 | Slave 9 platform RGB3 — turbine vortex. | `turbine_v3_sound` | `pgu-storymode-motor-1955-turbine-v3-sound-5391d8f1` |
| STAGED | RGB4 | 3s: all signals green — Slave 3 RGB4 signal LEDs. | `SpecificColorPattern` | `pgu-storymode-motor-729-specificcolorpattern-5f7ab287` |
| STAGED | RGB4 | Slave 9 platform RGB4 — footplate effect. | `footplatev2` | `pgu-storymode-motor-1968-footplatev2-23fe73e1` |
| STAGED | RGB7 | Slave 9 platform RGB7/RGB9/RGB11 — GN drive running. | `GN_Drive_Running` | `pgu-storymode-motor-1979-gn-drive-running-e6a8149c` |
| STAGED | RGB8 | UNCONFIRMED COMPONENT — RGB8 | `SpecificColorPattern` | `pgu-storymode-motor-1816-specificcolorpattern-7d6df621`<br>`pgu-storymode-motor-1903-specificcolorpattern-6205b5f0`<br>`pgu-storymode-motor-2355-specificcolorpattern-64cba8e5` |
| STAGED | RGB9 | UNCONFIRMED COMPONENT — RGB9 | `GN_Drive_Running` | `pgu-storymode-motor-1989-gn-drive-running-7a60ddc8` |

### storyMode_motor_reset

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | Motor／servo channel '0' | UNCONFIRMED COMPONENT — Motor／servo channel '0' | `chFadeOut`、`chServoHold` | `pgu-storymode-motor-reset-571-chfadeout-797d8f0f`<br>`pgu-storymode-motor-reset-580-chservohold-64268179`<br>`pgu-storymode-motor-reset-779-chservohold-77c2bd0a`<br>`pgu-storymode-motor-reset-950-chservohold-e1eec3ed`<br>`pgu-storymode-motor-reset-1126-chservohold-3ac5be4b` |
| STAGED | Motor／servo channel '1' | UNCONFIRMED COMPONENT — Motor／servo channel '1' | `chFadeIn`、`chServoHold` | `pgu-storymode-motor-reset-572-chfadein-33de1d90`<br>`pgu-storymode-motor-reset-581-chservohold-a1b6bc8f`<br>`pgu-storymode-motor-reset-780-chservohold-e2890ac9`<br>`pgu-storymode-motor-reset-951-chservohold-d8754e6e`<br>`pgu-storymode-motor-reset-1127-chservohold-05fe6eab` |
| STAGED | Motor／servo channel '2' | UNCONFIRMED COMPONENT — Motor／servo channel '2' | `chFadeOut`、`chServoHold` | `pgu-storymode-motor-reset-569-chfadeout-1c0c0378`<br>`pgu-storymode-motor-reset-582-chservohold-75cf6791`<br>`pgu-storymode-motor-reset-781-chservohold-723c95c9`<br>`pgu-storymode-motor-reset-952-chservohold-52e26930`<br>`pgu-storymode-motor-reset-1128-chservohold-1a676de9` |
| STAGED | Motor／servo channel '3' | UNCONFIRMED COMPONENT — Motor／servo channel '3' | `chFadeIn`、`chServoHold` | `pgu-storymode-motor-reset-570-chfadein-3afb07f1`<br>`pgu-storymode-motor-reset-583-chservohold-9d8b37d7`<br>`pgu-storymode-motor-reset-782-chservohold-2490e4cb`<br>`pgu-storymode-motor-reset-953-chservohold-db8f438f`<br>`pgu-storymode-motor-reset-1129-chservohold-df7ccc92` |
| STAGED | Motor／servo channel '4' | UNCONFIRMED COMPONENT — Motor／servo channel '4' | `chFadeOut`、`chServoHold` | `pgu-storymode-motor-reset-567-chfadeout-a883d246`<br>`pgu-storymode-motor-reset-584-chservohold-c66e444a`<br>`pgu-storymode-motor-reset-783-chservohold-e9832422`<br>`pgu-storymode-motor-reset-954-chservohold-1ba1e6c3`<br>`pgu-storymode-motor-reset-1130-chservohold-6f0a5e68` |
| STAGED | Motor／servo channel '5' | UNCONFIRMED COMPONENT — Motor／servo channel '5' | `chFadeIn`、`chServoHold` | `pgu-storymode-motor-reset-568-chfadein-8b51661e`<br>`pgu-storymode-motor-reset-585-chservohold-3ea8a5c7`<br>`pgu-storymode-motor-reset-784-chservohold-c31a7ebb`<br>`pgu-storymode-motor-reset-955-chservohold-ef5ef11b`<br>`pgu-storymode-motor-reset-1131-chservohold-d6bdd75f` |
| STAGED | RGB10 | UNCONFIRMED COMPONENT — RGB10 | `SpecificColorPattern`、`rgbOff` | `pgu-storymode-motor-reset-535-specificcolorpattern-ffa2754b`<br>`pgu-storymode-motor-reset-771-rgboff-d1762b3a`<br>`pgu-storymode-motor-reset-942-rgboff-147ce2c1`<br>`pgu-storymode-motor-reset-1118-rgboff-e2951ea0` |
| STAGED | RGB12 | UNCONFIRMED COMPONENT — RGB12 | `SpecificColorPattern`、`rgbOff` | `pgu-storymode-motor-reset-509-specificcolorpattern-d4f46d80`<br>`pgu-storymode-motor-reset-772-rgboff-c9221cfb`<br>`pgu-storymode-motor-reset-943-rgboff-5e1adf25`<br>`pgu-storymode-motor-reset-1119-rgboff-918e719f` |
| STAGED | RGB8 | UNCONFIRMED COMPONENT — RGB8 | `SpecificColorPattern`、`rgbOff` | `pgu-storymode-motor-reset-561-specificcolorpattern-d6854bca`<br>`pgu-storymode-motor-reset-770-rgboff-1bc725eb`<br>`pgu-storymode-motor-reset-941-rgboff-94e939c9`<br>`pgu-storymode-motor-reset-1117-rgboff-d689803b` |

## Slave 10

### storyMode_develop

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB1 | Hi-Nu Slave 8/10 RGB1/2/7/8：Develop 模式只保留 42 粒訊號燈。 | `rgbOff` | `pgu-storymode-develop-194-rgboff-2d3f0b2c` |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `rgbOff` | `pgu-storymode-develop-195-rgboff-dfa78c9c` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `rgbOff` | `pgu-storymode-develop-196-rgboff-53c1c290` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `SpecificColorPattern` | `pgu-storymode-develop-200-specificcolorpattern-c57094f5` |
| STAGED | RGB7 | UNCONFIRMED COMPONENT — RGB7 | `rgbOff` | `pgu-storymode-develop-197-rgboff-ee54a117` |
| STAGED | RGB8 | UNCONFIRMED COMPONENT — RGB8 | `rgbOff` | `pgu-storymode-develop-198-rgboff-ceab810f` |
| STAGED | Runtime／group target 'espLed[channel]' | GPIO48 白燈 4 粒；GPIO47／45／42 紅燈：Develop 模式低亮長亮。 | `chOn` | `pgu-storymode-develop-209-chon-5d047c79` |

### storyMode_signals

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB4 | Hi-Nu Slave 8/10 RGB4：42 粒訊號燈共用完整 Repair profile。 | `SpecificColorPattern` | `pgu-storymode-signals-176-specificcolorpattern-d94838a9` |
| STAGED | Runtime／group target 'espLed[channel]' | Hi-Nu Slave 8/10 GPIO48 白燈 4 粒；GPIO47／45／42 紅燈：進入 Signals 立即關閉。 | `chOff` | `pgu-storymode-signals-35-choff-6de79856` |

### storyMode_0_v1

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB1 | Hi-Nu Slave 8/10 左右腿 RGB：兩側固定使用相同 RGB pin。 | `randomLightUp`、`rgbOn` | `pgu-storymode-0-v1-1339-randomlightup-000ae4ad`<br>`pgu-storymode-0-v1-1800-randomlightup-95b36afc`<br>`pgu-storymode-0-v1-2470-rgbon-2c67ef52`<br>`pgu-storymode-0-v1-3026-rgbon-4954e367` |
| STAGED | RGB1 | Hi-Nu Slave 8/10 左右腿上段 RGB — shared PGU Slave 7 RGB source. | `randomFlashWithGap_multiple`、`randomLightUp` | `pgu-storymode-0-v1-480-randomflashwithgap-multiple-5cee67bb`<br>`pgu-storymode-0-v1-862-randomflashwithgap-multiple-c796a33e`<br>`pgu-storymode-0-v1-2232-randomlightup-897fa487` |
| STAGED | RGB10 | UNCONFIRMED COMPONENT — RGB10 | `randomFlashWithGap_multiple` | `pgu-storymode-0-v1-529-randomflashwithgap-multiple-35f38906` |
| STAGED | RGB11 | UNCONFIRMED COMPONENT — RGB11 | `randomFlashWithGap_multiple` | `pgu-storymode-0-v1-536-randomflashwithgap-multiple-6e452c5a` |
| STAGED | RGB12 | UNCONFIRMED COMPONENT — RGB12 | `randomFlashWithGap_multiple` | `pgu-storymode-0-v1-543-randomflashwithgap-multiple-9b5fec0d` |
| STAGED | RGB13 | UNCONFIRMED COMPONENT — RGB13 | `randomFlashWithGap_multiple` | `pgu-storymode-0-v1-550-randomflashwithgap-multiple-5cc38ea4` |
| STAGED | RGB16 | UNCONFIRMED COMPONENT — RGB16 | `randomFlashWithGap_multiple` | `pgu-storymode-0-v1-557-randomflashwithgap-multiple-02d938ff` |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v1-487-randomflashwithgap-multiple-bf13acc6`<br>`pgu-storymode-0-v1-869-randomflashwithgap-multiple-9b996d1b`<br>`pgu-storymode-0-v1-1346-randomlightup-640de706`<br>`pgu-storymode-0-v1-1807-randomlightup-9ff938bb`<br>`pgu-storymode-0-v1-2239-randomlightup-747ca70f`<br>`pgu-storymode-0-v1-2472-rgbon-9629c27a`<br>`pgu-storymode-0-v1-3028-rgbon-4a618cff` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v1-494-randomflashwithgap-multiple-53640921`<br>`pgu-storymode-0-v1-876-randomflashwithgap-multiple-b1de5839`<br>`pgu-storymode-0-v1-1353-randomlightup-1cdc2a0f`<br>`pgu-storymode-0-v1-1814-randomlightup-118b8350`<br>`pgu-storymode-0-v1-2246-randomlightup-c57aa0be`<br>`pgu-storymode-0-v1-2474-rgbon-486c859d`<br>`pgu-storymode-0-v1-3030-rgbon-36d0ad85` |
| STAGED | RGB4 | Hi-Nu Slave 8/10 RGB4 (42 粒) 腿部訊號：與其他腿部 RGB 同步長亮。 | `rgbOn` | `pgu-storymode-0-v1-2477-rgbon-97ce6031`<br>`pgu-storymode-0-v1-3033-rgbon-4a915a05` |
| STAGED | RGB4 | Hi-Nu Slave 8/10 RGB4 (42 粒) 腿部訊號：與其他腿部 RGB 同步隨機亮起。 | `randomLightUp` | `pgu-storymode-0-v1-1361-randomlightup-d4f3fe3c` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `randomFlashWithGap_multiple`、`randomLightUp` | `pgu-storymode-0-v1-501-randomflashwithgap-multiple-c3de7391`<br>`pgu-storymode-0-v1-883-randomflashwithgap-multiple-815c841c`<br>`pgu-storymode-0-v1-1821-randomlightup-24128e52`<br>`pgu-storymode-0-v1-2253-randomlightup-b9277b73` |
| STAGED | RGB7 | UNCONFIRMED COMPONENT — RGB7 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v1-508-randomflashwithgap-multiple-ada694bc`<br>`pgu-storymode-0-v1-890-randomflashwithgap-multiple-bad51f9c`<br>`pgu-storymode-0-v1-1368-randomlightup-dcced8b6`<br>`pgu-storymode-0-v1-1828-randomlightup-2d158799`<br>`pgu-storymode-0-v1-2260-randomlightup-17782b3b`<br>`pgu-storymode-0-v1-2479-rgbon-5bc4823d`<br>`pgu-storymode-0-v1-3035-rgbon-1803500b` |
| STAGED | RGB8 | UNCONFIRMED COMPONENT — RGB8 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v1-515-randomflashwithgap-multiple-2a4fae3a`<br>`pgu-storymode-0-v1-897-randomflashwithgap-multiple-079dc7ab`<br>`pgu-storymode-0-v1-1375-randomlightup-06678456`<br>`pgu-storymode-0-v1-1835-randomlightup-7b140595`<br>`pgu-storymode-0-v1-2267-randomlightup-141ac05a`<br>`pgu-storymode-0-v1-2481-rgbon-ca78834a`<br>`pgu-storymode-0-v1-3037-rgbon-1f41bba2` |
| STAGED | RGB9 | UNCONFIRMED COMPONENT — RGB9 | `randomFlashWithGap_multiple`、`randomLightUp` | `pgu-storymode-0-v1-522-randomflashwithgap-multiple-3770009e`<br>`pgu-storymode-0-v1-904-randomflashwithgap-multiple-31ad0ebc`<br>`pgu-storymode-0-v1-1382-randomlightup-aaa8ff31`<br>`pgu-storymode-0-v1-1842-randomlightup-b70358c9` |

### storyMode_awakening_3

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB2 | Hi-Nu Slave 8/10 左右腿上段 RGB — shared PGU Slave 7 RGB source. | `rgbOff` | `pgu-storymode-awakening-3-330-rgboff-9a3bb44d` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `rgbOff` | `pgu-storymode-awakening-3-332-rgboff-4b1eacd1` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `rgbOff` | `pgu-storymode-awakening-3-334-rgboff-1c1faa31` |
| STAGED | RGB7 | UNCONFIRMED COMPONENT — RGB7 | `rgbOff` | `pgu-storymode-awakening-3-336-rgboff-19e7c65f` |
| STAGED | RGB8 | UNCONFIRMED COMPONENT — RGB8 | `rgbOff` | `pgu-storymode-awakening-3-338-rgboff-3d951ed3` |
| STAGED | Runtime／group target 'espLed[0]' | (左／右小腿) 白、紅及大腿後甲燈：espLed[0-3] 與 RGB1 同週期呼吸。 | `chBreath` | `pgu-storymode-awakening-3-341-chbreath-b6ab97d9` |
| STAGED | Runtime／group target 'espLed[1]' | UNCONFIRMED COMPONENT — Runtime／group target 'espLed[1]' | `chBreath` | `pgu-storymode-awakening-3-342-chbreath-8c002e46` |
| STAGED | Runtime／group target 'espLed[2]' | UNCONFIRMED COMPONENT — Runtime／group target 'espLed[2]' | `chBreath` | `pgu-storymode-awakening-3-343-chbreath-ef44fd2c` |
| STAGED | Runtime／group target 'espLed[3]' | UNCONFIRMED COMPONENT — Runtime／group target 'espLed[3]' | `chBreath` | `pgu-storymode-awakening-3-344-chbreath-c84fbad8` |

### storyMode_activation

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `gradientVentPalette`、`randomFillAll_V2` | `pgu-storymode-activation-524-randomfillall-v2-760ba794`<br>`pgu-storymode-activation-527-gradientventpalette-f8d3c801` |
| STAGED | RGB4 | Hi-Nu Slave 8/10 RGB4：共用 42 粒腿部訊號 Normal profile。 | `SpecificColorPattern` | `pgu-storymode-activation-516-specificcolorpattern-a5ab43e3` |
| STAGED | RGB7 | Slave 8 RGB7 (63粒) 左膝關節／大漩渦：覺醒渦輪。 | `turbine_v3` | `pgu-storymode-activation-544-turbine-v3-0c653df2` |
| STAGED | RGB8 | Slave 8 RGB8 (49粒) 左腳腳底燈：覺醒 footplate。 | `footplatev2` | `pgu-storymode-activation-556-footplatev2-79125c7f` |
| STAGED | Runtime／group target 'espLed[channel]' | GPIO48 白燈 4 粒；GPIO47／45／42 紅燈：Activation 模式低亮長亮。 | `chOn` | `pgu-storymode-activation-572-chon-98ce9bfb` |

### storyMode_0_v2

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB1 | Hi-Nu Slave 8/10 左右腿 RGB：兩側固定使用相同 RGB pin。 | `randomLightUp`、`rgbOn` | `pgu-storymode-0-v2-991-randomlightup-52b7b564`<br>`pgu-storymode-0-v2-1377-randomlightup-938d2f38`<br>`pgu-storymode-0-v2-1734-randomlightup-7b203f2a`<br>`pgu-storymode-0-v2-1953-rgbon-a143406d`<br>`pgu-storymode-0-v2-2139-rgbon-a38e1e6b` |
| STAGED | RGB1 | UNCONFIRMED COMPONENT — RGB1 | `randomFlashWithGap_multiple` | `pgu-storymode-0-v2-592-randomflashwithgap-multiple-dd79f85e` |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v2-599-randomflashwithgap-multiple-e2563ca8`<br>`pgu-storymode-0-v2-998-randomlightup-8414e177`<br>`pgu-storymode-0-v2-1384-randomlightup-800162a9`<br>`pgu-storymode-0-v2-1741-randomlightup-024630b9`<br>`pgu-storymode-0-v2-1955-rgbon-54a31a5d`<br>`pgu-storymode-0-v2-2141-rgbon-9d2ca258` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v2-606-randomflashwithgap-multiple-92dd43b6`<br>`pgu-storymode-0-v2-1005-randomlightup-fc9cbd8b`<br>`pgu-storymode-0-v2-1391-randomlightup-9bc0195a`<br>`pgu-storymode-0-v2-1748-randomlightup-ff17367b`<br>`pgu-storymode-0-v2-1957-rgbon-8ff82eec`<br>`pgu-storymode-0-v2-2143-rgbon-7ca171ed` |
| STAGED | RGB4 | Hi-Nu Slave 8/10 RGB4 (42 粒) 腿部訊號：與其他腿部 RGB 同步長亮。 | `rgbOn` | `pgu-storymode-0-v2-1960-rgbon-83f8d002`<br>`pgu-storymode-0-v2-2146-rgbon-4bc2ff28` |
| STAGED | RGB4 | Hi-Nu Slave 8/10 RGB4 (42 粒) 腿部訊號：與其他腿部 RGB 同步隨機亮起。 | `randomLightUp` | `pgu-storymode-0-v2-1013-randomlightup-674b8fd0`<br>`pgu-storymode-0-v2-1399-randomlightup-bda9756e`<br>`pgu-storymode-0-v2-1756-randomlightup-9f09258d` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `randomFlashWithGap_multiple` | `pgu-storymode-0-v2-613-randomflashwithgap-multiple-e28cee9c` |
| STAGED | RGB7 | UNCONFIRMED COMPONENT — RGB7 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v2-620-randomflashwithgap-multiple-32ba20d7`<br>`pgu-storymode-0-v2-1020-randomlightup-a7451ee3`<br>`pgu-storymode-0-v2-1406-randomlightup-c7519570`<br>`pgu-storymode-0-v2-1763-randomlightup-e94aaf65`<br>`pgu-storymode-0-v2-1962-rgbon-880b74c3`<br>`pgu-storymode-0-v2-2148-rgbon-216fa10d` |
| STAGED | RGB8 | UNCONFIRMED COMPONENT — RGB8 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v2-627-randomflashwithgap-multiple-2c3b0208`<br>`pgu-storymode-0-v2-1027-randomlightup-5fad5866`<br>`pgu-storymode-0-v2-1413-randomlightup-f27f6561`<br>`pgu-storymode-0-v2-1770-randomlightup-11702929`<br>`pgu-storymode-0-v2-1964-rgbon-a1751b28`<br>`pgu-storymode-0-v2-2150-rgbon-a648b183` |
| STAGED | RGB9 | UNCONFIRMED COMPONENT — RGB9 | `randomLightUp` | `pgu-storymode-0-v2-1034-randomlightup-6bac79d3`<br>`pgu-storymode-0-v2-1420-randomlightup-18782fa3` |
| STAGED | Runtime／group target 'strips' | UNCONFIRMED COMPONENT — Runtime／group target 'strips' | `randomFlashFixedCount_multiple` | `pgu-storymode-0-v2-262-randomflashfixedcount-multiple-290d18b8` |

### storyMode_storing_energy

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB1 | Hi-Nu Slave 8/10 左右腿 RGB：滿能量時共用同一套效果與接線。 | `renderSlave78Rgb1StorySpecificColor` | `pgu-storymode-storing-energy-1417-renderslave78rgb1storyspecificcolor-ed28ee22` |
| STAGED | RGB1 | Hi-Nu Slave 8/10 左右腿上段 RGB — shared PGU Slave 7 RGB source. | `paletteWave_80Percent_SpecialWave` | `pgu-storymode-storing-energy-779-palettewave-80percent-specialwave-08e4d8a1` |
| STAGED | RGB2 | Hi-Nu Slave 8/10 RGB2/3/4：儲能初始化時保持關閉。 | `rgbOff` | `pgu-storymode-storing-energy-439-rgboff-18c69cf1` |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `GN_Wire_Normal`、`paletteWave_80Percent_SpecialWave` | `pgu-storymode-storing-energy-788-palettewave-80percent-specialwave-0f4b3ddc`<br>`pgu-storymode-storing-energy-1419-gn-wire-normal-1e63e9b7` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `rgbOff` | `pgu-storymode-storing-energy-440-rgboff-620e3b63` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `SpecificColorPattern`、`rgbOff` | `pgu-storymode-storing-energy-442-rgboff-7b05a8ed`<br>`pgu-storymode-storing-energy-809-rgboff-09b587c3`<br>`pgu-storymode-storing-energy-1442-specificcolorpattern-0baaf235` |
| STAGED | RGB7 | Slave 8 RGB7 (63粒) 左膝關節／大漩渦：儲能渦輪。 | `turbine_v3` | `pgu-storymode-storing-energy-798-turbine-v3-f56b6625` |
| STAGED | RGB7 | Slave 8 RGB7 (63粒) 左膝關節／大漩渦：滿能量渦輪。 | `turbine_v3` | `pgu-storymode-storing-energy-1431-turbine-v3-d6177cec` |
| STAGED | RGB8 | Slave 8 RGB8 (49粒) 左腳腳底燈：滿能量 footplate。 | `footplatev2` | `pgu-storymode-storing-energy-1449-footplatev2-a9907858` |
| ON | Runtime／group target 'espLed[channel]' | Hi-Nu Slave 8/10 GPIO48 白燈 4 粒；GPIO47／45／42 紅燈：儲能全程每幀低亮長亮。 | `chOn` | `pgu-storymode-storing-energy-305-chon-e22625cf` |

### storyMode_2

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `gradientVentPalette`、`randomFillAll_V2` | `pgu-storymode-2-486-randomfillall-v2-ee59ebb1`<br>`pgu-storymode-2-495-gradientventpalette-945968f1` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `SpecificColorPattern` | `pgu-storymode-2-543-specificcolorpattern-8a4df028` |
| STAGED | RGB7 | Slave 8 RGB7 (63粒) 左膝關節／大漩渦：長著模式渦輪。 | `turbine_v3` | `pgu-storymode-2-516-turbine-v3-a54a0ccb` |
| STAGED | RGB8 | Slave 8 RGB8 (49粒) 左腳腳底燈：長著模式 footplate。 | `footplatev2` | `pgu-storymode-2-529-footplatev2-42349674` |
| STAGED | Runtime／group target 'espLed[channel]' | GPIO48 白燈 4 粒；GPIO47／45／42 紅燈：Normal 模式低亮長亮。 | `chOn` | `pgu-storymode-2-550-chon-06ce96d3` |

### storyMode_plasma

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB4 | Hi-Nu Slave 8/10 RGB4：共用 42 粒腿部訊號 Normal profile。 | `SpecificColorPattern` | `pgu-storymode-plasma-673-specificcolorpattern-bbbb180d` |
| ON | Runtime／group target 'espLed[channel]' | Hi-Nu Slave 8/10 GPIO48 白燈 4 粒；GPIO47／45／42 紅燈：Plasma 全程每幀低亮長亮。 | `chOn` | `pgu-storymode-plasma-62-chon-77ce5cc1` |

### storyMode_trans_am

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB1 | Hi-Nu Slave 8/10 左右腿 RGB：兩側共用同一套效果與接線。 | `GN_Drive_Running` | `pgu-storymode-trans-am-361-gn-drive-running-a1c9c2d3` |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `GN_Wire_TransAM` | `pgu-storymode-trans-am-372-gn-wire-transam-fad757a0` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `SpecificColorPattern` | `pgu-storymode-trans-am-412-specificcolorpattern-54da8473` |
| STAGED | RGB7 | Slave 8 RGB7 (63粒) 左膝關節／大漩渦：Trans-Am 渦輪。 | `turbine_v3` | `pgu-storymode-trans-am-385-turbine-v3-18ef4d66` |
| STAGED | RGB8 | Slave 8 RGB8 (49粒) 左腳腳底燈：Trans-Am footplate。 | `footplatev2` | `pgu-storymode-trans-am-398-footplatev2-4324bcfd` |
| STAGED | Runtime／group target 'espLed[channel]' | GPIO48 白燈 4 粒；GPIO47／45／42 紅燈：Trans-Am 模式低亮長亮。 | `chOn` | `pgu-storymode-trans-am-420-chon-add4fee6` |

### storyMode_3

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB2 | Hi-Nu Slave 8/10 左右腿上段 RGB — shared PGU Slave 7 RGB source. | `gradientVentPalette` | `pgu-storymode-3-514-gradientventpalette-11629449` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `SpecificColorPattern` | `pgu-storymode-3-562-specificcolorpattern-567c9d50` |
| STAGED | RGB7 | Slave 8 RGB7 (63粒) 左膝關節／大漩渦：呼吸模式渦輪。 | `turbine_v3` | `pgu-storymode-3-535-turbine-v3-053276bf` |
| STAGED | RGB8 | Slave 8 RGB8 (49粒) 左腳腳底燈：呼吸模式 footplate。 | `footplatev2` | `pgu-storymode-3-548-footplatev2-88571b47` |
| STAGED | Runtime／group target 'espLed[channel]' | GPIO48 白燈 4 粒；GPIO47／45／42 紅燈：呼吸模式低亮長亮。 | `chOn` | `pgu-storymode-3-570-chon-b5fd1004` |

### storyMode_idle

OFF／no direct call in this Slave context。

### storyMode_motor

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | All PCA／channel output | Slave 8 GPIO48／47／45／42 單色燈：保持 20%。 | `chOnAll` | `pgu-storymode-motor-551-chonall-56d52b7c` |
| STAGED | All PCA／channel output | Slave 8 GPIO48／47／45／42 單色燈：同步淡入至 20%。 | `chOnAll` | `pgu-storymode-motor-357-chonall-bb7c807b` |
| STAGED | RGB1 | UNCONFIRMED COMPONENT — RGB1 | `rgbOff` | `pgu-storymode-motor-304-rgboff-caa38919`<br>`pgu-storymode-motor-563-rgboff-75625402` |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `VentEffect`、`rgbOff` | `pgu-storymode-motor-305-rgboff-88ca7a64`<br>`pgu-storymode-motor-500-venteffect-e8ee854e`<br>`pgu-storymode-motor-520-rgboff-259eccb7`<br>`pgu-storymode-motor-564-rgboff-254d7d12` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `rgbOff` | `pgu-storymode-motor-306-rgboff-96a1c0cf`<br>`pgu-storymode-motor-565-rgboff-343ea7db` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `SpecificColorPattern`、`rgbOff` | `pgu-storymode-motor-307-rgboff-cdd4677a`<br>`pgu-storymode-motor-346-specificcolorpattern-aca35478`<br>`pgu-storymode-motor-468-specificcolorpattern-1ad863a1`<br>`pgu-storymode-motor-475-specificcolorpattern-299ff24e`<br>`pgu-storymode-motor-566-rgboff-8e7fbb41` |
| STAGED | RGB7 | Slave 8 RGB7 (63粒) 左膝關節／大漩渦：20% 上限渦輪效果。 | `turbine_v3_sound` | `pgu-storymode-motor-524-turbine-v3-sound-7a70bd98` |
| STAGED | RGB7 | UNCONFIRMED COMPONENT — RGB7 | `rgbOff` | `pgu-storymode-motor-308-rgboff-568a59bf`<br>`pgu-storymode-motor-567-rgboff-670e0cf1` |
| STAGED | RGB8 | Slave 8 RGB8 (49粒) 左腳腳底燈：20% 上限 footplate 效果。 | `footplatev2` | `pgu-storymode-motor-537-footplatev2-8fda3de5` |
| STAGED | RGB8 | UNCONFIRMED COMPONENT — RGB8 | `rgbOff` | `pgu-storymode-motor-309-rgboff-42cc6e9f`<br>`pgu-storymode-motor-568-rgboff-a6f4055f` |
| STAGED | Runtime／group target 'slaveId' | UNCONFIRMED COMPONENT — Runtime／group target 'slaveId' | `RGBActivationCometCross` | `pgu-storymode-motor-361-rgbactivationcometcross-1112c67a` |

### storyMode_motor_reset

OFF／no direct call in this Slave context。

## Slave 11

### storyMode_develop

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB1 | Hi-Nu Slave 19/20 左右腳掌 RGB — shared PGU Slave 7 RGB source. | `rgbOff` | `pgu-storymode-develop-232-rgboff-cd9c19be` |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `rgbOff` | `pgu-storymode-develop-233-rgboff-b222cedb` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `rgbOff` | `pgu-storymode-develop-234-rgboff-fb9fcc55` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `SpecificColorPattern` | `pgu-storymode-develop-235-specificcolorpattern-9ec0269b` |

### storyMode_signals

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB4 | Hi-Nu Slave 19/20 左右腳掌 RGB — shared PGU Slave 7 RGB source. | `SpecificColorPattern` | `pgu-storymode-signals-187-specificcolorpattern-40e9ed43` |

### storyMode_0_v1

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB1 | Hi-Nu Slave 19/20 左右腳掌 RGB — shared PGU Slave 7 RGB source. | `randomFlashWithGap_multiple`、`randomLightUp` | `pgu-storymode-0-v1-569-randomflashwithgap-multiple-6e1ce021`<br>`pgu-storymode-0-v1-2279-randomlightup-3e9945d1` |
| STAGED | RGB1 | UNCONFIRMED COMPONENT — RGB1 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v1-922-randomflashwithgap-multiple-7a837a14`<br>`pgu-storymode-0-v1-1399-randomlightup-46f159ad`<br>`pgu-storymode-0-v1-1860-randomlightup-71795bb8`<br>`pgu-storymode-0-v1-2494-rgbon-9534d053`<br>`pgu-storymode-0-v1-3050-rgbon-27c680ae` |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v1-576-randomflashwithgap-multiple-d38a0466`<br>`pgu-storymode-0-v1-929-randomflashwithgap-multiple-3864e3ce`<br>`pgu-storymode-0-v1-1406-randomlightup-eeaa9563`<br>`pgu-storymode-0-v1-1867-randomlightup-2e8d3d42`<br>`pgu-storymode-0-v1-2286-randomlightup-43d01ff8`<br>`pgu-storymode-0-v1-2496-rgbon-2c226342`<br>`pgu-storymode-0-v1-3052-rgbon-462411d1` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v1-583-randomflashwithgap-multiple-e4e814fe`<br>`pgu-storymode-0-v1-936-randomflashwithgap-multiple-9ab206d9`<br>`pgu-storymode-0-v1-1413-randomlightup-f801d52e`<br>`pgu-storymode-0-v1-1874-randomlightup-255732f2`<br>`pgu-storymode-0-v1-2293-randomlightup-1a979921`<br>`pgu-storymode-0-v1-2498-rgbon-3fab67c8`<br>`pgu-storymode-0-v1-3054-rgbon-cb844724` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v1-590-randomflashwithgap-multiple-dadbbf6a`<br>`pgu-storymode-0-v1-943-randomflashwithgap-multiple-03c667ba`<br>`pgu-storymode-0-v1-1421-randomlightup-3520cdf0`<br>`pgu-storymode-0-v1-1881-randomlightup-55a0c4d9`<br>`pgu-storymode-0-v1-2300-randomlightup-ce156ffa`<br>`pgu-storymode-0-v1-2501-rgbon-5e21ac60`<br>`pgu-storymode-0-v1-3057-rgbon-16e8bfd6` |

### storyMode_awakening_3

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB2 | Hi-Nu Slave 19/20 左右腳掌 RGB — shared PGU Slave 7 RGB source. | `rgbOff` | `pgu-storymode-awakening-3-351-rgboff-aec52258` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `rgbOff` | `pgu-storymode-awakening-3-353-rgboff-054b6761` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `rgbOff` | `pgu-storymode-awakening-3-355-rgboff-0b886234` |
| STAGED | Runtime／group target 'espLed[0]' | (左／右腳掌) 後腳踭紅燈及腳掌白燈：espLed[0-3] 與 RGB1 同週期呼吸。 | `chBreath` | `pgu-storymode-awakening-3-358-chbreath-6c2a7e9a` |
| STAGED | Runtime／group target 'espLed[1]' | UNCONFIRMED COMPONENT — Runtime／group target 'espLed[1]' | `chBreath` | `pgu-storymode-awakening-3-359-chbreath-26e237ad` |
| STAGED | Runtime／group target 'espLed[2]' | UNCONFIRMED COMPONENT — Runtime／group target 'espLed[2]' | `chBreath` | `pgu-storymode-awakening-3-360-chbreath-f31355bc` |
| STAGED | Runtime／group target 'espLed[3]' | UNCONFIRMED COMPONENT — Runtime／group target 'espLed[3]' | `chBreath` | `pgu-storymode-awakening-3-361-chbreath-d27db3aa` |

### storyMode_activation

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `gradientVentPalette`、`randomFillAll_V2` | `pgu-storymode-activation-603-randomfillall-v2-43b9819d`<br>`pgu-storymode-activation-606-gradientventpalette-69f93047` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `turbine_v3` | `pgu-storymode-activation-622-turbine-v3-011e8747` |
| STAGED | RGB4 | Hi-Nu Slave 19/20 左右腳掌 RGB — shared PGU Slave 7 RGB source. | `SpecificColorPattern` | `pgu-storymode-activation-595-specificcolorpattern-f210bb16` |

### storyMode_0_v2

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB1 | Hi-Nu Slave 19/20 左右腳掌 RGB — shared PGU Slave 7 RGB source. | `randomLightUp` | `pgu-storymode-0-v2-1782-randomlightup-e7d0c4af` |
| STAGED | RGB1 | UNCONFIRMED COMPONENT — RGB1 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v2-646-randomflashwithgap-multiple-1d73a958`<br>`pgu-storymode-0-v2-1051-randomlightup-d6865cfd`<br>`pgu-storymode-0-v2-1438-randomlightup-f21ef008`<br>`pgu-storymode-0-v2-1977-rgbon-a97241a2`<br>`pgu-storymode-0-v2-2163-rgbon-cf5daa50` |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v2-653-randomflashwithgap-multiple-c183fb6f`<br>`pgu-storymode-0-v2-1058-randomlightup-762e453a`<br>`pgu-storymode-0-v2-1445-randomlightup-349341d3`<br>`pgu-storymode-0-v2-1789-randomlightup-e166e14d`<br>`pgu-storymode-0-v2-1979-rgbon-d123171f`<br>`pgu-storymode-0-v2-2165-rgbon-1a3447c9` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v2-660-randomflashwithgap-multiple-16bff609`<br>`pgu-storymode-0-v2-1065-randomlightup-d7294d5c`<br>`pgu-storymode-0-v2-1452-randomlightup-9407d3f7`<br>`pgu-storymode-0-v2-1796-randomlightup-abcf061a`<br>`pgu-storymode-0-v2-1981-rgbon-c54e2357`<br>`pgu-storymode-0-v2-2167-rgbon-a3fc1ed5` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v2-667-randomflashwithgap-multiple-e57728bf`<br>`pgu-storymode-0-v2-1073-randomlightup-f3428508`<br>`pgu-storymode-0-v2-1459-randomlightup-edc73f29`<br>`pgu-storymode-0-v2-1804-randomlightup-cb8ac12a`<br>`pgu-storymode-0-v2-1984-rgbon-f1131ca9`<br>`pgu-storymode-0-v2-2170-rgbon-c1668c0d` |
| STAGED | Runtime／group target 'strips' | UNCONFIRMED COMPONENT — Runtime／group target 'strips' | `randomFlashFixedCount_multiple` | `pgu-storymode-0-v2-285-randomflashfixedcount-multiple-d8f707cd` |

### storyMode_storing_energy

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB1 | Hi-Nu Slave 19/20 左右腳掌 RGB — shared PGU Slave 7 RGB source. | `paletteWave_80Percent_SpecialWave`、`renderSlave78Rgb1StorySpecificColor` | `pgu-storymode-storing-energy-815-palettewave-80percent-specialwave-7b2f89e4`<br>`pgu-storymode-storing-energy-1464-renderslave78rgb1storyspecificcolor-105ae191` |
| STAGED | RGB2 | Hi-Nu Slave 19/20 左右腳掌 RGB — shared PGU Slave 7 RGB source. | `rgbOff` | `pgu-storymode-storing-energy-448-rgboff-895ab9e1` |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `GN_Wire_Normal`、`paletteWave_80Percent_SpecialWave` | `pgu-storymode-storing-energy-824-palettewave-80percent-specialwave-b02ffc06`<br>`pgu-storymode-storing-energy-1466-gn-wire-normal-72e0a923` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `rgbOff`、`turbine_v3` | `pgu-storymode-storing-energy-449-rgboff-7cf852ac`<br>`pgu-storymode-storing-energy-833-turbine-v3-0ffe89f3`<br>`pgu-storymode-storing-energy-1477-turbine-v3-b4b255a8` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `SpecificColorPattern`、`rgbOff` | `pgu-storymode-storing-energy-451-rgboff-72712967`<br>`pgu-storymode-storing-energy-844-rgboff-70071ea6`<br>`pgu-storymode-storing-energy-1488-specificcolorpattern-baf42f24` |

### storyMode_2

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `gradientVentPalette`、`randomFillAll_V2` | `pgu-storymode-2-566-randomfillall-v2-e1218298`<br>`pgu-storymode-2-575-gradientventpalette-fcf76e9f` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `turbine_v3` | `pgu-storymode-2-595-turbine-v3-38966b7a` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `SpecificColorPattern` | `pgu-storymode-2-607-specificcolorpattern-8261079a` |

### storyMode_plasma

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB4 | Hi-Nu Slave 9/11 左右腳掌 RGB — shared PGU Slave 7 RGB source. | `SpecificColorPattern` | `pgu-storymode-plasma-683-specificcolorpattern-0cb64a28` |

### storyMode_trans_am

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB1 | Hi-Nu Slave 19/20 左右腳掌 RGB — shared PGU Slave 7 RGB source. | `GN_Drive_Running` | `pgu-storymode-trans-am-433-gn-drive-running-558dd4be` |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `GN_Wire_TransAM` | `pgu-storymode-trans-am-444-gn-wire-transam-a760d0c4` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `turbine_v3` | `pgu-storymode-trans-am-456-turbine-v3-be937ee7` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `SpecificColorPattern` | `pgu-storymode-trans-am-468-specificcolorpattern-a8bc8918` |

### storyMode_3

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB2 | Hi-Nu Slave 19/20 左右腳掌 RGB — shared PGU Slave 7 RGB source. | `gradientVentPalette` | `pgu-storymode-3-583-gradientventpalette-b96aedc7` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `turbine_v3` | `pgu-storymode-3-603-turbine-v3-6530d150` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `SpecificColorPattern` | `pgu-storymode-3-615-specificcolorpattern-ffae20b5` |

### storyMode_idle

OFF／no direct call in this Slave context。

### storyMode_motor

OFF／no direct call in this Slave context。

### storyMode_motor_reset

OFF／no direct call in this Slave context。

## Slave 12

### storyMode_develop

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB1 | Hi-Nu Slave 12 RGB1 (138 粒) 背包流光：Develop 保持關閉。 | `rgbOff` | `pgu-storymode-develop-261-rgboff-78fb3bed` |
| STAGED | RGB2 | Hi-Nu Slave 12 RGB2 (134 粒) 背包散氣：Develop 保持關閉。 | `rgbOff` | `pgu-storymode-develop-263-rgboff-3ce40333` |
| STAGED | RGB3 | Hi-Nu Slave 12 RGB3 (10 粒) 背包大漩渦：Develop 保持關閉。 | `rgbOff` | `pgu-storymode-develop-265-rgboff-9711cc51` |
| STAGED | RGB4 | Hi-Nu Slave 12 RGB4 (10 粒) 背包訊號：使用獨立 Develop profile。 | `SpecificColorPattern` | `pgu-storymode-develop-267-specificcolorpattern-9dc9c5fb` |

### storyMode_signals

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB1 | Hi-Nu Slave 12 RGB1 (138 粒) 背包流光：Repair 訊號模式保持關閉。 | `rgbOff` | `pgu-storymode-signals-302-rgboff-55949eef` |
| STAGED | RGB2 | Hi-Nu Slave 12 RGB2 (134 粒) 背包散氣：Repair 訊號模式保持關閉。 | `rgbOff` | `pgu-storymode-signals-304-rgboff-856d3233` |
| STAGED | RGB3 | Hi-Nu Slave 12 RGB3 (10 粒) 背包大漩渦：Repair 訊號模式保持關閉。 | `rgbOff` | `pgu-storymode-signals-306-rgboff-19216556` |
| STAGED | RGB4 | Hi-Nu Slave 12 RGB4 (10 粒) 背包訊號：使用獨立 Repair profile。 | `SpecificColorPattern` | `pgu-storymode-signals-308-specificcolorpattern-5ad5e6eb` |

### storyMode_0_v1

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB1 | Hi-Nu Slave 12 RGB1-4：全部白色長亮。 | `rgbOn` | `pgu-storymode-0-v1-2521-rgbon-1c29b43a`<br>`pgu-storymode-0-v1-3077-rgbon-765a7651` |
| STAGED | RGB1 | Hi-Nu Slave 12 RGB1-4：分段隨機亮起。 | `randomLightUp` | `pgu-storymode-0-v1-1454-randomlightup-1fe3d71d`<br>`pgu-storymode-0-v1-1912-randomlightup-00e969ca`<br>`pgu-storymode-0-v1-2338-randomlightup-5098dc49` |
| STAGED | RGB1 | Hi-Nu Slave 12 RGB1-4：白色 random flash。 | `randomFlashWithGap_multiple` | `pgu-storymode-0-v1-981-randomflashwithgap-multiple-f2cbd8c0` |
| STAGED | RGB2 | Hi-Nu Slave 12 RGB1 (138 粒) 背包流光：由跨 Slave 白色 comet 控制。 ／ Hi-Nu Slave 12 RGB2 (134 粒) 背包散氣：白色 comet 階段保持關閉。 | `rgbOff` | `pgu-storymode-0-v1-257-rgboff-badc782f` |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v1-987-randomflashwithgap-multiple-d67c489c`<br>`pgu-storymode-0-v1-1459-randomlightup-930015c9`<br>`pgu-storymode-0-v1-1917-randomlightup-bce6c76e`<br>`pgu-storymode-0-v1-2343-randomlightup-fbb3b758`<br>`pgu-storymode-0-v1-2522-rgbon-be0ab2ec`<br>`pgu-storymode-0-v1-3078-rgbon-cc1dbb95` |
| STAGED | RGB3 | Hi-Nu Slave 12 RGB3 (10 粒) 背包大漩渦：白色 comet 階段保持關閉。 | `rgbOff` | `pgu-storymode-0-v1-259-rgboff-7916bad1` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v1-993-randomflashwithgap-multiple-9a24e2b4`<br>`pgu-storymode-0-v1-1464-randomlightup-071f72ed`<br>`pgu-storymode-0-v1-1922-randomlightup-5a41f961`<br>`pgu-storymode-0-v1-2348-randomlightup-855519cb`<br>`pgu-storymode-0-v1-2523-rgbon-04abdb0f`<br>`pgu-storymode-0-v1-3079-rgbon-6ef8485c` |
| STAGED | RGB4 | Hi-Nu Slave 12 RGB4 (10 粒) 背包訊號：白色 comet 階段保持關閉。 | `rgbOff` | `pgu-storymode-0-v1-261-rgboff-c9651a19` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v1-999-randomflashwithgap-multiple-ff53c5d4`<br>`pgu-storymode-0-v1-1469-randomlightup-061323b0`<br>`pgu-storymode-0-v1-1927-randomlightup-03351be8`<br>`pgu-storymode-0-v1-2353-randomlightup-74d21ef4`<br>`pgu-storymode-0-v1-2524-rgbon-37a0a17a`<br>`pgu-storymode-0-v1-3080-rgbon-933c43d0` |
| STAGED | Runtime／group target 'strips' | UNCONFIRMED COMPONENT — Runtime／group target 'strips' | `randomFlashFixedCount_multiple` | `pgu-storymode-0-v1-630-randomflashfixedcount-multiple-ab9bc810` |

### storyMode_awakening_3

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB2 | Hi-Nu Slave 12 RGB1 (138 粒) 背包流光：由跨 Slave 白色流光控制。 ／ Hi-Nu Slave 12 RGB2 (134 粒) 背包散氣：Awakening 保持關閉。 | `rgbOff` | `pgu-storymode-awakening-3-430-rgboff-12690d7d` |
| STAGED | RGB3 | Hi-Nu Slave 12 RGB3 (10 粒) 背包大漩渦：Awakening 保持關閉。 | `rgbOff` | `pgu-storymode-awakening-3-432-rgboff-8a8fea0b` |
| STAGED | RGB4 | Hi-Nu Slave 12 RGB4 (10 粒) 背包訊號：Awakening 保持關閉。 | `rgbOff` | `pgu-storymode-awakening-3-434-rgboff-d911428e` |

### storyMode_activation

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB2 | Hi-Nu Slave 12 RGB1 (138 粒) 背包流光：由跨 Slave 啟動流光控制。 ／ Hi-Nu Slave 12 RGB2 (134 粒) 背包散氣。 | `gradientVentPalette` | `pgu-storymode-activation-715-gradientventpalette-49aaa0be` |
| STAGED | RGB3 | Hi-Nu Slave 12 RGB3 (10 粒) 背包大漩渦。 | `GN_Drive_Normal` | `pgu-storymode-activation-735-gn-drive-normal-93be9460` |
| STAGED | RGB4 | Hi-Nu Slave 12 RGB4 (10 粒) 背包訊號：使用獨立 Normal profile。 | `SpecificColorPattern` | `pgu-storymode-activation-746-specificcolorpattern-849e885d` |

### storyMode_0_v2

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB1 | Hi-Nu Slave 12 RGB1-4：全部白色長亮。 | `rgbOn` | `pgu-storymode-0-v2-2004-rgbon-32f41b05`<br>`pgu-storymode-0-v2-2190-rgbon-fb322a2a` |
| STAGED | RGB1 | Hi-Nu Slave 12 RGB1-4：分段隨機亮起。 | `randomLightUp` | `pgu-storymode-0-v2-1106-randomlightup-70622c93`<br>`pgu-storymode-0-v2-1497-randomlightup-f430ecc2`<br>`pgu-storymode-0-v2-1844-randomlightup-1e0d24e4` |
| STAGED | RGB1 | Hi-Nu Slave 12 RGB1-4：白色 random flash。 | `randomFlashWithGap_multiple` | `pgu-storymode-0-v2-706-randomflashwithgap-multiple-5677ee59` |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v2-712-randomflashwithgap-multiple-acff12b3`<br>`pgu-storymode-0-v2-1111-randomlightup-1f1d7bb4`<br>`pgu-storymode-0-v2-1501-randomlightup-67fae05d`<br>`pgu-storymode-0-v2-1848-randomlightup-3061df16`<br>`pgu-storymode-0-v2-2005-rgbon-2fdb5341`<br>`pgu-storymode-0-v2-2191-rgbon-62bfe65c` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v2-718-randomflashwithgap-multiple-f3806c94`<br>`pgu-storymode-0-v2-1116-randomlightup-6a53d1e1`<br>`pgu-storymode-0-v2-1505-randomlightup-b0a994d7`<br>`pgu-storymode-0-v2-1852-randomlightup-97876ca5`<br>`pgu-storymode-0-v2-2006-rgbon-289b4289`<br>`pgu-storymode-0-v2-2192-rgbon-8d9868a0` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v2-724-randomflashwithgap-multiple-6073aaf5`<br>`pgu-storymode-0-v2-1121-randomlightup-b8c3b117`<br>`pgu-storymode-0-v2-1509-randomlightup-db3be256`<br>`pgu-storymode-0-v2-1856-randomlightup-8467503c`<br>`pgu-storymode-0-v2-2007-rgbon-d567daa8`<br>`pgu-storymode-0-v2-2193-rgbon-0e5a696d` |
| STAGED | Runtime／group target 'strips' | UNCONFIRMED COMPONENT — Runtime／group target 'strips' | `randomFlashFixedCount_multiple` | `pgu-storymode-0-v2-329-randomflashfixedcount-multiple-dda3ae6b` |

### storyMode_storing_energy

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB1 | Hi-Nu Slave 12 RGB1 (138 粒) 背包流光：80% 儲能波。 | `paletteWave_80Percent_SpecialWave` | `pgu-storymode-storing-energy-911-palettewave-80percent-specialwave-7d78eaac` |
| STAGED | RGB1 | Hi-Nu Slave 12 RGB1 (138 粒) 背包流光：儲能初始化保持關閉。 | `rgbOff` | `pgu-storymode-storing-energy-518-rgboff-7cb26db3` |
| STAGED | RGB2 | Hi-Nu Slave 12 RGB2 (134 粒) 背包散氣：儲能初始化保持關閉。 | `rgbOff` | `pgu-storymode-storing-energy-520-rgboff-f58745fb` |
| STAGED | RGB3 | Hi-Nu Slave 12 RGB3 (10 粒) 背包大漩渦：儲能初始化保持關閉。 | `rgbOff` | `pgu-storymode-storing-energy-522-rgboff-3a9b8863` |
| STAGED | RGB4 | Hi-Nu Slave 12 RGB4 (10 粒) 背包訊號：儲能初始化保持關閉。 | `rgbOff` | `pgu-storymode-storing-energy-524-rgboff-b57e0fb2` |

### storyMode_2

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB2 | Hi-Nu Slave 12 RGB1 (138 粒) 背包流光：由跨 Slave Normal 流光控制。 ／ Hi-Nu Slave 12 RGB2 (134 粒) 背包散氣。 | `gradientVentPalette` | `pgu-storymode-2-883-gradientventpalette-c5031714` |
| STAGED | RGB3 | Hi-Nu Slave 12 RGB3 (10 粒) 背包大漩渦。 | `turbine_v3` | `pgu-storymode-2-903-turbine-v3-08cebe24` |
| STAGED | RGB4 | Hi-Nu Slave 12 RGB4 (10 粒) 背包訊號：使用獨立 Normal profile。 | `SpecificColorPattern` | `pgu-storymode-2-914-specificcolorpattern-d4e382d4` |

### storyMode_plasma

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB4 | Hi-Nu Slave 12 RGB4 (10 粒) 背包訊號：Plasma 第四階段使用獨立 Normal profile。 | `SpecificColorPattern` | `pgu-storymode-plasma-694-specificcolorpattern-9dcff5ec` |

### storyMode_trans_am

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB1 | Hi-Nu Slave 12 RGB1 (138 粒) 背包流光。 | `GN_Drive_Running` | `pgu-storymode-trans-am-545-gn-drive-running-4cdf00f3` |
| STAGED | RGB2 | Hi-Nu Slave 12 RGB2 (134 粒) 背包散氣。 | `VentEffect` | `pgu-storymode-trans-am-556-venteffect-9e401faa` |
| STAGED | RGB3 | Hi-Nu Slave 12 RGB3 (10 粒) 背包大漩渦。 | `turbine_v3` | `pgu-storymode-trans-am-567-turbine-v3-ae71f30d` |
| STAGED | RGB4 | Hi-Nu Slave 12 RGB4 (10 粒) 背包訊號：使用獨立 Normal profile。 | `SpecificColorPattern` | `pgu-storymode-trans-am-578-specificcolorpattern-4ded1970` |

### storyMode_3

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB2 | Hi-Nu Slave 12 RGB1 (138 粒) 背包流光：由跨 Slave Normal 流光控制。 ／ Hi-Nu Slave 12 RGB2 (134 粒) 背包散氣。 | `VentEffect` | `pgu-storymode-3-693-venteffect-c352cbdc` |
| STAGED | RGB3 | Hi-Nu Slave 12 RGB3 (10 粒) 背包大漩渦。 | `GN_Capacitor_Normal` | `pgu-storymode-3-704-gn-capacitor-normal-4c3b1c35` |
| STAGED | RGB4 | Hi-Nu Slave 12 RGB4 (10 粒) 背包訊號：使用獨立 Normal profile。 | `SpecificColorPattern` | `pgu-storymode-3-716-specificcolorpattern-49c14675` |

### storyMode_idle

OFF／no direct call in this Slave context。

### storyMode_motor

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB1 | Hi-Nu Slave 12 RGB1 (138 粒) 背包流光。 | `GN_Drive_Running` | `pgu-storymode-motor-1286-gn-drive-running-c545fa73` |
| STAGED | RGB2 | Hi-Nu Slave 12 RGB2 (134 粒) 背包散氣。 | `VentEffect` | `pgu-storymode-motor-1297-venteffect-9da22b69` |
| STAGED | RGB3 | Hi-Nu Slave 12 RGB3 (10 粒) 背包大漩渦。 | `turbine_v3` | `pgu-storymode-motor-1308-turbine-v3-c7aeecbe` |
| STAGED | RGB4 | Hi-Nu Slave 12 RGB1 (138 粒) 背包流光：Prelude 由跨 Slave comet 控制。 ／ Hi-Nu Slave 12 RGB4 (10 粒) 背包訊號：3 秒起使用獨立 Normal profile。 | `SpecificColorPattern` | `pgu-storymode-motor-744-specificcolorpattern-7d0840d2` |
| STAGED | RGB4 | Hi-Nu Slave 12 RGB4 (10 粒) 背包訊號：Motor 模式維持獨立 Normal profile。 | `SpecificColorPattern` | `pgu-storymode-motor-1319-specificcolorpattern-22dcf529` |

### storyMode_motor_reset

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB1 | Hi-Nu Slave 12 RGB1 (138 粒) 背包流光：Motor reset 保持關閉。 | `rgbOff` | `pgu-storymode-motor-reset-590-rgboff-d965df70`<br>`pgu-storymode-motor-reset-788-rgboff-7d61518d`<br>`pgu-storymode-motor-reset-959-rgboff-d58423f0`<br>`pgu-storymode-motor-reset-1135-rgboff-fbe501e8` |
| STAGED | RGB2 | Hi-Nu Slave 12 RGB2 (134 粒) 背包散氣：Motor reset 保持關閉。 | `rgbOff` | `pgu-storymode-motor-reset-592-rgboff-8fd8a96f`<br>`pgu-storymode-motor-reset-790-rgboff-47f36de3`<br>`pgu-storymode-motor-reset-961-rgboff-2bfefcb1`<br>`pgu-storymode-motor-reset-1137-rgboff-c5af50f0` |
| STAGED | RGB3 | Hi-Nu Slave 12 RGB3 (10 粒) 背包大漩渦：Motor reset 保持關閉。 | `rgbOff` | `pgu-storymode-motor-reset-594-rgboff-a9f58e92`<br>`pgu-storymode-motor-reset-792-rgboff-8e069509`<br>`pgu-storymode-motor-reset-963-rgboff-a329ff49`<br>`pgu-storymode-motor-reset-1139-rgboff-76dcd313` |
| STAGED | RGB4 | Hi-Nu Slave 12 RGB4 (10 粒) 背包訊號：Motor reset 使用獨立 Repair profile。 | `SpecificColorPattern` | `pgu-storymode-motor-reset-596-specificcolorpattern-d0154831`<br>`pgu-storymode-motor-reset-794-specificcolorpattern-483c5ca7`<br>`pgu-storymode-motor-reset-965-specificcolorpattern-b55ad4f0`<br>`pgu-storymode-motor-reset-1141-specificcolorpattern-7218d97c` |

## Slave 13

### storyMode_develop

OFF／no direct call in this Slave context。

### storyMode_signals

OFF／no direct call in this Slave context。

### storyMode_0_v1

OFF／no direct call in this Slave context。

### storyMode_awakening_3

OFF／no direct call in this Slave context。

### storyMode_activation

OFF／no direct call in this Slave context。

### storyMode_0_v2

OFF／no direct call in this Slave context。

### storyMode_storing_energy

OFF／no direct call in this Slave context。

### storyMode_2

OFF／no direct call in this Slave context。

### storyMode_plasma

OFF／no direct call in this Slave context。

### storyMode_trans_am

OFF／no direct call in this Slave context。

### storyMode_3

OFF／no direct call in this Slave context。

### storyMode_idle

OFF／no direct call in this Slave context。

### storyMode_motor

OFF／no direct call in this Slave context。

### storyMode_motor_reset

OFF／no direct call in this Slave context。

## Slave 14

### storyMode_develop

OFF／no direct call in this Slave context。

### storyMode_signals

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `gradientVentPalette`、`randomFillAll_V2` | `pgu-storymode-signals-245-randomfillall-v2-ed06d162`<br>`pgu-storymode-signals-253-gradientventpalette-2e88477b` |
| STAGED | RGB3 | Hi-Nu Slave 14/15 RGB3 浮游炮渦輪。 | `turbine_v3` | `pgu-storymode-signals-275-turbine-v3-a74ce0be` |
| STAGED | RGB4 | Hi-Nu Slave 14/15 RGB4 浮游炮腳踏板 v2。 | `footplatev2` | `pgu-storymode-signals-288-footplatev2-85eed41b` |

### storyMode_0_v1

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB2 | Hi-Nu Slave 14 浮游炮 1-3／Slave 15 浮游炮 4-6 RGB — PGU Slave 10 RGB source。 ／ RGB2 散氣／RGB3 渦輪／RGB4 腳踏板在亮點模式一律跟隨 randomFlash 節奏。 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v1-603-randomflashwithgap-multiple-57f078d6`<br>`pgu-storymode-0-v1-956-randomflashwithgap-multiple-35822e0d`<br>`pgu-storymode-0-v1-1436-randomlightup-656e2ff5`<br>`pgu-storymode-0-v1-1894-randomlightup-81378c10`<br>`pgu-storymode-0-v1-2313-randomlightup-d443f97d`<br>`pgu-storymode-0-v1-2511-rgbon-adad2c2e`<br>`pgu-storymode-0-v1-3067-rgbon-222fee84` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v1-610-randomflashwithgap-multiple-f5e9cab9`<br>`pgu-storymode-0-v1-963-randomflashwithgap-multiple-710d4eb1`<br>`pgu-storymode-0-v1-1443-randomlightup-f5f077f1`<br>`pgu-storymode-0-v1-1901-randomlightup-df20eb05`<br>`pgu-storymode-0-v1-2320-randomlightup-ffb51b1f`<br>`pgu-storymode-0-v1-2513-rgbon-a1762553`<br>`pgu-storymode-0-v1-3069-rgbon-44bad66e` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v1-617-randomflashwithgap-multiple-9db04f1d`<br>`pgu-storymode-0-v1-970-randomflashwithgap-multiple-08cf7ce4`<br>`pgu-storymode-0-v1-2327-randomlightup-32169851`<br>`pgu-storymode-0-v1-2515-rgbon-afa7cbc7`<br>`pgu-storymode-0-v1-3071-rgbon-87236520` |

### storyMode_awakening_3

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `gradientVentPalette`、`randomFillAll_V2` | `pgu-storymode-awakening-3-372-randomfillall-v2-87bc8fbb`<br>`pgu-storymode-awakening-3-380-gradientventpalette-7590ec5a` |
| STAGED | RGB3 | Hi-Nu Slave 14/15 RGB3 浮游炮渦輪。 | `turbine_v3` | `pgu-storymode-awakening-3-402-turbine-v3-04bfae8f` |
| STAGED | RGB4 | Hi-Nu Slave 14/15 RGB4 浮游炮腳踏板 v2。 | `footplatev2` | `pgu-storymode-awakening-3-415-footplatev2-71f8ba72` |

### storyMode_activation

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `gradientVentPalette`、`randomFillAll_V2` | `pgu-storymode-activation-657-randomfillall-v2-1757467b`<br>`pgu-storymode-activation-665-gradientventpalette-cd9e7767` |
| STAGED | RGB3 | Hi-Nu Slave 14/15 RGB3 浮游炮渦輪。 | `turbine_v3` | `pgu-storymode-activation-687-turbine-v3-a84155a7` |
| STAGED | RGB4 | Hi-Nu Slave 14/15 RGB4 浮游炮腳踏板 v2。 | `footplatev2` | `pgu-storymode-activation-700-footplatev2-d6ed367e` |

### storyMode_0_v2

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB2 | Hi-Nu Slave 14 浮游炮 1-3／Slave 15 浮游炮 4-6 RGB — PGU Slave 10 RGB source。 ／ RGB2 散氣／RGB3 渦輪／RGB4 腳踏板在亮點模式一律跟隨 randomFlash 節奏。 | `randomLightUp`、`rgbOn` | `pgu-storymode-0-v2-1088-randomlightup-6452aee8`<br>`pgu-storymode-0-v2-1472-randomlightup-512755fd`<br>`pgu-storymode-0-v2-1819-randomlightup-421a2894`<br>`pgu-storymode-0-v2-1994-rgbon-cacd2a43`<br>`pgu-storymode-0-v2-2180-rgbon-7058ef5b` |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `randomFlashWithGap_multiple` | `pgu-storymode-0-v2-681-randomflashwithgap-multiple-88e0cfd1` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v2-688-randomflashwithgap-multiple-78d5929b`<br>`pgu-storymode-0-v2-1095-randomlightup-0730206e`<br>`pgu-storymode-0-v2-1479-randomlightup-2ce3fca8`<br>`pgu-storymode-0-v2-1826-randomlightup-bd763a3e`<br>`pgu-storymode-0-v2-1996-rgbon-92c78106`<br>`pgu-storymode-0-v2-2182-rgbon-b3e527cf` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v2-695-randomflashwithgap-multiple-0ab2727a`<br>`pgu-storymode-0-v2-1486-randomlightup-a975d313`<br>`pgu-storymode-0-v2-1833-randomlightup-c4e51c54`<br>`pgu-storymode-0-v2-1998-rgbon-ba93704b`<br>`pgu-storymode-0-v2-2184-rgbon-b51fff0d` |
| STAGED | Runtime／group target 'strips' | UNCONFIRMED COMPONENT — Runtime／group target 'strips' | `randomFlashFixedCount_multiple` | `pgu-storymode-0-v2-308-randomflashfixedcount-multiple-72edf909` |

### storyMode_storing_energy

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB2 | Hi-Nu Slave 14/15/16/17 Funnel Gun 專屬 RGB pin — Stage 2 同步淡至 5%。 | `RGBAllFadeBetween` | `pgu-storymode-storing-energy-552-rgballfadebetween-4472df4c` |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `gradientVentPalette`、`randomFillAll_V2` | `pgu-storymode-storing-energy-461-randomfillall-v2-57d3320d`<br>`pgu-storymode-storing-energy-469-gradientventpalette-d799886d`<br>`pgu-storymode-storing-energy-854-randomfillall-v2-ac5707de`<br>`pgu-storymode-storing-energy-862-gradientventpalette-0ee49dd4`<br>`pgu-storymode-storing-energy-1505-randomfillall-v2-03b75a35`<br>`pgu-storymode-storing-energy-1513-gradientventpalette-b7e3edd6` |
| STAGED | RGB3 | Hi-Nu Slave 14/15 RGB3 浮游炮渦輪。 | `turbine_v3` | `pgu-storymode-storing-energy-491-turbine-v3-788aef8b`<br>`pgu-storymode-storing-energy-884-turbine-v3-27ec8979`<br>`pgu-storymode-storing-energy-1535-turbine-v3-4df705bb` |
| STAGED | RGB4 | Hi-Nu Slave 14/15 RGB4 浮游炮腳踏板 v2。 | `footplatev2` | `pgu-storymode-storing-energy-504-footplatev2-624aefff`<br>`pgu-storymode-storing-energy-897-footplatev2-e848472c`<br>`pgu-storymode-storing-energy-1548-footplatev2-1ba19ade` |

### storyMode_2

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `gradientVentPalette`、`randomFillAll_V2` | `pgu-storymode-2-825-randomfillall-v2-aed28c5f`<br>`pgu-storymode-2-833-gradientventpalette-2ee976f8` |
| STAGED | RGB3 | Hi-Nu Slave 14/15 RGB3 浮游炮渦輪。 | `turbine_v3` | `pgu-storymode-2-855-turbine-v3-619b4905` |
| STAGED | RGB4 | Hi-Nu Slave 14/15 RGB4 浮游炮腳踏板 v2。 | `footplatev2` | `pgu-storymode-2-868-footplatev2-14e03188` |

### storyMode_plasma

OFF／no direct call in this Slave context。

### storyMode_trans_am

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `gradientVentPalette`、`randomFillAll_V2` | `pgu-storymode-trans-am-488-randomfillall-v2-4f7497e6`<br>`pgu-storymode-trans-am-496-gradientventpalette-fab0c94e` |
| STAGED | RGB3 | Hi-Nu Slave 14/15 RGB3 浮游炮渦輪。 | `turbine_v3` | `pgu-storymode-trans-am-518-turbine-v3-a96e8035` |
| STAGED | RGB4 | Hi-Nu Slave 14/15 RGB4 浮游炮腳踏板 v2。 | `footplatev2` | `pgu-storymode-trans-am-531-footplatev2-03bf4a1d` |

### storyMode_3

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `gradientVentPalette`、`randomFillAll_V2` | `pgu-storymode-3-635-randomfillall-v2-d3ae7ede`<br>`pgu-storymode-3-643-gradientventpalette-736a3fd1` |
| STAGED | RGB3 | Hi-Nu Slave 14/15 RGB3 浮游炮渦輪。 | `turbine_v3` | `pgu-storymode-3-665-turbine-v3-c87ef02b` |
| STAGED | RGB4 | Hi-Nu Slave 14/15 RGB4 浮游炮腳踏板 v2。 | `footplatev2` | `pgu-storymode-3-678-footplatev2-5f76cef8` |

### storyMode_idle

OFF／no direct call in this Slave context。

### storyMode_motor

OFF／no direct call in this Slave context。

### storyMode_motor_reset

OFF／no direct call in this Slave context。

## Slave 15

### storyMode_develop

OFF／no direct call in this Slave context。

### storyMode_signals

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `gradientVentPalette`、`randomFillAll_V2` | `pgu-storymode-signals-245-randomfillall-v2-ed06d162`<br>`pgu-storymode-signals-253-gradientventpalette-2e88477b` |
| STAGED | RGB3 | Hi-Nu Slave 14/15 RGB3 浮游炮渦輪。 | `turbine_v3` | `pgu-storymode-signals-275-turbine-v3-a74ce0be` |
| STAGED | RGB4 | Hi-Nu Slave 14/15 RGB4 浮游炮腳踏板 v2。 | `footplatev2` | `pgu-storymode-signals-288-footplatev2-85eed41b` |

### storyMode_0_v1

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB2 | Hi-Nu Slave 14 浮游炮 1-3／Slave 15 浮游炮 4-6 RGB — PGU Slave 10 RGB source。 ／ RGB2 散氣／RGB3 渦輪／RGB4 腳踏板在亮點模式一律跟隨 randomFlash 節奏。 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v1-603-randomflashwithgap-multiple-57f078d6`<br>`pgu-storymode-0-v1-956-randomflashwithgap-multiple-35822e0d`<br>`pgu-storymode-0-v1-1436-randomlightup-656e2ff5`<br>`pgu-storymode-0-v1-1894-randomlightup-81378c10`<br>`pgu-storymode-0-v1-2313-randomlightup-d443f97d`<br>`pgu-storymode-0-v1-2511-rgbon-adad2c2e`<br>`pgu-storymode-0-v1-3067-rgbon-222fee84` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v1-610-randomflashwithgap-multiple-f5e9cab9`<br>`pgu-storymode-0-v1-963-randomflashwithgap-multiple-710d4eb1`<br>`pgu-storymode-0-v1-1443-randomlightup-f5f077f1`<br>`pgu-storymode-0-v1-1901-randomlightup-df20eb05`<br>`pgu-storymode-0-v1-2320-randomlightup-ffb51b1f`<br>`pgu-storymode-0-v1-2513-rgbon-a1762553`<br>`pgu-storymode-0-v1-3069-rgbon-44bad66e` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v1-617-randomflashwithgap-multiple-9db04f1d`<br>`pgu-storymode-0-v1-970-randomflashwithgap-multiple-08cf7ce4`<br>`pgu-storymode-0-v1-2327-randomlightup-32169851`<br>`pgu-storymode-0-v1-2515-rgbon-afa7cbc7`<br>`pgu-storymode-0-v1-3071-rgbon-87236520` |

### storyMode_awakening_3

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `gradientVentPalette`、`randomFillAll_V2` | `pgu-storymode-awakening-3-372-randomfillall-v2-87bc8fbb`<br>`pgu-storymode-awakening-3-380-gradientventpalette-7590ec5a` |
| STAGED | RGB3 | Hi-Nu Slave 14/15 RGB3 浮游炮渦輪。 | `turbine_v3` | `pgu-storymode-awakening-3-402-turbine-v3-04bfae8f` |
| STAGED | RGB4 | Hi-Nu Slave 14/15 RGB4 浮游炮腳踏板 v2。 | `footplatev2` | `pgu-storymode-awakening-3-415-footplatev2-71f8ba72` |

### storyMode_activation

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `gradientVentPalette`、`randomFillAll_V2` | `pgu-storymode-activation-657-randomfillall-v2-1757467b`<br>`pgu-storymode-activation-665-gradientventpalette-cd9e7767` |
| STAGED | RGB3 | Hi-Nu Slave 14/15 RGB3 浮游炮渦輪。 | `turbine_v3` | `pgu-storymode-activation-687-turbine-v3-a84155a7` |
| STAGED | RGB4 | Hi-Nu Slave 14/15 RGB4 浮游炮腳踏板 v2。 | `footplatev2` | `pgu-storymode-activation-700-footplatev2-d6ed367e` |

### storyMode_0_v2

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB2 | Hi-Nu Slave 14 浮游炮 1-3／Slave 15 浮游炮 4-6 RGB — PGU Slave 10 RGB source。 ／ RGB2 散氣／RGB3 渦輪／RGB4 腳踏板在亮點模式一律跟隨 randomFlash 節奏。 | `randomLightUp`、`rgbOn` | `pgu-storymode-0-v2-1088-randomlightup-6452aee8`<br>`pgu-storymode-0-v2-1472-randomlightup-512755fd`<br>`pgu-storymode-0-v2-1819-randomlightup-421a2894`<br>`pgu-storymode-0-v2-1994-rgbon-cacd2a43`<br>`pgu-storymode-0-v2-2180-rgbon-7058ef5b` |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `randomFlashWithGap_multiple` | `pgu-storymode-0-v2-681-randomflashwithgap-multiple-88e0cfd1` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v2-688-randomflashwithgap-multiple-78d5929b`<br>`pgu-storymode-0-v2-1095-randomlightup-0730206e`<br>`pgu-storymode-0-v2-1479-randomlightup-2ce3fca8`<br>`pgu-storymode-0-v2-1826-randomlightup-bd763a3e`<br>`pgu-storymode-0-v2-1996-rgbon-92c78106`<br>`pgu-storymode-0-v2-2182-rgbon-b3e527cf` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `randomFlashWithGap_multiple`、`randomLightUp`、`rgbOn` | `pgu-storymode-0-v2-695-randomflashwithgap-multiple-0ab2727a`<br>`pgu-storymode-0-v2-1486-randomlightup-a975d313`<br>`pgu-storymode-0-v2-1833-randomlightup-c4e51c54`<br>`pgu-storymode-0-v2-1998-rgbon-ba93704b`<br>`pgu-storymode-0-v2-2184-rgbon-b51fff0d` |
| STAGED | Runtime／group target 'strips' | UNCONFIRMED COMPONENT — Runtime／group target 'strips' | `randomFlashFixedCount_multiple` | `pgu-storymode-0-v2-308-randomflashfixedcount-multiple-72edf909` |

### storyMode_storing_energy

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `gradientVentPalette`、`randomFillAll_V2` | `pgu-storymode-storing-energy-461-randomfillall-v2-57d3320d`<br>`pgu-storymode-storing-energy-469-gradientventpalette-d799886d`<br>`pgu-storymode-storing-energy-854-randomfillall-v2-ac5707de`<br>`pgu-storymode-storing-energy-862-gradientventpalette-0ee49dd4`<br>`pgu-storymode-storing-energy-1505-randomfillall-v2-03b75a35`<br>`pgu-storymode-storing-energy-1513-gradientventpalette-b7e3edd6` |
| STAGED | RGB3 | Hi-Nu Slave 14/15 RGB3 浮游炮渦輪。 | `turbine_v3` | `pgu-storymode-storing-energy-491-turbine-v3-788aef8b`<br>`pgu-storymode-storing-energy-884-turbine-v3-27ec8979`<br>`pgu-storymode-storing-energy-1535-turbine-v3-4df705bb` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `RGBAllFadeBetween` | `pgu-storymode-storing-energy-559-rgballfadebetween-40857b1c` |
| STAGED | RGB4 | Hi-Nu Slave 14/15 RGB4 浮游炮腳踏板 v2。 | `footplatev2` | `pgu-storymode-storing-energy-504-footplatev2-624aefff`<br>`pgu-storymode-storing-energy-897-footplatev2-e848472c`<br>`pgu-storymode-storing-energy-1548-footplatev2-1ba19ade` |

### storyMode_2

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `gradientVentPalette`、`randomFillAll_V2` | `pgu-storymode-2-825-randomfillall-v2-aed28c5f`<br>`pgu-storymode-2-833-gradientventpalette-2ee976f8` |
| STAGED | RGB3 | Hi-Nu Slave 14/15 RGB3 浮游炮渦輪。 | `turbine_v3` | `pgu-storymode-2-855-turbine-v3-619b4905` |
| STAGED | RGB4 | Hi-Nu Slave 14/15 RGB4 浮游炮腳踏板 v2。 | `footplatev2` | `pgu-storymode-2-868-footplatev2-14e03188` |

### storyMode_plasma

OFF／no direct call in this Slave context。

### storyMode_trans_am

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `gradientVentPalette`、`randomFillAll_V2` | `pgu-storymode-trans-am-488-randomfillall-v2-4f7497e6`<br>`pgu-storymode-trans-am-496-gradientventpalette-fab0c94e` |
| STAGED | RGB3 | Hi-Nu Slave 14/15 RGB3 浮游炮渦輪。 | `turbine_v3` | `pgu-storymode-trans-am-518-turbine-v3-a96e8035` |
| STAGED | RGB4 | Hi-Nu Slave 14/15 RGB4 浮游炮腳踏板 v2。 | `footplatev2` | `pgu-storymode-trans-am-531-footplatev2-03bf4a1d` |

### storyMode_3

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `gradientVentPalette`、`randomFillAll_V2` | `pgu-storymode-3-635-randomfillall-v2-d3ae7ede`<br>`pgu-storymode-3-643-gradientventpalette-736a3fd1` |
| STAGED | RGB3 | Hi-Nu Slave 14/15 RGB3 浮游炮渦輪。 | `turbine_v3` | `pgu-storymode-3-665-turbine-v3-c87ef02b` |
| STAGED | RGB4 | Hi-Nu Slave 14/15 RGB4 浮游炮腳踏板 v2。 | `footplatev2` | `pgu-storymode-3-678-footplatev2-5f76cef8` |

### storyMode_idle

OFF／no direct call in this Slave context。

### storyMode_motor

OFF／no direct call in this Slave context。

### storyMode_motor_reset

OFF／no direct call in this Slave context。

## Slave 16

### storyMode_develop

OFF／no direct call in this Slave context。

### storyMode_signals

OFF／no direct call in this Slave context。

### storyMode_0_v1

OFF／no direct call in this Slave context。

### storyMode_awakening_3

OFF／no direct call in this Slave context。

### storyMode_activation

OFF／no direct call in this Slave context。

### storyMode_0_v2

OFF／no direct call in this Slave context。

### storyMode_storing_energy

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `RGBAllFadeBetween` | `pgu-storymode-storing-energy-566-rgballfadebetween-e978b166` |

### storyMode_2

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB10 | UNCONFIRMED COMPONENT — RGB10 | `gradientVentPalette`、`randomFillAll_V2` | `pgu-storymode-2-657-randomfillall-v2-7179d06a`<br>`pgu-storymode-2-665-gradientventpalette-870822d1` |
| STAGED | RGB11 | UNCONFIRMED COMPONENT — RGB11 | `gradientVentPalette`、`randomFillAll_V2` | `pgu-storymode-2-689-randomfillall-v2-eec12d13`<br>`pgu-storymode-2-697-gradientventpalette-82c55fb7` |
| STAGED | RGB9 | UNCONFIRMED COMPONENT — RGB9 | `gradientVentPalette`、`randomFillAll_V2` | `pgu-storymode-2-625-randomfillall-v2-6659f2ef`<br>`pgu-storymode-2-633-gradientventpalette-a9ad102b` |

### storyMode_plasma

OFF／no direct call in this Slave context。

### storyMode_trans_am

OFF／no direct call in this Slave context。

### storyMode_3

OFF／no direct call in this Slave context。

### storyMode_idle

OFF／no direct call in this Slave context。

### storyMode_motor

OFF／no direct call in this Slave context。

### storyMode_motor_reset

OFF／no direct call in this Slave context。

## Slave 17

### storyMode_develop

OFF／no direct call in this Slave context。

### storyMode_signals

OFF／no direct call in this Slave context。

### storyMode_0_v1

OFF／no direct call in this Slave context。

### storyMode_awakening_3

OFF／no direct call in this Slave context。

### storyMode_activation

OFF／no direct call in this Slave context。

### storyMode_0_v2

OFF／no direct call in this Slave context。

### storyMode_storing_energy

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB7 | UNCONFIRMED COMPONENT — RGB7 | `RGBAllFadeBetween` | `pgu-storymode-storing-energy-573-rgballfadebetween-d67b943e` |

### storyMode_2

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB10 | UNCONFIRMED COMPONENT — RGB10 | `gradientVentPalette`、`randomFillAll_V2` | `pgu-storymode-2-756-randomfillall-v2-e20bf287`<br>`pgu-storymode-2-764-gradientventpalette-178cdfa8` |
| STAGED | RGB11 | UNCONFIRMED COMPONENT — RGB11 | `gradientVentPalette`、`randomFillAll_V2` | `pgu-storymode-2-788-randomfillall-v2-61d5da45`<br>`pgu-storymode-2-796-gradientventpalette-bd8d734a` |
| STAGED | RGB9 | UNCONFIRMED COMPONENT — RGB9 | `gradientVentPalette`、`randomFillAll_V2` | `pgu-storymode-2-724-randomfillall-v2-71da1915`<br>`pgu-storymode-2-732-gradientventpalette-1479cc15` |

### storyMode_plasma

OFF／no direct call in this Slave context。

### storyMode_trans_am

OFF／no direct call in this Slave context。

### storyMode_3

OFF／no direct call in this Slave context。

### storyMode_idle

OFF／no direct call in this Slave context。

### storyMode_motor

OFF／no direct call in this Slave context。

### storyMode_motor_reset

OFF／no direct call in this Slave context。

## Slave 18

### storyMode_develop

OFF／no direct call in this Slave context。

### storyMode_signals

OFF／no direct call in this Slave context。

### storyMode_0_v1

OFF／no direct call in this Slave context。

### storyMode_awakening_3

OFF／no direct call in this Slave context。

### storyMode_activation

OFF／no direct call in this Slave context。

### storyMode_0_v2

OFF／no direct call in this Slave context。

### storyMode_storing_energy

OFF／no direct call in this Slave context。

### storyMode_2

OFF／no direct call in this Slave context。

### storyMode_plasma

OFF／no direct call in this Slave context。

### storyMode_trans_am

OFF／no direct call in this Slave context。

### storyMode_3

OFF／no direct call in this Slave context。

### storyMode_idle

OFF／no direct call in this Slave context。

### storyMode_motor

OFF／no direct call in this Slave context。

### storyMode_motor_reset

OFF／no direct call in this Slave context。

## Slave 19

### storyMode_develop

OFF／no direct call in this Slave context。

### storyMode_signals

OFF／no direct call in this Slave context。

### storyMode_0_v1

OFF／no direct call in this Slave context。

### storyMode_awakening_3

OFF／no direct call in this Slave context。

### storyMode_activation

OFF／no direct call in this Slave context。

### storyMode_0_v2

OFF／no direct call in this Slave context。

### storyMode_storing_energy

OFF／no direct call in this Slave context。

### storyMode_2

OFF／no direct call in this Slave context。

### storyMode_plasma

OFF／no direct call in this Slave context。

### storyMode_trans_am

OFF／no direct call in this Slave context。

### storyMode_3

OFF／no direct call in this Slave context。

### storyMode_idle

OFF／no direct call in this Slave context。

### storyMode_motor

OFF／no direct call in this Slave context。

### storyMode_motor_reset

OFF／no direct call in this Slave context。

## Slave 20

### storyMode_develop

OFF／no direct call in this Slave context。

### storyMode_signals

OFF／no direct call in this Slave context。

### storyMode_0_v1

OFF／no direct call in this Slave context。

### storyMode_awakening_3

OFF／no direct call in this Slave context。

### storyMode_activation

OFF／no direct call in this Slave context。

### storyMode_0_v2

OFF／no direct call in this Slave context。

### storyMode_storing_energy

OFF／no direct call in this Slave context。

### storyMode_2

OFF／no direct call in this Slave context。

### storyMode_plasma

OFF／no direct call in this Slave context。

### storyMode_trans_am

OFF／no direct call in this Slave context。

### storyMode_3

OFF／no direct call in this Slave context。

### storyMode_idle

OFF／no direct call in this Slave context。

### storyMode_motor

OFF／no direct call in this Slave context。

### storyMode_motor_reset

OFF／no direct call in this Slave context。

## Shared／global and function-level-unresolved calls

### storyMode_develop

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB1 | UNCONFIRMED COMPONENT — RGB1 | `rgbOff` | `pgu-storymode-develop-25-rgboff-0b248fd1`<br>`pgu-storymode-develop-287-rgboff-292f4170` |
| STAGED | RGB10 | UNCONFIRMED COMPONENT — RGB10 | `rgbOff` | `pgu-storymode-develop-32-rgboff-ad45d6bc`<br>`pgu-storymode-develop-294-rgboff-dab685dd` |
| STAGED | RGB11 | UNCONFIRMED COMPONENT — RGB11 | `rgbOff` | `pgu-storymode-develop-33-rgboff-432db4f2`<br>`pgu-storymode-develop-295-rgboff-444c8f75` |
| STAGED | RGB12 | UNCONFIRMED COMPONENT — RGB12 | `rgbOff` | `pgu-storymode-develop-34-rgboff-f18e6fb9`<br>`pgu-storymode-develop-296-rgboff-ffd651c4` |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `rgbOff` | `pgu-storymode-develop-26-rgboff-fbb0c921`<br>`pgu-storymode-develop-288-rgboff-33bbcce0` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `rgbOff` | `pgu-storymode-develop-27-rgboff-eb422d2b`<br>`pgu-storymode-develop-289-rgboff-e9012741` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `rgbOff` | `pgu-storymode-develop-28-rgboff-5b45eb64`<br>`pgu-storymode-develop-290-rgboff-463d161d` |
| STAGED | RGB7 | UNCONFIRMED COMPONENT — RGB7 | `rgbOff` | `pgu-storymode-develop-29-rgboff-c8769b1d`<br>`pgu-storymode-develop-291-rgboff-d98dd050` |
| STAGED | RGB8 | UNCONFIRMED COMPONENT — RGB8 | `rgbOff` | `pgu-storymode-develop-30-rgboff-aa0fc4a2`<br>`pgu-storymode-develop-292-rgboff-5dc2088a` |
| STAGED | RGB9 | UNCONFIRMED COMPONENT — RGB9 | `rgbOff` | `pgu-storymode-develop-31-rgboff-33cecd40`<br>`pgu-storymode-develop-293-rgboff-11897da0` |

### storyMode_signals

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB1 | UNCONFIRMED COMPONENT — RGB1 | `rgbOff` | `pgu-storymode-signals-19-rgboff-cb3e7bc6`<br>`pgu-storymode-signals-328-rgboff-4e9577c5` |
| STAGED | RGB10 | UNCONFIRMED COMPONENT — RGB10 | `rgbOff` | `pgu-storymode-signals-26-rgboff-da40e3c0`<br>`pgu-storymode-signals-335-rgboff-fde3c63b` |
| STAGED | RGB11 | UNCONFIRMED COMPONENT — RGB11 | `rgbOff` | `pgu-storymode-signals-27-rgboff-0a07924f`<br>`pgu-storymode-signals-336-rgboff-29cd22e1` |
| STAGED | RGB12 | UNCONFIRMED COMPONENT — RGB12 | `rgbOff` | `pgu-storymode-signals-28-rgboff-cbc287be`<br>`pgu-storymode-signals-337-rgboff-a2355161` |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `rgbOff` | `pgu-storymode-signals-20-rgboff-2e52d77d`<br>`pgu-storymode-signals-329-rgboff-7d7a55ee` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `rgbOff` | `pgu-storymode-signals-21-rgboff-7330a84f`<br>`pgu-storymode-signals-330-rgboff-e279a5cb` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `rgbOff` | `pgu-storymode-signals-22-rgboff-398d0d0e`<br>`pgu-storymode-signals-331-rgboff-a619195a` |
| STAGED | RGB7 | UNCONFIRMED COMPONENT — RGB7 | `rgbOff` | `pgu-storymode-signals-23-rgboff-dffd6264`<br>`pgu-storymode-signals-332-rgboff-f9ec1104` |
| STAGED | RGB8 | UNCONFIRMED COMPONENT — RGB8 | `rgbOff` | `pgu-storymode-signals-24-rgboff-062a05d0`<br>`pgu-storymode-signals-333-rgboff-d5f0c5f5` |
| STAGED | RGB9 | UNCONFIRMED COMPONENT — RGB9 | `rgbOff` | `pgu-storymode-signals-25-rgboff-4f117693`<br>`pgu-storymode-signals-334-rgboff-524262b8` |

### storyMode_0_v1

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| ON | Global FastLED brightness | UNCONFIRMED COMPONENT — Global FastLED brightness | `setBrightness` | `pgu-storymode-0-v1-106-setbrightness-57b7753f` |
| STAGED | RGB1 | UNCONFIRMED COMPONENT — RGB1 | `RGBWhiteSwipeCometCross`、`rgbOff` | `pgu-storymode-0-v1-150-rgboff-4c583566`<br>`pgu-storymode-0-v1-186-rgbwhiteswipecometcross-a41c5f42` |
| STAGED | RGB10 | UNCONFIRMED COMPONENT — RGB10 | `rgbOff` | `pgu-storymode-0-v1-157-rgboff-0a36b274` |
| STAGED | RGB11 | UNCONFIRMED COMPONENT — RGB11 | `rgbOff` | `pgu-storymode-0-v1-158-rgboff-662f6498` |
| STAGED | RGB12 | UNCONFIRMED COMPONENT — RGB12 | `rgbOff` | `pgu-storymode-0-v1-159-rgboff-b2f03af9` |
| STAGED | RGB13 | UNCONFIRMED COMPONENT — RGB13 | `rgbOff` | `pgu-storymode-0-v1-160-rgboff-e6a31942` |
| STAGED | RGB16 | UNCONFIRMED COMPONENT — RGB16 | `rgbOff` | `pgu-storymode-0-v1-161-rgboff-e0b8e785` |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `rgbOff` | `pgu-storymode-0-v1-151-rgboff-727572b0` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `rgbOff` | `pgu-storymode-0-v1-152-rgboff-9e26f6d8` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `rgbOff` | `pgu-storymode-0-v1-153-rgboff-8dab5d0e` |
| STAGED | RGB7 | UNCONFIRMED COMPONENT — RGB7 | `rgbOff` | `pgu-storymode-0-v1-154-rgboff-abc93bcc` |
| STAGED | RGB8 | UNCONFIRMED COMPONENT — RGB8 | `rgbOff` | `pgu-storymode-0-v1-155-rgboff-de7c2986` |
| STAGED | RGB9 | UNCONFIRMED COMPONENT — RGB9 | `rgbOff` | `pgu-storymode-0-v1-156-rgboff-cfeb73a7` |

### storyMode_awakening_3

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| ON | Global FastLED brightness | Awakening 3 所有 RGB：沿用 Story Mode 3 實測 FastLED 全域亮度 90/255。 | `setBrightness` | `pgu-storymode-awakening-3-172-setbrightness-70bb23b5` |
| STAGED | Global FastLED brightness | 離開前還原一般 Story Mode 的 FastLED 全域亮度 60/255。 | `setBrightness` | `pgu-storymode-awakening-3-500-setbrightness-1d0df7ac` |
| STAGED | RGB1 | Slave 1-12、19-20 RGB1 蘇醒流光：Hi-Nu 三分支 S1 頭 → S2 身體 → {S3/5、S7、S12} 綠色 V3Cross 掃入， ／ 之後以 smoothSineBreath 同款曲線呼吸；S13/S14/S15/S16/S17 Funnel Gun 在各自 case 以專屬 RGB pin 加入 Branch 3。 | `RGBBreathSwipePaletteV3Cross` | `pgu-storymode-awakening-3-190-rgbbreathswipepalettev3cross-05a12fe3` |
| STAGED | RGB1 | UNCONFIRMED COMPONENT — RGB1 | `rgbOff`、`rgb_fadeOut` | `pgu-storymode-awakening-3-461-rgb-fadeout-d71472f8`<br>`pgu-storymode-awakening-3-483-rgb-fadeout-a132c5c2`<br>`pgu-storymode-awakening-3-492-rgboff-7a40800e` |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `rgbOff` | `pgu-storymode-awakening-3-493-rgboff-fb070548` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `rgbOff`、`rgb_fadeOut` | `pgu-storymode-awakening-3-480-rgb-fadeout-933a414c`<br>`pgu-storymode-awakening-3-494-rgboff-c2625b26` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `rgbOff`、`rgb_fadeOut` | `pgu-storymode-awakening-3-481-rgb-fadeout-6c6e7d2f`<br>`pgu-storymode-awakening-3-495-rgboff-b9b7acf7` |
| STAGED | RGB7 | UNCONFIRMED COMPONENT — RGB7 | `rgbOff`、`rgb_fadeOut` | `pgu-storymode-awakening-3-482-rgb-fadeout-fa946ed6`<br>`pgu-storymode-awakening-3-496-rgboff-bd6931f5` |
| STAGED | RGB8 | UNCONFIRMED COMPONENT — RGB8 | `rgbOff` | `pgu-storymode-awakening-3-497-rgboff-f2f4bfb2` |
| STAGED | Runtime／group target 'espLed[0]' | 左／右腿與腳掌 espLed[0-3]：繼續淡出至全暗。 | `chFadeOut` | `pgu-storymode-awakening-3-473-chfadeout-eabb3c8e` |
| STAGED | Runtime／group target 'espLed[0]' | 左／右腿與腳掌 espLed[0-3]：與 RGB1 同步淡出。 | `chFadeOut` | `pgu-storymode-awakening-3-455-chfadeout-f4bb5756` |
| STAGED | Runtime／group target 'espLed[0]' | 離開 Awakening 3 前關閉左／右腿與腳掌 espLed[0-3]。 | `chOff` | `pgu-storymode-awakening-3-487-choff-1d997964` |
| STAGED | Runtime／group target 'espLed[1]' | UNCONFIRMED COMPONENT — Runtime／group target 'espLed[1]' | `chFadeOut`、`chOff` | `pgu-storymode-awakening-3-456-chfadeout-9562f031`<br>`pgu-storymode-awakening-3-474-chfadeout-8335aa77`<br>`pgu-storymode-awakening-3-488-choff-3c0138aa` |
| STAGED | Runtime／group target 'espLed[2]' | UNCONFIRMED COMPONENT — Runtime／group target 'espLed[2]' | `chFadeOut`、`chOff` | `pgu-storymode-awakening-3-457-chfadeout-f40980ed`<br>`pgu-storymode-awakening-3-475-chfadeout-d091defc`<br>`pgu-storymode-awakening-3-489-choff-f196bf03` |
| STAGED | Runtime／group target 'espLed[3]' | UNCONFIRMED COMPONENT — Runtime／group target 'espLed[3]' | `chFadeOut`、`chOff` | `pgu-storymode-awakening-3-458-chfadeout-2983d1e7`<br>`pgu-storymode-awakening-3-476-chfadeout-f30ca14b`<br>`pgu-storymode-awakening-3-490-choff-c08c982d` |

### storyMode_activation

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB1 | Slave 1-12、19-20 RGB1 覺醒能量：Hi-Nu 三分支 S1 頭 → S2 身體 → {S3/5、S7、S12} 展開； ／ S13/S14/S15/S16/S17 Funnel Gun 在各自 case 以專屬 RGB pin 加入 Branch 3。 | `RGBActivationCometCross` | `pgu-storymode-activation-207-rgbactivationcometcross-dc2d4639` |
| STAGED | RGB1 | UNCONFIRMED COMPONENT — RGB1 | `rgb_fadeOut` | `pgu-storymode-activation-777-rgb-fadeout-28470e5f` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `rgb_fadeOut` | `pgu-storymode-activation-771-rgb-fadeout-22573fcc` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `rgb_fadeOut` | `pgu-storymode-activation-772-rgb-fadeout-5eb68620` |
| STAGED | RGB7 | UNCONFIRMED COMPONENT — RGB7 | `rgb_fadeOut` | `pgu-storymode-activation-773-rgb-fadeout-2bf87ba7` |
| STAGED | RGB8 | UNCONFIRMED COMPONENT — RGB8 | `rgb_fadeOut` | `pgu-storymode-activation-774-rgb-fadeout-0430e915` |
| STAGED | RGB9 | UNCONFIRMED COMPONENT — RGB9 | `rgb_fadeOut` | `pgu-storymode-activation-775-rgb-fadeout-c447adc4` |
| STAGED | Runtime／group target 'storyMode_2_params::s1_rgb2_fill' | UNCONFIRMED COMPONENT — Runtime／group target 'storyMode_2_params::s1_rgb2_fill' | `resetRandomFillAllInstance` | `pgu-storymode-activation-184-resetrandomfillallinstance-afbc4a83` |
| STAGED | Runtime／group target 'storyMode_2_params::s2_rgb2_fill' | UNCONFIRMED COMPONENT — Runtime／group target 'storyMode_2_params::s2_rgb2_fill' | `resetRandomFillAllInstance` | `pgu-storymode-activation-186-resetrandomfillallinstance-709d324f` |
| STAGED | Runtime／group target 'storyMode_2_params::s3_rgb2_fill' | UNCONFIRMED COMPONENT — Runtime／group target 'storyMode_2_params::s3_rgb2_fill' | `resetRandomFillAllInstance` | `pgu-storymode-activation-188-resetrandomfillallinstance-401b1a88` |
| STAGED | Runtime／group target 'storyMode_2_params::s4s5_rgb2_fill' | UNCONFIRMED COMPONENT — Runtime／group target 'storyMode_2_params::s4s5_rgb2_fill' | `resetRandomFillAllInstance` | `pgu-storymode-activation-190-resetrandomfillallinstance-bf658c06` |
| STAGED | Runtime／group target 'storyMode_2_params::s6_rgb2_fill' | UNCONFIRMED COMPONENT — Runtime／group target 'storyMode_2_params::s6_rgb2_fill' | `resetRandomFillAllInstance` | `pgu-storymode-activation-192-resetrandomfillallinstance-daccc0d3` |

### storyMode_0_v2

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| ON | Global FastLED brightness | UNCONFIRMED COMPONENT — Global FastLED brightness | `setBrightness` | `pgu-storymode-0-v2-70-setbrightness-6d38a3f2` |
| STAGED | RGB1 | UNCONFIRMED COMPONENT — RGB1 | `rgbOff` | `pgu-storymode-0-v2-114-rgboff-e46970c3` |
| STAGED | RGB10 | UNCONFIRMED COMPONENT — RGB10 | `rgbOff` | `pgu-storymode-0-v2-121-rgboff-64c0fcd8` |
| STAGED | RGB11 | UNCONFIRMED COMPONENT — RGB11 | `rgbOff` | `pgu-storymode-0-v2-122-rgboff-d35242b4` |
| STAGED | RGB12 | UNCONFIRMED COMPONENT — RGB12 | `rgbOff` | `pgu-storymode-0-v2-123-rgboff-bfe7608a` |
| STAGED | RGB13 | UNCONFIRMED COMPONENT — RGB13 | `rgbOff` | `pgu-storymode-0-v2-124-rgboff-556f861c` |
| STAGED | RGB16 | UNCONFIRMED COMPONENT — RGB16 | `rgbOff` | `pgu-storymode-0-v2-125-rgboff-6517c570` |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `rgbOff` | `pgu-storymode-0-v2-115-rgboff-596d7eb3` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `rgbOff` | `pgu-storymode-0-v2-116-rgboff-c89fe80a` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `rgbOff` | `pgu-storymode-0-v2-117-rgboff-341b540f` |
| STAGED | RGB7 | UNCONFIRMED COMPONENT — RGB7 | `rgbOff` | `pgu-storymode-0-v2-118-rgboff-d03e6fd0` |
| STAGED | RGB8 | UNCONFIRMED COMPONENT — RGB8 | `rgbOff` | `pgu-storymode-0-v2-119-rgboff-19773523` |
| STAGED | RGB9 | UNCONFIRMED COMPONENT — RGB9 | `rgbOff` | `pgu-storymode-0-v2-120-rgboff-71434c67` |

### storyMode_storing_energy

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | Global FastLED brightness | UNCONFIRMED COMPONENT — Global FastLED brightness | `setBrightness` | `pgu-storymode-storing-energy-589-setbrightness-382114bb`<br>`pgu-storymode-storing-energy-1254-setbrightness-863a9f56` |
| STAGED | Global FastLED brightness | 還原一般 story mode 的 FastLED 全域亮度，避免 140/255 洩漏到下一模式。 | `setBrightness` | `pgu-storymode-storing-energy-1704-setbrightness-3c61a56d` |
| STAGED | RGB1 | Slave 1-12、19-20 RGB1 儲能帶：Hi-Nu 三分支 20-LED wave 由 S1 頭經 S2 身體分流； ／ S13、S14、S15、S16、S17 Funnel Gun 在各自 case 以專屬 RGB pin 加入 Branch 3。 | `paletteWave_StoringEnergyCross` | `pgu-storymode-storing-energy-337-palettewave-storingenergycross-32b99c45` |
| STAGED | RGB1 | Slave 1-13 RGB1 儲滿能量帶：由 cross effect 在 2 秒內淡至 5%，不改 FastLED global brightness。 | `RGBAllFadeBetween` | `pgu-storymode-storing-energy-545-rgballfadebetween-777b9e2c` |
| STAGED | RGB1 | Slave 1-9 RGB1-RGB9：Stage 6 立即全關。 | `rgbOff` | `pgu-storymode-storing-energy-1695-rgboff-e042a77e` |
| STAGED | RGB1 | Slave 1-9 RGB1：Stage 4 在 1 秒內由 80% 效果亮度淡至 50%。 | `RGBAllFadeBetween` | `pgu-storymode-storing-energy-1622-rgballfadebetween-1d4a387c` |
| STAGED | RGB2 | Slave 1-9 RGB2：Stage 4 在 1 秒內由 80% 效果亮度淡至 50%。 | `RGBAllFadeBetween` | `pgu-storymode-storing-energy-1628-rgballfadebetween-1ac1b76f` |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `rgbOff` | `pgu-storymode-storing-energy-1696-rgboff-b68c0a20` |
| STAGED | RGB3 | Slave 1-9 RGB3：Stage 4 在 1 秒內由 80% 效果亮度淡至 50%。 | `RGBAllFadeBetween` | `pgu-storymode-storing-energy-1634-rgballfadebetween-06a1ed49` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `rgbOff` | `pgu-storymode-storing-energy-1697-rgboff-13f84781` |
| STAGED | RGB4 | Slave 1-9 RGB4：Stage 4 在 1 秒內由 80% 效果亮度淡至 50%。 | `RGBAllFadeBetween` | `pgu-storymode-storing-energy-1640-rgballfadebetween-6f5266a0` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `rgbOff` | `pgu-storymode-storing-energy-1698-rgboff-b90f8020` |
| STAGED | RGB7 | Slave 1-9 RGB7：Stage 4 在 1 秒內由 80% 效果亮度淡至 50%。 | `RGBAllFadeBetween` | `pgu-storymode-storing-energy-1646-rgballfadebetween-ae61b61c` |
| STAGED | RGB7 | UNCONFIRMED COMPONENT — RGB7 | `rgbOff` | `pgu-storymode-storing-energy-1699-rgboff-be0a2058` |
| STAGED | RGB8 | Slave 1-9 RGB8：Stage 4 在 1 秒內由 80% 效果亮度淡至 50%。 | `RGBAllFadeBetween` | `pgu-storymode-storing-energy-1652-rgballfadebetween-3335c9fd` |
| STAGED | RGB8 | UNCONFIRMED COMPONENT — RGB8 | `rgbOff` | `pgu-storymode-storing-energy-1700-rgboff-23818599` |
| STAGED | RGB9 | Slave 1-9 RGB9：Stage 4 在 1 秒內由 80% 效果亮度淡至 50%。 | `RGBAllFadeBetween` | `pgu-storymode-storing-energy-1658-rgballfadebetween-dec707a5` |
| STAGED | RGB9 | UNCONFIRMED COMPONENT — RGB9 | `rgbOff` | `pgu-storymode-storing-energy-1701-rgboff-23443820` |

### storyMode_2

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB1 | Slave 1-20 RGB1：S1 頭 → S2 身體後分成手臂、腰腿及背包三條 branch； ／ 背包 branch 依序經過 S14/S15 → S16/S17 → S13 Funnel Gun。 | `RGBSeqOnV3` | `pgu-storymode-2-235-rgbseqonv3-d57d9546` |
| STAGED | RGB1 | UNCONFIRMED COMPONENT — RGB1 | `rgbOff`、`rgb_fadeOut` | `pgu-storymode-2-204-rgboff-b7742556`<br>`pgu-storymode-2-1190-rgb-fadeout-ec70d011`<br>`pgu-storymode-2-1197-rgboff-52e96a8a` |
| STAGED | RGB10 | UNCONFIRMED COMPONENT — RGB10 | `rgbOff`、`rgb_fadeOut` | `pgu-storymode-2-211-rgboff-f6aba0c1`<br>`pgu-storymode-2-1186-rgb-fadeout-78dcdafa`<br>`pgu-storymode-2-1204-rgboff-bea56c9a` |
| STAGED | RGB11 | UNCONFIRMED COMPONENT — RGB11 | `rgbOff`、`rgb_fadeOut` | `pgu-storymode-2-212-rgboff-683da20b`<br>`pgu-storymode-2-1187-rgb-fadeout-34987586`<br>`pgu-storymode-2-1205-rgboff-eb6fead6` |
| STAGED | RGB12 | UNCONFIRMED COMPONENT — RGB12 | `rgbOff`、`rgb_fadeOut` | `pgu-storymode-2-213-rgboff-6f36e054`<br>`pgu-storymode-2-1188-rgb-fadeout-4d744b3e`<br>`pgu-storymode-2-1206-rgboff-b6d0cc4d` |
| STAGED | RGB13 | UNCONFIRMED COMPONENT — RGB13 | `rgbOff` | `pgu-storymode-2-214-rgboff-ef77b0c6` |
| STAGED | RGB16 | UNCONFIRMED COMPONENT — RGB16 | `rgbOff` | `pgu-storymode-2-215-rgboff-e42ee94d` |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `rgbOff`、`rgb_fadeOut` | `pgu-storymode-2-205-rgboff-5ade57d1`<br>`pgu-storymode-2-1180-rgb-fadeout-3bd30d5d`<br>`pgu-storymode-2-1198-rgboff-c06cb125` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `rgbOff`、`rgb_fadeOut` | `pgu-storymode-2-206-rgboff-3df4d2c7`<br>`pgu-storymode-2-1181-rgb-fadeout-625bc9d1`<br>`pgu-storymode-2-1199-rgboff-32918e92` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `rgbOff`、`rgb_fadeOut` | `pgu-storymode-2-207-rgboff-382af551`<br>`pgu-storymode-2-1182-rgb-fadeout-67064d79`<br>`pgu-storymode-2-1200-rgboff-5c4c6f20` |
| STAGED | RGB7 | UNCONFIRMED COMPONENT — RGB7 | `rgbOff`、`rgb_fadeOut` | `pgu-storymode-2-208-rgboff-356bbb46`<br>`pgu-storymode-2-1183-rgb-fadeout-f040b5d5`<br>`pgu-storymode-2-1201-rgboff-844fb632` |
| STAGED | RGB8 | UNCONFIRMED COMPONENT — RGB8 | `rgbOff`、`rgb_fadeOut` | `pgu-storymode-2-209-rgboff-2b86370c`<br>`pgu-storymode-2-1184-rgb-fadeout-597b86ba`<br>`pgu-storymode-2-1202-rgboff-5f5f7354` |
| STAGED | RGB9 | UNCONFIRMED COMPONENT — RGB9 | `rgbOff`、`rgb_fadeOut` | `pgu-storymode-2-210-rgboff-80900895`<br>`pgu-storymode-2-1185-rgb-fadeout-61f9d2f7`<br>`pgu-storymode-2-1203-rgboff-1cc46b5d` |
| STAGED | Runtime／group target 's2_rgb2_fill' | UNCONFIRMED COMPONENT — Runtime／group target 's2_rgb2_fill' | `resetRandomFillAllInstance` | `pgu-storymode-2-198-resetrandomfillallinstance-3ee4e27b` |
| STAGED | Runtime／group target 's4s5_rgb2_fill' | UNCONFIRMED COMPONENT — Runtime／group target 's4s5_rgb2_fill' | `resetRandomFillAllInstance` | `pgu-storymode-2-199-resetrandomfillallinstance-0996db69` |

### storyMode_plasma

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| ON | Global FastLED brightness | UNCONFIRMED COMPONENT — Global FastLED brightness | `setBrightness` | `pgu-storymode-plasma-35-setbrightness-1639e90c` |
| STAGED | Global FastLED brightness | UNCONFIRMED COMPONENT — Global FastLED brightness | `setBrightness` | `pgu-storymode-plasma-845-setbrightness-4a62bfab` |
| STAGED | RGB1 | 先關閉 RGB1 - 跨 slave 共用燈條，rgbOff 收尾清空。 | `rgbOff` | `pgu-storymode-plasma-837-rgboff-893ca900` |
| STAGED | RGB1 | 先關閉 RGB1 - 跨 slave 共用燈條，rgbOff 確保乾淨狀態。 | `rgbOff` | `pgu-storymode-plasma-79-rgboff-8f417e74` |
| STAGED | RGB2 | Hi-Nu Slave 14-17 浮游炮 1-6 專屬 RGB pin：Plasma 初始化清除。 | `rgbOff` | `pgu-storymode-plasma-81-rgboff-84f9f3bf` |
| STAGED | RGB2 | Hi-Nu Slave 14-17 浮游炮 1-6 專屬 RGB pin：Plasma 收尾清除。 | `rgbOff` | `pgu-storymode-plasma-839-rgboff-5e5130a0` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `rgbOff` | `pgu-storymode-plasma-82-rgboff-0500a138`<br>`pgu-storymode-plasma-840-rgboff-bcf9cfde` |
| STAGED | RGB4 | Slave 1-13 RGB4 - rgbOff 清除 Stage 4 signal 殘留。 | `rgbOff` | `pgu-storymode-plasma-718-rgboff-cb8a7140` |
| STAGED | RGB4 | Slave 1-13 RGB4 - rgbOff 避免殘留 signals，留給 Stage 4 使用。 | `rgbOff` | `pgu-storymode-plasma-148-rgboff-454adfbd`<br>`pgu-storymode-plasma-261-rgboff-1e35b35a`<br>`pgu-storymode-plasma-375-rgboff-bec19146` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `rgbOff` | `pgu-storymode-plasma-83-rgboff-84aa5f19`<br>`pgu-storymode-plasma-841-rgboff-eef80b98` |
| STAGED | RGB4 | 先關閉 RGB4 - rgbOff 收尾清空。 | `rgbOff` | `pgu-storymode-plasma-833-rgboff-40e71712` |
| STAGED | RGB4 | 先關閉 RGB4 - rgbOff 確保乾淨狀態，Stage 4 會重新設定。 | `rgbOff` | `pgu-storymode-plasma-75-rgboff-15b260e2` |
| STAGED | RGB4 | 先關閉 RGB4 - rgbOff 避免殘留 signals，留給 Stage 4 使用。 | `rgbOff` | `pgu-storymode-plasma-128-rgboff-094746ca` |
| STAGED | RGB7 | UNCONFIRMED COMPONENT — RGB7 | `rgbOff` | `pgu-storymode-plasma-84-rgboff-aa359a99`<br>`pgu-storymode-plasma-842-rgboff-f32a7ccf` |
| STAGED | RGB8 | UNCONFIRMED COMPONENT — RGB8 | `rgbOff` | `pgu-storymode-plasma-85-rgboff-98ff23ce`<br>`pgu-storymode-plasma-843-rgboff-266ccf06` |
| STAGED | RGB9 | 先關閉 RGB9 - rgbOff 收尾清空。 | `rgbOff` | `pgu-storymode-plasma-835-rgboff-ea1d757f` |
| STAGED | RGB9 | 先關閉 RGB9 - rgbOff 清除 Stage 4 signal 殘留。 | `rgbOff` | `pgu-storymode-plasma-720-rgboff-30464d5d` |
| STAGED | RGB9 | 先關閉 RGB9 - rgbOff 確保乾淨狀態（slave 8 signal buffer）。 | `rgbOff` | `pgu-storymode-plasma-77-rgboff-e549999a` |
| STAGED | RGB9 | 先關閉 RGB9 - rgbOff 避免殘留 signals，留給 Stage 4 使用。 | `rgbOff` | `pgu-storymode-plasma-130-rgboff-b0808b6a`<br>`pgu-storymode-plasma-150-rgboff-4f1eafb2`<br>`pgu-storymode-plasma-263-rgboff-e18d8606`<br>`pgu-storymode-plasma-377-rgboff-e6959d16` |
| STAGED | Runtime／group target 'slaveId' | Slave 3 PWM1 CH7-15 (0x5B) 胸，白，1粒；左胸，白，2粒；右胸，白，2粒；左胸前，紅，2粒；右胸前，紅，2粒；左胸後，紅，2粒；右胸後，紅，2粒。 ／ Plasma Cross 全 branch 同步閃亮；S16/S17 同時處理 RGB1/2/3。 | `RGBAllFadeIn` | `pgu-storymode-plasma-273-rgballfadein-45e72e0c` |
| STAGED | Runtime／group target 'slaveId' | Slave 3 PWM1 CH7-15 (0x5B) 胸，白，1粒；左胸，白，2粒；右胸，白，2粒；左胸前，紅，2粒；右胸前，紅，2粒；左胸後，紅，2粒；右胸後，紅，2粒。 ／ Plasma Cross：S1 → S2，再沿手臂、腰腿、背包三條 branch 向外淡入。 | `RGBSeqOn` | `pgu-storymode-plasma-160-rgbseqon-327a4de8` |
| STAGED | Runtime／group target 'slaveId' | Slave 3 PWM1 CH7-15 (0x5B) 胸，白，1粒；左胸，白，2粒；右胸，白，2粒；左胸前，紅，2粒；右胸前，紅，2粒；左胸後，紅，2粒；右胸後，紅，2粒。 ／ Plasma 雷電依 S1 → S2 → 三 branch 路徑播放；S16/S17 同時跑 RGB1/2/3。 | `RGBLightningPlasmaCross` | `pgu-storymode-plasma-578-rgblightningplasmacross-6a80b8e7` |
| STAGED | Runtime／group target 'slaveId' | Slave 3 PWM1 CH7-15 (0x5B) 胸，白，1粒；左胸，白，2粒；右胸，白，2粒；左胸前，紅，2粒；右胸前，紅，2粒；左胸後，紅，2粒；右胸後，紅，2粒。 ／ S1 → S2 → 三 branch 依序收光；S16/S17 同時處理 RGB1/2/3。 | `RGBSeqFadeOut` | `pgu-storymode-plasma-730-rgbseqfadeout-febb3631` |
| STAGED | Runtime／group target 'slaveId' | Slave 3 PWM1 CH7-15 (0x5B) 胸，白，1粒；左胸，白，2粒；右胸，白，2粒；左胸前，紅，2粒；右胸前，紅，2粒；左胸後，紅，2粒；右胸後，紅，2粒。 ／ 三條 branch 由末端向 S2/S1 收光；S16/S17 同時處理 RGB1/2/3。 | `RGBSeqSwipeOut` | `pgu-storymode-plasma-387-rgbseqswipeout-6736fffe` |
| STAGED | Runtime／group target 'variationSeed' | UNCONFIRMED COMPONENT — Runtime／group target 'variationSeed' | `plasmaVariationForBlock` | `pgu-storymode-plasma-537-plasmavariationforblock-d7be768e` |

### storyMode_trans_am

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB1 | UNCONFIRMED COMPONENT — RGB1 | `rgbOff`、`rgb_fadeOut` | `pgu-storymode-trans-am-606-rgb-fadeout-09739957`<br>`pgu-storymode-trans-am-614-rgboff-f457932e` |
| STAGED | RGB10 | UNCONFIRMED COMPONENT — RGB10 | `rgbOff` | `pgu-storymode-trans-am-621-rgboff-96b9f582` |
| STAGED | RGB11 | UNCONFIRMED COMPONENT — RGB11 | `rgbOff` | `pgu-storymode-trans-am-622-rgboff-1f64a57a` |
| STAGED | RGB12 | UNCONFIRMED COMPONENT — RGB12 | `rgbOff` | `pgu-storymode-trans-am-623-rgboff-f7b1c166` |
| STAGED | RGB13 | UNCONFIRMED COMPONENT — RGB13 | `rgbOff` | `pgu-storymode-trans-am-624-rgboff-261e04af` |
| STAGED | RGB16 | UNCONFIRMED COMPONENT — RGB16 | `rgbOff` | `pgu-storymode-trans-am-627-rgboff-b46b7217` |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `rgbOff`、`rgb_fadeOut` | `pgu-storymode-trans-am-599-rgb-fadeout-9df9e5cd`<br>`pgu-storymode-trans-am-615-rgboff-35f761e7` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `rgbOff`、`rgb_fadeOut` | `pgu-storymode-trans-am-600-rgb-fadeout-a63f1f46`<br>`pgu-storymode-trans-am-616-rgboff-8b754b84` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `rgbOff`、`rgb_fadeOut` | `pgu-storymode-trans-am-601-rgb-fadeout-e2bf04a6`<br>`pgu-storymode-trans-am-617-rgboff-c7e8b9f9` |
| STAGED | RGB7 | UNCONFIRMED COMPONENT — RGB7 | `rgbOff`、`rgb_fadeOut` | `pgu-storymode-trans-am-602-rgb-fadeout-57069109`<br>`pgu-storymode-trans-am-618-rgboff-b713c5ac` |
| STAGED | RGB8 | UNCONFIRMED COMPONENT — RGB8 | `rgbOff`、`rgb_fadeOut` | `pgu-storymode-trans-am-603-rgb-fadeout-e742e2fd`<br>`pgu-storymode-trans-am-619-rgboff-66a99af7` |
| STAGED | RGB9 | UNCONFIRMED COMPONENT — RGB9 | `rgbOff`、`rgb_fadeOut` | `pgu-storymode-trans-am-604-rgb-fadeout-e3985b20`<br>`pgu-storymode-trans-am-620-rgboff-2d93a13c` |

### storyMode_3

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| ON | Global FastLED brightness | Story Mode 3 所有 RGB：第三輪實機測試 FastLED 全域亮度 90/255。 | `setBrightness` | `pgu-storymode-3-160-setbrightness-57643ece` |
| STAGED | Global FastLED brightness | 離開前還原一般 Story Mode 的 FastLED 全域亮度 60/255。 | `setBrightness` | `pgu-storymode-3-765-setbrightness-9aaaee33` |
| STAGED | RGB1 | RGB ／ Slave 1-12、19-20 RGB1：Hi-Nu 三分支 S1 頭 → S2 身體 → {S3/5、S7、S12} 展開，實測 CRGB(180,65,0)、 ／ local 15-210／actual 約 5-74 的 smooth-sine breath swipe；S13/14/15/16/17 Funnel Gun 在各自 case 以專屬 RGB pin 加入 Branch 3。 | `RGBBreathSwipePaletteV3Cross` | `pgu-storymode-3-243-rgbbreathswipepalettev3cross-2f220c69` |
| STAGED | RGB1 | UNCONFIRMED COMPONENT — RGB1 | `rgbOff`、`rgb_fadeOut` | `pgu-storymode-3-165-rgboff-8fe51923`<br>`pgu-storymode-3-751-rgb-fadeout-b7b7d8be`<br>`pgu-storymode-3-757-rgboff-99392b88` |
| STAGED | RGB10 | UNCONFIRMED COMPONENT — RGB10 | `rgbOff` | `pgu-storymode-3-172-rgboff-9f96f8b2` |
| STAGED | RGB11 | UNCONFIRMED COMPONENT — RGB11 | `rgbOff` | `pgu-storymode-3-173-rgboff-e548775b` |
| STAGED | RGB12 | UNCONFIRMED COMPONENT — RGB12 | `rgbOff` | `pgu-storymode-3-174-rgboff-d28ec136` |
| STAGED | RGB13 | UNCONFIRMED COMPONENT — RGB13 | `rgbOff` | `pgu-storymode-3-175-rgboff-7cb59237` |
| STAGED | RGB16 | UNCONFIRMED COMPONENT — RGB16 | `rgbOff` | `pgu-storymode-3-176-rgboff-4d4f514f` |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `rgbOff`、`rgb_fadeOut` | `pgu-storymode-3-166-rgboff-5e025134`<br>`pgu-storymode-3-743-rgb-fadeout-39dabae5`<br>`pgu-storymode-3-758-rgboff-2b6465e5` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `rgbOff`、`rgb_fadeOut` | `pgu-storymode-3-167-rgboff-eb244338`<br>`pgu-storymode-3-744-rgb-fadeout-9d9470ef`<br>`pgu-storymode-3-759-rgboff-089ab75c` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `rgbOff`、`rgb_fadeOut` | `pgu-storymode-3-168-rgboff-645fe3ce`<br>`pgu-storymode-3-745-rgb-fadeout-ac1fc715`<br>`pgu-storymode-3-760-rgboff-91559ad1` |
| STAGED | RGB7 | UNCONFIRMED COMPONENT — RGB7 | `rgbOff`、`rgb_fadeOut` | `pgu-storymode-3-169-rgboff-98f1acbc`<br>`pgu-storymode-3-746-rgb-fadeout-768a6349`<br>`pgu-storymode-3-761-rgboff-3dc5daa4` |
| STAGED | RGB8 | UNCONFIRMED COMPONENT — RGB8 | `rgbOff`、`rgb_fadeOut` | `pgu-storymode-3-170-rgboff-a82f78d0`<br>`pgu-storymode-3-747-rgb-fadeout-c3aa348a`<br>`pgu-storymode-3-762-rgboff-f74e76c1` |
| STAGED | RGB9 | UNCONFIRMED COMPONENT — RGB9 | `rgbOff`、`rgb_fadeOut` | `pgu-storymode-3-171-rgboff-6fb1468a`<br>`pgu-storymode-3-748-rgb-fadeout-444df0cf`<br>`pgu-storymode-3-763-rgboff-91661f9c` |

### storyMode_idle

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB1 | UNCONFIRMED COMPONENT — RGB1 | `rgbOff` | `pgu-storymode-idle-102-rgboff-32a4ffcf` |
| STAGED | RGB10 | Slave 2 backpack funnel inner + signals also dark. | `rgbOff` | `pgu-storymode-idle-110-rgboff-f4ad6e72` |
| STAGED | RGB11 | UNCONFIRMED COMPONENT — RGB11 | `rgbOff` | `pgu-storymode-idle-111-rgboff-c27bd82c` |
| STAGED | RGB12 | UNCONFIRMED COMPONENT — RGB12 | `rgbOff` | `pgu-storymode-idle-112-rgboff-a193120f` |
| STAGED | RGB13 | UNCONFIRMED COMPONENT — RGB13 | `rgbOff` | `pgu-storymode-idle-113-rgboff-b4654941` |
| STAGED | RGB16 | UNCONFIRMED COMPONENT — RGB16 | `rgbOff` | `pgu-storymode-idle-114-rgboff-41a2d979` |
| STAGED | RGB17 | UNCONFIRMED COMPONENT — RGB17 | `rgbOff` | `pgu-storymode-idle-115-rgboff-982dfe7e` |
| STAGED | RGB18 | UNCONFIRMED COMPONENT — RGB18 | `rgbOff` | `pgu-storymode-idle-116-rgboff-9129dd45` |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `rgbOff` | `pgu-storymode-idle-103-rgboff-4655f253` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `rgbOff` | `pgu-storymode-idle-104-rgboff-ae042228` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `rgbOff` | `pgu-storymode-idle-105-rgboff-58642ac3` |
| STAGED | RGB7 | UNCONFIRMED COMPONENT — RGB7 | `rgbOff` | `pgu-storymode-idle-106-rgboff-091f1611` |
| STAGED | RGB8 | UNCONFIRMED COMPONENT — RGB8 | `rgbOff` | `pgu-storymode-idle-107-rgboff-a9dca5f4` |
| STAGED | RGB9 | UNCONFIRMED COMPONENT — RGB9 | `rgbOff` | `pgu-storymode-idle-108-rgboff-a4aa725c` |

### storyMode_motor

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB1 | UNCONFIRMED COMPONENT — RGB1 | `rgbOff` | `pgu-storymode-motor-588-rgboff-400d5223`<br>`pgu-storymode-motor-2387-rgboff-5eb58902` |
| STAGED | RGB10 | UNCONFIRMED COMPONENT — RGB10 | `rgbOff` | `pgu-storymode-motor-595-rgboff-a2008fdb`<br>`pgu-storymode-motor-2394-rgboff-637c7c77` |
| STAGED | RGB11 | UNCONFIRMED COMPONENT — RGB11 | `rgbOff` | `pgu-storymode-motor-596-rgboff-811906db`<br>`pgu-storymode-motor-2395-rgboff-d853c736` |
| STAGED | RGB12 | UNCONFIRMED COMPONENT — RGB12 | `rgbOff` | `pgu-storymode-motor-597-rgboff-067164f0`<br>`pgu-storymode-motor-2396-rgboff-2d8a763a` |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `rgbOff` | `pgu-storymode-motor-589-rgboff-1404ee65`<br>`pgu-storymode-motor-2388-rgboff-bb23406c` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `rgbOff` | `pgu-storymode-motor-590-rgboff-8ab57512`<br>`pgu-storymode-motor-2389-rgboff-8a2f4d5b` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `rgbOff` | `pgu-storymode-motor-591-rgboff-8dc35aef`<br>`pgu-storymode-motor-2390-rgboff-65b3c322` |
| STAGED | RGB7 | UNCONFIRMED COMPONENT — RGB7 | `rgbOff` | `pgu-storymode-motor-592-rgboff-9d9df623`<br>`pgu-storymode-motor-2391-rgboff-0f6b63ae` |
| STAGED | RGB8 | UNCONFIRMED COMPONENT — RGB8 | `rgbOff` | `pgu-storymode-motor-593-rgboff-07fffd96`<br>`pgu-storymode-motor-2392-rgboff-26e4c6a6` |
| STAGED | RGB9 | UNCONFIRMED COMPONENT — RGB9 | `rgbOff` | `pgu-storymode-motor-594-rgboff-d20233a5`<br>`pgu-storymode-motor-2393-rgboff-3f433009` |
| STAGED | Runtime／group target '12' | UNCONFIRMED COMPONENT — Runtime／group target '12' | `chBreathAll` | `pgu-storymode-motor-2381-chbreathall-7b2102b9` |
| STAGED | Runtime／group target 'slaveId' | UNCONFIRMED COMPONENT — Runtime／group target 'slaveId' | `RGBActivationCometCross` | `pgu-storymode-motor-630-rgbactivationcometcross-db38efe3` |

### storyMode_motor_reset

| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |
| --- | --- | --- | --- | --- |
| STAGED | RGB1 | UNCONFIRMED COMPONENT — RGB1 | `rgbOff` | `pgu-storymode-motor-reset-1161-rgboff-bab77342` |
| STAGED | RGB10 | UNCONFIRMED COMPONENT — RGB10 | `rgbOff` | `pgu-storymode-motor-reset-1168-rgboff-f852e1b0` |
| STAGED | RGB11 | UNCONFIRMED COMPONENT — RGB11 | `rgbOff` | `pgu-storymode-motor-reset-1169-rgboff-3028d2ad` |
| STAGED | RGB12 | UNCONFIRMED COMPONENT — RGB12 | `rgbOff` | `pgu-storymode-motor-reset-1170-rgboff-9639b946` |
| STAGED | RGB2 | UNCONFIRMED COMPONENT — RGB2 | `rgbOff` | `pgu-storymode-motor-reset-1162-rgboff-4bc88991` |
| STAGED | RGB3 | UNCONFIRMED COMPONENT — RGB3 | `rgbOff` | `pgu-storymode-motor-reset-1163-rgboff-896bfef9` |
| STAGED | RGB4 | UNCONFIRMED COMPONENT — RGB4 | `rgbOff` | `pgu-storymode-motor-reset-1164-rgboff-365f8509` |
| STAGED | RGB7 | UNCONFIRMED COMPONENT — RGB7 | `rgbOff` | `pgu-storymode-motor-reset-1165-rgboff-6a484701` |
| STAGED | RGB8 | UNCONFIRMED COMPONENT — RGB8 | `rgbOff` | `pgu-storymode-motor-reset-1166-rgboff-b42cb130` |
| STAGED | RGB9 | UNCONFIRMED COMPONENT — RGB9 | `rgbOff` | `pgu-storymode-motor-reset-1167-rgboff-974eb11f` |
| STAGED | Runtime／group target '12' | UNCONFIRMED COMPONENT — Runtime／group target '12' | `chBreathAll` | `pgu-storymode-motor-reset-610-chbreathall-400a21e6`<br>`pgu-storymode-motor-reset-808-chbreathall-49a7f51f`<br>`pgu-storymode-motor-reset-979-chbreathall-f29c44ab`<br>`pgu-storymode-motor-reset-1155-chbreathall-cf29e323` |

## SpecificColorPattern design contract

`RGB4／SpecificColorPattern` 是逐粒訊號分派器：`profile namespace` 選 registry/index/override arrays，index 再選 `sub-pattern`。Normal、Repair、Develop profile 不可因顏色相同而共用硬體 arrays。

- Slave 1 RGB4 是頭部 3 粒訊號燈；每燈 state 依實際 `numLeds` 動態配置。
- Normal：三粒機械綠慢速呼吸。
- Repair：三粒琥珀橙雙脈衝。
- Develop：三粒科技藍 120 ms 規律閃爍。
- Registry ID 1、11、12、13 共用 `BlinkBurstSingleLedPattern`；其他 sub-pattern 包括 `BreathGreenSingleLedPattern`、`BlinkBlueSingleLedPattern`、`MachineGunSingleLedPattern`、`LongTurnOnSingleLedPattern`、`SolidOnSingleLedPattern`。
- `CRGB::Black` override 是沿用 registry 原色，不是 OFF；OFF 必須使用 index `0`。

## Brightness and protected hardware contract

- Slave 1 使用各 StoryMode 的 global／local brightness；接線 mapping 不另加專屬亮度 cap。
- Slave 8／10 是共用腿部 group；使用相同 StoryMode code 與 brightness policy，不保留舊 Slave 10 platform 的 `42/255` cap。
- `Slave 1 head PCA`：只有 `0x5F` 一片；CH0–12 依頭部 StoryMode 分配，CH13–15 未接線。
- `Slave 3 Head／Chest PCA`：以上 Slave 3 表與 function-level records 共同表示頭部／胸部 PCA 呼叫。
- Slave 3 PWM0 CH0／CH6 protected eyes 放在 function-level 獨立更新；不能被 case 內 off/all-board effect 覆蓋。
- PCA 顏色由實體 LED 決定；顏色不能單獨選 effect。

## Regeneration

```bash
python3 .codex/skills/project-automation-rules/scripts/generate_project_call_filing.py
```

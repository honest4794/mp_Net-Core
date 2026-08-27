---
title: File classification for PR (allow / remind / protect)
tags: pull-request, classification, protected-modules, local-config
---

# PR 檔案分類（單一真相來源）

吸收自已退役的 selective-merge-lighting 工作流程。本表是專案 PR 分類的唯一權威來源。

## 不允許（偵測到就提醒，並自動剝除）

| 檔案 | 原因 |
| --- | --- |
| `.claude/settings.local.json` | 本機 Claude 設定，不該進 PR |
| `compile_commands.json` | 自動產生物 |
| `changed_files.txt` | 臨時 scratch 檔 |

剝除後告知開發者哪些檔被移出 PR。

## 允許但提醒（偵測到就提醒，不自動剝除）

| 檔案 | 提醒語意 |
| --- | --- |
| `platformio_local.ini` | 本機/範本設定，確定要進 PR 嗎？確認後可保留 |

> 注意：`platformio.ini`（共用基底）為正常可 PR，不在任何清單。

## 核心保護分類（碰到就特別提醒，非禁止）

| 類別 | 路徑特徵 |
| --- | --- |
| Controllers | `firmware/*/{src,include}/*Controller.*` |
| OTA | `otaManager.*`、`otaProtocol.h` |
| WiFi / network | `wifi*`、`network*`、`web/`、`data/html` |
| UART 協議 | timer/video UART controller 與協議 |

碰到核心保護分類時，提醒：「這碰到受保護核心模組，請確認這正是你要的」。

> Story mode（`firmware/*/{src,include}/storymode/*`）**不列為保護區**，視為一般可 PR 範圍。

## 一般燈效類（常見可直接 PR）

`firmware/*/{src,include}/lib/*`、`firmware/*/{src,include}/patterns/*`、`palettes.*`、`lib_effects`/`lib_led`/`lib_rgb`/`lib_channel`。

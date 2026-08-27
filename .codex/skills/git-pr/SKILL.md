---
name: git-pr
description: Use when creating a pull request in this project, cherry-picking a single feature onto the dev branch, or extracting one feature from a messy branch to PR. Triggers on "open a PR", "開pr", "幫我發 PR", "PR 到 dev", "PR this feature", "cherry-pick to dev". Targets dev (never master/main); never PRs the whole current branch.
license: MIT
metadata:
  tags: github, gh-cli, pull-request, cherry-pick, dev-branch, single-feature
---

# git-pr

本專案所有 PR 知識的單一真相來源。把當前分支裡的**單一 feature** 乾淨抽出，cherry-pick 到 `dev`，建立 PR。

## 不變式

- **Target 永遠 `origin/dev`**，絕不 master/main。
- **永不整支 PR 當前分支**；先問開發者要 PR 哪個 feature。
- **一次一個 feature**；過大或跨多子系統就擋下、要求拆分。
- 任何 commit/push/branch/PR 前**先問開發者同意**。
- 永不自動解衝突。

## 主流程

1. **問是哪個 feature**（強制第一步）。開發者用文字描述；要具體，不清就追問。絕不略過、絕不整支 PR。
2. **定位改動**：`git fetch origin dev`，在 `git log origin/dev..HEAD` 與 `git diff origin/dev...HEAD` 找對應 commit/檔案/hunk，分類為（a）乾淨 commit 或（b）糾纏改動。
3. **計畫預覽 + 二次確認**（任何 git 動作前的硬性閘門）。給開發者一份簡短、清楚、精確的預覽：Feature 一句話、Target=`origin/dev`、新分支 `feat/<slug>`、要抽的 commit/檔案清單、提醒旗標。**未明確二次確認不動手。**
   - **範圍跳閘（不得默默放行）**：若 **>5 檔案**、或 **>~200 行**、或 **跨 >1 子系統** → 在預覽中明確標示「超出單一 feature 範圍」並建議拆成 N 個 PR，由開發者決定。即使他說「要快」也要先標示。
4. **從 dev 開分支**：`git checkout -b feat/<slug> origin/dev`。
5. **抽取**：乾淨 commit → `git cherry-pick <hash...>`；糾纏 → `git cherry-pick -n` 後 `git restore` 掉不要的，或套限定檔案/hunk 的 patch。
6. **衝突預檢**：驗證能乾淨套到最新 dev。有衝突 → 分析並**提建議解法給開發者確認，不自動套**。
7. **完成前驗證**：分支基於最新 `origin/dev`、改動存在、`git diff origin/dev...HEAD` 只含此 feature。夾帶不允許清單檔 → 提醒並自動剝除；夾帶 `platformio_local.ini` → 提醒（見下表）。環境有 superpowers 可順手套 `verification-before-completion`。
8. **建 PR 前最終衝突閘門**：`git fetch origin dev` 後 dry-run（`git merge-tree $(git merge-base HEAD origin/dev) HEAD origin/dev`），確認對**最新 dev**（可能已前進）無衝突。有衝突 → 提解法給開發者確認，不自動套。
9. **建 PR**：`gh pr create --base dev`，標題沿用 repo 慣例（`fix(...)`/`docs:`，繁中）。建完驗證 PR 存在且 base=dev。

詳細逐步與邊界情況見 [cherry-pick-feature-pr.md](references/cherry-pick-feature-pr.md)。

## 不允許清單（偵測到就提醒，並自動剝除）

`.claude/settings.local.json`、`compile_commands.json`、`changed_files.txt`（本機設定 / 產生物 / scratch 檔，剝除後告知開發者）。

## 允許但提醒清單（偵測到就提醒，不自動剝除）

`platformio_local.ini`（本機/範本設定，確認後可保留）。

## 核心保護分類（碰到就特別提醒，非禁止）

Controllers（`*Controller.*`）、OTA（`otaManager.*`/`otaProtocol.h`）、WiFi/network（`wifi*`/`network*`/`web/`）、UART 協議。完整分類見 [file-classification.md](references/file-classification.md)。

> Story mode（`*/storymode/*`）**不是**保護區，視為一般可 PR 範圍。

## 衝突處理

永不自動解。列出衝突檔案 + 原因 + **建議解法**，等開發者點頭；可要求中止（`git cherry-pick --abort` / 刪分支）。

## 常見錯誤

| 錯誤 | 正解 |
| --- | --- |
| 整支 PR 當前分支 | 只抽開發者指名的單一 feature |
| target master/main | 一律 `--base dev` |
| 略過計畫預覽直接動手 | 先列計畫、二次確認 |
| 自動解衝突 | 提解法給開發者確認 |
| 「要快」就放行巨量變更 | 觸發範圍跳閘，先標示並建議拆分 |
| 只信 cherry-pick 乾淨、不對最新 dev 預檢 | 建 PR 前 `git fetch` + merge-tree dry-run |

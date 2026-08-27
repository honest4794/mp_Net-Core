---
title: Cherry-pick single feature → PR to dev
tags: pull-request, cherry-pick, dev-branch, single-feature, conflict-precheck
---

# Cherry-pick 單一 feature → PR 到 dev（逐步）

## 0. 前提

- 永遠 target `origin/dev`。任何 commit/push/branch/PR 前先問開發者同意。

## 1. 問是哪個 feature

開發者用文字描述。描述不清（含多件事、看不出範圍）就追問到能對應到具體改動為止。

## 2. 定位改動

```bash
git fetch origin dev
git log --oneline origin/dev..HEAD          # 本分支獨有 commit
git diff --stat origin/dev...HEAD           # 本分支獨有檔案改動
```

判斷該 feature 屬於：
- **(a) 乾淨 commit**：一個或數個 commit 剛好等於這個 feature。
- **(b) 糾纏改動**：feature 與其他東西混在同一批 commit 裡，需按檔案/hunk 抽。

## 3. 計畫預覽 + 二次確認（硬性閘門）

動任何 git 之前，給開發者這份預覽：

```
PR 計畫預覽
- Feature：<一句話>
- Target：origin/dev
- 新分支：feat/<slug>
- 抽取方式：(a) cherry-pick <hash 清單>  或  (b) 限定檔案/hunk patch
- 內容：<commit hash + 標題  或  檔案/hunk 清單>
- 提醒：<若含允許+提醒清單檔案 / 碰到核心保護分類，列出>
- 範圍：<OK / 過大建議拆成 N 個>
```

未取得明確「確認」前不執行。

**範圍跳閘（不得默默放行）**：若 **>5 檔案**、或 **>~200 行**、或 **跨 >1 子系統**，必須在預覽中標示「超出單一 feature」並建議拆成 N 個 PR。即使開發者說「要快」也要先標示再讓他決定。

```bash
git diff --shortstat origin/dev...HEAD     # 檔案數 / 行數，判斷是否超標
```

## 4. 從 dev 開分支

```bash
git checkout -b feat/<slug> origin/dev
```

## 5. 抽取

### (a) 乾淨 commit

```bash
git cherry-pick <hash1> <hash2> ...
```

### (b) 糾纏改動 — 只留要的檔案/hunk

方法一（按檔案）：
```bash
git cherry-pick -n <hash>          # 套用但不 commit
git restore --staged <不要的檔案>   # 退出 index
git checkout -- <不要的檔案>        # 還原工作區
git commit -m "<feature 描述>"
```

方法二（按 hunk，改動散在同檔）：
```bash
git checkout origin/dev -- <檔案>   # 先取 dev 版
git checkout <來源分支> -- <檔案>    # 取整檔再...
git restore -p <檔案>               # 互動式只退掉不要的 hunk
```
或直接 `git diff origin/dev...<來源> -- <檔案> > /tmp/f.patch`，手動裁切後 `git apply`。

## 6. 衝突預檢

cherry-pick / apply 當下若衝突，git 會停住。**不自動解**：

1. 列出衝突檔案：`git status`
2. 分析衝突原因，**提出建議解法**給開發者。
3. 等開發者確認後才 `git add <files> && git cherry-pick --continue`。
4. 開發者要放棄：`git cherry-pick --abort`，必要時刪分支 `git checkout dev && git branch -D feat/<slug>`。

## 7. 完成前驗證

```bash
git merge-base --is-ancestor origin/dev HEAD && echo "分支基於最新 dev"
git diff --stat origin/dev...HEAD          # 應只含此 feature
```
逐項確認：分支基於最新 dev、改動存在、diff 只含此 feature。
依分類處理夾帶檔（見 [file-classification.md](file-classification.md)）：
- **不允許清單**（`.claude/settings.local.json`/`compile_commands.json`/`changed_files.txt`）→ 提醒並自動剝除，剝除後告知開發者。
- **允許但提醒**（`platformio_local.ini`）→ 提醒開發者確認是否真要 PR，確認後保留。

## 8. 建 PR 前最終衝突閘門

cherry-pick 乾淨 ≠ 對「最新」dev 無衝突——dev 可能在開分支後又前進。建 PR 前重新預檢：

```bash
git fetch origin dev
git merge-tree $(git merge-base HEAD origin/dev) HEAD origin/dev   # 有衝突會印出 <<<<<<< 標記
```
若印出衝突標記 → 列出衝突檔案、**提建議解法給開發者確認**，不自動套（同 §6 規則）。乾淨才往下。

## 9. 建 PR

```bash
git push -u origin feat/<slug>             # push 前先問同意
gh pr create --base dev --title "<repo 慣例標題>" --body "<繁中說明>"
gh pr view --json baseRefName,number       # 驗證 base=dev、PR 存在
```

## 邊界情況

- **feature 已部分在 dev**：cherry-pick 時 git 會自動略過已存在的改動；確認最終 diff 仍正確。
- **改動只在 working tree（未 commit）**：用 `git stash` 或直接在新分支上 `git checkout <來源> -- <檔案>` 後 commit。
- **多個 commit 同檔交錯**：優先按 hunk（方法二），必要時請開發者協助界定哪些 hunk 屬於此 feature。

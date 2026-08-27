#!/usr/bin/env python3
"""Render the complete PGU call archive and component/storyMode matrix."""

from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
import argparse
import re

from project_call_inventory import (
    CallRecord,
    FORMAL_MODES,
    NON_FORMAL_MODES,
    ROOT,
    SKILL_ROOT,
    load_pgu_records,
    load_red_astray_active_gun_records,
    unknown_project_calls,
)


ARCHIVE = SKILL_ROOT / "references/project_call_archive.md"
MATRIX = SKILL_ROOT / "references/component_storymode_matrix.md"


def inline(value: str) -> str:
    return value.replace("`", "'").replace("\n", " ").strip()


def record_sort_key(record: CallRecord) -> tuple[int, int, str]:
    mode_order = {
        mode.name: index for index, mode in enumerate(FORMAL_MODES + NON_FORMAL_MODES)
    }
    return mode_order.get(record.story_mode, 999), record.source_line, record.function


def render_record(record: CallRecord) -> list[str]:
    definitions = "; ".join(record.parameter_definitions)
    groups = "、".join(record.parameter_groups)
    return [
        f"<!-- CALL:{record.record_id} -->",
        f"### `{record.record_id}` — `{record.function}` · {inline(record.hardware_target)}",
        "",
        f"- Project／Authority: {record.authority}",
        f"- Status: `{record.status}`",
        f"- StoryMode: `{record.story_mode}`（{record.controller_id}）",
        f"- Stage／Condition: {inline(record.stage_condition)}",
        f"- Slave context: {inline(record.slave_context)}",
        f"- Hardware target: {inline(record.hardware_target)}",
        f"- Component description: {inline(record.component_description)}",
        f"- Function: `{record.function}`",
        "- Complete call:",
        "",
        "```cpp",
        record.complete_call.rstrip(),
        "```",
        "",
        f"- Loop context: `{inline(record.loop_context)}`",
        f"- Parameter groups: {groups}",
        f"- Parameter definitions: {inline(definitions)}",
        f"- Source: `{record.source_path}:{record.source_line}`",
        "",
    ]


def render_mode_index(records: list[CallRecord]) -> list[str]:
    by_slave = Counter(record.slave_context for record in records)
    by_function = Counter(record.function for record in records)
    by_target = Counter(record.hardware_target for record in records)
    lines = [
        f"Records：**{len(records)}**；Slave contexts：**{len(by_slave)}**；"
        f"functions：**{len(by_function)}**；targets：**{len(by_target)}**。",
        "",
        "| Slave context | Records |",
        "| --- | ---: |",
    ]
    lines.extend(f"| {inline(name)} | {count} |" for name, count in sorted(by_slave.items()))
    lines.extend(["", "Functions：" + "、".join(
        f"`{name}`×{count}" for name, count in sorted(by_function.items())
    ), ""])
    return lines


def render_archive(pgu_records: list[CallRecord],
                   historical_records: list[CallRecord]) -> str:
    formal = [record for record in pgu_records if record.status == "formal active"]
    non_formal = [record for record in pgu_records if record.status == "non-formal active"]
    unknown = sorted(unknown_project_calls())
    unconfirmed = sum(
        record.component_description.startswith("UNCONFIRMED")
        for record in formal
    )
    lines = [
        "# Project Call Archive — Complete Call-Site Register",
        "",
        "> 這不是 example list。PGU 正式 StoryMode 每個符合範圍的硬體／效果 source call site 都有獨立 record；loop 保留原 call，不展開 channel。",
        "",
        "## Authority and scope",
        "",
        "1. `dev_PGU_V2 — CURRENT STANDARD`：完整保存 12 LED＋2 servo 正式 modes。",
        "2. `all_off`、demo、dev、VU：只放 non-formal section。",
        "3. `dev_Red_Astray_Honest`：只保存 Controller 正式啟用 modes 的 active gun calls。",
        "4. Historical records 全部標記 `DO NOT COPY BRIGHTNESS`；Red Astray 不是 brightness authority，PGU brightness／Slave grouping 永遠優先。",
        "5. 一般 utility calls（例如 `millis`、`min`、`fill_solid`）不屬本 archive。",
        "",
        "## Coverage summary",
        "",
        f"- PGU formal records：**{len(formal)}**",
        f"- PGU formal modes：**{len({record.story_mode for record in formal})} / 14**",
        f"- Formal functions：**{len({record.function for record in formal})}**",
        f"- Formal hardware targets：**{len({record.hardware_target for record in formal})}**",
        f"- Formal Slave contexts：**{len({record.slave_context for record in formal})}**",
        f"- Formal records marked `UNCONFIRMED COMPONENT`：**{unconfirmed}**",
        f"- PGU non-formal records：**{len(non_formal)}**",
        f"- Red Astray active historical gun records：**{len(historical_records)}**",
        f"- Unknown project-defined hardware calls：**{len(unknown)}**",
        "",
        "## PGU formal StoryModes",
        "",
    ]
    formal_by_mode: dict[str, list[CallRecord]] = defaultdict(list)
    for record in formal:
        formal_by_mode[record.story_mode].append(record)
    for mode in FORMAL_MODES:
        records = sorted(formal_by_mode[mode.name], key=record_sort_key)
        lines.extend([f"## {mode.name}", ""])
        lines.extend(render_mode_index(records))
        for record in records:
            lines.extend(render_record(record))

    lines.extend(["## PGU non-formal entries", ""])
    non_formal_by_mode: dict[str, list[CallRecord]] = defaultdict(list)
    for record in non_formal:
        non_formal_by_mode[record.story_mode].append(record)
    for mode in NON_FORMAL_MODES:
        lines.extend([f"## {mode.name} — NON-FORMAL", ""])
        records = sorted(non_formal_by_mode[mode.name], key=record_sort_key)
        lines.extend(render_mode_index(records))
        for record in records:
            lines.extend(render_record(record))

    lines.extend([
        "## dev_Red_Astray_Honest — HISTORICAL GUN REFERENCE",
        "",
        "> **DO NOT COPY BRIGHTNESS.** 只保留該 branch Controller 正式啟用 modes 中未被註解的 active gun calls；demo、commented calls、未註冊 `storyMode_1`／`storyMode_stream` 全部排除。",
        "",
    ])
    for record in historical_records:
        lines.extend(render_record(record))

    lines.extend([
        "## Unconfirmed component audit",
        "",
        "`UNCONFIRMED COMPONENT` 代表 source call 存在，但附近沒有足夠硬體描述；它仍保留 target、function、完整參數與 source，不以顏色猜 component。",
        "",
        f"目前正式 records 中共有 **{unconfirmed}** 筆。可用 `project_call_component_overrides.json` 依接線資料逐步補正。",
        "",
        "## Filing rules",
        "",
        "- 每個 source call site 一筆 record；不同 Slave、stage、target 或 source line 不合併。",
        "- 每次正式 StoryMode hardware/effect call 改動後執行 `python3 .codex/skills/project-automation-rules/scripts/generate_project_call_filing.py`。",
        "- Generator 重跑不得產生 diff；completeness test 必須比對 source call-site key。",
        "- Component description 優先 source 硬體註解，其次 confirmed override；無資料時明確標記，不可猜測。",
    ])
    return "\n".join(lines).rstrip() + "\n"


def lifecycle(record: CallRecord) -> str:
    name = record.function.lower()
    if "fade" in name or record.stage_condition != "always／current mode state":
        return "STAGED"
    if any(token in name for token in ("off", "clear", "reset", "stop")):
        return "OFF"
    return "ON"


def slave_numbers(context: str) -> set[int]:
    match = re.match(r"Slave ([0-9/]+)", context)
    if not match:
        return set()
    return {int(value) for value in match.group(1).split("/")}


def render_matrix_group(records: list[CallRecord]) -> list[str]:
    grouped: dict[tuple[str, str, str, str], list[CallRecord]] = defaultdict(list)
    for record in records:
        key = (
            record.story_mode,
            record.hardware_target,
            record.component_description,
            lifecycle(record),
        )
        grouped[key].append(record)
    lines: list[str] = []
    for mode in FORMAL_MODES:
        mode_groups = [
            (key, values) for key, values in grouped.items() if key[0] == mode.name
        ]
        lines.extend([f"### {mode.name}", ""])
        if not mode_groups:
            lines.extend(["OFF／no direct call in this Slave context。", ""])
            continue
        lines.extend([
            "| ON／OFF／STAGED | Hardware target | Component description | Functions | Archive record IDs |",
            "| --- | --- | --- | --- | --- |",
        ])
        for key, values in sorted(mode_groups, key=lambda item: (item[0][1], item[0][2], item[0][3])):
            _, target, component, state = key
            functions = "、".join(f"`{name}`" for name in sorted({item.function for item in values}))
            record_ids = "<br>".join(f"`{item.record_id}`" for item in sorted(values, key=lambda item: item.source_line))
            lines.append(
                f"| {state} | {inline(target)} | {inline(component)} | {functions} | {record_ids} |"
            )
        lines.append("")
    return lines


def render_component_matrix(pgu_records: list[CallRecord]) -> str:
    formal = [record for record in pgu_records if record.status == "formal active"]
    lines = [
        "# PGU Complete Component × StoryMode Matrix",
        "",
        "> 本矩陣與 `project_call_archive.md` 使用同一份 source-derived records。每個正式 record ID 必須在此出現；完整 call 與參數見 archive。",
        "",
        "## Legend and authority",
        "",
        "- `ON`：目前 mode/context 的直接持續 effect call。",
        "- `OFF`：明確 off/clear/reset/stop；功能需要時 off is acceptable。",
        "- `STAGED`：受 stage/condition 控制，或 fade transition。",
        "- `candidate—not firmware authority`：未寫入目前 source 的候選值不可當現況。",
        "- Loop 保留一筆 call 與 loop range，不展開逐 channel records。",
        "",
        "## Controller order",
        "",
    ]
    lines.extend(
        f"- {mode.controller_set} {mode.controller_id}: `{mode.name}`"
        for mode in FORMAL_MODES
    )
    lines.append("")

    # Hi-Nu 20-slave grouping：matrix 依 Slave 1-20 分組。
    for slave in range(1, 21):
        records = [record for record in formal if slave in slave_numbers(record.slave_context)]
        lines.extend([f"## Slave {slave}", ""])
        lines.extend(render_matrix_group(records))

    shared = [record for record in formal if not slave_numbers(record.slave_context)]
    lines.extend(["## Shared／global and function-level-unresolved calls", ""])
    lines.extend(render_matrix_group(shared))

    lines.extend([
        "## SpecificColorPattern design contract",
        "",
        "`RGB4／SpecificColorPattern` 是逐粒訊號分派器：`profile namespace` 選 registry/index/override arrays，index 再選 `sub-pattern`。Normal、Repair、Develop profile 不可因顏色相同而共用硬體 arrays。",
        "",
        "- Slave 1 RGB4 是頭部 3 粒訊號燈；每燈 state 依實際 `numLeds` 動態配置。",
        "- Normal：三粒機械綠慢速呼吸。",
        "- Repair：三粒琥珀橙雙脈衝。",
        "- Develop：三粒科技藍 120 ms 規律閃爍。",
        "- Registry ID 1、11、12、13 共用 `BlinkBurstSingleLedPattern`；其他 sub-pattern 包括 `BreathGreenSingleLedPattern`、`BlinkBlueSingleLedPattern`、`MachineGunSingleLedPattern`、`LongTurnOnSingleLedPattern`、`SolidOnSingleLedPattern`。",
        "- `CRGB::Black` override 是沿用 registry 原色，不是 OFF；OFF 必須使用 index `0`。",
        "",
        "## Brightness and protected hardware contract",
        "",
        "- Slave 1 使用各 StoryMode 的 global／local brightness；接線 mapping 不另加專屬亮度 cap。",
        "- Slave 8／10 是共用腿部 group；使用相同 StoryMode code 與 brightness policy，不保留舊 Slave 10 platform 的 `42/255` cap。",
        "- `Slave 1 head PCA`：只有 `0x5F` 一片；CH0–12 依頭部 StoryMode 分配，CH13–15 未接線。",
        "- `Slave 3 Head／Chest PCA`：以上 Slave 3 表與 function-level records 共同表示頭部／胸部 PCA 呼叫。",
        "- Slave 3 PWM0 CH0／CH6 protected eyes 放在 function-level 獨立更新；不能被 case 內 off/all-board effect 覆蓋。",
        "- PCA 顏色由實體 LED 決定；顏色不能單獨選 effect。",
        "",
        "## Regeneration",
        "",
        "```bash",
        "python3 .codex/skills/project-automation-rules/scripts/generate_project_call_filing.py",
        "```",
    ])
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive-only", action="store_true")
    parser.add_argument("--matrix-only", action="store_true")
    args = parser.parse_args()
    if args.archive_only and args.matrix_only:
        parser.error("--archive-only and --matrix-only are mutually exclusive")

    pgu_records = load_pgu_records(ROOT, include_non_formal=True)
    if not args.matrix_only:
        historical = load_red_astray_active_gun_records(ROOT)
        ARCHIVE.write_text(render_archive(pgu_records, historical), encoding="utf-8")
    if not args.archive_only:
        MATRIX.write_text(render_component_matrix(pgu_records), encoding="utf-8")


if __name__ == "__main__":
    main()

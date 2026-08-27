#!/usr/bin/env python3
"""Build source-derived hardware/effect call records for project filing."""

from __future__ import annotations

from dataclasses import dataclass, replace
from functools import lru_cache
from pathlib import Path
import hashlib
import json
import re
import subprocess
from typing import Iterable


ROOT = Path(__file__).resolve().parents[4]
STORY_ROOT = ROOT / "firmware/shared/src/storymode"
SKILL_ROOT = ROOT / ".codex/skills/project-automation-rules"
CATALOG = SKILL_ROOT / "references/effect_function_catalog.md"
OVERRIDES = SKILL_ROOT / "references/project_call_component_overrides.json"


@dataclass(frozen=True)
class ModeSpec:
    name: str
    filename: str
    controller_set: str
    controller_id: str
    status: str = "formal active"


@dataclass(frozen=True)
class CallRecord:
    record_id: str
    project: str
    authority: str
    status: str
    story_mode: str
    controller_id: str
    stage_condition: str
    slave_context: str
    hardware_target: str
    component_description: str
    function: str
    complete_call: str
    loop_context: str
    parameter_groups: tuple[str, ...]
    parameter_definitions: tuple[str, ...]
    source_path: str
    source_line: int


FORMAL_MODES = (
    ModeSpec("storyMode_develop", "storyMode_develop.cpp", "LED", "0"),
    ModeSpec("storyMode_signals", "storyMode_signals.cpp", "LED", "1"),
    ModeSpec("storyMode_0_v1", "storyMode_0_v1.cpp", "LED", "2"),
    ModeSpec("storyMode_awakening_3", "storyMode_awakening_3.cpp", "LED", "3"),
    ModeSpec("storyMode_activation", "storyMode_activation.cpp", "LED", "4"),
    ModeSpec("storyMode_0_v2", "storyMode_0_v2.cpp", "LED", "5"),
    ModeSpec("storyMode_storing_energy", "storyMode_storing_energy.cpp", "LED", "6"),
    ModeSpec("storyMode_2", "storyMode_2.cpp", "LED", "7"),
    ModeSpec("storyMode_plasma", "storyMode_plasma.cpp", "LED", "8"),
    ModeSpec("storyMode_trans_am", "storyMode_trans_am.cpp", "LED", "9"),
    ModeSpec("storyMode_3", "storyMode_3.cpp", "LED", "10"),
    ModeSpec("storyMode_idle", "storyMode_idle.cpp", "LED", "11"),
    ModeSpec("storyMode_motor", "storyMode_motor.cpp", "SERVO", "0"),
    ModeSpec("storyMode_motor_reset", "storyMode_motor_reset.cpp", "SERVO", "1"),
)

NON_FORMAL_MODES = (
    ModeSpec("storyMode_all_off", "storyMode_all_off.cpp", "NON_FORMAL", "none", "non-formal active"),
    ModeSpec("storyMode_demo", "storyMode_demo.cpp", "NON_FORMAL", "none", "non-formal active"),
    ModeSpec("storyMode_dev", "storyMode_dev.cpp", "NON_FORMAL", "none", "non-formal active"),
    ModeSpec("storyMode_vu", "storyMode_vu.cpp", "NON_FORMAL", "none", "non-formal active"),
)

RED_ASTRAY_GUN_FUNCTIONS = {
    "Machine_Gun",
    "Machine_Gun_RedAstrayLimited",
    "Missile_Launcher",
    "Missile_Launcher_breath",
    "Missile_Launcher_F16",
    "gunStoringEnergy",
    "GunFirePattern",
    "gunfire",
}

PROJECT_EFFECT_HELPERS = {
    "renderSlave3Rgb4SpecificColor",
    "renderSlave78Rgb1StorySpecificColor",
}

CONTROL_WORDS = {
    "if", "else", "for", "while", "switch", "return", "sizeof", "min", "max",
    "constrain", "map", "abs", "round", "floor", "ceil", "sin", "cos", "sqrt",
    "static_cast", "reinterpret_cast", "const_cast", "dynamic_cast",
}
UTILITY_DENYLIST = CONTROL_WORDS | {
    "millis", "micros", "delay", "memset", "memcpy", "memmove", "fill_solid",
    "fill_rainbow", "fadeToBlackBy", "nblend", "ColorFromPalette", "beatsin8",
    "beatsin16", "sin8", "sin16", "random", "random8", "random16", "random16_add_entropy",
    "qadd8", "qsub8", "scale8", "lerp8by8", "inoise8", "inoise16", "EVERY_N_MILLISECONDS",
    "String", "Serial", "LOG_STORY", "LOG_DEBUG", "LOG_ERROR",
}

CALL_RE = re.compile(
    r"(?<![A-Za-z0-9_])(?:(?P<object>[A-Za-z_]\w*)\s*\.\s*)?"
    r"(?P<name>[A-Za-z_]\w*)\s*\("
)
DECL_RE = re.compile(
    r"^(?!\s*(?:if|for|while|switch|return|typedef)\b)"
    r"\s*(?:inline\s+)?[A-Za-z_][A-Za-z0-9_:<>,*& ]+\s+"
    r"(?P<name>[A-Za-z_]\w*)\s*\("
)


def strip_comments_preserve_layout(text: str, strip_strings: bool = True) -> str:
    """Replace comments and optionally strings with spaces while preserving offsets."""
    output = list(text)
    index = 0
    state = "normal"
    while index < len(text):
        char = text[index]
        following = text[index + 1] if index + 1 < len(text) else ""
        if state == "normal":
            if char == "/" and following == "/":
                output[index] = output[index + 1] = " "
                index += 2
                state = "line_comment"
                continue
            if char == "/" and following == "*":
                output[index] = output[index + 1] = " "
                index += 2
                state = "block_comment"
                continue
            if char == '"':
                state = "string"
                if strip_strings:
                    output[index] = " "
            elif char == "'":
                state = "character"
                if strip_strings:
                    output[index] = " "
        elif state == "line_comment":
            if char == "\n":
                state = "normal"
            else:
                output[index] = " "
        elif state == "block_comment":
            if char == "*" and following == "/":
                output[index] = output[index + 1] = " "
                index += 2
                state = "normal"
                continue
            if char != "\n":
                output[index] = " "
        elif state in {"string", "character"}:
            quote = '"' if state == "string" else "'"
            if char == "\\":
                if strip_strings and char != "\n":
                    output[index] = " "
                if index + 1 < len(text) and strip_strings and text[index + 1] != "\n":
                    output[index + 1] = " "
                index += 2
                continue
            if char == quote:
                state = "normal"
            if strip_strings and char != "\n":
                output[index] = " "
        index += 1
    return "".join(output)


def find_matching(text: str, opening: int, opening_char: str, closing_char: str) -> int:
    depth = 0
    for index in range(opening, len(text)):
        if text[index] == opening_char:
            depth += 1
        elif text[index] == closing_char:
            depth -= 1
            if depth == 0:
                return index
    return -1


def brace_pairs(sanitized: str) -> tuple[tuple[int, int], ...]:
    stack: list[int] = []
    pairs: list[tuple[int, int]] = []
    for index, character in enumerate(sanitized):
        if character == "{":
            stack.append(index)
        elif character == "}" and stack:
            pairs.append((stack.pop(), index))
    return tuple(sorted(pairs))


def block_header(original: str, sanitized: str, opening: int) -> str:
    cursor = opening - 1
    while cursor >= 0 and sanitized[cursor].isspace():
        cursor -= 1
    if cursor >= 0 and sanitized[cursor] == ")":
        depth = 0
        parenthesis = -1
        for index in range(cursor, -1, -1):
            if sanitized[index] == ")":
                depth += 1
            elif sanitized[index] == "(":
                depth -= 1
                if depth == 0:
                    parenthesis = index
                    break
        if parenthesis >= 0:
            keyword_match = re.search(r"(?:else\s+)?(?:if|for|while|switch)\s*$",
                                      sanitized[:parenthesis])
            if keyword_match:
                return " ".join(original[keyword_match.start():opening].split())
    previous = max(
        sanitized.rfind(";", 0, opening),
        sanitized.rfind("{", 0, opening),
        sanitized.rfind("}", 0, opening),
    )
    return " ".join(original[previous + 1:opening].split())


def declaration_names(header: Path) -> set[str]:
    names: set[str] = set()
    for line in header.read_text(encoding="utf-8", errors="ignore").splitlines():
        match = DECL_RE.match(line)
        if match:
            names.add(match.group("name"))
    return names


@lru_cache(maxsize=4)
def discover_callable_names(root: Path = ROOT) -> set[str]:
    names = set(re.findall(r"<!-- API:([A-Za-z_]\w*) -->", CATALOG.read_text(encoding="utf-8")))
    headers = (
        root / "firmware/shared/include/lib/lib_channel.h",
        root / "firmware/shared/include/patterns/patterns_channel.h",
        root / "firmware/shared/include/patterns/patterns_cross_effects.h",
        root / "firmware/shared/include/patterns/patterns_matrix.h",
    )
    for header in headers:
        names.update(declaration_names(header))
    names.update({"digitalWrite", "setBrightness", "clear", "show"})
    names.update(PROJECT_EFFECT_HELPERS)
    return names - UTILITY_DENYLIST


def expression_start(original: str, name_start: int) -> int:
    line_start = original.rfind("\n", 0, name_start) + 1
    prefix = original[line_start:name_start]
    member = re.search(
        r"([A-Za-z_]\w*(?:\s*\[[^\]\n]+\])?(?:\s*(?:\.|->)\s*))$",
        prefix,
    )
    return line_start + member.start(1) if member else name_start


def enclosing_header(original: str, sanitized: str, pairs: tuple[tuple[int, int], ...],
                     position: int, keyword: str) -> list[str]:
    headers: list[str] = []
    for opening, closing in pairs:
        if not (opening < position < closing):
            continue
        header = block_header(original, sanitized, opening)
        if re.search(rf"\b{re.escape(keyword)}\s*\(", header):
            headers.append(header)
    return headers


def loop_context(original: str, sanitized: str, pairs: tuple[tuple[int, int], ...],
                 position: int) -> str:
    loops = enclosing_header(original, sanitized, pairs, position, "for")
    return loops[-1] if loops else "none"


def switch_slave_context(sanitized: str, pairs: tuple[tuple[int, int], ...],
                         position: int) -> str | None:
    switch_re = re.compile(r"switch\s*\(\s*slaveId\s*\)\s*\{")
    for match in switch_re.finditer(sanitized):
        opening = sanitized.find("{", match.start(), match.end())
        closing = next((end for start, end in pairs if start == opening), -1)
        if not (opening < position < closing):
            continue
        cases = list(re.finditer(r"\bcase\s+(\d+)\s*:", sanitized[opening:position]))
        if not cases:
            return "Shared／global"
        last = cases[-1]
        labels = [last.group(1)]
        cursor = last.start()
        for previous in reversed(cases[:-1]):
            between = sanitized[opening + previous.end():opening + cursor]
            if re.sub(r"\s+", "", between) == "":
                labels.append(previous.group(1))
                cursor = previous.start()
            else:
                break
        return "Slave " + "/".join(reversed(labels))
    return None


def slave_context(original: str, sanitized: str, pairs: tuple[tuple[int, int], ...],
                  position: int) -> str:
    switched = switch_slave_context(sanitized, pairs, position)
    if switched:
        return switched
    conditions = enclosing_header(original, sanitized, pairs, position, "if")
    for condition in reversed(conditions):
        match = re.search(r"slaveId\s*==\s*(\d+)", condition)
        if match:
            return f"Slave {match.group(1)} (function-level)"
        match = re.search(r"(\d+)\s*==\s*slaveId", condition)
        if match:
            return f"Slave {match.group(1)} (function-level)"
    return "Shared／global"


def stage_condition(original: str, sanitized: str, pairs: tuple[tuple[int, int], ...],
                    position: int) -> str:
    conditions = enclosing_header(original, sanitized, pairs, position, "if")
    useful = []
    for condition in conditions:
        if re.search(r"\b(?:time|elapsed|state|Stage|stage|mode|Mode)\b", condition):
            useful.append(condition)
    switch_re = re.compile(r"switch\s*\(\s*([^\)]+?)\s*\)\s*\{")
    for match in switch_re.finditer(sanitized):
        expression = " ".join(match.group(1).split())
        if expression == "slaveId":
            continue
        opening = sanitized.find("{", match.start(), match.end())
        closing = next((end for start, end in pairs if start == opening), -1)
        if not (opening < position < closing):
            continue
        cases = list(re.finditer(
            r"\bcase\s+([A-Za-z_][A-Za-z0-9_:]*|\d+)\s*:",
            sanitized[opening:position],
        ))
        if cases:
            useful.append(f"switch ({expression}) case {cases[-1].group(1)}")
    return " → ".join(useful[-3:]) if useful else "always／current mode state"


def nearest_component_comment(original: str, source_line: int) -> str | None:
    lines = original.splitlines()
    index = source_line - 2
    collected: list[str] = []
    skipped_structural = 0
    while index >= 0 and source_line - index <= 10:
        stripped = lines[index].strip()
        if stripped.startswith("//"):
            content = stripped[2:].strip()
            code_like = re.match(
                r"^(?:[{}]|if\b|else\b|for\b|while\b|switch\b|case\b|break\b|"
                r"return\b|startTime\w*\s*=|[A-Za-z_]\w*\s*\()",
                content,
            )
            code_like = code_like or re.search(
                r"(?:&[A-Za-z_]\w*|\)\s*\{?\s*$|;\s*$)", content
            )
            hardware_word = re.search(
                r"(?:Slave|RGB\d*|PWM\d*|\bCH\d*|PCA|GPIO|motor|servo|LED|"
                r"燈|眼|胸|肩|手|腳|腿|腰|盾|炮|槍|推進|散氣|電容|背包|平台|地台|"
                r"結構|內構|渦輪|噴口|膝)",
                content,
                re.I,
            )
            if (content and not code_like and hardware_word
                    and not re.match(r"^-{3,}$", content)):
                collected.append(content)
            index -= 1
            continue
        if not stripped or stripped in {"{", "}"} or re.match(r"^(?:for|if|else|case)\b", stripped):
            skipped_structural += 1
            if skipped_structural <= 3:
                index -= 1
                continue
        break
    if not collected:
        return None
    description = " ／ ".join(reversed(collected[-3:]))
    return re.sub(r"\s+", " ", description)


def parse_loop_range(loop: str, variable: str) -> str | None:
    if loop == "none":
        return None
    match = re.search(
        rf"\b{re.escape(variable)}\s*=\s*([^;]+);\s*{re.escape(variable)}\s*(<=|<)\s*([^;]+)",
        loop,
    )
    if not match:
        return None
    operator = match.group(2)
    return f"{match.group(1).strip()}..{match.group(3).strip()}{' inclusive' if operator == '<=' else ' exclusive'}"


def hardware_target(complete_call: str, loop: str) -> str:
    rgb = re.search(r"\bleds_RGB(\d+)\b", complete_call)
    if rgb:
        return f"RGB{rgb.group(1)}"
    selected_rgb = re.search(r"\b(selectedRgb\w*)\b", complete_call)
    if selected_rgb:
        return f"RGB runtime target `{selected_rgb.group(1)}`"
    pca = re.search(r"pcaLed\s*\[\s*([^\]]+)\]", complete_call, re.S)
    if pca:
        expression = " ".join(pca.group(1).split())
        board = re.search(r"\bPWM(\d+)\b", expression)
        channel = re.search(r"PWM_CHANNEL_(\d+)", expression)
        if channel:
            channel_label = f"CH{channel.group(1)}"
        else:
            trailing = expression.split("+")[-1].strip()
            loop_range = parse_loop_range(loop, trailing)
            channel_label = f"CH {trailing}"
            if loop_range:
                channel_label += f" (loop {loop_range})"
        board_label = f"PWM{board.group(1)}" if board else "PWM runtime board"
        return f"PCA {board_label} {channel_label}"
    motor = re.search(r"\b(?:espMotor|motorPca|servo\w*)\s*\[\s*([^\]]+)\]", complete_call, re.I)
    if motor:
        return f"Motor／servo channel `{motor.group(1).strip()}`"
    gpio = re.search(r"digitalWrite\s*\(\s*([^,]+)", complete_call)
    if gpio:
        return f"GPIO `{gpio.group(1).strip()}`"
    if re.search(r"FastLED\s*\.\s*setBrightness", complete_call):
        return "Global FastLED brightness"
    if re.search(r"FastLED\s*\.\s*(?:clear|show)", complete_call):
        return "Global FastLED output"
    if re.search(r"\bch(?:OffAll|OffLeds|OnAll|FadeOutAll|InitialStateAll)\s*\(", complete_call):
        return "All PCA／channel output"
    first_argument = complete_call[complete_call.find("(") + 1:]
    first_argument = first_argument.split(",", 1)[0].split(")", 1)[0].strip()
    return f"Runtime／group target `{first_argument or 'implicit'}`"


def parameter_groups(complete_call: str) -> tuple[str, ...]:
    lower = complete_call.lower()
    groups: list[str] = []
    for terms, label in (
        (("pcaled", "leds_rgb", "channel", "motor", "gpio", "pin"), "target／channel"),
        (("brightness", "bright", " high", " low", "fade"), "brightness／fade"),
        (("time", "duration", "interval", "speed", "bpm", "period", "delay", "rest"), "timing／speed"),
        (("color", "crgb", "palette", "hue", "saturation"), "color／palette"),
        (("state", "instance", "lastupdate", "count", "index"), "state／lifecycle"),
        (("direction", "reverse", "width", "height", "radius", "position", "length"), "geometry／direction"),
        (("servo", "motor", "angle", "duty", "step"), "motor／servo motion"),
    ):
        if any(term in lower for term in terms):
            groups.append(label)
    return tuple(groups or ["effect configuration"])


def build_symbol_index(text: str, source_path: str) -> dict[str, tuple[str, ...]]:
    found: dict[str, list[str]] = {}
    type_pattern = re.compile(
        r"\b(?:const\s+|static\s+|constexpr\s+|volatile\s+)*"
        r"(?:[A-Z][A-Za-z0-9_:]*(?:<[^;=()]+>)?|unsigned\s+long|unsigned\s+int|unsigned|"
        r"long|int|bool|float|double|uint8_t|uint16_t|uint32_t|int8_t|int16_t|"
        r"int32_t|size_t|fract8|accum88|saccum78)(?![A-Za-z0-9_:])"
        r"\s*[*&]?\s*([A-Za-z_]\w*)"
    )
    qualified_assignment = re.compile(
        r"^\s*(?:[A-Za-z_]\w*::)+([A-Za-z_]\w*)\s*(?:\[.*?\])?\s*="
    )
    define_pattern = re.compile(r"^\s*#\s*define\s+([A-Za-z_]\w*)")
    build_flag_pattern = re.compile(r"(?:^|\s)-D\s*([A-Za-z_]\w*)")
    type_declaration_pattern = re.compile(
        r"^\s*(?:struct|class|enum(?:\s+class)?)\s+([A-Za-z_]\w*)"
    )
    enum_value_pattern = re.compile(r"^\s*([A-Z][A-Z0-9_]+)\s*(?:=|,)")
    for line_number, line in enumerate(text.splitlines(), 1):
        code = strip_comments_preserve_layout(line, strip_strings=False)
        names = [match.group(1) for match in type_pattern.finditer(code)]
        assignment = qualified_assignment.match(code)
        if assignment:
            names.append(assignment.group(1))
        macro = define_pattern.match(code)
        if macro:
            names.append(macro.group(1))
        names.extend(match.group(1) for match in build_flag_pattern.finditer(code))
        type_declaration = type_declaration_pattern.match(code)
        if type_declaration:
            names.append(type_declaration.group(1))
        enum_value = enum_value_pattern.match(code)
        if enum_value:
            names.append(enum_value.group(1))
        for name in names:
            location = f"`{source_path}:{line_number}`"
            if location not in found.setdefault(name, []):
                found[name].append(location)
    return {name: tuple(locations) for name, locations in found.items()}


@lru_cache(maxsize=1)
def shared_symbol_index() -> dict[str, tuple[str, ...]]:
    merged: dict[str, list[str]] = {}
    paths: list[Path] = []
    for base in (
        ROOT / "firmware/shared",
        ROOT / "firmware/slave/include",
        ROOT / "firmware/master/include",
    ):
        for suffix in ("*.h", "*.hpp", "*.cpp"):
            paths.extend(base.rglob(suffix))
    paths.extend((ROOT / "platformio.ini", ROOT / "platformio_local.ini"))
    paths = sorted(set(paths))
    for path in paths:
        if not path.exists():
            continue
        relative = path.relative_to(ROOT).as_posix()
        for name, locations in build_symbol_index(
                path.read_text(encoding="utf-8", errors="ignore"), relative).items():
            destination = merged.setdefault(name, [])
            for location in locations:
                if location not in destination:
                    destination.append(location)
    return {name: tuple(locations) for name, locations in merged.items()}


def parameter_definition_summary(
        complete_call: str, source_path: str, source_line: int,
        source_symbols: dict[str, tuple[str, ...]],
        external_symbols: dict[str, tuple[str, ...]] | None = None) -> tuple[str, ...]:
    identifiers = re.findall(r"(?:[A-Za-z_]\w*::)*[A-Za-z_]\w*", complete_call)
    ignored = discover_callable_names() | CONTROL_WORDS | {
        "CRGB", "true", "false", "nullptr", "HIGH", "LOW", "PWM_CHANNEL",
        "U", "UL", "ULL", "L", "LL", "F",
    }
    symbols: list[str] = []
    for identifier in identifiers[1:]:
        leaf = identifier.split("::")[-1]
        if leaf in ignored:
            continue
        if identifier not in symbols:
            symbols.append(identifier)
    if not symbols:
        return (f"inline literals／implicit state; `{source_path}:{source_line}`",)
    shared = shared_symbol_index()
    definitions: list[str] = []
    for symbol in symbols:
        leaf = symbol.split("::")[-1]
        local_locations = [
            location for location in source_symbols.get(leaf, ())
            if int(location.rsplit(":", 1)[1].rstrip("`")) <= source_line
        ]
        external_locations = list((external_symbols or {}).get(leaf, ())[:2])
        locations = local_locations[-1:] or external_locations or list(shared.get(leaf, ())[:2])
        if locations:
            definitions.append(f"`{symbol}` → {', '.join(locations)}")
        else:
            definitions.append(
                f"`{symbol}` → definition not found; usage at `{source_path}:{source_line}`"
            )
    return tuple(definitions)


@lru_cache(maxsize=1)
def load_overrides() -> dict[str, dict[str, str]]:
    if not OVERRIDES.exists():
        return {}
    data = json.loads(OVERRIDES.read_text(encoding="utf-8"))
    return data.get("overrides", {})


def component_description(mode: str, slave: str, target: str, function: str,
                          source_comment: str | None,
                          overrides: dict[str, dict[str, str]]) -> str:
    if source_comment:
        return source_comment
    key = f"{mode}|{slave}|{target}|{function}"
    if key in overrides:
        return overrides[key]["description"]
    return f"UNCONFIRMED COMPONENT — {target}"


def slug(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return normalized or "item"


def make_record_id(project: str, mode: str, source_path: str, line: int,
                   function: str, target: str) -> str:
    digest = hashlib.sha1(f"{source_path}:{line}:{function}:{target}".encode()).hexdigest()[:8]
    return f"{slug(project)}-{slug(mode)}-{line}-{slug(function)}-{digest}"


def scan_cpp_calls(original: str, path: Path, mode: ModeSpec,
                   callable_names: set[str] | None = None,
                   project: str = "pgu",
                   external_symbols: dict[str, tuple[str, ...]] | None = None) -> list[CallRecord]:
    callable_names = callable_names or discover_callable_names()
    sanitized = strip_comments_preserve_layout(original)
    pairs = brace_pairs(sanitized)
    overrides = load_overrides()
    relative_path = path.relative_to(ROOT).as_posix() if path.is_absolute() else path.as_posix()
    source_symbols = build_symbol_index(original, relative_path)
    records: list[CallRecord] = []
    seen_keys: set[tuple[int, str]] = set()
    for match in CALL_RE.finditer(sanitized):
        function = match.group("name")
        if function not in callable_names or function in UTILITY_DENYLIST:
            continue
        opening = sanitized.find("(", match.start(), match.end())
        closing = find_matching(sanitized, opening, "(", ")")
        if closing < 0:
            continue
        source_line = sanitized.count("\n", 0, match.start()) + 1
        key = (source_line, function)
        if key in seen_keys:
            continue
        seen_keys.add(key)
        start = expression_start(original, match.start("name"))
        end = closing + 1
        cursor = end
        while cursor < len(original) and original[cursor].isspace() and original[cursor] != "\n":
            cursor += 1
        if cursor < len(original) and original[cursor] == ";":
            end = cursor + 1
        complete = original[start:end].strip()
        loop = loop_context(original, sanitized, pairs, match.start())
        slave = slave_context(original, sanitized, pairs, match.start())
        target = hardware_target(complete, loop)
        description = component_description(
            mode.name, slave, target, function,
            nearest_component_comment(original, source_line), overrides,
        )
        record = CallRecord(
            record_id=make_record_id(project, mode.name, relative_path, source_line, function, target),
            project=project,
            authority="dev_PGU_V2 — CURRENT STANDARD" if project == "pgu" else project,
            status=mode.status,
            story_mode=mode.name,
            controller_id=f"{mode.controller_set} {mode.controller_id}",
            stage_condition=stage_condition(original, sanitized, pairs, match.start()),
            slave_context=slave,
            hardware_target=target,
            component_description=description,
            function=function,
            complete_call=complete,
            loop_context=loop,
            parameter_groups=parameter_groups(complete),
            parameter_definitions=parameter_definition_summary(
                complete, relative_path, source_line, source_symbols, external_symbols
            ),
            source_path=relative_path,
            source_line=source_line,
        )
        records.append(record)
    return records


def load_pgu_records(root: Path = ROOT, include_non_formal: bool = True) -> list[CallRecord]:
    callable_names = discover_callable_names(root)
    records: list[CallRecord] = []
    modes: Iterable[ModeSpec] = FORMAL_MODES + (NON_FORMAL_MODES if include_non_formal else ())
    for mode in modes:
        path = root / "firmware/shared/src/storymode" / mode.filename
        if not path.exists():
            continue
        records.extend(
            scan_cpp_calls(path.read_text(encoding="utf-8"), path, mode, callable_names, "pgu")
        )
    return sorted(records, key=lambda record: (
        next((index for index, item in enumerate(FORMAL_MODES + NON_FORMAL_MODES)
              if item.name == record.story_mode), 999),
        record.source_line,
        record.function,
    ))


@lru_cache(maxsize=4)
def resolve_git_ref(branch: str, root: Path = ROOT) -> str:
    candidates = (branch,) if branch.startswith("origin/") else (
        branch,
        f"origin/{branch}",
    )
    last_result: subprocess.CompletedProcess[str] | None = None
    for candidate in candidates:
        last_result = subprocess.run(
            ["git", "rev-parse", "--verify", f"{candidate}^{{commit}}"],
            cwd=root,
            check=False,
            text=True,
            capture_output=True,
        )
        if last_result.returncode == 0:
            return candidate
    assert last_result is not None
    raise subprocess.CalledProcessError(
        last_result.returncode,
        last_result.args,
        output=last_result.stdout,
        stderr=last_result.stderr,
    )


def git_show(branch: str, path: str, root: Path = ROOT) -> str:
    resolved_branch = resolve_git_ref(branch, root)
    return subprocess.run(
        ["git", "show", f"{resolved_branch}:{path}"],
        cwd=root,
        check=True,
        text=True,
        capture_output=True,
    ).stdout


def red_astray_active_modes(branch: str = "dev_Red_Astray_Honest") -> tuple[str, ...]:
    controller_path = "firmware/shared/src/storymode/storyModeController.cpp"
    controller = strip_comments_preserve_layout(git_show(branch, controller_path))
    array_match = re.search(r"StoryModeAndNameList\s+storyModes\s*=\s*\{(?P<body>.*?)\};", controller, re.S)
    if not array_match:
        return ()
    return tuple(re.findall(r"\{\s*(storyMode_[A-Za-z0-9_]+)\s*,", array_match.group("body")))


@lru_cache(maxsize=2)
def historical_symbol_index(branch: str = "dev_Red_Astray_Honest") -> dict[str, tuple[str, ...]]:
    merged: dict[str, list[str]] = {}
    paths = (
        "firmware/shared/include/storymode/storyMode_parameter.h",
        "firmware/shared/src/storymode/storyMode_parameter.cpp",
        "firmware/shared/include/globals.h",
        "firmware/shared/src/globals.cpp",
        "firmware/shared/include/patterns/patterns_rgb/weapon.h",
        "firmware/shared/src/patterns/patterns_rgb/weapon.cpp",
    )
    for path in paths:
        try:
            source = git_show(branch, path)
        except subprocess.CalledProcessError:
            continue
        label = f"{branch}:{path}"
        for name, locations in build_symbol_index(source, label).items():
            destination = merged.setdefault(name, [])
            for location in locations:
                if location not in destination:
                    destination.append(location)
    return {name: tuple(locations) for name, locations in merged.items()}


def load_red_astray_active_gun_records(root: Path = ROOT,
                                       branch: str = "dev_Red_Astray_Honest") -> list[CallRecord]:
    records: list[CallRecord] = []
    branch_symbols = historical_symbol_index(branch)
    for mode_name in red_astray_active_modes(branch):
        source_path = f"firmware/shared/src/storymode/{mode_name}.cpp"
        try:
            source = git_show(branch, source_path, root)
        except subprocess.CalledProcessError:
            continue
        mode = ModeSpec(mode_name, Path(source_path).name, "HISTORICAL", "active", "historical active")
        virtual_path = Path(source_path)
        scanned = scan_cpp_calls(
            source, virtual_path, mode, RED_ASTRAY_GUN_FUNCTIONS,
            "red-astray-honest", external_symbols=branch_symbols,
        )
        for record in scanned:
            definitions = tuple(
                definition.replace(
                    f"`{source_path}:", f"`{branch}:{source_path}:"
                )
                for definition in record.parameter_definitions
            )
            records.append(replace(
                record,
                authority="dev_Red_Astray_Honest — HISTORICAL GUN REFERENCE · DO NOT COPY BRIGHTNESS",
                component_description=(
                    record.component_description
                    if not record.component_description.startswith("UNCONFIRMED")
                    else f"UNCONFIRMED HISTORICAL GUN COMPONENT — {record.hardware_target}"
                ),
                parameter_definitions=definitions,
                source_path=f"{branch}:{source_path}",
            ))
    return sorted(records, key=lambda record: (record.story_mode, record.source_line, record.function))


def unknown_project_calls(root: Path = ROOT) -> set[tuple[str, int, str]]:
    """Return likely project calls not covered by callable/utility classification."""
    callable_names = discover_callable_names(root)
    unknown: set[tuple[str, int, str]] = set()
    for mode in FORMAL_MODES:
        path = root / "firmware/shared/src/storymode" / mode.filename
        source = strip_comments_preserve_layout(path.read_text(encoding="utf-8"))
        for match in CALL_RE.finditer(source):
            name = match.group("name")
            if name in callable_names or name in UTILITY_DENYLIST or name in CONTROL_WORDS:
                continue
            if name.startswith(("storyMode_", "reset", "update", "calculate", "get", "set")):
                continue
            call_end = find_matching(source, source.find("(", match.start(), match.end()), "(", ")")
            if call_end < 0:
                continue
            call = source[match.start():call_end + 1]
            if re.search(r"leds_RGB|pcaLed|espMotor|slaveId|PWM_CHANNEL|LED_PIN", call):
                unknown.add((path.relative_to(root).as_posix(), source.count("\n", 0, match.start()) + 1, name))
    return unknown


__all__ = [
    "CallRecord",
    "FORMAL_MODES",
    "ModeSpec",
    "NON_FORMAL_MODES",
    "RED_ASTRAY_GUN_FUNCTIONS",
    "discover_callable_names",
    "load_pgu_records",
    "load_red_astray_active_gun_records",
    "scan_cpp_calls",
    "strip_comments_preserve_layout",
    "unknown_project_calls",
]

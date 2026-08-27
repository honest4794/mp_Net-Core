#!/usr/bin/env python3
"""Generate the project automation effect API catalog from public headers."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[4]
OUTPUT = ROOT / ".codex/skills/project-automation-rules/references/effect_function_catalog.md"
SOURCE_ROOTS = (
    ROOT / "firmware/shared/include/lib/lib_rgb",
    ROOT / "firmware/shared/include/patterns/patterns_rgb",
)
PUBLIC_HEADERS = tuple(
    sorted(path for source_root in SOURCE_ROOTS for path in source_root.glob("*.h"))
) + tuple(
    sorted(
        (ROOT / "firmware/shared/include/patterns/patterns_wled").glob("*.h")
    )
)
MATRIX_HEADER = ROOT / "firmware/shared/include/patterns/patterns_matrix.h"
MANUAL_API_HEADERS = {
    ROOT / "firmware/shared/include/lib/lib_channel.h": {"chValcanGun"},
    ROOT / "firmware/shared/include/patterns/patterns_channel.h": {"chProgressiveFlash"},
}
MATRIX_PUBLIC_EFFECTS = (
    "runPattern",
    "runHoneycombGradient",
    "runDiagonalGradient",
    "runWaveGradient",
    "runScanlineGradient",
    "runGNWireNormalSnake",
    "runGNWireTransAMSnake",
    "runPaletteGradientStream",
    "runControlledGradientStream",
    "runDiagonalComet",
    "runRippleEffect",
    "runWaterRipples",
    "runBlurSinDuet",
    "runOctaveResonance",
    "runFifthCounterpoint",
    "runSympatheticHeartbeat",
    "runStandingWaveResonance",
    "runPhotosynthesisDawn",
    "runSequentialLight",
    "runChevrons",
    "runSequentialChevron",
    "runSquareSpotLight",
)
DECL_RE = re.compile(
    r"^(?!static\b)(?!typedef\b)(?:inline\s+)?[A-Za-z_][A-Za-z0-9_:<>,*& ]+\s+"
    r"([A-Za-z_][A-Za-z0-9_]*)\s*\("
)


def collapse(text: str) -> str:
    return " ".join(text.replace("\n", " ").split())


def collect_declaration(lines: list[str], start: int) -> str:
    declaration = lines[start].strip()
    index = start + 1
    while ";" not in declaration and index < len(lines):
        declaration += " " + lines[index].strip()
        index += 1
    return collapse(declaration.split(";", 1)[0] + ";")


def public_declarations() -> dict[str, list[tuple[Path, str]]]:
    declarations: dict[str, list[tuple[Path, str]]] = defaultdict(list)
    for header in PUBLIC_HEADERS:
        lines = header.read_text(encoding="utf-8").splitlines()
        for index, line in enumerate(lines):
            if line[:1].isspace():
                continue
            match = DECL_RE.match(line)
            if match:
                declarations[match.group(1)].append(
                    (header, collect_declaration(lines, index))
                )

    for header, allowed_names in MANUAL_API_HEADERS.items():
        lines = header.read_text(encoding="utf-8").splitlines()
        for index, line in enumerate(lines):
            match = DECL_RE.match(line)
            if match and match.group(1) in allowed_names:
                declarations[match.group(1)].append(
                    (header, collect_declaration(lines, index))
                )

    matrix_lines = MATRIX_HEADER.read_text(encoding="utf-8").splitlines()
    for name in MATRIX_PUBLIC_EFFECTS:
        for index, line in enumerate(matrix_lines):
            if re.search(rf"\b{re.escape(name)}\s*\(", line):
                declarations[name].append(
                    (MATRIX_HEADER, collect_declaration(matrix_lines, index))
                )
    return declarations


def split_parameters(signature: str) -> list[str]:
    body = signature[signature.find("(") + 1 : signature.rfind(")")].strip()
    if not body or body == "void":
        return []
    parameters: list[str] = []
    current = ""
    depth = 0
    for character in body:
        if character in "(<[{":
            depth += 1
        elif character in ")>]}":
            depth -= 1
        if character == "," and depth == 0:
            parameters.append(current.strip())
            current = ""
        else:
            current += character
    if current.strip():
        parameters.append(current.strip())
    return parameters


def parameter_name(parameter: str, position: int) -> str:
    without_default = parameter.split("=", 1)[0].strip()
    function_pointer = re.search(r"\(\s*\*\s*([A-Za-z_]\w*)\s*\)", without_default)
    if function_pointer:
        return function_pointer.group(1)
    identifiers = re.findall(r"[A-Za-z_]\w*", without_default)
    ignored = {
        "const", "volatile", "unsigned", "signed", "long", "short", "int",
        "bool", "void", "float", "double", "char", "uint8_t", "uint16_t",
        "uint32_t", "int8_t", "int16_t", "int32_t", "size_t", "CRGB",
        "CRGBPalette16", "TProgmemRGBPalette16", "PROGMEM",
    }
    candidates = [identifier for identifier in identifiers if identifier not in ignored]
    return candidates[-1] if candidates else f"argument{position}"


def canonical_call(name: str, signature: str) -> str:
    if name == "SpecificColorPattern":
        return (
            "SpecificColorPattern(leds_RGB4, NUM_LEDS_RGB4,\n"
            "                     storyMode_2_params::specificColor_registry,\n"
            "                     storyMode_2_params::specificColorPatternCount,\n"
            "                     storyMode_2_params::slave1_rgb4_specificColorIndex);"
        )
    if name == "chValcanGun":
        return (
            "chValcanGun(pcaLed[PWM0 * 16 + i], chBeaconFastFlashBrightness,\n"
            "            chBeaconFlashMin, chBeaconFastFlashOn2, flashCount_pwm0[i],\n"
            "            isOnArr_pwm0[i], lastUpdateArr_pwm0[i], chGunBurstRestMs,\n"
            "            chGunBurstCount, chGunFadeOutMs);"
        )
    if name == "chProgressiveFlash":
        return (
            "chProgressiveFlash(pcaLed[PWM0 * 16 + PWM_CHANNEL_3],\n"
            "                   chBrightnessFlashHigh, chBrightnessFlashLow,\n"
            "                   totalDuration, stopSecond);"
        )
    parameters = split_parameters(signature)
    arguments = [parameter_name(parameter, index + 1) for index, parameter in enumerate(parameters)]
    prefix = "matrixPattern." if name in MATRIX_PUBLIC_EFFECTS else ""
    if not arguments:
        return f"{prefix}{name}();"
    joined = ", ".join(arguments)
    return f"{prefix}{name}({joined});"


def parameter_groups(signatures: list[str]) -> str:
    combined = " ".join(signatures).lower()
    groups: list[str] = []
    for terms, label in (
        (("channel",), "channel target"),
        (("led", "num_rgb", "num_led"), "LED target／range"),
        (("color", "palette", "hue", "saturation"), "color／palette"),
        (("brightness", "fade", "intensity", " high", " low"), "brightness／fade"),
        (("interval", "duration", "speed", "time", "bpm", "delay"), "timing／speed"),
        (("state", "lastupdate", "phase", "count", "index"), "state／lifecycle"),
        (("direction", "reverse", "position", "width", "radius", "length"), "geometry／direction"),
    ):
        if any(term in combined for term in terms):
            groups.append(label)
    return "、".join(groups) if groups else "control／configuration"


def find_consumers(name: str) -> list[str]:
    consumers: list[str] = []
    source_roots = (
        ROOT / "firmware/shared/src/storymode",
        ROOT / "firmware/shared/src/recorder",
    )
    pattern = re.compile(rf"\b{re.escape(name)}\s*\(")
    for source_root in source_roots:
        for path in sorted(source_root.rglob("*.cpp")):
            if pattern.search(path.read_text(encoding="utf-8", errors="ignore")):
                consumers.append(path.relative_to(ROOT).as_posix())
    return consumers


def library_label(path: Path) -> str:
    relative = path.relative_to(ROOT).as_posix()
    if "lib/lib_rgb/" in relative:
        return f"lib_rgb/ — `{relative}`"
    if "patterns/patterns_rgb/" in relative:
        return f"patterns_rgb/ — `{relative}`"
    if relative.endswith("patterns_wled.h"):
        return f"patterns_wled — `{relative}`"
    if relative.endswith("lib_channel.h"):
        return f"PCA channel library — `{relative}`"
    if relative.endswith("patterns_channel.h"):
        return f"PCA channel patterns — `{relative}`"
    return f"patterns_matrix — `{relative}`"


def general_component(name: str, sources: list[str]) -> str:
    if name == "chValcanGun":
        return "PCA 火神炮／Vulcan；只有部件功能明確是武器時使用。"
    if name == "chProgressiveFlash":
        return "PCA 散氣、內構、推進或漸進閃；功能需要時可以保持 OFF。"
    if name == "SpecificColorPattern" or name.endswith("SingleLedPattern"):
        return "RGB signal／marker；由 profile namespace 與 sub-pattern 決定逐粒功能。"
    if any("patterns_wled" in source for source in sources):
        return "WLED-derived RGB effect；使用前確認 instance state 與 strip geometry。"
    if any("patterns_matrix" in source for source in sources):
        return "Matrix RGB effect；使用前確認 mapping、width、height 與方向。"
    return "RGB effect／support API；實際部件由 PGU consumer 與接線表決定。"


def render() -> str:
    declarations = public_declarations()
    lines = [
        "# Effect Function Catalog",
        "",
        "> PGU `dev_PGU_V2` 是目前標準。此檔由公開 header 產生；完整參數以 Signature 為準，例子列出全部 argument，不省略。",
        "> `PGU consumers` 只表示目前程式有直接呼叫；`available` 不代表可自行套入 storyMode。",
        "",
        "## SpecificColorPattern signal design",
        "",
        "`RGB4／SpecificColorPattern` 是訊號燈分派器：registry ID／名稱是 profile 合約，sub-function 是可共用的目前實作；Normal／Repair／Develop 必須用各自參數組。ID 1、11、12、13 共用 `BlinkBurstSingleLedPattern`，由 `BlinkTwiceState` 調整閃爍次數、ON、gap、idle、顏色與亮度；不要為只差時序或顏色的 profile 新增重複 pattern。其他常用 sub-pattern 包括 `BreathGreenSingleLedPattern`、`BlinkBlueSingleLedPattern`、`MachineGunSingleLedPattern`、`LongTurnOnSingleLedPattern`、`SolidOnSingleLedPattern`。每燈 state 依實際 `numLeds` 動態配置。",
        "",
    ]
    for name in sorted(declarations):
        entries = declarations[name]
        signatures = list(dict.fromkeys(signature for _, signature in entries))
        sources = list(dict.fromkeys(library_label(path) for path, _ in entries))
        consumers = find_consumers(name)
        if name == "void":
            status = "type alias；不是可直接呼叫的 effect"
        elif consumers:
            status = "CURRENT PGU direct consumer"
        else:
            status = "available API；目前 PGU storyMode 無直接 consumer"
        lines.extend(
            [
                f"<!-- API:{name} -->",
                f"### `{name}`",
                "",
                f"- Library／Source: {'; '.join(sources)}",
                f"- Signature: {' / '.join(f'`{signature}`' for signature in signatures)}",
                f"- General／Component: {general_component(name, sources)}",
                f"- Parameter groups: {parameter_groups(signatures)}",
                "- Complete example call:",
                "",
                "```cpp",
                canonical_call(name, signatures[0]),
                "```",
                "",
                f"- PGU consumers: {', '.join(f'`{consumer}`' for consumer in consumers) if consumers else 'none found'}",
                f"- Consumer status: {status}",
                "- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    OUTPUT.write_text(render(), encoding="utf-8")


if __name__ == "__main__":
    main()

---
name: figma-to-lvgl-touchlcd
description: Port the FastLED Touch LCD ColorPicker UI from preview.html / simulator HTML / Figma MCP design context into LVGL v8 for touch_lcd_controller. Use when working on HTML to Figma to LVGL, Figma MCP handoff, preserving the existing 800x480 scrolling design, or implementing the UI in touch_lcd_5_usb_test without redesigning it.
---

# Figma To LVGL Touch LCD

## Overview

Use this skill to preserve the existing ColorPicker design while translating it into LVGL v8 widgets. The source of truth is the 800x480 scrolling UI shown by `touch_lcd_controller/preview.html`, whose iframe loads `simulator/colorpicker.html`.

## Required Context

- Also use `$fastled-project-guide` and `$html-to-lvgl` for this project.
- Read `.codex/skills/html-to-lvgl/references/lvgl_mapping.md` before planning widgets.
- Read `.codex/skills/html-to-lvgl/references/external_tools.md` before changing MCP/Figma/LVGL tooling.
- For MON UI phase, stay inside `touch_lcd_controller/` unless the user explicitly asks for master/slave firmware changes.

## Workflow

1. Confirm MCP availability:

```bash
codex mcp list
```

Expected useful MCP servers:

- `figma`: official Figma remote MCP at `https://mcp.figma.com/mcp`
- `html-to-lvgl`: repo-local inventory and mapping MCP

2. Treat visual input in this order:

- Figma MCP design context or selected frame link, when available.
- `touch_lcd_controller/preview.html` screenshot at 800x480.
- `simulator/colorpicker.html` / `touch_lcd_controller/data/html/colorpicker.html` DOM inventory.

3. Inventory the HTML before changing LVGL:

```bash
python3 .codex/skills/html-to-lvgl/scripts/html_to_lvgl_inventory.py simulator/colorpicker.html --format md
```

4. Convert design into LVGL zones:

- fixed title / language / theme row
- fixed control / connection row
- fixed horizontal page tabs
- one vertical scroll `contentPanel`
- page-specific builders that rebuild only the active page

5. Map behavior, not CSS:

- pills/buttons -> `lv_btn`
- tabs -> custom `lv_btn` row
- range inputs -> `lv_slider`
- selects -> `lv_dropdown`
- checkbox/chip grids -> clickable LVGL rows/cards
- candy/cyber visual wheels -> bitmap assets plus touch coordinate mapping
- panels/cards -> `lv_obj` with modest border/radius/shadow

## Project Rules

- Do not redesign. The goal is to preserve the `preview.html` design within LVGL constraints.
- Do not paste generated LVGL 9 / LVGL XML code directly into this LVGL v8 project.
- Keep command behavior aligned with `docs/colorpicker/touch_lcd/協議規格_touchLCD_colorpickerUART.md`.
- Use `colorpicker_catalog.h` for pattern, palette, strip, target, and effect lists when possible.
- Avoid expensive CSS equivalents: large blur, many shadows, animation layers, and complex gradients.
- If Chinese UI text changes, run a glyph/missing-character check before claiming completion.
- Do not build master/slave for MON UI-only work. Build `touch_lcd_5_usb_test`.

## Verification

Use the relevant subset:

```bash
python3 touch_lcd_controller/scripts/validate_lvgl_runtime_layout.py
arch -arm64 pio run -d touch_lcd_controller -e touch_lcd_5_usb_test
pio device monitor -d touch_lcd_controller -e touch_lcd_5_usb_test -b 115200
```

If hardware monitor is not run, say so explicitly.

---
name: html-to-lvgl
description: Convert HTML, CSS, web ColorPicker screens, screenshots, or simulator UI references into LVGL implementation plans and ESP32 C++ LVGL skeletons. Use when porting browser UI to Waveshare ESP32-S3 Touch LCD, matching page order/tabs/controls, planning scrollable LVGL screens, or auditing whether HTML controls have LVGL equivalents.
---

# HTML To LVGL

## Purpose

Use this skill to port web UI into LVGL without pretending HTML/CSS can be copied directly. The output should be an LVGL screen plan first, then C++ widgets that match behavior and layout within embedded limits.

## Workflow

1. Identify the source: HTML file, screenshot, Figma export, or current firmware UI.
2. Run the inventory helper when HTML is available:

```bash
python3 .codex/skills/html-to-lvgl/scripts/html_to_lvgl_inventory.py path/to/page.html --format md
```

3. Read `references/lvgl_mapping.md` before writing LVGL code.
4. Read `references/external_tools.md` before installing or recommending Figma/LVGL tooling.
5. Convert layout into LVGL zones:
   - fixed shell/header
   - fixed top tabs
   - one scrollable content viewport
   - page-specific reusable controls
6. Map controls by behavior, not by CSS:
   - button or pill -> `lv_btn`
   - tab row -> custom `lv_btn` row or `lv_tabview` only when it fits
   - range slider -> `lv_slider`
   - select/dropdown -> `lv_dropdown`
   - checkbox grid -> `lv_checkbox`
   - color wheel -> `lv_colorwheel` or an image/canvas when a candy swirl is required
7. Keep the command behavior exact. UI appearance can be approximated; UART/USB commands must match firmware protocol.
8. Verify with both static review and hardware/log feedback:
   - build `touch_lcd_controller`
   - check boot logs
   - test touch navigation, scroll, and command output

## Output Expectations

For planning-only tasks, produce:

- page list and page order
- component inventory
- LVGL widget mapping
- scroll strategy
- data source mapping
- commands emitted by each control

For implementation tasks, produce:

- C++ LVGL helper functions
- page builders with scrollable content
- callback wiring to existing event/transport code
- no unrelated firmware changes

## Embedded Constraints

- Prefer one fixed shell and rebuild only the active content page.
- Do not compress long web pages into one 800x480 screen; use vertical scrolling.
- Avoid web-only effects that are expensive on ESP32-S3. Replace CSS blur, large shadows, and complex gradients with simpler LVGL styles or bitmap assets.
- Use generated image assets only for visuals that LVGL cannot draw well, such as candy swirl color wheels.
- Keep text sizes stable; do not scale with viewport width.

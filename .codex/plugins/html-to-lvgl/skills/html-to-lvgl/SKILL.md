---
name: html-to-lvgl
description: Convert HTML, CSS, web ColorPicker screens, screenshots, or simulator UI references into LVGL implementation plans and ESP32 C++ LVGL skeletons. Use when porting browser UI to Waveshare ESP32-S3 Touch LCD, matching page order/tabs/controls, planning scrollable LVGL screens, or auditing whether HTML controls have LVGL equivalents.
---

# HTML To LVGL

Use this skill with the `html-to-lvgl` MCP server when available.

## Workflow

1. Search for existing MCP/plugins before adding new tooling.
2. Use MCP tool `inventory_html` or script `scripts/html_to_lvgl_inventory.py` when HTML is available.
3. Use MCP tool `mapping_reference` before writing LVGL code.
4. Convert web layout into fixed shell + fixed tabs + scrollable content panel.
5. Map controls by behavior, not CSS.
6. Keep ColorPicker command behavior exact even when visuals are approximated.

## Key Rule

Do not claim HTML/CSS can be directly pasted into LVGL. Treat Figma/LVGL plugin output as a reference unless the project LVGL version matches the generated code.

# External Tool Candidates

Use this file before creating a new local converter. Search/verify current status first, because these projects can change.

## Recommended Chain

For this project, prefer:

```text
HTML source / screenshot
  -> html.to.design or Builder.io Figma import
  -> Figma MCP / TalkToFigma for reading Figma frames
  -> LVGL Editor / XML for style extraction and preview
  -> manual LVGL v8 implementation in touch_lcd_controller
```

## Candidates

| Tool | Role | Notes |
| --- | --- | --- |
| LVGL Editor / LVGL XML | LVGL-native editor, XML, preview, C export | Best official LVGL path. Check LVGL version compatibility before using generated C. |
| LVGL Figma plugin | Extract style information from Figma into LVGL Editor | Useful for colors, sizes, fonts; not a full screen converter. |
| Figma MCP server | Read Figma design context from an agent | Requires Figma access/auth and may have rate limits. |
| TalkToFigma MCP | Agent-to-Figma bridge that can read/modify designs through a Figma plugin | Useful if the user can run Figma Desktop and install the bridge plugin. |
| html.to.design | Import a webpage into editable Figma layers | Good for HTML -> Figma first pass. Usually still needs cleanup. |
| Builder.io HTML to Design | Import website/HTML into Figma/design workflow | Useful for editable Figma reconstruction; not LVGL-specific. |
| html-figma / html-to-figma libraries | DOM -> Figma node experiments | Useful for research; expect manual integration. |
| Lvgl-mcp-esp32 | Visual feedback loop for LVGL code on ESP32/simulator | Useful after LVGL code exists; not an HTML converter. |
| LVGL image/font converters | Asset conversion | Use for candy wheel bitmap, icons, and CJK fonts. |

## Decision Rules

- If the user has Figma Desktop and can install plugins, use Figma MCP or TalkToFigma.
- If the user only has HTML and no Figma access, use local screenshots plus the inventory helper.
- If exact candy visuals matter, convert difficult visuals to LVGL image assets rather than recreating them with many objects.
- If the project stays on LVGL v8, treat LVGL Editor/LVGL XML/LVGL 9 output as reference, not directly pasteable firmware code.
- If a tool claims "automatic HTML to LVGL", verify with a tiny page first before applying it to ColorPicker.


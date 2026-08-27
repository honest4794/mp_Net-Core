# LVGL Mapping Reference

## Core Rule

HTML describes browser layout. LVGL describes a tree of widgets. Port the intent and command behavior, not the CSS implementation.

## Recommended 800x480 Structure

Use this layout for the ESP32-S3 Touch LCD MON UI:

```text
[ fixed title / language / theme row ]
[ fixed target + connection + Enter/Exit row ]
[ fixed page tabs row ]
[ scrollable content viewport ]
```

The content viewport should be the only vertical scrolling region for normal pages.

## Widget Mapping

| HTML / CSS idea | LVGL mapping | Notes |
| --- | --- | --- |
| `<button>` / pill | `lv_btn` + `lv_label` | Use gradient only if cheap enough. |
| link-like tab | `lv_btn` row | Easier than `lv_tabview` for candy UI. |
| `<input type=range>` | `lv_slider` | Value label should be a separate `lv_label`. |
| `<select>` | `lv_dropdown` | Good for pattern/palette choices. |
| checkbox grid | `lv_checkbox` inside flex/grid container | Use scroll when list is long. |
| color input | `lv_colorwheel` | For normal color wheel. |
| candy swirl wheel | image asset or canvas + touch mapping | `lv_colorwheel` cannot recreate the swirl exactly. |
| card | `lv_obj` with rounded border | Avoid card-inside-card unless it is a list item. |
| CSS shadow | LVGL shadow style | Keep blur/spread modest. |
| CSS gradient | LVGL bg gradient | Use simple two-color horizontal/vertical gradient. |
| HTML page scroll | one LVGL scrollable content object | Header and tabs stay fixed. |

## ColorPicker Page Mapping

Keep the same page order as the simulator:

1. 模擬器首頁 / 裝置 WiFi
2. 調色盤 / RGB 測試
3. 效果預覽 / 燈條效果
4. 故事模式

Within RGB 測試:

- strip selection lives in a scrollable section
- mode selection uses three pill buttons: 單一色 / 色盤 / 圖樣
- single color uses color wheel + RGB sliders + brightness slider
- color preview emits the same command behavior as the web ColorPicker

Within 燈條效果:

- each RGB strip is a list item/card
- expanded item shows pattern dropdown and parameter sliders
- collapsed items only show strip name, LED count, effect name

## Command Behavior

Preserve protocol behavior exactly:

- UI widgets call existing event functions where possible.
- Do not invent new UART commands when an existing `LC:*` command covers the behavior.
- If a control affects pattern parameters, separate base pattern command from extended parameter commands.

## LVGL Code Pattern

Use small helpers:

```cpp
static lv_obj_t *makePill(lv_obj_t *parent, const char *text, bool active);
static lv_obj_t *makeCard(lv_obj_t *parent);
static lv_obj_t *makeValueSlider(lv_obj_t *parent, const char *label, int min, int max, int value);
static void rebuildContent(UiPage page);
```

Avoid a direct one-function-per-HTML-node translation. Build meaningful LVGL sections.

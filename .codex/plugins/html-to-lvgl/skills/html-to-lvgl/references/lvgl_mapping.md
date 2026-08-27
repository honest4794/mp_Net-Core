# LVGL Mapping Reference

HTML describes browser layout. LVGL describes a widget tree. Port intent and behavior, not CSS implementation.

## Recommended Screen Structure

```text
[ fixed title / language / theme row ]
[ fixed target + connection + Enter/Exit row ]
[ fixed page tabs row ]
[ scrollable content viewport ]
```

## Widget Mapping

| HTML / CSS idea | LVGL mapping | Notes |
| --- | --- | --- |
| button / pill | `lv_btn` + `lv_label` | Use simple active/inactive styles. |
| tab row | custom `lv_btn` row | Easier than `lv_tabview` for candy UI. |
| range input | `lv_slider` | Add separate value label. |
| select | `lv_dropdown` | Good for pattern/palette choices. |
| checkbox grid | `lv_checkbox` | Put long lists in vertical scroll. |
| color wheel | `lv_colorwheel` | Stable normal version. |
| candy swirl wheel | image asset + touch mapping | Needed for closest visual match. |
| card/panel | `lv_obj` | Rounded border and light fill. |
| CSS shadow/blur | LVGL shadow style | Keep modest for ESP32-S3. |
| page scroll | one `lv_obj` content viewport | Header/tabs stay fixed. |

## ColorPicker Notes

- Keep page order and command behavior aligned with `simulator/colorpicker.html`.
- Use `colorpicker_catalog.h` for pattern/palette lists.
- For LVGL v8, do not paste LVGL 9 / LVGL XML generated code directly.

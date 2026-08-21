/*
 * modrs485_hd.c — mp_rs485_hd: ESP32 原生 RS485 半雙工模式 for machine.UART
 *
 * 目標:
 *   用 ESP-IDF 的 uart_set_mode(UART_MODE_RS485_HALF_DUPLEX) 讓 ESP32 硬體
 *   自動控制 DE 方向腳，Python 端完全不用手動拉 EN、不用 sleep settle、
 *   不用 txdone 輪詢。write() 一 call，硬體在第一個 bit 前自動拉 RTS(DE)、
 *   送完(TX_DONE)自動放低、自動清自己的回波。
 *
 * 用法 (Python):
 *   import rs485_hd
 *   rs485_hd.enable(1, de=7)     # UART1, DE=GPIO7 (RTS)
 *   uart = UART(1, baudrate=9600, tx=Pin(8), rx=Pin(9))
 *   uart.write(...)              # 硬體自動控 DE，全自動
 *
 * 注意:
 *   - 只在 ESP32 系有效（ESP-IDF 才有 RS485 模式）；其他 port 不會編譯本檔
 *     （micropython.cmake 有 ESP_PLATFORM guard），所以不影響 RP2040 等。
 *   - machine.UART 初始化時 flow 參數不要設 rts（本模組會自己設 DE 腳）。
 */

#include <stdio.h>
#include <string.h>

#include "py/mpconfig.h"
#include "py/obj.h"
#include "py/runtime.h"
#include "py/mperrno.h"
#include "py/mphal.h"

#if defined(ESP_PLATFORM)
#include "driver/uart.h"
#include "hal/uart_types.h"
#include "esp_log.h"
#endif

static const char *TAG = "rs485_hd";

// ── rs485_hd.enable(uart_id, de) ──────────────────────────────────────────
// 把 UART 設成 RS485 半雙工模式，DE 腳 = RTS（硬體自動控制）。
static mp_obj_t mp_rs485_hd_enable(size_t n_args, const mp_obj_t *args) {
    mp_int_t uart_id = mp_obj_get_int(args[0]);
    mp_int_t de_pin = -1;
    for (mp_uint_t i = 1; i < n_args; i += 2) {
        if (i + 1 >= n_args) {
            break;
        }
        qstr kw = mp_obj_str_get_qstr(args[i]);
        if (kw == MP_QSTR_de) {
            de_pin = mp_obj_get_int(args[i + 1]);
        }
    }

    #if !defined(ESP_PLATFORM)
    mp_raise_ValueError(MP_ERROR_TEXT("rs485_hd: only ESP32 targets support RS485_HALF_DUPLEX"));
    return mp_const_none;
    #else

    uart_port_t uart_num = (uart_port_t)uart_id;

    // 1) 設成 RS485 半雙工（硬體自動控 RTS = DE）
    esp_err_t err = uart_set_mode(uart_num, UART_MODE_RS485_HALF_DUPLEX);
    if (err != ESP_OK) {
        mp_raise_msg_varg(&mp_type_RuntimeError,
            MP_ERROR_TEXT("rs485_hd: uart_set_mode(%d) failed: %d"), (int)uart_num, (int)err);
    }
    ESP_LOGI(TAG, "UART%d -> RS485_HALF_DUPLEX ok", (int)uart_num);

    // 2) 指定 DE 腳 = RTS。保留現有 TX/RX（UART_PIN_NO_CHANGE），只改 RTS。
    if (de_pin >= 0) {
        err = uart_set_pin(uart_num, UART_PIN_NO_CHANGE, UART_PIN_NO_CHANGE, de_pin, UART_PIN_NO_CHANGE);
        if (err != ESP_OK) {
            mp_raise_msg_varg(&mp_type_RuntimeError,
                MP_ERROR_TEXT("rs485_hd: uart_set_pin(de=%d) failed: %d"), de_pin, (int)err);
        }
        ESP_LOGI(TAG, "DE=GPIO%d (RTS) ok", de_pin);
    }

    // 3) 設 RX 逾時（以 baud 週期為單位）：RS485 模式需要一個「幀結束」判斷，
    //    讓硬體知道何時清掉自己的回波。設成約 1 個 byte 時間（10 bit）。
    uart_set_rx_timeout(uart_num, 10);

    return mp_const_none;
    #endif // ESP_PLATFORM
}
static MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(mp_rs485_hd_enable_obj, 1, 6, mp_rs485_hd_enable);

// ── rs485_hd.disable(uart_id) ──────────────────────────────────────────────
// 恢復正常 UART 模式。
static mp_obj_t mp_rs485_hd_disable(mp_obj_t uart_id_in) {
    #if !defined(ESP_PLATFORM)
    mp_raise_ValueError(MP_ERROR_TEXT("rs485_hd: only ESP32 targets"));
    return mp_const_none;
    #else
    uart_port_t uart_num = (uart_port_t)mp_obj_get_int(uart_id_in);
    esp_err_t err = uart_set_mode(uart_num, UART_MODE_UART);
    if (err != ESP_OK) {
        mp_raise_msg_varg(&mp_type_RuntimeError,
            MP_ERROR_TEXT("rs485_hd: uart_set_mode(UART) failed: %d"), (int)err);
    }
    return mp_const_none;
    #endif
}
static MP_DEFINE_CONST_FUN_OBJ_1(mp_rs485_hd_disable_obj, mp_rs485_hd_disable);

// ── 模組方法表 ─────────────────────────────────────────────────────────────
static const mp_rom_map_elem_t mp_module_rs485_hd_globals_table[] = {
    { MP_ROM_QSTR(MP_QSTR_enable),  MP_ROM_PTR(&mp_rs485_hd_enable_obj) },
    { MP_ROM_QSTR(MP_QSTR_disable), MP_ROM_PTR(&mp_rs485_hd_disable_obj) },
};
static MP_DEFINE_CONST_DICT(mp_module_rs485_hd_globals, mp_module_rs485_hd_globals_table);

const mp_obj_module_t mp_module_rs485_hd = {
    .base = { &mp_type_module },
    .globals = (mp_obj_dict_t *)&mp_module_rs485_hd_globals,
};

MP_REGISTER_MODULE(MP_QSTR_rs485_hd, mp_module_rs485_hd);

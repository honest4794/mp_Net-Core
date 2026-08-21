# micropython.cmake — mp_rs485_hd: ESP-IDF native RS485 half-duplex for machine.UART
# 讓 machine.UART 能用 RS485 半雙工模式（硬體自動控 DE），不動 MicroPython 核心。
#
# 掛載（mp_Make-Tools 的 exmod.list 或 USER_C_MODULES）：
#   /ext_mod/mp_rs485_hd/micropython.cmake

add_library(usermod_mp_rs485_hd INTERFACE)

set(INCLUDES
    ${CMAKE_CURRENT_LIST_DIR}
)

set(SOURCES
    ${CMAKE_CURRENT_LIST_DIR}/modrs485_hd.c
)

if(ESP_PLATFORM)
    # ESP-IDF uart driver include path (esp_driver_uart) + hal uart_types
    idf_component_get_property(uart_includes esp_driver_uart INCLUDE_DIRS)
    idf_component_get_property(uart_dir esp_driver_uart COMPONENT_DIR)
    if(uart_includes)
        list(TRANSFORM uart_includes PREPEND ${uart_dir}/)
        list(APPEND INCLUDES ${uart_includes})
    endif()
    idf_component_get_property(hal_includes hal INCLUDE_DIRS)
    idf_component_get_property(hal_dir hal COMPONENT_DIR)
    if(hal_includes)
        list(TRANSFORM hal_includes PREPEND ${hal_dir}/)
        list(APPEND INCLUDES ${hal_includes})
    endif()
endif(ESP_PLATFORM)

target_sources(usermod_mp_rs485_hd INTERFACE ${SOURCES})
target_include_directories(usermod_mp_rs485_hd INTERFACE ${INCLUDES})
target_link_libraries(usermod INTERFACE usermod_mp_rs485_hd)

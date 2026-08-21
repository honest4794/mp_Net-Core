# micropython.mk — mp_rs485_hd build rules (legacy make build system)
MOD_DIR := $(USERMOD_DIR)

CFLAGS_USERMOD += -I$(MOD_DIR)
SRC_USERMOD_C += $(MOD_DIR)/modrs485_hd.c

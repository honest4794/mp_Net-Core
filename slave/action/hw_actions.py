from lib.sys_bus import bus
from lib.hw_manager import HW


def _pin_by_id(hw_id):
    plist = bus.get_service("pin_list")
    if plist and 0 <= hw_id < len(plist):
        return plist[hw_id]
    return None


def _pin_label(hw_id):
    cfg = bus.shared.get("PIN") or {}
    lst = cfg.get("list") or []
    if 0 <= hw_id < len(lst):
        return lst[hw_id].get("label", "?")
    return "?"


def on_hw_ctl(ctx, args):
    hw_type = int(args.get("type", 0) or 0)
    hw_id   = int(args.get("id", 0) or 0)
    value   = int(args.get("value", 0) or 0)
    label   = args.get("label") or ""

    # ── VBTN: 虛擬按鈕 ──
    if hw_type == HW.VBTN:
        HW.set(HW.VBTN, hw_id, value)
        # 專用高速旗標，供 action_task_1 直接讀取
        if hw_id == 1:
            bus.shared["_vbtn1_event"] = value
        print("[HW] vbtn {}={}".format(hw_id, value))
        return

    # ── PIN: 實體 GPIO ──
    if hw_type == HW.PIN:
        try:
            p = _pin_by_id(hw_id)
            if p is not None:
                p.value(value)
                lbl = _pin_label(hw_id)
                print("[HW] {}={}".format(lbl, value))
            else:
                print("[HW] pin id {} out of range".format(hw_id))
        except Exception as e:
            print("[HW] pin err: {}".format(e))
        return

    # ── PWM ──
    if hw_type == HW.PWM:
        pwm_list = bus.get_service("pwm_list")
        if not pwm_list or hw_id >= len(pwm_list):
            print("[HW] pwm idx {} out of range".format(hw_id))
            return
        try:
            pwm_list[hw_id].duty_u16(value)
            print("[HW] pwm {} duty={}".format(hw_id, value))
        except Exception as e:
            print("[HW] pwm err: {}".format(e))
        return

    # ── 舊式兼容：type 無意義時依 label 分派 ──
    if label:
        print("[HW] {}={}".format(label, value))
        bus.shared["hw_events"] = {"label": label, "value": value}
        return

    print("[HW] unknown type=0x{:02X}".format(hw_type))


def on_hw_query(ctx, args):
    hw_type = int(args.get("type", 0) or 0)
    hw_id   = int(args.get("id", 0) or 0)

    if hw_type == HW.PIN:
        from machine import Pin
        try:
            p = Pin(hw_id, Pin.IN)
            val = p.value()
            print("[HW] pin {} = {}".format(hw_id, val))
        except Exception as e:
            print("[HW] pin query err: {}".format(e))

    elif hw_type == HW.PWM:
        pwm_list = bus.get_service("pwm_list")
        if not pwm_list or hw_id >= len(pwm_list):
            print("[HW] pwm idx {} out of range".format(hw_id))
            return
        try:
            duty = pwm_list[hw_id].duty_u16()
            print("[HW] pwm {} duty={}".format(hw_id, duty))
        except Exception as e:
            print("[HW] pwm query err: {}".format(e))


def register(app):
    app.disp.on(0x1401, on_hw_ctl)
    app.disp.on(0x1402, on_hw_query)
    print("[HW] Hardware actions registered")

# Core0.py
# Worker/Engine（極速）模式 — Core 0 控制核
#
# 核心理念：簡單、快速、專注完成任務（極速模式），不追求最大靈活性。
# 職責：統一指令線路（網絡 + 實體線）收發 + dispatch。
#   - 直接初始化網絡 bus / UART bus / decode loop / log loop
#   - 所有流程直接寫在 Core0，不依賴 tasks / 額外 worker lib
# 指令（play / pause / 切源）由 action 層寫入 bus.shared，Core1 播放引擎讀取。
#
# 由 main.py 在 worker_engine 模式下呼叫 worker_start()（阻塞於本核心）。

import time
import machine
import ubinascii

from app import App
from lib.sys_bus import bus
from lib.log_service import get_log, _viper_read_i32


def _log_info(msg):
    if bus.shared.get("verbose_print"):
        print(msg)
    else:
        get_log().info(msg)


def _ensure_bus_sources():
    from lib.bus_sources import BusSources

    sources = bus.get_service("bus_sources")
    if not sources:
        sources = BusSources()
        bus.register_service("bus_sources", sources)
    return sources


def _setup_network_runtime(app):
    from lib.net_bus import NetBus
    from lib.network_manager import NetworkManager
    from action.sys_actions import on_connect_request

    st = {
        "app": app,
        "nm": bus.get_service("network_manager"),
        "ctrl_bus": None,
        "discovery_bus": None,
        "tried_config_connect": False,
        "s": {"f_local": None, "last_hb": time.ticks_ms()},
        "hub": None,
        "now_bus": None,
        "last_discv_poll": 0,
        "connect_wrapper": None,
    }

    _log_info("🌐 [Network] 開始初始化網路...")

    if not st["nm"]:
        _log_info("🌐 [Network] 建立 NetworkManager...")
        st["nm"] = NetworkManager(bus)
        st["nm"].init_from_config()
        bus.register_service("network_manager", st["nm"])

        for name, iface in st["nm"].interfaces.items():
            ip = "?"
            try:
                cfg = iface.ifconfig()
                ip = cfg[0]
            except Exception:
                pass
            _log_info("🌐 {} 就緒 | IP: {}".format(name.upper(), ip))

        if st["nm"].interfaces:
            _log_info("🌐 [Network] 網路連線完成")
        else:
            get_log().warn("🌐 [Network] 沒有可用網路介面")

    esp_cfg = bus.shared.get("Network", {}).get("ESP_now", {})
    if esp_cfg.get("enable", 0):
        try:
            from lib.now_bus import NowBus

            wifi_cfg = bus.shared.get("Network", {}).get("wifi", {})
            wifi_enable = wifi_cfg.get("enable", 0)
            esp_ch = esp_cfg.get("channel", 1)
            now = NowBus(label="NOW-Bus")

            if wifi_enable:
                ok = now.init()
                if not ok:
                    get_log().warn("ESP-NOW: WiFi radio not ready, fallback ch={}".format(esp_ch))
                    ok = now.init(channel=esp_ch)
            else:
                _log_info("ESP-NOW: standalone mode, ch={}".format(esp_ch))
                ok = now.init(channel=esp_ch)

            if ok:
                st["now_bus"] = now
                bus.register_service("NowBus", now)
                _log_info("ESP-NOW ready, ch={}".format(now._channel()))
            else:
                get_log().warn("ESP-NOW init failed")
        except Exception as e:
            get_log().error("ESP-NOW init error: {}".format(e))

    bus_sys = bus.shared["System"]
    st["ctrl_bus"] = NetBus(NetBus.TYPE_WS, label="CTRL-WS")
    st["discovery_bus"] = NetBus(NetBus.TYPE_UDP, label="UDP-DISCV")
    st["discovery_bus"].connect(None, bus_sys["discovery_port"])
    bus.register_service("net_bus_ctrl", st["ctrl_bus"])
    bus.register_service("net_bus_discovery", st["discovery_bus"])

    sources = _ensure_bus_sources()
    sources.add(st["discovery_bus"])
    sources.add(st["ctrl_bus"])
    if st["now_bus"]:
        sources.add(st["now_bus"])

    st["hub"] = bus.get_service("pixel_stream")
    st["connect_wrapper"] = lambda url: on_connect_request(st["ctrl_bus"], url)

    _log_info("🚀 [Network] Data Router Active")
    return st


def _poll_network_runtime(st):
    if not st:
        return

    from action.stream_actions import handle_supply_chain

    now = time.ticks_ms()
    ctrl_bus = st["ctrl_bus"]
    nm = st["nm"]
    bus.shared["app_connected"] = ctrl_bus.connected or bus.shared.get("manual_keep_alive", False)

    if st["now_bus"]:
        st["now_bus"].poll()

    network_ok = nm.check_network()
    if network_ok:
        bus_sys = bus.shared["System"]
        if not st["tried_config_connect"] and not ctrl_bus.connected:
            st["tried_config_connect"] = True
            m_ip = bus_sys.get("master_IP", "")
            m_port = bus_sys.get("master_port", 0)
            if m_ip and m_port:
                _log_info("🔄 Auto-Connecting to stored Master: {}:{}".format(m_ip, m_port))
                full_url = "ws://{}:{}/ws/{}".format(m_ip, m_port, bus.slave_id)
                if st["connect_wrapper"](full_url):
                    _log_info("✅ Auto-Connect Success!")
                else:
                    get_log().warn("⚠️ Auto-Connect Failed, waiting for discovery...")

        ctx_extra = {
            "app": st["app"],
            "ctrl_bus": ctrl_bus,
            "on_connect": st["connect_wrapper"],
        }
        if ctrl_bus.connected:
            try:
                ctrl_bus.poll()
            except Exception as e:
                get_log().error("Ctrl Bus Poll Error: {}".format(e))
        else:
            if time.ticks_diff(now, st["last_discv_poll"]) > 250:
                st["last_discv_poll"] = now
                try:
                    st["discovery_bus"].poll(**ctx_extra)
                except Exception as e:
                    get_log().error("Discovery Poll Error: {}".format(e))

    worker_ctx = {"app": st["app"], "send": ctrl_bus.write}
    if st["hub"] is not None:
        handle_supply_chain(st["hub"], st["s"], worker_ctx)


def _stop_network_runtime(st):
    if not st:
        return
    if st.get("ctrl_bus"):
        st["ctrl_bus"].disconnect()
    if st.get("now_bus"):
        st["now_bus"].deinit()
        st["now_bus"] = None


def _get_selected_circuit_sources():
    cfg = bus.shared.get("CircuitDecode", {}) or {}
    if not int(cfg.get("enable", 0) or 0):
        return None
    selected = set()

    lst = cfg.get("list", None)
    if lst is None:
        lst = cfg.get("sources", []) or []
    for it in lst or []:
        if isinstance(it, str):
            selected.add(it)
            continue
        if not isinstance(it, dict):
            continue
        gpio = it.get("GPIO", {}) or {}
        if "uart" in gpio:
            try:
                selected.add(("uart", int(gpio.get("uart"))))
            except Exception:
                pass
        if "spi" in gpio:
            try:
                selected.add(("spi", int(gpio.get("spi"))))
            except Exception:
                pass
        if "i2c" in gpio:
            try:
                selected.add(("i2c", int(gpio.get("i2c"))))
            except Exception:
                pass
        if "i2c_target" in gpio:
            try:
                selected.add(("i2c_target", int(gpio.get("i2c_target"))))
            except Exception:
                pass
        if "can" in gpio:
            try:
                selected.add(("can", int(gpio.get("can"))))
            except Exception:
                pass
        svc = it.get("service", None)
        if svc:
            selected.add(svc)
    return selected


def _build_circuit_ctx(uid, baud, tx, rx, item):
    ctx = {
        "transport": "circuit",
        "uart_id": uid,
        "uart_baudrate": baud,
        "uart_tx": tx if tx is not None else -1,
        "uart_rx": rx if rx is not None else -1,
    }
    link = item.get("link", None)
    if link:
        ctx["link"] = link
    return ctx


def _setup_circuit_runtime():
    from lib.circuit_bus import CircuitBus

    st = {"buses": [], "ctx_by_bus_id": {}}
    selected = _get_selected_circuit_sources()

    uart_cfg = bus.shared.get("UART", {}) or {}
    if not int(uart_cfg.get("enable", 0) or 0):
        bus.register_service("circuit_bus_all_list", [])
        bus.register_service("circuit_bus_all_by_id", {})
        bus.register_service("circuit_bus_list", [])
        bus.register_service("circuit_bus_by_id", {})
        return st

    all_buses = []
    all_by_id = {}
    buses = []
    by_id = {}
    lst = uart_cfg.get("list", []) or []
    for idx, item in enumerate(lst):
        uid = int(item.get("id", 1) or 1)
        baud = int(item.get("baudrate", 115200) or 115200)
        gpio = item.get("GPIO", {}) or {}
        tx = gpio.get("tx", None)
        rx = gpio.get("rx", None)

        uart = None
        try:
            uart = machine.UART(
                uid,
                baudrate=baud,
                bits=8,
                parity=None,
                stop=1,
                tx=machine.Pin(tx) if tx is not None else None,
                rx=machine.Pin(rx) if rx is not None else None,
                timeout=0,
                timeout_char=0,
            )
        except TypeError:
            uart = machine.UART(
                uid,
                baudrate=baud,
                bits=8,
                parity=None,
                stop=1,
                tx=tx,
                rx=rx,
                timeout=0,
                timeout_char=0,
            )
        except Exception as e:
            get_log().error("❌ [Circuit] UART init failed (id={}): {}".format(uid, e))
            continue

        label = "CIRCUIT-UART{}".format(uid)
        cb = CircuitBus(uart, label=label)
        ctx_extra = _build_circuit_ctx(uid, baud, tx, rx, item)
        svc = "circuit_bus_uart{}".format(uid)
        all_buses.append(cb)
        all_by_id[uid] = cb
        bus.register_service(svc, cb)

        if selected is None or ("uart", idx) in selected or svc in selected:
            buses.append(cb)
            by_id[uid] = cb
            st["ctx_by_bus_id"][id(cb)] = ctx_extra

    st["buses"] = buses
    bus.register_service("circuit_bus_all_list", all_buses)
    bus.register_service("circuit_bus_all_by_id", all_by_id)
    bus.register_service("circuit_bus_list", buses)
    bus.register_service("circuit_bus_by_id", by_id)

    sources = _ensure_bus_sources()
    for cb in buses:
        sources.add(cb)

    if buses:
        _log_info("🔌 [Circuit] {} circuit bus(es) online".format(len(buses)))
    return st


def _poll_circuit_runtime(st):
    if not st:
        return
    for b in st.get("buses", ()):
        ctx_extra = st["ctx_by_bus_id"].get(id(b), None)
        if ctx_extra is not None:
            b._decode_ctx = ctx_extra
        b.poll()


def _stop_circuit_runtime(st):
    if not st:
        return
    st["buses"] = []
    st["ctx_by_bus_id"] = {}


def _setup_decode_runtime(app):
    buf_cfg = bus.shared.get("Buffer") or {}
    max_slots = int(buf_cfg.get("decode_budget_slots", 32) or 0)
    if max_slots <= 0:
        max_slots = 1
    return {
        "app": app,
        "buses": [],
        "parsers": {},
        "read_buf": None,
        "src_ts": 0,
        "max_slots": max_slots,
    }


def _refresh_decode_sources(st):
    sources = bus.get_service("bus_sources")
    if sources:
        st["buses"] = list(sources.list() or [])
        return

    buses = []
    ctrl = bus.get_service("net_bus_ctrl")
    discv = bus.get_service("net_bus_discovery")
    if ctrl:
        buses.append(ctrl)
    if discv:
        buses.append(discv)
    circuit_list = bus.get_service("circuit_bus_list")
    if circuit_list:
        for cb in circuit_list:
            buses.append(cb)
    st["buses"] = buses


def _ensure_decode_buf(st, size):
    buf = st.get("read_buf")
    if buf is None or len(buf) < size:
        st["read_buf"] = bytearray(size)


def _poll_decode_runtime(st):
    if not st:
        return

    now = time.ticks_ms()
    if time.ticks_diff(now, st["src_ts"]) > 100:
        st["src_ts"] = now
        _refresh_decode_sources(st)
    if not st["buses"]:
        return

    used = 0
    for b in st["buses"]:
        hub = getattr(b, "rx_hub", None)
        if hub is None:
            continue
        _ensure_decode_buf(st, hub.size)
        parser = st["parsers"].get(id(b))
        if parser is None:
            parser = st["app"].create_parser()
            st["parsers"][id(b)] = parser
        ctx_extra = getattr(b, "_decode_ctx", None) or {}
        read_buf = st["read_buf"]
        mv = memoryview(read_buf)
        while True:
            if used >= st["max_slots"]:
                return
            if not hub.read_into(read_buf):
                break
            ln = read_buf[0] | (read_buf[1] << 8)
            if ln <= 0:
                continue
            data = mv[2:2 + ln]
            st["app"].handle_stream(
                parser,
                data,
                transport_name=getattr(b, "label", "Bus"),
                send_func=b.write,
                **ctx_extra
            )
            used += 1


def _stop_decode_runtime(st):
    if not st:
        return
    st["buses"] = []
    st["parsers"] = {}
    st["read_buf"] = None


def _setup_log_runtime():
    bus.shared["log_task_ready"] = True
    st = {
        "cpu0": False,
        "cpu1": False,
        "core_buf": None,
        "rows": (),
        "others": (),
        "last_print_ms": 0,
    }

    names = bus.shared.get("log_subscribe", [])
    if not isinstance(names, (list, tuple)) and names != "__list__":
        names = []
    log = get_log()

    if names == "__list__":
        all_names = log.get_metric_names()
        task_bufs = bus.shared.get("_task_bufs", {})
        custom = sorted(
            n for n in all_names
            if not (str(n).startswith("core0_") or str(n).startswith("core1_"))
        )
        tnames = sorted(task_bufs)
        print("[LOG] -- copy-paste subscribe list ----------------------------------")
        print("subscribe = [")
        print('    "cpu0",')
        print('    "cpu1",')
        for n in custom:
            print('    "' + n + '",')
        for tn in tnames:
            print('    "' + tn + '",')
        print("]")
        return st

    task_bufs = bus.shared.get("_task_bufs", {})
    core_buf = bus.shared.get("_core_buf")
    if isinstance(names, (list, tuple)):
        for n in names:
            if n == "cpu0":
                st["cpu0"] = True
            elif n == "cpu1":
                st["cpu1"] = True
    st["core_buf"] = core_buf

    sub_tasks = set()
    sub_names = []
    for n in names:
        if n == "cpu0" or n == "cpu1":
            continue
        if n in task_bufs:
            sub_tasks.add(n)
        else:
            sub_names.append(n)

    if sub_tasks:
        st["rows"] = tuple((tn, b) for tn, b in sorted(task_bufs.items()) if tn in sub_tasks)
    if sub_names:
        slots = log.subscribe(sub_names)
        st["others"] = tuple((n, b, o) for n, b, o in slots)
    return st


def _poll_log_runtime(st):
    if not st:
        return

    rows = st["rows"]
    others = st["others"]
    if not rows and not others and not st["cpu0"] and not st["cpu1"]:
        return

    now = time.ticks_ms()
    interval = int(bus.shared.get("log_print_interval_ms", 1000) or 1000)
    if interval <= 0:
        interval = 1000
    if time.ticks_diff(now, st["last_print_ms"]) < interval:
        return
    st["last_print_ms"] = now

    out = []
    for task_name, buf in rows:
        avg = _viper_read_i32(buf, 0)
        mx = _viper_read_i32(buf, 4)
        cnt = _viper_read_i32(buf, 8)
        touch_v = _viper_read_i32(buf, 12)
        succ_v = _viper_read_i32(buf, 16)
        if avg <= 0 and touch_v <= 0 and succ_v <= 0:
            continue
        out.append(
            "Task[" + task_name + "] avg=" + str(avg) + "us max=" + str(mx) +
            "us n=" + str(cnt) + " t=" + str(touch_v) + " s=" + str(succ_v)
        )

    core_buf = st["core_buf"]
    if core_buf:
        if st["cpu0"]:
            loops = _viper_read_i32(core_buf, 0)
            out.append("CPU0 loops=" + str(loops))
        if st["cpu1"]:
            loops = _viper_read_i32(core_buf, 12)
            out.append("CPU1 loops=" + str(loops))

    for name, buf, off in others:
        v = _viper_read_i32(buf, off)
        if v > 0:
            out.append(str(name) + "=" + str(v))

    if out:
        print("[IMMEDIATE]")
        for line in out:
            print("  - " + line)
        get_log().flush()


def worker_start():
    """Core 0 入口 — 極速控制核主迴圈（阻塞）"""
    log = get_log()

    _log_info("⚡ [Core0] Worker/Engine Mode — control core")

    bus.slave_id = ubinascii.hexlify(machine.unique_id()).decode().upper()
    bus.shared["engine_run"] = True
    bus.shared["spi_busy"] = False
    bus.register_service("log", log)

    sys_cfg = bus.shared.get("System", {})
    interval = sys_cfg.get("log_interval_ms")
    if interval is None:
        log_cfg = sys_cfg.get("Log") or bus.shared.get("Log", {})
        interval = log_cfg.get("print_interval_ms", 1000)
    bus.shared["log_print"] = True
    bus.shared["log_print_interval_ms"] = int(interval or 1000)
    bus.shared["log_print_levels"] = ["info", "warn", "error", "immediate"]
    bus.shared["log_subscribe"] = []

    app = App()
    state = {
        "app": app,
        "network": _setup_network_runtime(app),
        "circuit": _setup_circuit_runtime(),
        "decode": _setup_decode_runtime(app),
        "log": _setup_log_runtime(),
    }

    _log_info("⚡ [Core0] Command line online (net + circuit): {}".format(bus.slave_id))

    sys_cfg2 = bus.shared.get("System", {})
    _tw = int(sys_cfg2.get("tft_width", sys_cfg2.get("player_width", 240)))
    _th = int(sys_cfg2.get("tft_height", sys_cfg2.get("player_height", 320)))
    _tbpp = int(sys_cfg2.get("player_bpp", 2))
    _tfs = _tw * _th * _tbpp

    from lib.buffer_hub import AtomicStreamHub
    _hub = AtomicStreamHub(_tfs, num_buffers=4)
    bus.register_service("frame_hub", _hub)
    _log_info("[Core0] frame_hub {}B x4".format(_tfs))

    if bus.shared.get("jpeg_test_hub"):
        if _tbpp == 3:
            _wb = bytearray(b"\xff\xff\xff" * (_tfs // 3))
        else:
            _wb = bytearray(b"\xff\xff" * (_tfs // 2))
        if len(_wb) < _tfs:
            _wb += b"\xff" * (_tfs - len(_wb))
        _bb = bytearray(_tfs)
        _src = (_wb, _bb, _wb, _bb)
        for i in range(4):
            w = _hub.get_write_view()
            w[:_tfs] = _src[i]
            _hub.commit()
        _log_info("[Core0] test_hub 4 slots pre-filled")

    try:
        while bus.shared.get("engine_run", True):
            try:
                if bus.shared.get("jpeg_test_hub"):
                    while True:
                        w = _hub.get_write_view()
                        if w is None:
                            break
                        _hub.commit()
                    time.sleep_ms(0)

                _poll_log_runtime(state["log"])
                _poll_network_runtime(state["network"])
                _poll_circuit_runtime(state["circuit"])
                _poll_decode_runtime(state["decode"])
            except Exception as e:
                if bus.shared.get("verbose_print"):
                    print("[Core0] loop err: {}".format(e))
                else:
                    get_log().error("[Core0] loop err: {}".format(e))
            time.sleep_ms(0)
    except KeyboardInterrupt:
        if bus.shared.get("verbose_print"):
            print("[Core0] User stop requested.")
    finally:
        bus.shared["engine_run"] = False
        _stop_network_runtime(state["network"])
        _stop_circuit_runtime(state["circuit"])
        _stop_decode_runtime(state["decode"])
        _log_info("[Core0] Control core stopped.")

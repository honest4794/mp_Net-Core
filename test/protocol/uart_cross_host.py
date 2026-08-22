# -*- coding: utf-8 -*-
"""UART 交叉直連能力測試 — host orchestrator（主機端）

用法（需 pyserial + mpremote，例如 ESP-IDF venv）：
    python -B uart_cross_host.py
    python -B uart_cross_host.py --bauds 9600,115200,921600
    python -B uart_cross_host.py --only 115200

流程：對每個 baud——
  1) REFLECT 板 (1401) 背景執行 run_reflect(baud, budget)（即時 echo）
  2) SENDER 板 (1201) 執行 run_sender(baud)（pingpong / burst / throughput）
  3) 等 SENDER 完成，join REFLECT 至 budget 結束，進下一個 baud

接線：GPIO9(TX) 交叉接對端 GPIO8(RX)，兩板 GND 共地。
"""

import os
import subprocess
import sys
import time
import threading

PORT_SENDER = '/dev/cu.usbmodem1201'
PORT_REFLECT = '/dev/cu.usbmodem1401'
AGENT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uart_cross_bench.py')
MPREMOTE = [sys.executable, '-m', 'mpremote']

BAUDS = (9600, 57600, 115200, 230400, 460800, 921600)
REFLECT_LEAD_S = 2.0          # 讓 REFLECT 先開好 UART 再讓 SENDER 開始


def _budget_s(baud):
    # 保守給大；REFLECT 收到最後一筆資料 2s 無新資料就自停，不會空等滿 budget
    if baud <= 9600:
        return 35.0
    if baud <= 57600:
        return 25.0
    return 18.0


def _exec(port, code):
    cp = subprocess.run(MPREMOTE + ['connect', port, 'exec', code],
                        capture_output=True, text=True, timeout=180)
    out = cp.stdout or ''
    if cp.returncode != 0:
        out += '\n[stderr] ' + (cp.stderr or '')
    return out


def _run_baud(baud):
    agent = open(AGENT_PATH, encoding='utf-8').read()
    budget = _budget_s(baud)
    print('--- baud={} budget={:.1f}s ---'.format(baud, budget), flush=True)

    result = {}

    def reflex_worker():
        try:
            result['reflect'] = _exec(PORT_REFLECT,
                                      agent + '\nrun_reflect(%d, %.1f)' % (baud, budget))
        except Exception as e:
            result['reflect_err'] = repr(e)

    t = threading.Thread(target=reflex_worker)
    t.start()
    time.sleep(REFLECT_LEAD_S)

    try:
        out = _exec(PORT_SENDER, agent + '\nrun_sender(%d)' % baud)
    except Exception as e:
        out = 'SENDER ERROR: {!r}'.format(e)
    print(out, flush=True)

    t.join()
    if 'reflect' in result:
        print(result['reflect'], flush=True)
    elif 'reflect_err' in result:
        print('REFLECT ERROR:', result['reflect_err'], flush=True)


def _check_ports():
    for p in (PORT_SENDER, PORT_REFLECT):
        try:
            s = _port_open(p)
            s.close()
        except Exception as e:
            print('PORT {} 無法開啟: {!r}\n  （若被 Thonny/其他程式佔用，請先關閉該連線）'.format(p, e))
            return False
    return True


def _port_open(p):
    import serial
    s = serial.Serial(p, 115200, timeout=0.2)
    return s


def main():
    bauds = list(BAUDS)
    args = sys.argv[1:]
    for i, a in enumerate(args):
        if a == '--bauds' and i + 1 < len(args):
            bauds = [int(x) for x in args[i + 1].split(',')]
        elif a == '--only' and i + 1 < len(args):
            bauds = [int(args[i + 1])]
    if not _check_ports():
        sys.exit(1)
    print('UART 交叉直連測試  sender={}  reflect={}'.format(PORT_SENDER, PORT_REFLECT))
    print('bauds={}  agent={}'.format(bauds, AGENT_PATH))
    t0 = time.time()
    for b in bauds:
        _run_baud(b)
    print('=' * 60)
    print('ALL DONE in {:.0f}s'.format(time.time() - t0))


if __name__ == '__main__':
    main()

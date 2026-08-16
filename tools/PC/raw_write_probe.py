"""Windows raw sector write test — 寫一個 sector 即刻讀返"""
import ctypes, os

S = 512

def main():
    print("SD Raw Write Test")
    print("=" * 40)

    # list USB disks
    import subprocess as SP
    r = SP.run(["powershell", "-NoProfile", "-Command",
        'Get-Disk | Where-Object { $_.BusType -eq "USB" } | ForEach-Object { $n=$_.Number; $s=$_.Size; "$n,$s" }'],
        capture_output=True, text=True)
    disks = []
    for line in r.stdout.strip().split("\n"):
        p = line.strip().split(",")
        if len(p) >= 2:
            disks.append((int(p[0]), int(p[1])))
    if not disks:
        print("No USB disk found")
        return
    for i, (n, sz) in enumerate(disks):
        print(" {}. PhysicalDrive{} ({:.1f}GB)".format(i+1, n, sz/1073741824))
    
    sel = input("Select: ").strip()
    if not sel: return
    dev = "PhysicalDrive" + str(disks[int(sel)-1][0])
    print("\nUsing:", dev)

    # Open disk
    k = ctypes.windll.kernel32
    GENERIC_READ = 0x80000000
    GENERIC_WRITE = 0x40000000
    h = k.CreateFileW(
        "\\\\.\\" + dev,
        GENERIC_READ | GENERIC_WRITE,
        0x1 | 0x2, None, 3, 0, None
    )
    INVALID = ctypes.c_void_p(-1).value
    if not h or h == INVALID:
        print("FAIL: CreateFileW err={}".format(ctypes.get_last_error()))
        return
    print("Handle OK")

    from ctypes import wintypes

    sector = 1214484  # output_rgb565.bin start
    buf = bytearray(S)
    for i in range(S):
        buf[i] = (i & 0xFF)

    pos = ctypes.c_longlong(sector * S)
    newpos = ctypes.c_longlong(0)
    k.SetFilePointerEx(h, pos, ctypes.byref(newpos), 0)

    cb = ctypes.create_string_buffer(bytes(buf), S)
    done = wintypes.DWORD(0)
    ok = k.WriteFile(h, cb, S, ctypes.byref(done), None)
    err = ctypes.get_last_error()
    print("WriteFile sector {}: ok={} wrote={} err={}".format(sector, ok, done.value, err))

    if not ok or done.value != S:
        print("FAIL: cannot write")
        k.CloseHandle(h)
        return
    print("Write OK")

    # Flush
    k.FlushFileBuffers(h)

    # Read back
    pos2 = ctypes.c_longlong(sector * S)
    newpos2 = ctypes.c_longlong(0)
    k.SetFilePointerEx(h, pos2, ctypes.byref(newpos2), 0)
    rdbuf = ctypes.create_string_buffer(S)
    done2 = wintypes.DWORD(0)
    ok2 = k.ReadFile(h, rdbuf, S, ctypes.byref(done2), None)
    err2 = ctypes.get_last_error()
    print("ReadFile sector {}: ok={} read={} err={}".format(sector, ok2, done2.value, err2))

    k.CloseHandle(h)

    if done2.value == S:
        first8 = rdbuf.raw[:8].hex()
        match = rdbuf.raw[:S] == bytes(buf)
        print("First 8 bytes: {}".format(first8))
        print("Expected:       0001020304050607")
        if match:
            print("MATCH! Raw sector write works!")
        else:
            all_00 = all(b == 0x00 for b in rdbuf.raw)
            all_ff = all(b == 0xFF for b in rdbuf.raw)
            print("MISMATCH (all_00={} all_ff={})".format(all_00, all_ff))
    else:
        print("FAIL: read {} bytes".format(done2.value))


if __name__ == "__main__":
    main()

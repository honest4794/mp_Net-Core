import subprocess, re
for d in ["/dev/disk0", "/dev/disk3", "/dev/disk4"]:
    r = subprocess.run(["diskutil","info",d], capture_output=True, text=True)
    int_ = re.search(r"Internal:\s+", r.stdout)
    print("{}  Internal={}".format(d, int_.group() if int_ else "NONE"))

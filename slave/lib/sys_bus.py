class SysBus:
    def __init__(self):
        self._services = {}
        self._providers = {}
        self.shared = {}
        self.slave_id = "UNKNOWN"
        self.cid = 0xFFFF        # 協議定址短身份 (uint16); 由 ConfigManager 於 T0 推動
        self.master_cid = 0xFFFF # 回應定址目標 (uint16); 0xFFFF=廣播(未設定), 由 SET_MASTER/IDENTIFY 設定, 僅內存
        self._gpio_claims = {}

    def register_service(self, name, obj):
        if name in self._services:
            return False
        self._services[name] = obj
        return True

    def get_service(self, name):
        return self._services.get(name)

    def has_lcd(self):
        """LCD 是否存在於 bus 上(boot.py 的 init_tft 成功才有)。
        用來 gate 依賴 LCD 的模組(lvgl)。
        沒有 LCD 時這些模組會 import 失敗或無法運作,因此整段 import/註冊都跳過。"""
        return self.get_service("lcd") is not None

    def register_provider(self, key, func):
        if key in self._providers:
            return False
        self._providers[key] = func
        return True

    def get_metrics(self):
        res = {k: f() for k, f in self._providers.items()}
        res["slave_id"] = self.slave_id
        return res

    def gpio_claim(self, gpio, driver, label=""):
        label = label or "{}:{}".format(driver, gpio)
        if gpio not in self._gpio_claims:
            self._gpio_claims[gpio] = []
        self._gpio_claims[gpio].append({"driver": driver, "label": label})

    def gpio_validate(self):
        conflicts = {}
        for gpio, claims in self._gpio_claims.items():
            drivers = set(c["driver"] for c in claims)
            if len(drivers) > 1:
                conflicts[gpio] = claims
        if conflicts:
            lines = ["GPIO CONFLICT:"]
            for gpio, claims in conflicts.items():
                names = ", ".join(c["driver"] for c in claims)
                lines.append("  GPIO {} → [{}]".format(gpio, names))
            raise ValueError("\n".join(lines))
        return True

    def gpio_dump(self):
        if not self._gpio_claims:
            print("[GPIO] (none claimed)")
            return
        print("[GPIO] claimed pins:")
        for gpio in sorted(self._gpio_claims.keys()):
            for c in self._gpio_claims[gpio]:
                print("  {:>3}  {:<16} {}".format(gpio, c["driver"], c["label"]))


bus = SysBus()

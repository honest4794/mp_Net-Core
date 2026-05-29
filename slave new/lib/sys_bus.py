class SysBus:
    def __init__(self):
        self._services = {}
        self._providers = {}
        self.shared = {}
        self.slave_id = "UNKNOWN"
        self._gpio_claims = {}

    def register_service(self, name, obj):
        if name in self._services:
            return False
        self._services[name] = obj
        return True

    def get_service(self, name):
        return self._services.get(name)

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

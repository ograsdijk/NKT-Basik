import nkt_basik.functions as discovery


class _FakeBasik:
    def __init__(self, port: str, dev_id: int):
        self.port = port
        self.dev_id = dev_id
        self.name = f"seed-{dev_id}"

    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        return None


def test_find_devices_returns_collection(monkeypatch) -> None:
    open_port_snapshots = iter(["", "COM1", "COM1"])

    monkeypatch.setattr(discovery, "openPorts", lambda *_args, **_kwargs: 0)
    monkeypatch.setattr(discovery, "closePorts", lambda *_args, **_kwargs: 0)
    monkeypatch.setattr(discovery, "getAllPorts", lambda: "COM1")
    monkeypatch.setattr(discovery, "getOpenPorts", lambda: next(open_port_snapshots))
    monkeypatch.setattr(discovery, "deviceGetAllTypes", lambda _port: (0, [1, 0, 1]))
    monkeypatch.setattr(discovery, "Basik", _FakeBasik)

    devices = discovery.find_devices()

    assert len(devices) == 2
    assert devices[0].port == "COM1"


def test_discovery_closes_only_ports_it_opened(monkeypatch) -> None:
    close_calls: list[str] = []
    open_port_snapshots = iter(
        ["COM_EXISTING", "COM_EXISTING,COM1", "COM_EXISTING,COM1"]
    )

    monkeypatch.setattr(discovery, "openPorts", lambda *_args, **_kwargs: 0)
    monkeypatch.setattr(discovery, "closePorts", close_calls.append)
    monkeypatch.setattr(discovery, "getAllPorts", lambda: "COM1")
    monkeypatch.setattr(
        discovery,
        "getOpenPorts",
        lambda: next(open_port_snapshots),
    )
    monkeypatch.setattr(discovery, "deviceGetAllTypes", lambda _port: (0, [1]))

    devices = discovery._discover_raw()

    assert devices == [("COM1", 0)]
    assert close_calls == ["COM1"]


def test_discovery_returns_empty_when_open_ports_fails(monkeypatch) -> None:
    close_calls: list[str] = []

    monkeypatch.setattr(discovery, "openPorts", lambda *_args, **_kwargs: 2)
    monkeypatch.setattr(discovery, "closePorts", close_calls.append)
    monkeypatch.setattr(discovery, "getAllPorts", lambda: "COM1")
    monkeypatch.setattr(discovery, "getOpenPorts", lambda: "")

    assert discovery._discover_raw() == []
    assert close_calls == []


def test_find_devices_by_names_includes_empty_groups(monkeypatch) -> None:
    monkeypatch.setattr(
        discovery,
        "find_devices",
        lambda ports=None: [
            discovery.DeviceRef(port="COM1", dev_id=0, name="seed-a"),
            discovery.DeviceRef(port="COM2", dev_id=1, name="seed-b"),
        ],
    )

    grouped = discovery.find_devices_by_names(["seed-a", "seed-c"])

    assert len(grouped["seed-a"]) == 1
    assert grouped["seed-c"] == []

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
    monkeypatch.setattr(discovery, "openPorts", lambda *_args, **_kwargs: 0)
    monkeypatch.setattr(discovery, "closePorts", lambda *_args, **_kwargs: 0)
    monkeypatch.setattr(discovery, "getAllPorts", lambda: "COM1")
    monkeypatch.setattr(discovery, "getOpenPorts", lambda: "COM1")
    monkeypatch.setattr(discovery, "deviceGetAllTypes", lambda _port: (0, [1, 0, 1]))
    monkeypatch.setattr(discovery, "Basik", _FakeBasik)

    devices = discovery.find_devices()

    assert len(devices) == 2
    assert devices[0].port == "COM1"


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

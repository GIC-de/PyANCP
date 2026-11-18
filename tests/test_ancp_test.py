import importlib.util
from pathlib import Path

import pytest


spec = importlib.util.spec_from_file_location("ancp_test", Path(__file__).parents[1] / "bin" / "ancp_test.py")
ancp_test = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ancp_test)


@pytest.mark.parametrize("technology", ["dsl", "pon"])
@pytest.mark.parametrize("version", ["00", "01", "02", "03", "04", "14", "99"])
def test_cli_sends_selected_draft_and_cleans_up(monkeypatch, technology, version):
    events = []

    class Established:
        def is_set(self):
            return True

    class Client:
        established = Established()

        def __init__(self, **kwargs):
            events.append(("client", kwargs))

        def connect(self):
            return True

        def port_up(self, subscriber):
            events.append(("up", subscriber))

        def port_down(self, subscriber):
            events.append(("down", subscriber))

        def disconnect(self):
            events.append(("disconnect",))

    ticks = iter((0, 0, 0, 2))
    monkeypatch.setattr(ancp_test, "Client", Client)
    monkeypatch.setattr(ancp_test.time, "monotonic", lambda: next(ticks))
    monkeypatch.setattr(ancp_test.time, "sleep", lambda _: None)
    assert ancp_test.main([
        "--target", "192.0.2.1", "--source", "192.0.2.2",
        "--aci", "circuit", "--ari", "remote", "--up", "100", "--down", "200",
        "--technology", technology, "--draft-version", version, "--hold-seconds", "1",
    ]) == 0
    expected_technology = ancp_test.TechTypes.PON if technology == "pon" else ancp_test.TechTypes.DSL
    assert events[0][1]["tech_type"] == expected_technology
    assert events[1][1].draft_version == version
    if technology == "pon":
        assert events[1][1].ont_onu_max_up == 100
        assert events[1][1].ont_onu_avg_down == 200
    else:
        assert events[1][1].up == 100
        assert events[1][1].down == 200
    assert events[2] == ("down", events[1][1])
    assert events[3] == ("disconnect",)


@pytest.mark.parametrize("version", ["4", "100", "0a"])
def test_cli_rejects_invalid_draft_before_connecting(monkeypatch, version):
    monkeypatch.setattr(ancp_test, "Client", lambda **kwargs: pytest.fail("unexpected connection"))
    with pytest.raises(SystemExit) as error:
        ancp_test.main([
            "--target", "192.0.2.1", "--source", "192.0.2.2",
            "--aci", "circuit", "--ari", "remote", "--up", "100", "--down", "200",
            "--draft-version", version,
        ])
    assert error.value.code == 2

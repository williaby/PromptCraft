from datetime import datetime
from typing import Any

import pytest

from src.monitoring.integration_utils import (
    CloudWatchIntegration,
    DataDogIntegration,
    GrafanaIntegration,
    IntegrationManager,
    PrometheusIntegration,
    SlackIntegration,
)


class DummyResponse:
    def __init__(self, status: int, json_data: dict[str, Any] | None = None):
        self.status = status
        self._json_data = json_data or {}

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def json(self):
        return self._json_data


class DummySession:
    """Async context manager that returns fixed responses for get/post."""

    def __init__(self, *, get_status: int = 200, post_status: int = 200, post_json: dict[str, Any] | None = None):
        self._get_status = get_status
        self._post_status = post_status
        self._post_json = post_json

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    def get(self, url, *_, **__):
        return DummyResponse(self._get_status)

    def post(self, url, *_, **__):
        return DummyResponse(self._post_status, json_data=self._post_json)


@pytest.mark.asyncio
async def test_prometheus_convert_and_send(monkeypatch):
    metrics = {
        "system_health": {"overall_success_rate": 97.5, "average_loading_latency": 123},
        "validation_status": {"optimization_validated": True, "validation_confidence": 0.88},
        "tier_performance": {
            "gold": {"success_rate": 98.0},
            "silver": {"success_rate": 95.0},
        },
    }

    # Conversion format contains expected metrics and labels
    p = PrometheusIntegration({"enabled": True, "pushgateway_url": "http://pg:9091"})
    out = p._convert_to_prometheus_format(metrics)
    assert "token_optimization_overall_success_rate" in out
    assert "token_optimization_validated" in out
    assert 'token_optimization_tier_success_rate{tier="gold"}' in out

    # Early return when disabled
    p_disabled = PrometheusIntegration({"enabled": False})
    assert await p_disabled.send_metrics(metrics) is True

    # Success
    monkeypatch.setattr(
        "aiohttp.ClientSession",
        lambda: DummySession(post_status=200),
    )
    assert await p.send_metrics(metrics) is True

    # Failure status
    monkeypatch.setattr(
        "aiohttp.ClientSession",
        lambda: DummySession(post_status=500),
    )
    assert await p.send_metrics(metrics) is False

    # Exception path
    class Boom:
        def __init__(self):
            pass

        async def __aenter__(self):
            raise RuntimeError("boom")

        async def __aexit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr("aiohttp.ClientSession", lambda: Boom())
    assert await p.send_metrics(metrics) is False

    # send_alert returns True (no-op)
    assert await p_disabled.send_alert({"title": "t"}) is True
    assert await p.send_alert({"title": "t"}) is True

    # validate_configuration success and failure
    monkeypatch.setattr(
        "aiohttp.ClientSession",
        lambda: DummySession(get_status=200),
    )
    assert await p.validate_configuration() is True
    monkeypatch.setattr(
        "aiohttp.ClientSession",
        lambda: DummySession(get_status=404),
    )
    assert await p.validate_configuration() is False


@pytest.mark.asyncio
async def test_grafana_integration_flows(monkeypatch):
    g = GrafanaIntegration({"enabled": True, "api_key": "k", "api_url": "http://g/api"})
    assert await g.send_metrics({}) is True

    # send_alert early returns when disabled or missing key
    g_disabled = GrafanaIntegration({"enabled": False})
    assert await g_disabled.send_alert({"title": "t", "message": "m", "level": "warning"}) is True
    g_no_key = GrafanaIntegration({"enabled": True})
    assert await g_no_key.send_alert({"title": "t", "message": "m", "level": "warning"}) is True

    # send_alert success and failure
    monkeypatch.setattr("aiohttp.ClientSession", lambda: DummySession(post_status=200))
    assert await g.send_alert({"title": "t", "message": "m", "level": "info"}) is True
    monkeypatch.setattr("aiohttp.ClientSession", lambda: DummySession(post_status=500))
    assert await g.send_alert({"title": "t", "message": "m", "level": "error"}) is False

    # validate_configuration key missing -> False; success and exception
    assert await g_no_key.validate_configuration() is False
    monkeypatch.setattr("aiohttp.ClientSession", lambda: DummySession(get_status=200))
    assert await g.validate_configuration() is True
    monkeypatch.setattr("aiohttp.ClientSession", lambda: DummySession(get_status=500))
    assert await g.validate_configuration() is False

    # create_dashboard success, failure, exception
    cfg = g._generate_dashboard_config({})
    assert isinstance(cfg, dict) and "dashboard" in cfg and len(cfg["dashboard"]["panels"]) >= 4

    monkeypatch.setattr(
        "aiohttp.ClientSession",
        lambda: DummySession(post_status=200, post_json={"url": "http://g/d/abc"}),
    )
    url = await g.create_dashboard({})
    assert url == "http://g/d/abc"

    monkeypatch.setattr("aiohttp.ClientSession", lambda: DummySession(post_status=500))
    assert await g.create_dashboard({}) is None


@pytest.mark.asyncio
async def test_datadog_integration_paths(monkeypatch):
    d_disabled = DataDogIntegration({"enabled": False})
    assert await d_disabled.send_metrics({}) is True

    d = DataDogIntegration({"enabled": True, "api_key": "k", "site": "example.com"})
    # send_metrics success and failure
    monkeypatch.setattr("aiohttp.ClientSession", lambda: DummySession(post_status=202))
    assert await d.send_metrics({"system_health": {"overall_success_rate": 1}}) is True
    monkeypatch.setattr("aiohttp.ClientSession", lambda: DummySession(post_status=400))
    assert await d.send_metrics({}) is False

    # exception path
    class Boom2:
        async def __aenter__(self):
            raise RuntimeError("boom")

        async def __aexit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr("aiohttp.ClientSession", lambda: Boom2())
    assert await d.send_metrics({}) is False

    # send_alert success and failure
    monkeypatch.setattr("aiohttp.ClientSession", lambda: DummySession(post_status=202))
    assert await d.send_alert({"title": "t", "message": "m", "level": "info"}) is True
    monkeypatch.setattr("aiohttp.ClientSession", lambda: DummySession(post_status=400))
    assert await d.send_alert({"title": "t", "message": "m", "level": "error"}) is False

    # validate_configuration
    d_no_key = DataDogIntegration({"enabled": True})
    assert await d_no_key.validate_configuration() is False
    monkeypatch.setattr("aiohttp.ClientSession", lambda: DummySession(get_status=200))
    assert await d.validate_configuration() is True
    monkeypatch.setattr("aiohttp.ClientSession", lambda: DummySession(get_status=500))
    assert await d.validate_configuration() is False

    # _convert_to_datadog_format structure
    pts = d._convert_to_datadog_format(
        {
            "system_health": {"overall_success_rate": 97},
            "validation_status": {"optimization_validated": True, "validation_confidence": 0.9},
            "tier_performance": {"gold": {"success_rate": 99}},
        },
    )
    names = {p["metric"] for p in pts}
    assert "token_optimization.overall_success_rate" in names
    assert "token_optimization.validated" in names
    assert "token_optimization.tier.success_rate" in names


@pytest.mark.asyncio
async def test_cloudwatch_integration_simple():
    cw_disabled = CloudWatchIntegration({"enabled": False})
    assert await cw_disabled.send_metrics({}) is True
    assert await cw_disabled.send_alert({"title": "t"}) is True

    cw = CloudWatchIntegration({"enabled": True, "aws_access_key": "A", "aws_secret_key": "S"})
    assert await cw.send_metrics({}) is True
    assert await cw.send_alert({"title": "t"}) is True
    assert await cw.validate_configuration() is True

    cw_bad = CloudWatchIntegration({"enabled": True})
    assert await cw_bad.validate_configuration() is False


@pytest.mark.asyncio
async def test_slack_integration_paths(monkeypatch):
    s = SlackIntegration({"enabled": True, "webhook_url": "http://hook"})
    assert await s.send_metrics({}) is True

    # Early returns
    s_disabled = SlackIntegration({"enabled": False})
    assert (
        await s_disabled.send_alert(
            {"title": "t", "message": "m", "level": "warning", "timestamp": datetime.now().isoformat()},
        )
        is True
    )
    s_no_hook = SlackIntegration({"enabled": True})
    assert (
        await s_no_hook.send_alert(
            {"title": "t", "message": "m", "level": "info", "timestamp": datetime.now().isoformat()},
        )
        is True
    )

    # Success
    monkeypatch.setattr("aiohttp.ClientSession", lambda: DummySession(post_status=200))
    assert (
        await s.send_alert({"title": "t", "message": "m", "level": "error", "timestamp": datetime.now().isoformat()})
        is True
    )
    # Failure
    monkeypatch.setattr("aiohttp.ClientSession", lambda: DummySession(post_status=500))
    assert (
        await s.send_alert({"title": "t", "message": "m", "level": "error", "timestamp": datetime.now().isoformat()})
        is False
    )

    # validate_configuration
    assert await s_no_hook.validate_configuration() is False
    monkeypatch.setattr("aiohttp.ClientSession", lambda: DummySession(post_status=200))
    assert await s.validate_configuration() is True
    monkeypatch.setattr("aiohttp.ClientSession", lambda: DummySession(post_status=400))
    assert await s.validate_configuration() is False


@pytest.mark.asyncio
async def test_additional_exception_paths_and_helpers(tmp_path, monkeypatch):
    # Grafana create_dashboard exception
    g = GrafanaIntegration({"enabled": True, "api_key": "k"})

    class Boom3:
        async def __aenter__(self):
            raise RuntimeError("boom")

        async def __aexit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr("aiohttp.ClientSession", lambda: Boom3())
    assert await g.create_dashboard({}) is None

    # DataDog validate_configuration exception
    d = DataDogIntegration({"enabled": True, "api_key": "k"})
    monkeypatch.setattr("aiohttp.ClientSession", lambda: Boom3())
    assert await d.validate_configuration() is False

    # Slack validate_configuration exception
    s = SlackIntegration({"enabled": True, "webhook_url": "http://hook"})
    monkeypatch.setattr("aiohttp.ClientSession", lambda: Boom3())
    assert await s.validate_configuration() is False

    # CloudWatch exception in send methods via logger
    cw = CloudWatchIntegration({"enabled": True})
    called = {"info": 0}

    def boom_info(*args, **kwargs):
        called["info"] += 1
        raise RuntimeError("boom")

    # Patch logger methods to trigger exception
    cw.logger.info = boom_info  # type: ignore[attr-defined]
    assert await cw.send_metrics({}) is False
    assert await cw.send_alert({"title": "t"}) is False

    # load_integration_config default and merge
    from src.monitoring import integration_utils as integ_mod

    cfg_default = integ_mod.load_integration_config()
    assert cfg_default["prometheus"]["job_name"] == "token_optimization"
    # Write a temp config file to merge
    custom = {
        "prometheus": {"enabled": True, "instance": "ci"},
        "slack": {"enabled": True, "channel": "#ci"},
    }
    p = tmp_path / "cfg.json"
    p.write_text(__import__("json").dumps(custom))
    cfg = integ_mod.load_integration_config(str(p))
    assert cfg["prometheus"]["enabled"] is True and cfg["prometheus"]["instance"] == "ci"
    assert cfg["slack"]["channel"] == "#ci"

    # get_integration_manager returns singleton
    integ_mod._integration_manager = None
    m1 = integ_mod.get_integration_manager(str(p))
    m2 = integ_mod.get_integration_manager(str(p))
    assert m1 is m2

    # initialize_integrations uses manager and returns it
    class FakeMgr:
        def __init__(self):
            self.validated = False

        async def validate_all_configurations(self):
            self.validated = True
            return {"prometheus": True}

    monkeypatch.setattr(integ_mod, "get_integration_manager", lambda _=None: FakeMgr())
    ret = await integ_mod.initialize_integrations(str(p))
    assert isinstance(ret, FakeMgr) and ret.validated is True


@pytest.mark.asyncio
async def test_integration_manager_behaviors(monkeypatch):
    cfg = {
        "prometheus": {"enabled": True},
        "grafana": {"enabled": True},
        "datadog": {"enabled": True, "api_key": "k"},
        "cloudwatch": {"enabled": True, "aws_access_key": "A", "aws_secret_key": "S"},
        "slack": {"enabled": True, "webhook_url": "http://hook"},
        "unknown": {"enabled": True},
    }
    mgr = IntegrationManager(cfg)
    names = mgr.list_integrations()
    assert set(names) == {"prometheus", "grafana", "datadog", "cloudwatch", "slack"}
    assert mgr.get_integration("slack") is not None
    assert mgr.get_integration("unknown") is None

    # Replace integrations with fakes to control behavior
    class FakeInt:
        def __init__(self, name, *, enabled=True, valid=True, send_ok=True, alert_ok=True, raise_on=None):
            self.name = name
            self.enabled = enabled
            self._valid = valid
            self._send_ok = send_ok
            self._alert_ok = alert_ok
            self._raise_on = raise_on or set()

        async def validate_configuration(self):
            if "validate" in self._raise_on:
                raise RuntimeError("fail validate")
            return self._valid

        async def send_metrics(self, metrics):
            if "metrics" in self._raise_on:
                raise RuntimeError("fail metrics")
            return self._send_ok

        async def send_alert(self, alert):
            if "alert" in self._raise_on:
                raise RuntimeError("fail alert")
            return self._alert_ok

    mgr.integrations = {
        "a": FakeInt("a", enabled=True, valid=True),
        "b": FakeInt("b", enabled=True, valid=False),
        "c": FakeInt("c", enabled=False, valid=True),
        "d": FakeInt("d", enabled=True, valid=True, send_ok=False),
        "e": FakeInt("e", enabled=True, valid=True, raise_on={"validate", "metrics", "alert"}),
    }

    # validate_all_configurations collects results and handles errors
    val = await mgr.validate_all_configurations()
    assert val == {"a": True, "b": False, "c": True, "d": True, "e": False}

    # send_metrics_to_all returns per-integration success and handles errors
    met = await mgr.send_metrics_to_all({})
    assert met == {"a": True, "b": True, "c": True, "d": False, "e": False}

    # send_alert_to_all
    al = await mgr.send_alert_to_all({"title": "t"})
    assert al == {"a": True, "b": True, "c": True, "d": True, "e": False}

    # health_check reflects enabled and validation status
    health = await mgr.health_check()
    assert isinstance(health, dict)
    assert "integrations" in health and "overall_healthy" in health
    # Because b is invalid and enabled, overall_healthy should be False
    assert health["overall_healthy"] is False

    # All healthy case
    mgr.integrations = {
        "x": FakeInt("x", enabled=True, valid=True),
        "y": FakeInt("y", enabled=True, valid=True),
    }
    health2 = await mgr.health_check()
    assert health2["overall_healthy"] is True

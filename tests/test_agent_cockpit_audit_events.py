import json
import tempfile
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.integrations.agent_cockpit_audit_events import (
    AUDIT_STORAGE_PATH,
    BLOCKED_ACTIONS,
    READ_ONLY_EXECUTION_GUARANTEES,
    append_audit_event,
    router,
)


def _payload(event_type: str = "readiness_checked") -> dict:
    return {
        "event_type": event_type,
        "source": "test",
        "actor": "test_operator",
        "workflow_phase": "2G",
        "user_visible_summary": "Checked cockpit readiness.",
        "notes": "Focused test event.",
    }


def _read_lines(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_valid_event_appends_one_jsonl_line():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "audit" / "operator-run-history.jsonl"

        result = append_audit_event(_payload(), storage_path=path)
        lines = _read_lines(path)

        assert result["ok"] is True
        assert len(lines) == 1
        assert lines[0]["event_id"] == result["event_id"]


def test_audit_directory_is_created_if_missing():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "missing" / "audit.jsonl"

        append_audit_event(_payload(), storage_path=path)

        assert path.exists()
        assert path.parent.exists()


def test_allowed_event_type_succeeds():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "audit.jsonl"

        result = append_audit_event(_payload("implementation_plan_generated"), storage_path=path)

        assert result["event_type"] == "implementation_plan_generated"


def test_disallowed_event_type_is_rejected():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "audit.jsonl"

        try:
            append_audit_event(_payload("deploy_triggered"), storage_path=path)
        except Exception as exc:
            assert getattr(exc, "detail", None) == "disallowed_event_type"
        else:
            raise AssertionError("disallowed event type was not rejected")

        assert not path.exists()


def test_unknown_event_type_is_rejected():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "audit.jsonl"

        try:
            append_audit_event(_payload("unknown_event"), storage_path=path)
        except Exception as exc:
            assert getattr(exc, "detail", None) == "unknown_event_type"
        else:
            raise AssertionError("unknown event type was not rejected")

        assert not path.exists()


def test_caller_cannot_override_storage_path():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "audit.jsonl"
        payload = _payload()
        payload["storage_path"] = r"C:\Projects\GitHub\turboservices\unsafe.jsonl"

        result = append_audit_event(payload, storage_path=path)
        event = _read_lines(path)[0]

        assert result["storage_path"] == str(path)
        assert "storage_path" not in event
        assert r"C:\Projects\GitHub\turboservices\unsafe.jsonl" not in json.dumps(event)


def test_event_includes_safety_state_and_blocked_actions():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "audit.jsonl"

        append_audit_event(_payload(), storage_path=path)
        event = _read_lines(path)[0]

        assert event["safety_state"] == "audit_only_no_execution"
        for action in BLOCKED_ACTIONS:
            assert action in event["blocked_actions"]


def test_event_includes_read_only_execution_guarantees():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "audit.jsonl"

        append_audit_event(_payload(), storage_path=path)
        event = _read_lines(path)[0]

        for guarantee in READ_ONLY_EXECUTION_GUARANTEES:
            assert guarantee in event["read_only_execution_guarantees"]


def test_event_does_not_contain_obvious_secret_like_input_fields():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "audit.jsonl"
        payload = _payload()
        payload.update(
            {
                "api_key": "secret-api-key",
                "oauth_token": "secret-oauth-token",
                "private_key": "secret-private-key",
                "refresh_token": "secret-refresh-token",
                "credentials": "secret-credentials",
            }
        )

        append_audit_event(payload, storage_path=path)
        event_text = path.read_text(encoding="utf-8")

        assert "secret-api-key" not in event_text
        assert "secret-oauth-token" not in event_text
        assert "secret-private-key" not in event_text
        assert "secret-refresh-token" not in event_text
        assert "secret-credentials" not in event_text


def test_secret_like_content_in_allowed_fields_is_rejected():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "audit.jsonl"
        payload = _payload()
        payload["notes"] = "client_secret should never be stored"

        try:
            append_audit_event(payload, storage_path=path)
        except Exception as exc:
            assert getattr(exc, "detail", None) == "secret_like_content_rejected"
        else:
            raise AssertionError("secret-like content was not rejected")

        assert not path.exists()


def test_endpoint_uses_patched_path_and_does_not_write_real_audit_file():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "audit.jsonl"
        import app.integrations.agent_cockpit_audit_events as audit_events

        original = audit_events.AUDIT_STORAGE_PATH
        audit_events.AUDIT_STORAGE_PATH = path
        try:
            app = FastAPI()
            app.include_router(router, prefix="/api/agent-cockpit")
            client = TestClient(app)

            response = client.post("/api/agent-cockpit/audit-events", json=_payload())
        finally:
            audit_events.AUDIT_STORAGE_PATH = original

        assert response.status_code == 200
        assert path.exists()
        assert AUDIT_STORAGE_PATH != path
        assert str(AUDIT_STORAGE_PATH) == (
            r"C:\Projects\TurboWorkspace\audit\operator-run-history.jsonl"
        )

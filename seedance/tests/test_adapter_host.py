import base64
import hashlib
import io
import json
from pathlib import Path

import httpx
import pytest

from seedance_icons.adapter_host import AdapterError, execute, main
from seedance_icons.openrouter import OpenRouterHTTPError


def request(operation: str, kind: str = "image") -> dict:
    body = b"locked-reference"
    media_type = "image/png" if kind == "image" else "video/mp4"
    return {
        "adapter_protocol_version": "1",
        "operation": operation,
        "model": "bytedance/seedance-test",
        "objective": "Move once, then return.",
        "video_plan": {"expectedMedia": {"width": 64, "height": 48, "durationSeconds": 1, "audioExpected": False}},
        "payload": {"input_references": [{f"{kind}_url": {"url": {
            "applicationPath": f"references/source.{media_type.split('/')[-1]}",
            "bytesBase64": base64.b64encode(body).decode(),
            "mediaType": media_type,
            "sha256": hashlib.sha256(body).hexdigest(),
            **({"providerUrl": "https://example.com/motion.mp4"} if kind == "video" else {}),
        }}}]},
        **({"job_id": "job-1"} if operation == "poll" else {}),
    }


def test_adapter_host_normalizes_submit_pending_completed_and_refusal(tmp_path: Path) -> None:
    submitted_requests = []

    class SubmitClient:
        def submit(self, value: dict) -> dict:
            submitted_requests.append(value)
            return {"id": "job-1", "status": "queued"}

    submitted = execute(request("submit"), client=SubmitClient())
    assert submitted["job_id"] == "job-1"
    assert submitted_requests[0]["frame_images"][0]["frame_type"] == "first_frame"
    assert "input_references" not in submitted_requests[0]

    class PendingClient:
        def status(self, _job_id: str) -> dict:
            return {"id": "job-1", "status": "processing"}

    assert execute(request("poll"), client=PendingClient())["status"] == "pending"

    class CompletedClient:
        def status(self, _job_id: str) -> dict:
            return {"id": "job-1", "status": "completed", "usage": {"cost": 0.125}}

        def download(self, _job_id: str, destination: Path) -> str:
            destination.write_bytes(b"video")
            return hashlib.sha256(b"video").hexdigest()

    completed = execute(request("poll"), client=CompletedClient())
    assert completed["status"] == "completed"
    assert completed["cost"] == {"state": "actual", "actual_cost_usd": "0.125"}
    assert base64.b64decode(completed["outputs"][0]["body_base64"]) == b"video"

    class RejectedClient:
        def status(self, _job_id: str) -> dict:
            return {"id": "job-1", "status": "rejected"}

    with pytest.raises(AdapterError, match="rejected"):
        execute(request("poll"), client=RejectedClient())

    malformed = request("submit")
    malformed["payload"]["input_references"][0]["image_url"]["url"]["sha256"] = "0" * 64
    with pytest.raises(AdapterError, match="locked evidence"):
        execute(malformed, client=SubmitClient())

    video_submit = request("submit", "video")
    execute(video_submit, client=SubmitClient())
    assert submitted_requests[-1]["input_references"][0]["type"] == "video_url"
    assert submitted_requests[-1]["input_references"][0]["video_url"]["url"] == "https://example.com/motion.mp4"
    video_submit["payload"]["input_references"][0]["video_url"]["url"]["providerUrl"] = "data:video/mp4;base64,abc"
    with pytest.raises(AdapterError, match="HTTPS"):
        execute(video_submit, client=SubmitClient())


def test_submit_http_rejection_preserves_safe_diagnostic(monkeypatch, capsys) -> None:
    class RejectedClient:
        def submit(self, _value: dict) -> dict:
            req = httpx.Request("POST", "https://openrouter.ai/api/v1/videos")
            response = httpx.Response(400, request=req, json={"error": {
                "code": "bad_input", "message": "video reference is too short",
                "api_key": "sk-or-v1-private",
            }}, headers={"x-request-id": "req-400"})
            raise OpenRouterHTTPError("submit", "/videos", response)

        def close(self) -> None:
            pass

    monkeypatch.setenv("OPENROUTER_API_KEY", "fixture-key")
    monkeypatch.setattr("seedance_icons.adapter_host.OpenRouterVideoClient", RejectedClient)
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(request("submit", "video"))))
    assert main() == 2
    result = json.loads(capsys.readouterr().out)
    assert result["adapter_error"]["code"] == "PROVIDER_AMBIGUOUS"
    assert result["adapter_error"]["provider_diagnostic"] == {
        "status_code": 400,
        "request_id": "req-400",
        "reason": "video reference is too short",
    }
    assert "sk-or-v1-private" not in json.dumps(result)


def test_submit_http_rejection_redacts_url_but_keeps_reason() -> None:
    req = httpx.Request("POST", "https://openrouter.ai/api/v1/videos")
    response = httpx.Response(400, request=req, json={"error": {
        "message": "Invalid reference URL: https://example.com/private.mp4 is too small"
    }})
    from seedance_icons.adapter_host import _provider_diagnostic

    assert _provider_diagnostic(OpenRouterHTTPError("submit", "/videos", response))["reason"] == (
        "Invalid reference URL: <URL> is too small"
    )

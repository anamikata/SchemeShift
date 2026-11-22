from __future__ import annotations

import json
from types import SimpleNamespace

import pytest
from google.genai.errors import APIError

from app import ai_extract
from app.models import RuleExtraction
from app.pdf_extract import ExtractedDocument, ExtractedPage


def _api_error(code: int, status: str, message: str) -> APIError:
    return APIError(code, {"error": {"code": code, "status": status, "message": message}})


def _settings(monkeypatch):
    monkeypatch.setattr(
        ai_extract,
        "settings",
        SimpleNamespace(
            gemini_api_key="test-key-must-not-be-logged",
            gemini_model="primary-model",
            gemini_fallback_model="fallback-model",
        ),
    )


def _install_client(monkeypatch, responses):
    calls = []
    client_options = []

    class FakeModels:
        def generate_content(self, *, model, contents, config):
            calls.append((model, contents, config))
            result = responses.pop(0)
            if isinstance(result, Exception):
                raise result
            return SimpleNamespace(text=result)

    class FakeClient:
        def __init__(self, **kwargs):
            client_options.append(kwargs)
            self.models = FakeModels()

    monkeypatch.setattr(ai_extract.genai, "Client", FakeClient)
    monkeypatch.setattr(ai_extract.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(ai_extract.random, "uniform", lambda _low, high: high / 2)
    return calls, client_options


def _document() -> ExtractedDocument:
    return ExtractedDocument(
        pages=[ExtractedPage(page_number=1, text="A searchable government order text.")],
        page_count=1,
        text_character_count=34,
        likely_scanned=False,
    )


def _valid_json() -> str:
    return RuleExtraction(rules=[]).model_dump_json()


def _assert_same_schema(calls):
    assert all(call[2].response_mime_type == "application/json" for call in calls)
    assert all(call[2].response_schema == RuleExtraction.model_json_schema() for call in calls)


def test_primary_model_succeeds_without_fallback(monkeypatch, caplog):
    _settings(monkeypatch)
    caplog.set_level("INFO", logger="app.ai_extract")
    calls, client_options = _install_client(monkeypatch, [_valid_json()])

    result = ai_extract.extract_rules_with_gemini(_document(), "order.pdf")

    assert result.rules == []
    assert [call[0] for call in calls] == ["primary-model"]
    _assert_same_schema(calls)
    assert client_options[0]["http_options"].retry_options.attempts == 1
    assert "model=primary-model" in caplog.text
    assert "test-key-must-not-be-logged" not in caplog.text


def test_primary_503_then_success_retries_primary_only(monkeypatch, caplog):
    _settings(monkeypatch)
    calls, _ = _install_client(
        monkeypatch,
        [_api_error(503, "UNAVAILABLE", "Service temporarily unavailable"), _valid_json()],
    )

    result = ai_extract.extract_rules_with_gemini(_document(), "order.pdf")

    assert result.rules == []
    assert [call[0] for call in calls] == ["primary-model", "primary-model"]
    _assert_same_schema(calls)
    assert "attempt=1/3" in caplog.text
    assert "test-key-must-not-be-logged" not in caplog.text


def test_persistent_primary_503_uses_fallback_model(monkeypatch):
    _settings(monkeypatch)
    calls, _ = _install_client(
        monkeypatch,
        [_api_error(503, "UNAVAILABLE", "Capacity unavailable") for _ in range(3)] + [_valid_json()],
    )

    result = ai_extract.extract_rules_with_gemini(_document(), "order.pdf")

    assert result.rules == []
    assert [call[0] for call in calls] == ["primary-model"] * 3 + ["fallback-model"]
    _assert_same_schema(calls)


def test_both_models_failing_returns_clear_error(monkeypatch):
    _settings(monkeypatch)
    calls, _ = _install_client(
        monkeypatch,
        [_api_error(503, "UNAVAILABLE", "Capacity unavailable") for _ in range(6)],
    )

    with pytest.raises(RuntimeError, match="primary model 'primary-model'.*fallback model 'fallback-model'"):
        ai_extract.extract_rules_with_gemini(_document(), "order.pdf")

    assert [call[0] for call in calls] == ["primary-model"] * 3 + ["fallback-model"] * 3


def test_invalid_fallback_json_is_rejected(monkeypatch):
    _settings(monkeypatch)
    calls, _ = _install_client(
        monkeypatch,
        [_api_error(503, "UNAVAILABLE", "Capacity unavailable") for _ in range(3)] + ["not-json"],
    )

    with pytest.raises(RuntimeError, match="did not match the expected extraction schema"):
        ai_extract.extract_rules_with_gemini(_document(), "order.pdf")

    assert [call[0] for call in calls] == ["primary-model"] * 3 + ["fallback-model"]


@pytest.mark.parametrize(
    ("status_code", "status", "message"),
    [
        (400, "INVALID_ARGUMENT", "API key not valid"),
        (403, "PERMISSION_DENIED", "The API key does not have permission"),
        (400, "INVALID_ARGUMENT", "The request configuration is invalid"),
        (404, "NOT_FOUND", "The requested model was not found"),
    ],
)
def test_client_errors_never_trigger_fallback(monkeypatch, status_code, status, message):
    _settings(monkeypatch)
    calls, _ = _install_client(monkeypatch, [_api_error(status_code, status, message)])

    with pytest.raises(RuntimeError):
        ai_extract.extract_rules_with_gemini(_document(), "order.pdf")

    assert [call[0] for call in calls] == ["primary-model"]


def test_temporary_429_retries_but_does_not_use_fallback(monkeypatch):
    _settings(monkeypatch)
    calls, _ = _install_client(
        monkeypatch,
        [_api_error(429, "RESOURCE_EXHAUSTED", "Rate limit exceeded: requests per minute"), _valid_json()],
    )

    result = ai_extract.extract_rules_with_gemini(_document(), "order.pdf")

    assert result.rules == []
    assert [call[0] for call in calls] == ["primary-model", "primary-model"]


def test_exhausted_quota_429_is_reported_without_fallback(monkeypatch):
    _settings(monkeypatch)
    calls, _ = _install_client(
        monkeypatch,
        [_api_error(429, "RESOURCE_EXHAUSTED", "Quota exceeded for requests per day")],
    )

    with pytest.raises(RuntimeError, match="exhausted Gemini quota"):
        ai_extract.extract_rules_with_gemini(_document(), "order.pdf")

    assert [call[0] for call in calls] == ["primary-model"]


def test_incomplete_json_cannot_be_accepted_as_empty_extraction(monkeypatch):
    _settings(monkeypatch)
    calls, _ = _install_client(monkeypatch, [json.dumps({"document_title": "Some order"})])

    with pytest.raises(RuntimeError, match="expected extraction schema"):
        ai_extract.extract_rules_with_gemini(_document(), "order.pdf")

    assert [call[0] for call in calls] == ["primary-model"]

"""LLM access layer.

* GeminiBackend  - thin wrapper over the google-genai SDK
* LLMService     - prompt rendering, retries, JSON parsing, schema validation and
                   one automatic "repair" attempt. Never returns unvalidated text
                   to an agent: failures raise LLMError / InvalidModelOutput.

Every call is stateless (no chat history is kept between calls or between users)."""
from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field
from typing import Protocol, TypeVar

from pydantic import BaseModel, ValidationError

from app.config import Settings, get_settings
from app.prompts import PromptSpec

T = TypeVar("T", bound=BaseModel)


class LLMError(Exception):
    """The model could not be reached or returned nothing usable."""


class InvalidModelOutput(LLMError):
    """The model answered, but the output failed JSON / schema validation twice."""


class LLMNotConfigured(LLMError):
    """No API key available."""


class BackendError(Exception):
    def __init__(self, message: str, code: int | None = None):
        super().__init__(message)
        self.code = code


class LLMBackend(Protocol):
    def generate(self, *, system: str, user: str, temperature: float, json_mode: bool,
                 model: str | None = None) -> str: ...


class GeminiBackend:
    def __init__(self, settings: Settings | None = None):
        s = settings or get_settings()
        if not s.gemini_api_key:
            raise LLMNotConfigured("GEMINI_API_KEY is not set. Copy .env.example to .env and add your key.")
        from google import genai  # imported lazily so tests do not need the SDK

        self._client = genai.Client(api_key=s.gemini_api_key)
        self.model = s.gemini_model

    def generate(self, *, system: str, user: str, temperature: float, json_mode: bool,
                 model: str | None = None) -> str:
        from google.genai import errors, types

        config = types.GenerateContentConfig(
            system_instruction=system or None,
            temperature=temperature,
            max_output_tokens=8192,
            response_mime_type="application/json" if json_mode else None,
        )
        try:
            resp = self._client.models.generate_content(model=model or self.model, contents=user, config=config)
        except errors.APIError as exc:
            raise BackendError(str(exc), code=getattr(exc, "code", None)) from exc
        except Exception as exc:  # network errors etc.
            raise BackendError(f"{type(exc).__name__}: {exc}") from exc
        text = getattr(resp, "text", None)
        if not text:
            raise BackendError("Model returned an empty response (possibly blocked by safety filters)")
        return text


@dataclass
class LLMStats:
    calls: int = 0
    retries: int = 0
    repairs: int = 0
    invalid_after_repair: int = 0
    failures: int = 0
    seconds: float = 0.0
    per_prompt: dict[str, dict[str, int]] = field(default_factory=dict)

    def bump(self, prompt_id: str, key: str) -> None:
        d = self.per_prompt.setdefault(prompt_id, {"calls": 0, "repairs": 0, "invalid": 0, "failures": 0})
        d[key] = d.get(key, 0) + 1

    def as_dict(self) -> dict:
        first_pass_valid = (self.calls - self.repairs - self.invalid_after_repair) / self.calls if self.calls else None
        return {"llm_calls": self.calls, "retries": self.retries, "repairs": self.repairs,
                "invalid_after_repair": self.invalid_after_repair, "failures": self.failures,
                "first_pass_valid_rate": None if first_pass_valid is None else round(first_pass_valid, 3),
                "llm_seconds": round(self.seconds, 2), "per_prompt": self.per_prompt}


_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$", re.I)


def parse_json_loose(text: str) -> object:
    """Parse JSON, tolerating markdown fences and leading/trailing prose."""
    s = _FENCE.sub("", text.strip()).strip()
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        a, b = s.find("{"), s.rfind("}")
        if a != -1 and b > a:
            return json.loads(s[a:b + 1])
        raise


class LLMService:
    RETRY_CODES = {429, 500, 502, 503, 504}

    def __init__(self, backend: LLMBackend, settings: Settings | None = None, sleep=time.sleep):
        self.backend = backend
        self.settings = settings or get_settings()
        self.stats = LLMStats()
        self._sleep = sleep

    # ------------------------------------------------------------------ low level
    def _generate(self, spec: PromptSpec, system: str, user: str, json_mode: bool) -> str:
        last: BackendError | None = None
        model = None
        for attempt in range(self.settings.llm_max_retries + 1):
            try:
                t0 = time.time()
                out = self.backend.generate(system=system, user=user, temperature=spec.temperature,
                                            json_mode=json_mode, model=model)
                self.stats.seconds += time.time() - t0
                return out
            except BackendError as exc:
                last = exc
                if exc.code == 404 and self.settings.gemini_fallback_model and model is None:
                    model = self.settings.gemini_fallback_model  # model retired -> try fallback
                    continue
                if exc.code in self.RETRY_CODES or exc.code is None:
                    if attempt < self.settings.llm_max_retries:
                        self.stats.retries += 1
                        self._sleep(min(2 ** (attempt + 1), 20))
                        continue
                break
        self.stats.failures += 1
        self.stats.bump(spec.id, "failures")
        raise LLMError(f"{spec.id} ({spec.name}) failed: {last}")

    # ------------------------------------------------------------------ public API
    def call_json(self, spec: PromptSpec, schema: type[T], **variables: str) -> T:
        system, user = spec.render(**variables)
        self.stats.calls += 1
        self.stats.bump(spec.id, "calls")
        raw = self._generate(spec, system, user, json_mode=True)
        try:
            return schema.model_validate(parse_json_loose(raw))
        except (json.JSONDecodeError, ValidationError, ValueError) as first_error:
            self.stats.repairs += 1
            self.stats.bump(spec.id, "repairs")
            repair_user = (
                f"{user}\n\n---\nYour previous reply was rejected by the validator:\n{str(first_error)[:600]}\n\n"
                f"Previous reply:\n{raw[:3000]}\n\nReturn ONLY the corrected JSON object. No prose, no markdown fences."
            )
            raw2 = self._generate(spec, system, repair_user, json_mode=True)
            try:
                return schema.model_validate(parse_json_loose(raw2))
            except (json.JSONDecodeError, ValidationError, ValueError) as second_error:
                self.stats.invalid_after_repair += 1
                self.stats.bump(spec.id, "invalid")
                raise InvalidModelOutput(
                    f"{spec.id} ({spec.name}) returned invalid output twice: {str(second_error)[:300]}"
                ) from second_error


def build_llm_service(settings: Settings | None = None) -> LLMService:
    s = settings or get_settings()
    return LLMService(GeminiBackend(s), s)

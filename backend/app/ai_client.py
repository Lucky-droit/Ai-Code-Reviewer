import logging
import time

from .config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a senior software engineer.

Analyze the provided code and return ONLY valid JSON in this format:
{
  "issues": [
    {
      "type": "bug | security | performance",
      "line": number,
      "severity": "low | medium | high",
      "message": "short explanation"
    }
  ]
}

Rules:
- Do not include any text outside JSON
- Ensure valid JSON format
- Identify real issues only
- Be concise and accurate
"""


class AIClientError(RuntimeError):
    pass


NON_RETRYABLE_MARKERS = (
    "insufficient_quota",
    "invalid_api_key",
    "authentication_error",
    "invalid_request_error",
    "model_not_found",
    "permission denied",
)


class AIReviewerClient:
    def __init__(self) -> None:
        self.provider = settings.model_provider
        self.model_name = settings.model_name

    def review_code(self, code: str, language: str) -> str:
        user_prompt = (
            f"Language: {language}\n"
            "Code:\n"
            "```\n"
            f"{code}\n"
            "```"
        )

        if self.provider == "openai":
            return self._with_retry(self._review_openai, user_prompt)
        if self.provider == "anthropic":
            return self._with_retry(self._review_anthropic, user_prompt)

        raise AIClientError("Unsupported MODEL_PROVIDER. Use 'openai' or 'anthropic'.")

    def _is_retryable_error(self, exc: AIClientError) -> bool:
        message = str(exc).lower()
        return not any(marker in message for marker in NON_RETRYABLE_MARKERS)

    def _with_retry(self, fn, user_prompt: str) -> str:
        retries = max(settings.ai_max_retries, 0)

        for attempt in range(retries + 1):
            try:
                return fn(user_prompt)
            except AIClientError as exc:
                retryable = self._is_retryable_error(exc)
                if attempt >= retries or not retryable:
                    raise

                delay_seconds = min(2**attempt, 4)
                logger.warning(
                    "AI request failed (attempt %s/%s): %s. Retrying in %ss.",
                    attempt + 1,
                    retries + 1,
                    exc,
                    delay_seconds,
                )
                time.sleep(delay_seconds)

        raise AIClientError("AI request failed after retries.")

    def _review_openai(self, user_prompt: str) -> str:
        if not settings.openai_api_key:
            raise AIClientError("OPENAI_API_KEY is missing.")

        try:
            from openai import OpenAI

            client = OpenAI(
                api_key=settings.openai_api_key,
                timeout=settings.request_timeout_seconds,
                max_retries=0,
            )
            response = client.responses.create(
                model=self.model_name,
                input=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0,
            )
            text = response.output_text or ""
            logger.info("Raw model output (openai): %s", text)
            return text
        except Exception as exc:  # noqa: BLE001
            raise AIClientError(f"OpenAI request failed: {exc}") from exc

    def _review_anthropic(self, user_prompt: str) -> str:
        if not settings.anthropic_api_key:
            raise AIClientError("ANTHROPIC_API_KEY is missing.")

        if self.model_name.startswith("gpt-"):
            raise AIClientError(
                "MODEL_NAME is set to an OpenAI model for Anthropic provider. "
                "Use an Anthropic model like 'claude-3-5-sonnet-latest'."
            )

        try:
            from anthropic import Anthropic
            from anthropic import APIStatusError

            client = Anthropic(
                api_key=settings.anthropic_api_key,
                timeout=settings.request_timeout_seconds,
            )
            message = client.messages.create(
                model=self.model_name,
                max_tokens=1200,
                temperature=0,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_prompt}],
            )
            text_blocks: list[str] = []
            for block in message.content:
                if getattr(block, "type", "") == "text":
                    text_blocks.append(block.text)
            text = "\n".join(text_blocks).strip()
            logger.info("Raw model output (anthropic): %s", text)
            return text
        except APIStatusError as exc:
            status_code = getattr(exc, "status_code", "unknown")
            response_body = getattr(exc, "body", None)
            raise AIClientError(
                f"Anthropic request failed with status {status_code}: {response_body}"
            ) from exc
        except Exception as exc:  # noqa: BLE001
            raise AIClientError(f"Anthropic request failed: {exc}") from exc
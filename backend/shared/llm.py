from langchain_mistralai import ChatMistralAI
import time
import logging
from dotenv import load_dotenv
from typing import ClassVar

load_dotenv()

logger = logging.getLogger("contract_agent")


class ResilientChatMistralAI(ChatMistralAI):
    """
    ChatMistralAI wrapper with exponential backoff for rate limits (429 errors).
    Retries for up to 20 minutes with exponential backoff starting at 5 seconds.
    """

    # ✅ Marked as ClassVar so Pydantic ignores them
    MAX_WAIT_TIME: ClassVar[int] = 1200  # 20 minutes
    BASE_WAIT: ClassVar[int] = 5  # Start with 5 seconds
    MAX_ATTEMPTS: ClassVar[int] = 100  # Safety limit

    def _invoke_with_retry(self, invoke_func, *args, **kwargs):
        """
        Execute invoke_func with exponential backoff for 429 errors.
        """
        attempt = 0
        total_wait = 0

        while attempt < self.MAX_ATTEMPTS and total_wait < self.MAX_WAIT_TIME:
            try:
                return invoke_func(*args, **kwargs)

            except Exception as e:
                error_str = str(e)

                is_rate_limit = (
                    "429" in error_str
                    or "rate_limit" in error_str.lower()
                    or "rate limit" in error_str.lower()
                    or "Too Many Requests" in error_str
                )

                if is_rate_limit and attempt < self.MAX_ATTEMPTS - 1:
                    attempt += 1

                    # Exponential backoff: 5, 10, 20, 40, ...
                    wait_time = min(
                        self.BASE_WAIT * (2 ** (attempt - 1)),
                        self.MAX_WAIT_TIME - total_wait,
                    )

                    total_wait += wait_time

                    if total_wait >= self.MAX_WAIT_TIME:
                        logger.error(
                            f"Rate limit retry exceeded timeout. "
                            f"Total wait: {total_wait}s. Giving up."
                        )
                        raise Exception(
                            f"API rate limit exceeded after {total_wait}s of retries."
                        )

                    logger.warning(
                        f"[Rate Limit - Attempt {attempt}] "
                        f"Retrying in {wait_time}s... "
                        f"(Total wait: {total_wait}s / {self.MAX_WAIT_TIME}s)"
                    )

                    time.sleep(wait_time)

                else:
                    # Not a rate limit error OR max attempts reached
                    logger.error(f"LLM Error: {error_str}")
                    raise

        raise Exception(
            f"Max attempts ({self.MAX_ATTEMPTS}) reached. "
            f"Total wait: {total_wait}s / {self.MAX_WAIT_TIME}s"
        )

    def invoke(self, input, config=None, **kwargs):
        """Override invoke to add retry logic."""
        return self._invoke_with_retry(
            super().invoke,
            input,
            config=config,
            **kwargs,
        )

    def batch(self, inputs, config=None, **kwargs):
        """Override batch to add retry logic."""
        return self._invoke_with_retry(
            super().batch,
            inputs,
            config=config,
            **kwargs,
        )

    def stream(self, input, config=None, **kwargs):
        """Override stream to add retry logic."""
        return self._invoke_with_retry(
            super().stream,
            input,
            config=config,
            **kwargs,
        )


# ✅ Create resilient LLM instance
llm = ResilientChatMistralAI(
    model="mistral-medium",
    temperature=0,
    timeout=122000,  # ~2 hours
)
"""Fail fast if local env is incomplete."""

from ai_application.config import settings


def main() -> None:
    problems: list[str] = []
    if not settings.llm_base_url:
        problems.append("LLM_BASE_URL is empty")
    if not settings.llm_model:
        problems.append("LLM_MODEL is empty")
    if not settings.llm_api_key:
        problems.append("LLM_API_KEY is empty (ok for some local servers)")

    print(f"base_url = {settings.llm_base_url}")
    print(f"model    = {settings.llm_model}")
    print(f"timeout  = {settings.request_timeout_s}s")
    if problems:
        print("warnings:")
        for item in problems:
            print(f"  - {item}")
        return
    print("env looks complete")


if __name__ == "__main__":
    main()

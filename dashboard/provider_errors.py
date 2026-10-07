"""Safe provider diagnostics: never display exception text, URLs or payloads."""

import httpx
from google.genai import errors


def provider_diagnostic(exc):
    """Return only fixed, reviewed messages; inspect provider text privately."""
    if isinstance(exc, errors.APIError):
        code = exc.code
        message = (exc.message or "").lower()
        if "leaked" in message:
            return (
                "AI-KEY-BLOCKED",
                "Google blocked this API key as exposed. Create a replacement in Google AI Studio and replace GEMINI_API_KEY in Streamlit secrets.",
            )
        if (
            code == 401
            or "api key not valid" in message
            or "api_key_invalid" in message
        ):
            return (
                "AI-KEY-INVALID",
                "Google rejected the API key. Replace GEMINI_API_KEY with a valid key from your free-tier project.",
            )
        if code == 403:
            return (
                "AI-PERMISSION",
                "Google denied access. Check the key's Gemini API restrictions and the project's permissions in Google AI Studio.",
            )
        if code == 429:
            return (
                "AI-QUOTA",
                "Google's request or token quota was reached. Check your free-tier limits in Google AI Studio and retry after the limit resets.",
            )
        if code == 404:
            return (
                "AI-MODEL",
                "Google could not find the configured model. Check GEMINI_MODEL and its availability for your project.",
            )
        if code == 400 and exc.status == "FAILED_PRECONDITION":
            return (
                "AI-ELIGIBILITY",
                "Google reported an unmet account prerequisite. Check your project's free-tier eligibility and region in Google AI Studio. Keep billing unlinked to retain the no-cost setup.",
            )
        if code == 400:
            return (
                "AI-REQUEST",
                "Google rejected the application's request format. Report this diagnostic so the model/tool request can be corrected.",
            )
        if code == 402:
            return (
                "AI-BILLING",
                "Google reported a billing requirement. Verify that the selected project and model support your intended free-tier setup; there is no paid fallback.",
            )
        if isinstance(code, int) and code >= 500:
            return (
                "AI-SERVICE",
                "Google's service is temporarily unavailable. Retry later.",
            )
        return (
            "AI-PROVIDER",
            "Google rejected the request. Check the project's API access in Google AI Studio.",
        )
    if isinstance(exc, httpx.TimeoutException):
        return (
            "AI-TIMEOUT",
            "The Gemini request timed out. Retry later with a shorter question.",
        )
    if isinstance(exc, httpx.TransportError):
        return (
            "AI-CONNECTION",
            "The app could not connect to Gemini. Retry later; if this persists, check the deployment's network connection.",
        )
    return (
        "AI-INTERNAL",
        "The AI workspace encountered an application or SDK error. Report this diagnostic for investigation.",
    )

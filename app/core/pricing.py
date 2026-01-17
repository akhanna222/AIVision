"""
Cost calculation for vision model API calls.
Prices are per 1M tokens (input) as of 2025.
"""

# Pricing per 1M input tokens (USD)
MODEL_PRICING = {
    # Google Gemini
    "gemini-2.0-flash-exp": 0.0,  # Free tier
    "gemini-1.5-flash": 0.075,
    "gemini-1.5-pro": 1.25,

    # OpenAI
    "gpt-4o": 2.50,
    "gpt-4o-mini": 0.15,
    "gpt-4-turbo": 10.00,

    # Anthropic Claude
    "claude-sonnet-4-20250514": 3.00,
    "claude-haiku-4-20250514": 0.25,
    "claude-3-5-sonnet-20241022": 3.00,
    "claude-3-haiku-20240307": 0.25,
}

# Average tokens per page (estimated)
TOKENS_PER_PAGE = 1500


def estimate_tokens(pages: int) -> int:
    """Estimate token count based on page count."""
    return pages * TOKENS_PER_PAGE


def calculate_cost(model: str, tokens: int) -> float:
    """
    Calculate cost for API call.

    Args:
        model: Model name
        tokens: Number of tokens used

    Returns:
        Cost in USD
    """
    price_per_million = MODEL_PRICING.get(model, 0.0)
    return (tokens / 1_000_000) * price_per_million


def calculate_extraction_cost(model: str, pages: int, tokens: int = 0) -> tuple[float, int]:
    """
    Calculate extraction cost.

    Args:
        model: Vision model used
        pages: Number of pages processed
        tokens: Actual tokens if known, otherwise estimated

    Returns:
        Tuple of (cost_usd, tokens_used)
    """
    if tokens == 0:
        tokens = estimate_tokens(pages)

    cost = calculate_cost(model, tokens)
    return round(cost, 6), tokens


def get_model_price(model: str) -> float:
    """Get price per 1M tokens for model."""
    return MODEL_PRICING.get(model, 0.0)

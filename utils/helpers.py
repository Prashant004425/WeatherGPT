"""Small shared helpers reserved for future integrations."""


def format_location(location: str) -> str:
    """Keep user-entered locations readable in the interface."""
    return " ".join(location.strip().split()) or "Patna, Bihar, India"

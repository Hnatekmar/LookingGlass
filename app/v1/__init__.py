"""Version 1 API routes."""

# Shared whitelist of supported translation languages — prevents prompt injection
SUPPORTED_LANGUAGES = frozenset({
    # Europe
    "english", "french", "german", "italian", "portuguese", "spanish",
    "dutch", "polish", "russian", "ukrainian", "turkish", "greek",
    "czech", "hungarian", "romanian", "swedish", "norwegian", "danish",
    "finnish", "bulgarian", "croatian", "slovak", "slovenian",
    "lithuanian", "latvian", "estonian",
    # Asia
    "japanese", "korean", "chinese", "thai", "vietnamese",
    "indonesian", "malay", "tamil", "hindi", "bengali",
    "telugu", "marathi", "urdu", "arabic", "persian", "hebrew",
    "burmese", "khmer", "lao",
    # Africa
    "swahili", "afrikaans", "amharic", "yoruba", "zulu",
    # Special
    "none",
})

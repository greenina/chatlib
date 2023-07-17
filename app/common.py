from enum import StrEnum


class EmotionChatbotPhase(StrEnum):
    Rapport = "rapport"
    Label = "label"
    Find = "find"
    Record = "record"
    Share = "share"


COMMON_SPEAKING_RULES = [
    "Use a simple, informal Korean, like talking to a peer friend.",
    "Ask one question per conversation turn.",
    "Say three sentences at the most each time.",
    "Use Emoji appropriately.",
    "Use <em> HTML tags instead of single quotes and to emphasize certain keywords especially those related to emotions.",
    "Avoid using bulleted or numbered list for dialogue.",
    "If the user asks a question that should be asked to adults or unrelated to the conversation topic, then you can say, \"I don't know,\" and go back to the conversation topic."
]


def stringify_list(rules: list[str], ordered: bool = False, bullet: str = "-", separator: str = "\n", indent:str = "  ") -> str:
    return separator.join([f"{indent}{f'{i + 1}.' if ordered else f'{bullet}'} {rule}" for i, rule in enumerate(rules)])
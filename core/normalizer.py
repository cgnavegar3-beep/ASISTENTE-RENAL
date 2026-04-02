import re


class Normalizer:

    def normalize_text(self, text: str) -> str:
        if not isinstance(text, str):
            return ""

        text = text.lower().strip()
        text = re.sub(r"\s+", " ", text)
        text = re.sub(r"[^\w\s]", "", text)

        return text

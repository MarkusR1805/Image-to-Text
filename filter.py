# filter.py
import re

def remove_think_blocks(text):
    """
    Entfernt alles zwischen <think> und </think>, auch bei kaputten Tags.
    Beispiel: </think> am Anfang oder <think> am Ende.
    """
    # Suche nach Start und Ende
    think_start = re.search(r"<think>", text, flags=re.IGNORECASE)
    think_end = re.search(r"</think>", text, flags=re.IGNORECASE)

    if think_start and think_end:
        # Beide Tags vorhanden → Inhalt dazwischen entfernen
        start = think_start.start()
        end = think_end.end()
        text = text[:start] + text[end:]
    elif think_start:
        # Nur Opening-Tag vorhanden → Alles bis zum Ende entfernen
        start = think_start.start()
        text = text[:start]
    elif think_end:
        # Nur Closing-Tag vorhanden → Alles vom Anfang bis dahin entfernen
        end = think_end.end()
        text = text[end:]

    # Leerzeichen normalisieren
    text = re.sub(r"\s+", " ", text).strip()
    return text


def remove_quotes(text):
    return text.strip('"')


def remove_special_quotes(text):
    pattern = r"['´`*#]"
    cleaned_text = re.sub(pattern, "", text)
    return cleaned_text


def remove_numbers_with_dot(text):
    pattern = r"\b\d+\.\s*"
    cleaned_text = re.sub(pattern, "", text)
    return cleaned_text


def remove_words(text):
    pattern = r"^(css|markdown|scss|less|lua)\s*"
    cleaned_text = re.sub(pattern, "", text, flags=re.MULTILINE)
    return cleaned_text


def remove_double_spaces(text):
    cleaned_text = re.sub(r"\s{2,}", " ", text)
    return cleaned_text


def clean_text(text):
    # 1. Denkblock entfernen
    cleaned = remove_think_blocks(text)

    # 2. Intro entfernen, z. B.: "Certainly! I'll produce a text-to-image prompt: ..."
    cleaned = re.sub(r"^.*?:\s*", "", cleaned, flags=re.IGNORECASE).strip()

    # 3. Weitere Cleanups
    cleaned = remove_quotes(cleaned)
    cleaned = remove_special_quotes(cleaned)
    cleaned = remove_numbers_with_dot(cleaned)
    cleaned = remove_double_spaces(cleaned)
    cleaned = remove_words(cleaned)

    # 4. Zeilenumbrüche entfernen
    cleaned = cleaned.replace('\n', '')

    return cleaned.strip()

"""
Bengali / Banglish Transliteration Module.

Converts Romanized Bengali (Banglish) to proper Bengali script using a
high-coverage phonetic dictionary and token-level phonetic mapping.
"""
from __future__ import annotations

import logging
import re

logger = logging.getLogger("transliterate")

# Core Banglish vocabulary dictionary covering frequent conversational words
BANGLISH_DICT: dict[str, str] = {
    # Greetings & Common phrases
    "kemon": "কেমন",
    "acho": "আছো",
    "achis": "আছিস",
    "achen": "আছেন",
    "achi": "আছি",
    "bhalo": "ভালো",
    "valo": "ভালো",
    "dhonnobad": "ধন্যবাদ",
    "shagotom": "স্বাগতম",
    "shundor": "সুন্দর",
    "thik": "ঠিক",
    "thikache": "ঠিক আছে",
    "shotti": "সত্যি",
    "shotti?": "সত্যি?",

    # Pronouns
    "ami": "আমি",
    "tumi": "তুমি",
    "apni": "আপনি",
    "tui": "তুই",
    "se": "সে",
    "she": "সে",
    "tini": "তিনি",
    "amra": "আমরা",
    "tomra": "তোমরা",
    "apnara": "আপনারা",
    "tara": "তারা",
    "amader": "আমাদের",
    "tomader": "তোমাদের",
    "apnader": "আপনাদের",
    "amar": "আমার",
    "tomar": "তোমার",
    "apnar": "আপনার",
    "tar": "তার",
    "take": "তাকে",
    "amake": "আমাকে",
    "tomake": "তোমাকে",
    "apnake": "আপনাকে",

    # Interrogatives (Questions)
    "ki": "কী",
    "kire": "কীরে",
    "keno": "কেন",
    "kothay": "কোথায়",
    "kobe": "কবে",
    "kokhon": "কখন",
    "kivabe": "কীভাবে",
    "kar": "কার",
    "kake": "কাকে",
    "koto": "কত",
    "koita": "কয়টা",

    # Common Verbs & Conjugations
    "korcho": "করছো",
    "korchen": "করছেন",
    "korchis": "করছিস",
    "koro": "করো",
    "korun": "করুন",
    "korbo": "করবো",
    "korchi": "করছি",
    "korechi": "করেছি",
    "korlam": "করলাম",
    "kore": "করে",
    "hobe": "হবে",
    "hoy": "হয়",
    "hocche": "হচ্ছে",
    "hoyeche": "হয়েছে",
    "holo": "হলো",
    "asho": "এসো",
    "ashun": "আসুন",
    "ashbo": "আসবো",
    "aschi": "আসছি",
    "eshechi": "এসেছি",
    "elo": "এলো",
    "jabo": "যাবো",
    "jao": "যাও",
    "jan": "যান",
    "jachhi": "যাচ্ছি",
    "gechi": "গেছি",
    "gecho": "গেছো",
    "gelo": "গেলো",
    "bolo": "বলো",
    "bolun": "বলুন",
    "bolchi": "বলছি",
    "bolbo": "বলবো",
    "dekho": "দেখো",
    "dekhun": "দেখুন",
    "dekhbo": "দেখবো",
    "dekhechi": "দেখেছি",
    "shuno": "শোনো",
    "shunun": "শুনুন",
    "shunchi": "শুনছি",
    "khabo": "খাবো",
    "khao": "খাও",
    "khan": "খান",
    "kheyechi": "খেয়েছি",
    "ghuma": "ঘুমা",
    "ghumao": "ঘুমাও",
    "ghumiye": "ঘুমিয়ে",
    "bujhechi": "বুঝেছি",
    "bujhte": "বুঝতে",
    "bujho": "বুঝ",

    # Particles & Conjunctions
    "ha": "হ্যাঁ",
    "haa": "হ্যাঁ",
    "na": "না",
    "ar": "আর",
    "r": "আর",
    "ebong": "এবং",
    "kintu": "কিন্তু",
    "karon": "কারণ",
    "tai": "তাই",
    "jodi": "যদি",
    "tobu": "তবু",
    "tobuo": "তবুও",
    "o": "ও",
    "to": "তো",
    "ba": "বা",

    # General Nouns & Adjectives
    "bondhu": "বন্ধু",
    "shobai": "সবাই",
    "shob": "সব",
    "kichu": "কিছু",
    "shobkichu": "সবকিছু",
    "khobor": "খবর",
    "kaaj": "কাজ",
    "basha": "বাসা",
    "bari": "বাড়ি",
    "desh": "দেশ",
    "shomoy": "সময়",
    "din": "দিন",
    "raat": "রাত",
    "sokal": "সকাল",
    "shokal": "সকাল",
    "dupur": "দুপুর",
    "bikal": "বিকাল",
    "shondha": "সন্ধ্যা",
    "valobashi": "ভালোবাসি",
    "bhalobashi": "ভালোবাসি",
    "mon": "মন",
    "manush": "মানুষ",
    "bhai": "ভাই",
    "bon": "বোন",
    "apu": "আপু",
    "bhaiya": "ভাইয়া",
}


def is_bengali_script(text: str) -> bool:
    """Check if text contains Bengali Unicode characters."""
    return bool(re.search(r"[\u0980-\u09FF]", text))


def _transliterate_word(word: str) -> str:
    """Transliterate a single token."""
    clean_lower = word.lower()
    if clean_lower in BANGLISH_DICT:
        return BANGLISH_DICT[clean_lower]

    try:
        from indic_transliteration import sanscript
        from indic_transliteration.sanscript import transliterate

        # Basic phonetic normalization before ITRANS
        itrans_text = (
            clean_lower.replace("kh", "kh")
            .replace("ch", "ch")
            .replace("jh", "jh")
            .replace("th", "th")
            .replace("dh", "dh")
            .replace("ph", "ph")
            .replace("bh", "bh")
            .replace("sh", "sh")
            .replace("oo", "u")
            .replace("ee", "i")
        )
        converted = transliterate(itrans_text, sanscript.ITRANS, sanscript.BENGALI)
        if converted and is_bengali_script(converted):
            return converted
    except Exception as e:
        logger.debug("ITRANS fallback failed for '%s': %s", word, e)

    return word


def banglish_to_bengali(text: str) -> str:
    """
    Convert Banglish (Bengali written in Latin script) to Bengali script.
    Preserves punctuation, whitespace, and existing Bengali script.
    """
    if not text or not text.strip():
        return ""

    if is_bengali_script(text) and not re.search(r"[a-zA-Z]", text):
        return text

    # Tokenize preserving spaces and punctuation
    tokens = re.findall(r"\w+|[^\w\s]|\s+", text, re.UNICODE)
    result = []
    for token in tokens:
        if token.isalpha():
            result.append(_transliterate_word(token))
        else:
            result.append(token)

    return "".join(result)


def normalize_bengali(text: str) -> str:
    """Clean up whitespace and punctuation in Bengali text."""
    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    return text


def process_input(text: str) -> dict:
    """
    Main entry point: takes raw user input, returns both
    the original and the Bengali script version.
    """
    original = text.strip()
    bengali = normalize_bengali(banglish_to_bengali(original))
    return {
        "original": original,
        "bengali": bengali,
        "was_transliterated": not is_bengali_script(original),
    }

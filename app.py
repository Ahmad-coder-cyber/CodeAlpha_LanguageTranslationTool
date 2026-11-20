"""
CodeAlpha AI Internship - Task 1: Language Translation Tool

A small Flask web app. The user types text, picks a source and a target
language, and the text is sent to Google Translate (through the
`deep-translator` library, which needs no API key) and the translation is
shown on the page. If Google refuses the request (for example "too many
requests"), the app automatically retries with the free MyMemory API. The
page also has a Copy button and a Speak (text-to-speech) button.

Run:
    pip install -r requirements.txt
    python app.py
Then open http://127.0.0.1:5000
"""

import html
import json
import re
import urllib.parse
import urllib.request

from flask import Flask, jsonify, render_template, request

try:
    from deep_translator import GoogleTranslator
except ImportError:  # keeps the app importable so the error is shown nicely
    GoogleTranslator = None

app = Flask(__name__)

# Google Translate accepts at most 5000 characters per request.
MAX_CHARS = 5000

# language code -> display name. "auto" is only valid as a *source* language.
LANGUAGES = {
    "auto": "Detect language",
    "en": "English",
    "ur": "Urdu",
    "hi": "Hindi",
    "ar": "Arabic",
    "fa": "Persian",
    "bn": "Bengali",
    "pa": "Punjabi",
    "fr": "French",
    "de": "German",
    "es": "Spanish",
    "it": "Italian",
    "pt": "Portuguese",
    "ru": "Russian",
    "tr": "Turkish",
    "nl": "Dutch",
    "id": "Indonesian",
    "ja": "Japanese",
    "ko": "Korean",
    "zh-CN": "Chinese (Simplified)",
}


# ----------------------------------------------------------- backup translator
# Google sometimes blocks requests with "too many requests" (shared Wi-Fi, VPN,
# busy network). When that happens the app retries with MyMemory, a second free
# translation service that needs no API key. It accepts at most 500 bytes per
# request, so long text is cut into small pieces and joined back together.

MYMEMORY_URL = "https://api.mymemory.translated.net/get"
MYMEMORY_LIMIT = 450  # bytes per piece, kept under MyMemory's limit of 500


def _size(text):
    return len(text.encode("utf-8"))


def _units(text, limit):
    """Yield sentences, or words / character cuts for very long sentences."""
    for sentence in re.split(r"(?<=[.!?۔।])\s+", text):
        if _size(sentence) <= limit:
            yield sentence
            continue
        for word in sentence.split(" "):
            while _size(word) > limit:  # extremely long word without spaces
                cut = len(word)
                while _size(word[:cut]) > limit:
                    cut -= 1
                yield word[:cut]
                word = word[cut:]
            if word:
                yield word


def split_text(text, limit=MYMEMORY_LIMIT):
    """Pack sentences into pieces of at most `limit` bytes."""
    pieces, current = [], ""
    for unit in _units(text, limit):
        candidate = f"{current} {unit}" if current else unit
        if _size(candidate) <= limit:
            current = candidate
        else:
            pieces.append(current)
            current = unit
    if current:
        pieces.append(current)
    return pieces


def translate_mymemory(text, source, target):
    """Translate with the free MyMemory API (keeps the original line breaks)."""
    langpair_source = "Autodetect" if source == "auto" else source
    translated_lines = []
    for line in text.split("\n"):
        if not line.strip():
            translated_lines.append("")
            continue
        parts = []
        for piece in split_text(line.strip()):
            query = urllib.parse.urlencode(
                {"q": piece, "langpair": f"{langpair_source}|{target}"})
            request_obj = urllib.request.Request(
                f"{MYMEMORY_URL}?{query}", headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(request_obj, timeout=15) as response:
                data = json.load(response)
            result = (data.get("responseData") or {}).get("translatedText") or ""
            if str(data.get("responseStatus")) != "200" or not result \
                    or "MYMEMORY WARNING" in result.upper():
                raise RuntimeError(result or "MyMemory returned an error")
            parts.append(html.unescape(result))
        translated_lines.append(" ".join(parts))
    return "\n".join(translated_lines)


@app.route("/")
def index():
    return render_template("index.html", languages=LANGUAGES)


@app.route("/translate", methods=["POST"])
def translate():
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    source = data.get("source", "auto")
    target = data.get("target", "en")

    if not text:
        return jsonify(error="Please enter some text to translate."), 400
    if len(text) > MAX_CHARS:
        return jsonify(error=f"Text is too long (max {MAX_CHARS} characters)."), 400
    if source not in LANGUAGES or target not in LANGUAGES or target == "auto":
        return jsonify(error="Invalid language selection."), 400
    translated, engine, errors = None, None, []

    # 1) Google Translate through deep-translator
    if GoogleTranslator is not None:
        try:
            translated = GoogleTranslator(source=source, target=target).translate(text)
            engine = "Google"
        except Exception as exc:  # network problems, rate limits, etc.
            errors.append(f"Google: {str(exc)[:120]}")
    else:
        errors.append("Google: deep-translator is not installed")

    # 2) Backup: MyMemory
    if not translated:
        try:
            translated = translate_mymemory(text, source, target)
            engine = "MyMemory"
        except Exception as exc:
            errors.append(f"MyMemory: {str(exc)[:120]}")

    if not translated:
        return jsonify(error="Translation failed. " + " | ".join(errors)), 502

    return jsonify(translation=translated, target=target, engine=engine)


if __name__ == "__main__":
    app.run(debug=True)

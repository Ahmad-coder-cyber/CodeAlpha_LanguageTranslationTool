# CodeAlpha_LanguageTranslationTool

**CodeAlpha AI Internship, Task 1: Language Translation Tool**

A simple web app where you type text, choose a source and a target language, and get the translation instantly.

## Features

- Text box with a live character counter (max 5000 characters)
- Source language (with **auto-detect**) and target language dropdowns, 20 languages including Urdu, Hindi and Arabic
- Swap button to flip the language pair
- Translation through Google Translate, using the `deep-translator` library (no API key needed)
- **Automatic backup**: if Google blocks the request ("too many requests"), the app retries with the free MyMemory API
- **Copy** button (copies the translation to the clipboard)
- **Speak** button (text-to-speech using the browser's built-in Web Speech API)
- Clear error messages (empty text, too long, no internet)

## Tech stack

- Python 3.9+
- Flask (backend and UI server)
- deep-translator (Google Translate wrapper)
- HTML, CSS and vanilla JavaScript (frontend)

## How it works

1. The user enters text and picks languages in the browser.
2. JavaScript sends `{text, source, target}` as JSON to the `/translate` endpoint.
3. Flask passes the text to `GoogleTranslator(source, target).translate(text)`. If that fails, it calls the MyMemory API instead (long text is split into small pieces because MyMemory accepts at most 500 bytes per request).
4. The translated text comes back as JSON and is shown in the output box.

## Setup and run

```bash
git clone https://github.com/<your-username>/CodeAlpha_LanguageTranslationTool.git
cd CodeAlpha_LanguageTranslationTool

python -m venv venv
# Windows:  venv\Scripts\activate
# Mac/Linux: source venv/bin/activate

pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000 in your browser. An internet connection is required for translation.

## Project structure

```
CodeAlpha_LanguageTranslationTool/
├── app.py              # Flask app and /translate API
├── templates/
│   └── index.html      # User interface
├── requirements.txt
└── README.md
```

## Using the official Google Cloud Translation API instead

`deep-translator` is used here so the project runs without billing or keys. To use the official API, replace the translate call in `app.py` with `google-cloud-translate`:

```python
from google.cloud import translate_v2 as translate
client = translate.Client()  # needs GOOGLE_APPLICATION_CREDENTIALS set
result = client.translate(text, source_language=source if source != "auto" else None,
                          target_language=target)
translated = result["translatedText"]
```

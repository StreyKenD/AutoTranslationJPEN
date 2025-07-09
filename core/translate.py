from deep_translator import GoogleTranslator
from typing import List
import logging

def translate_google(text):
    try:
        result = GoogleTranslator(source='auto', target='en').translate(text)
        logging.debug(f'Translated: {text} -> {result}')
        return result
    except Exception as e:
        logging.error(f"Google Translate error: {e}, text={text}")
        return ""

def translate_batch(texts: List[str]) -> List[str]:
    results = []
    for t in texts:
        try:
            result = GoogleTranslator(source='auto', target='en').translate(t)
            logging.debug(f'Translated: {t} -> {result}')
            results.append(result)
        except Exception as e:
            logging.error(f"Google Translate batch error: {e}, text={t}")
            results.append("")
    return results

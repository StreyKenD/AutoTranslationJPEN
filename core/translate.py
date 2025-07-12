from deep_translator import GoogleTranslator
from typing import List
import logging


def translate_batch(texts: List[str]) -> List[str]:
    results = []
    for t in texts:
        try:
            result = GoogleTranslator(source='ja', target='en').translate(t)
            logging.debug(f'Translated: {t} -> {result}')
            results.append(result)
        except Exception as e:
            logging.error(f"Google Translate batch error: {e}, text={t}")
            results.append("")
    return results

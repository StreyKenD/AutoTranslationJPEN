import pytesseract
import mss
import time
import requests
import csv
import os
import tkinter as tk
import keyboard
import re
from PIL import Image, ImageOps

# Configuracao do Tesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"

# DeepL API Key
DEEPL_API_KEY = "4a5103dd-9961-49ad-b52d-8a0fc95c1845:fx"

# Regiao da tela para OCR
region = {"top": 118, "left": 575, "width": 768, "height": 915}

# Arquivo CSV
csv_file = "historico_traducoes.csv"
if not os.path.exists(csv_file):
    with open(csv_file, "w", newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["Japonês", "Inglês"])

# In-memory cache for session
translated_cache = set()
def load_cache():
    if os.path.exists(csv_file):
        with open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader, None)
            for row in reader:
                if row and row[0].strip():
                    translated_cache.add(row[0].strip())
load_cache()

def ja_traduzido(texto_original):
    return texto_original.strip() in translated_cache

def texto_valido_para_traducao(texto):
    texto = texto.strip()
    if not texto:
        return False
    texto_limpo = texto.replace(" ", "").replace("\n", "")
    if len(texto_limpo) < 3:
        return False
    if re.search(r'[\u3040-\u30FF\u4E00-\u9FFF]', texto):
        return True
    if re.search(r'[a-zA-Z]{3,}', texto):
        return True
    simbolos = re.findall(r'[^a-zA-Z0-9\u3040-\u30FF\u4E00-\u9FFF\s.,!?ー…。、！？]', texto)
    if len(simbolos) > len(texto) * 0.4:
        return False
    return False

def translate_deepl(text):
    if not text.strip():
        return ""
    url = "https://api-free.deepl.com/v2/translate"
    params = {
        "auth_key": DEEPL_API_KEY,
        "text": text,
        "source_lang": "JA",
        "target_lang": "EN"
    }
    response = requests.post(url, data=params)
    if response.status_code == 200:
        return response.json()["translations"][0]["text"]
    else:
        print("Erro na tradução:", response.text)
        return ""

def capture_region():
    with mss.mss() as sct:
        img = sct.grab(region)
        pil_img = Image.frombytes('RGB', img.size, img.rgb)
        # Optional: improve OCR accuracy
        pil_img = ImageOps.grayscale(pil_img)
        pil_img = ImageOps.autocontrast(pil_img)
        return pil_img

def get_blocos_de_texto(img):
    custom_config = r'--oem 3 --psm 6'
    data = pytesseract.image_to_data(img, lang="jpn_vert+eng", config=custom_config, output_type=pytesseract.Output.DICT)
    blocos = {}
    for i in range(len(data['text'])):
        palavra = data['text'][i].strip()
        if not palavra:
            continue
        block_id = data['block_num'][i]
        x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
        centro = (x + w // 2, y + h // 2)
        if block_id not in blocos:
            blocos[block_id] = {"texto": palavra, "posicoes": [centro]}
        else:
            blocos[block_id]["texto"] += " " + palavra
            blocos[block_id]["posicoes"].append(centro)
    resultados = []
    for bloco in blocos.values():
        if not texto_valido_para_traducao(bloco["texto"]):
            continue
        x_medio = sum(p[0] for p in bloco["posicoes"]) // len(bloco["posicoes"])
        y_medio = sum(p[1] for p in bloco["posicoes"]) // len(bloco["posicoes"])
        resultados.append((bloco["texto"].strip(), (x_medio, y_medio)))
    return resultados

root = tk.Tk()
root.overrideredirect(True)
root.attributes("-topmost", True)
root.attributes("-transparentcolor", "white")
root.configure(bg="white")
labels = []

# Real-time translation loop
def atualizar_traducao():
    global labels
    root.withdraw()
    time.sleep(0.05)
    imagem = capture_region()
    root.deiconify()
    for l in labels:
        l.destroy()
    labels.clear()
    blocos = get_blocos_de_texto(imagem)
    for texto, pos in blocos:
        if ja_traduzido(texto):
            continue
        traducao = translate_deepl(texto)
        if traducao:
            lbl = tk.Label(root, text=traducao, font=("Arial", 14), bg="black", fg="white", wraplength=300, justify="left")
            lbl.place(x=pos[0] + 100, y=pos[1] - 50)
            labels.append(lbl)
            with open(csv_file, "a", newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([texto, traducao])
            translated_cache.add(texto)
    root.after(1000, atualizar_traducao)  # Atualiza a cada 1 segundo

keyboard.add_hotkey('esc', lambda: root.destroy())
atualizar_traducao()
root.mainloop()

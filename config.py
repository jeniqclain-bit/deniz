import json
from pathlib import Path
from aiogram.fsm.state import State, StatesGroup

BASE = Path(__file__).parent

def lj(f):
    with open(BASE / "data" / f, encoding="utf-8") as fp:
        return json.load(fp)

# JSON verileri
kelimeler = lj("kelimeler.json")
bilmeceler = lj("bilmeceler.json")
bilgi_data = lj("bilgi.json")
baskentler = lj("baskent.json")
plakalar = lj("plaka.json")
sozler = lj("sozler.json")
siirler = lj("siirler.json")
emojiler = lj("emoji.json")
dy_data = lj("dogruyanlis.json")
eser_data = lj("eser_yazar.json")
itiraf_data = lj("itiraf.json")
cesaret_data = lj("cesaret.json")

kelime_set = set(w["kelime"].lower() for w in kelimeler)

# Global değişkenler
cooldowns = {}
bot_username = ""
openai_client = None
SCORE_FILE = BASE / "scores.json"

# FSM States
class GS(StatesGroup):
    kelime_anlatma = State()
    bosluk_doldurma = State()
    kelime_sarmali = State()
    hizli_mat = State()
    sayi = State()
    bilgi_y = State()
    bayrak = State()
    kelime_zinciri = State()
    baskent = State()
    plaka = State()
    xo = State()
    dogru_yanlis = State()
    bilmece_st = State()
    emoji_st = State()
    eser = State()
    sicak_soguk = State()
    duello = State()
    ai = State()
    fark_bulmaca = State()
    sudoku = State()

# AI yanıtları
ai_kw = {
    "merhaba": "Merhaba! Ne sormak istersin? 😊",
    "nasılsın": "İyiyim, teşekkür ederim! Sen nasılsın?",
    "naber": "İyilik! Senden naber?",
    "selam": "Selam! Nasıl yardımcı olabilirim?",
    "teşekkür": "Rica ederim! 😊",
    "sağol": "Ne demek, her zaman! 🙌",
    "kim": "Ben bir oyun botuyum! Benimle oyun oynayabilirsin.",
    "adın": "Benim adım oyun botu! 🎮",
    "hava": "Hava durumunu maalesef bilmiyorum ama güzel bir gün olduğunu tahmin ediyorum! ☀️",
    "seviyorum": "Ben de seni seviyorum! 💕",
    "tamam": "Tamam! Başka bir sorun var mı?",
    "yardım": "Sana nasıl yardımcı olabilirim? Oyun oynamak için /baslat yaz!",
}
ai_gen = [
    "Hmm, ilginç bir soru! 🤔", "Bu konuda düşünmem lazım...",
    "Güzel soru! Ama cevabımı beğenmeyebilirsin 😄",
    "Bunu bilmiyorum ama öğrenebilirim!",
    "Vay canına, hiç düşünmemiştim! 😲", "Hayat çok güzel, değil mi? 🌸",
    "Sana katılıyorum! 👍", "Bu konuda hemfikiriz! 🤝",
    "İlginç bir bakış açısı! 💡", "Daha fazla bilgiye ihtiyacım var 📚",
]

# Fark bulmaca çiftleri
FARK_PAIRS = [
    ("🍎","🍏"),("🐶","🐕"),("😊","😄"),("🌸","🌺"),("⭐","🌟"),
    ("🔵","🔷"),("🟢","🟩"),("🟡","🟨"),("❤️","💗"),("🐱","🐈"),
    ("🌞","☀️"),("🌛","🌜"),("🎵","🎶"),("📘","📗"),("🟠","🟧"),
    ("🔴","🟥"),("💜","🟣"),("🐸","🐢"),("🦊","🐺"),("🎁","🎀")
]

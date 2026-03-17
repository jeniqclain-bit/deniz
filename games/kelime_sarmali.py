import random
import asyncio
from pathlib import Path
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup as IKM, InlineKeyboardButton as IKB, FSInputFile
from aiogram.fsm.context import FSMContext
from config import GS, BASE
from utils import add_score, get_scores_text, flood_ok

router = Router()

# Kelime sarmalı verilerini yükle
def load_kelime_sarmali():
    file_path = BASE / "data" / "kelimesarmalı.txt"
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        valid_words = []
        for line in lines:
            word = line.strip()
            if (word and 
                len(word) >= 3 and 
                len(word) <= 8 and 
                word.isalpha() and
                " " not in word and
                "/" not in word):
                valid_words.append(word.lower())
        
        return valid_words
    except FileNotFoundError:
        print(f"⚠️ {file_path} bulunamadı!")
        return []

KELIME_SARMALI_LIST = load_kelime_sarmali()

GIF_PATH = BASE / "data" / "giphy.gif"

def get_welcome_text():
    return (
        "~~ ♻️ Kelime sarmalına hoşgeldiniz! ♻️ ~~\n\n"
        "✏️ Bir kelime yazarak Başlatınız.\n"
        "📖 Daha sonra botun vereceği kelimelerin son harfi ile yeni kelimeler yazınız.\n"
        "📝⚠️ Uyarı: Bir kez kullanılan kelime bir daha kullanılamaz."
    )

def get_restart_kb():
    return IKM(inline_keyboard=[[IKB(text="🔄 Yeniden Başlat", callback_data="ks_restart")]])

async def start_kelime_sarmali(msg, state, caller=None):
    if not KELIME_SARMALI_LIST:
        await msg.answer("❌ Kelime veritabanı boş! data/kelimesarmalı.txt dosyasını kontrol edin.")
        return
    
    chat_id = msg.chat.id
    
    await state.set_state(GS.kelime_sarmali)
    await state.update_data(
        game="kelime_sarmali",
        tur=0,
        can=0.3,
        last_letter=None,
        waiting_start=True,
        used_words=set(),
        timer_task=None,
        last_bot_msg_id=None
    )
    
    # GIF ile birlikte gönder
    if GIF_PATH.exists():
        gif = FSInputFile(GIF_PATH)
        sent = await msg.answer_animation(gif, caption=get_welcome_text())
        await state.update_data(welcome_msg_id=sent.message_id)
        return sent
    else:
        sent = await msg.answer(get_welcome_text())
        await state.update_data(welcome_msg_id=sent.message_id)
        return sent

async def send_game_message(msg, state, word, tur, required_letter, reply_to_msg=None):
    """Oyun mesajını gönder ve timer başlat"""
    
    # Önceki timer'ı iptal et
    data = await state.get_data()
    old_timer = data.get("timer_task")
    if old_timer:
        old_timer.cancel()
    
    text = (
        f"🏁 Tur: {tur}\n"
        f"💫 Can ➔ 0.3\n\n"
        f"📖 {word}\n"
        f"✍️ {required_letter} ile başlayan bir şey yazınız!"
    )
    
    # Cevaba yanıt olarak gönder
    if reply_to_msg:
        sent = await reply_to_msg.reply(text)
    else:
        sent = await msg.answer(text)
    
    # Yeni timer başlat
    async def timeout_callback():
        await asyncio.sleep(15)
        current_data = await state.get_data()
        if (current_data.get("game") == "kelime_sarmali" and 
            current_data.get("tur") == tur):
            await end_game(msg, state, timeout=True)
    
    timer_task = asyncio.create_task(timeout_callback())
    await state.update_data(timer_task=timer_task, current_word=word, tur=tur, last_bot_msg_id=sent.message_id)
    
    return sent

async def end_game(msg, state, timeout=False):
    """Oyunu bitir ve skor göster"""
    chat_id = msg.chat.id
    data = await state.get_data()
    
    # Timer'ı iptal et
    timer = data.get("timer_task")
    if timer:
        timer.cancel()
    
    used_words = data.get("used_words", set())
    used_count = len(used_words)
    
    if timeout:
        text = f"⌛️ 15 saniyelik süre bitti, toplamda {used_count} kelime kullanıldı!\n\n"
    else:
        text = f"🎉 Oyun bitti! Toplamda {used_count} kelime kullanıldı!\n\n"
    
    text += "~~ 🎖 SKOR LİSTESİ 🎖 ~~\n\n"
    text += get_scores_text(chat_id)
    
    await state.clear()
    await msg.answer(text, reply_markup=get_restart_kb())

@router.callback_query(F.data == "ks_restart")
async def restart_game(cb: CallbackQuery, state: FSMContext):
    if cb.message.chat.type == "private":
        await cb.answer("🚫 Sadece gruplarda kullanılabilir!", show_alert=True)
        return
    
    await start_kelime_sarmali(cb.message, state)
    await cb.answer()

@router.message(GS.kelime_sarmali)
async def kelime_sarmali_answer(msg: Message, state: FSMContext):
    if msg.chat.type == "private":
        return
    
    chat_id = msg.chat.id
    text = msg.text.strip().lower() if msg.text else ""
    
    # Komut kontrolü
    if text.startswith('/'):
        return
    
    # Boşluk kontrolü (tek kelime mi?)
    if ' ' in text:
        return
    
    if not flood_ok(msg.from_user.id):
        return
    
    data = await state.get_data()
    waiting_start = data.get("waiting_start", True)
    last_letter = data.get("last_letter")
    tur = data.get("tur", 0)
    used_words = data.get("used_words", set())
    
    # Başlangıç: Herhangi bir kelime ile başla
    if waiting_start:
        # Veri setinde var mı kontrol et - yoksa sessizce geç
        if text not in KELIME_SARMALI_LIST:
            return  # Sessizce geç
        
        # Daha önce kullanıldı mı kontrol et
        if text in used_words:
            await msg.reply(f"❌ {text.upper()} kelimesi daha önce kullanılmış!")
            return
        
        used_words = {text}
        await state.update_data(used_words=used_words)
        
        new_letter = text[-1]
        
        # Bot cevabı - son harfle başlayan rastgele kelime
        bot_words = [w for w in KELIME_SARMALI_LIST 
                     if w.startswith(new_letter) and w not in used_words]
        
        if not bot_words:
            await msg.reply(f"🤖 '{new_letter.upper()}' ile kelime bulamadım. Kazandın! 🎉")
            await end_game(msg, state)
            return
        
        bw = random.choice(bot_words)
        used_words.add(bw)
        bot_new_letter = bw[-1]
        
        await state.update_data(
            waiting_start=False, 
            last_letter=bot_new_letter,
            used_words=used_words
        )
        # Kullanıcının mesajına yanıt olarak gönder
        await send_game_message(msg, state, bw, 1, bot_new_letter, reply_to_msg=msg)
        return
    
    # Normal oyun akışı
    required_letter = last_letter
    
    # Son harf kontrolü - yanlışsa sessizce geç
    if not text.startswith(required_letter):
        return  # Sessizce geç
    
    # Veri setinde var mı - yoksa sessizce geç
    if text not in KELIME_SARMALI_LIST:
        return  # Sessizce geç
    
    # Daha önce kullanıldı mı - UYARI GÖSTER
    if text in used_words:
        await msg.reply(f"❌ {text.upper()} kelimesi daha önce kullanılmış!")
        return
    
    # Doğru cevap
    used_words.add(text)
    new_letter = text[-1]
    tur += 1
    
    # Puan ekle
    add_score(msg.chat.id, msg.from_user.id, msg.from_user.first_name)
    
    # Bot cevabı
    bot_words = [w for w in KELIME_SARMALI_LIST 
                 if w.startswith(new_letter) and w not in used_words]
    
    if not bot_words:
        await msg.reply(f"✅ Güzel! +1 puan\n\n🤖 '{new_letter.upper()}' ile kelime bulamadım. Kazandın! 🎉")
        await end_game(msg, state)
        return
    
    bw = random.choice(bot_words)
    used_words.add(bw)
    bot_new_letter = bw[-1]
    
    await state.update_data(
        last_letter=bot_new_letter,
        used_words=used_words
    )
    # Kullanıcının mesajına yanıt olarak gönder
    await send_game_message(msg, state, bw, tur, bot_new_letter, reply_to_msg=msg)

import random
import time
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from config import GS
from utils import add_score, is_valid_answer, flood_ok

router = Router()

# Veri dosyasından kelimeleri yükle
def load_words():
    kolay = []
    zor = []
    current_section = None

    try:
        with open("boslukdoldurma.txt", "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line == "#kolay":
                    current_section = "kolay"
                elif line == "#zor":
                    current_section = "zor"
                elif line and "|" in line:
                    kelime, cumle = line.split("|", 1)
                    if current_section == "kolay":
                        kolay.append({"kelime": kelime.strip(), "cumle": cumle.strip()})
                    elif current_section == "zor":
                        zor.append({"kelime": kelime.strip(), "cumle": cumle.strip()})
    except FileNotFoundError:
        pass

    return {"kolay": kolay, "zor": zor}

WORDS = load_words()

# Round seçim klavyesi
def round_selection_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="15", callback_data="bd_round_15"),
            InlineKeyboardButton(text="30", callback_data="bd_round_30"),
            InlineKeyboardButton(text="45", callback_data="bd_round_45"),
            InlineKeyboardButton(text="60", callback_data="bd_round_60"),
            InlineKeyboardButton(text="75", callback_data="bd_round_75"),
            InlineKeyboardButton(text="100", callback_data="bd_round_100"),
        ],
        [
            InlineKeyboardButton(text="125", callback_data="bd_round_125"),
            InlineKeyboardButton(text="150", callback_data="bd_round_150"),
            InlineKeyboardButton(text="250", callback_data="bd_round_250"),
            InlineKeyboardButton(text="500", callback_data="bd_round_500"),
            InlineKeyboardButton(text="750", callback_data="bd_round_750"),
            InlineKeyboardButton(text="1000", callback_data="bd_round_1000"),
        ],
        [
            InlineKeyboardButton(text="Sonsuz? ♾", callback_data="bd_round_sonsuz"),
        ]
    ])

# Zorluk seçim klavyesi
def difficulty_kb(rounds):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="😊 Kolay (x1 puan)", callback_data=f"bd_diff_kolay_{rounds}"),
            InlineKeyboardButton(text="💣 Zor (x4 puan)", callback_data=f"bd_diff_zor_{rounds}"),
        ]
    ])

# Oyun içi klavye (Pas butonu)
def game_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Pas ♻️", callback_data="bd_pas")]
    ])

# Tekrar oyna klavyesi
def replay_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Tekrar Oyna 🧩", callback_data="bd_replay")]
    ])

# Kelimeyi karıştır ve göster
def prepare_word_display(kelime):
    harfler = list(kelime)
    random.shuffle(harfler)
    harfler_str = " ".join(harfler)

    # İlk harf görünür, diğerleri _
    masked = kelime[0] + " " + " ".join(["_"] * (len(kelime) - 1))

    return harfler_str, masked

# Yeni round başlat
async def start_new_round(message_or_callback, state: FSMContext, edit=False):
    data = await state.get_data()
    difficulty = data.get("difficulty", "kolay")
    current_round = data.get("round", 1)
    total_rounds = data.get("total_rounds", 15)
    score = data.get("score", 0)

    word_list = WORDS.get(difficulty, [])
    if not word_list:
        text = "❌ Kelime listesi boş!"
        if edit and hasattr(message_or_callback, 'message'):
            await message_or_callback.message.edit_text(text)
        else:
            await message_or_callback.answer(text)
        return

    w = random.choice(word_list)
    kelime = w["kelime"]
    harfler_str, masked = prepare_word_display(kelime)

    # Puan hesaplama
    base_puan = round(len(kelime) * 0.1, 1)
    if difficulty == "zor":
        base_puan *= 4

    await state.update_data(
        answer=kelime,
        current_puan=base_puan,
        last_word_time=time.time()
    )

    rounds_display = f"{current_round}/{total_rounds}" if total_rounds != -1 else f"{current_round}/♾"

    text = (
        f"🏆 Zorluk: {difficulty}\n"
        f"💵 Puan: {score}\n"
        f"📌 Round: {rounds_display}\n"
        f"📚 {len(kelime)} harf: {harfler_str}\n"
        f"🎲 {masked}"
    )

    if edit and hasattr(message_or_callback, 'message'):
        await message_or_callback.message.edit_text(text, reply_markup=game_kb())
    else:
        await message_or_callback.answer(text, reply_markup=game_kb())

# Oyunu başlat - Round seçim ekranı
async def start_bosluk_doldurma(msg, state, caller=None):
    await state.set_state(GS.bosluk_doldurma_setup)
    await state.update_data(game="bosluk_doldurma", last_game_data=None)

    return await msg.answer(
        "📍 Can, oyun kaç round olsun?",
        reply_markup=round_selection_kb()
    )

# Round seçimi callback
@router.callback_query(F.data.startswith("bd_round_"))
async def select_round(callback: CallbackQuery, state: FSMContext):
    round_str = callback.data.replace("bd_round_", "")

    if round_str == "sonsuz":
        rounds = -1
        display = "♾"
    else:
        rounds = int(round_str)
        display = str(rounds)

    await state.update_data(total_rounds=rounds)

    await callback.message.edit_text(
        f"🎯 Can, {display} round oyunun zorluğu ne olsun?",
        reply_markup=difficulty_kb(round_str)
    )
    await callback.answer()

# Zorluk seçimi callback
@router.callback_query(F.data.startswith("bd_diff_"))
async def select_difficulty(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    difficulty = parts[2]  # kolay veya zor

    data = await state.get_data()
    total_rounds = data.get("total_rounds", 15)

    await state.set_state(GS.bosluk_doldurma)
    await state.update_data(
        difficulty=difficulty,
        round=1,
        score=0,
        last_game_data={
            "difficulty": difficulty,
            "total_rounds": total_rounds
        }
    )

    await callback.answer()
    await start_new_round(callback, state, edit=True)

# Pas butonu callback
@router.callback_query(F.data == "bd_pas")
async def pass_word(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    last_word_time = data.get("last_word_time", 0)
    elapsed = time.time() - last_word_time

    if elapsed < 10:
        remaining = int(10 - elapsed)
        await callback.answer(
            f"⏳ Pas geçmek için 10 saniye geçmeli, şu anda geçen: {int(elapsed)} saniye",
            show_alert=True
        )
        return

    answer = data.get("answer", "???")
    difficulty = data.get("difficulty", "kolay")
    current_round = data.get("round", 1)
    total_rounds = data.get("total_rounds", 15)
    score = data.get("score", 0)

    # Oyun bitti mi kontrol et
    if total_rounds != -1 and current_round >= total_rounds:
        await state.clear()
        await callback.message.edit_text(
            f"🌪 Can pas geçti! Doğru cevap ➔ {answer} idi.\n\n"
            f"🏁 Oyun Bitti!\n"
            f"🏆 Toplam Puan: {score}",
            reply_markup=replay_kb()
        )
        return

    # Sonraki round
    await state.update_data(round=current_round + 1)

    # Pas mesajını göster ve yeni kelimeye geç
    await callback.message.edit_text(
        f"🌪 Can pas geçti! Doğru cevap ➔ {answer} idi."
    )

    # Kısa bir gecikme olmadan direkt yeni round başlat
    await start_new_round(callback, state, edit=False)
    await callback.answer()

# Tekrar oyna callback
@router.callback_query(F.data == "bd_replay")
async def replay_game(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    last_game_data = data.get("last_game_data")

    if last_game_data:
        await state.set_state(GS.bosluk_doldurma)
        await state.update_data(
            difficulty=last_game_data["difficulty"],
            total_rounds=last_game_data["total_rounds"],
            round=1,
            score=0
        )
        await callback.answer()
        await start_new_round(callback, state, edit=True)
    else:
        # Eğer önceki oyun verisi yoksa baştan başla
        await callback.message.edit_text(
            "📍 Can, oyun kaç round olsun?",
            reply_markup=round_selection_kb()
        )
        await state.set_state(GS.bosluk_doldurma_setup)
        await callback.answer()

# Cevap kontrolü
@router.message(GS.bosluk_doldurma)
async def bosluk_doldurma_answer(msg: Message, state: FSMContext):
    text = msg.text.strip() if msg.text else ""

    # /iptal komutu
    if text.lower() == "/iptal":
        await state.clear()
        await msg.answer(
            "🚫 Oyun İptal Edildi! ⟶ Yönetici",
            reply_markup=replay_kb()
        )
        return

    if msg.chat.type == "private":
        return
    if not is_valid_answer(text):
        return
    if not flood_ok(msg.from_user.id):
        return

    data = await state.get_data()
    answer = data.get("answer", "")
    current_puan = data.get("current_puan", 0)
    score = data.get("score", 0)
    current_round = data.get("round", 1)
    total_rounds = data.get("total_rounds", 15)
    difficulty = data.get("difficulty", "kolay")
    name = msg.from_user.first_name

    if text.lower() == answer.lower():
        new_score = round(score + current_puan, 1)

        # Puan ekle
        add_score(msg.chat.id, msg.from_user.id, name)

        # Oyun bitti mi kontrol et
        if total_rounds != -1 and current_round >= total_rounds:
            await state.clear()
            await state.update_data(
                last_game_data={
                    "difficulty": difficulty,
                    "total_rounds": total_rounds
                }
            )
            await msg.reply(
                f"✅ Doğru cevap! Tebrikler {name}! 🎉\n"
                f"+{current_puan} puan\n\n"
                f"🏁 Oyun Bitti!\n"
                f"🏆 Toplam Puan: {new_score}",
                reply_markup=replay_kb()
            )
            return

        # Sonraki round
        await state.update_data(
            round=current_round + 1,
            score=new_score
        )

        await msg.reply(
            f"✅ Doğru cevap! Tebrikler {name}! 🎉\n"
            f"+{current_puan} puan"
        )

        await start_new_round(msg, state, edit=False)
    else:
        await msg.reply("❌ Yanlış, tekrar dene!")

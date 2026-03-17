import random
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.types import InlineKeyboardMarkup as IKM, InlineKeyboardButton as IKB
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from config import sozler, siirler, itiraf_data, cesaret_data, ai_kw, ai_gen, bot_username, openai_client
from utils import safe_delete, games_menu_kb

router = Router()

@router.message(Command("start"))
async def cmd_start(msg: Message, state: FSMContext):
    await state.clear()
    kb = IKM(inline_keyboard=[
        [IKB(text="🎮 Oyunlar", callback_data="menu_games")],
        [IKB(text="📜 Komutlar", callback_data="menu_cmds")],
        [IKB(text="👑 Kurucum", url="https://t.me/karsilasiriz")],
        [IKB(text="➕ Beni Gruba Ekle",
             url=f"https://t.me/{bot_username}?startgroup=true")]
    ])
    await msg.answer(
        "🎮 Hoş geldin! Ben bir oyun botuyum.\nAşağıdan bir seçenek seç:",
        reply_markup=kb
    )

@router.message(Command("baslat"))
async def cmd_baslat(msg: Message, state: FSMContext):
    if msg.chat.type == "private":
        await msg.answer(
            "🚫 Bu bot sadece gruplarda kullanılabilir!\n\n"
            "Beni bir gruba ekleyip /baslat yazarak oyunları başlatabilirsin."
        )
        return
    await state.clear()
    await msg.answer("🎮 Bir oyun seç:", reply_markup=games_menu_kb())

@router.callback_query(F.data == "menu_games")
async def cb_games(cb: CallbackQuery):
    if cb.message.chat.type == "private":
        await cb.answer("🚫 Sadece gruplarda kullanılabilir!", show_alert=True)
        return
    try:
        await cb.message.edit_text("🎮 Bir oyun seç:", reply_markup=games_menu_kb())
    except Exception:
        await cb.message.answer("🎮 Bir oyun seç:", reply_markup=games_menu_kb())
    await cb.answer()

@router.callback_query(F.data == "menu_cmds")
async def cb_cmds(cb: CallbackQuery):
    if cb.message.chat.type == "private":
        await cb.answer("🚫 Sadece gruplarda kullanılabilir!", show_alert=True)
        return
    t = (
        "📜 Komutlar:\n\n"
        "/baslat - Menüyü aç\n"
        "/yapayzeka [soru] - ChatGPT'ye sor\n"
        "/iptal - Oyunu iptal et\n"
        "/soz - Rastgele söz\n"
        "/siir - Rastgele şiir\n"
        "/d - İtiraf sorusu\n"
        "/c - Cesaret görevi"
    )
    kb = IKM(inline_keyboard=[[IKB(text="🔙 Geri", callback_data="menu_back")]])
    await cb.message.edit_text(t, reply_markup=kb)
    await cb.answer()

@router.callback_query(F.data == "menu_back")
async def cb_back(cb: CallbackQuery, state: FSMContext):
    if cb.message.chat.type == "private":
        await cb.answer("🚫 Sadece gruplarda kullanılabilir!", show_alert=True)
        return
    await cmd_start(cb.message, state)
    await cb.answer()

@router.message(Command("soz"))
async def cmd_soz(msg: Message):
    if msg.chat.type == "private":
        await msg.answer(
            "🚫 Bu bot sadece gruplarda kullanılabilir!\n\n"
            "Beni bir gruba ekleyip /baslat yazarak oyunları başlatabilirsin."
        )
        return
    s = random.choice(sozler)
    await msg.answer(f'💬 "{s["soz"]}"\n\n— {s["yazar"]}')

@router.message(Command("siir"))
async def cmd_siir(msg: Message):
    if msg.chat.type == "private":
        await msg.answer(
            "🚫 Bu bot sadece gruplarda kullanılabilir!\n\n"
            "Beni bir gruba ekleyip /baslat yazarak oyunları başlatabilirsin."
        )
        return
    s = random.choice(siirler)
    await msg.answer(f"📜 {s['baslik']}\n👤 {s['sair']}\n\n{s['siir']}")

@router.message(Command("d"))
async def cmd_d(msg: Message):
    if msg.chat.type == "private":
        await msg.answer(
            "🚫 Bu bot sadece gruplarda kullanılabilir!\n\n"
            "Beni bir gruba ekleyip /baslat yazarak oyunları başlatabilirsin."
        )
        return
    s = random.choice(itiraf_data)
    await msg.answer(f"🔥 İtiraf Sorusu:\n\n{s['soru']}")

@router.message(Command("c"))
async def cmd_c(msg: Message):
    if msg.chat.type == "private":
        await msg.answer(
            "🚫 Bu bot sadece gruplarda kullanılabilir!\n\n"
            "Beni bir gruba ekleyip /baslat yazarak oyunları başlatabilirsin."
        )
        return
    s = random.choice(cesaret_data)
    await msg.answer(f"💪 Cesaret Görevi:\n\n{s['gorev']}")

@router.message(Command("iptal"))
async def cmd_iptal(msg: Message, state: FSMContext):
    if msg.chat.type == "private":
        await msg.answer(
            "🚫 Bu bot sadece gruplarda kullanılabilir!\n\n"
            "Beni bir gruba ekleyip /baslat yazarak oyunları başlatabilirsin."
        )
        return
    
    cur = await state.get_state()
    if cur is None:
        await msg.answer(
            "🧩 Aktif bir oyun yok. "
            "Oyun başlatmak için /baslat komutunu kullanınız."
        )
        return
    
    data = await state.get_data()
    ans = data.get("answer", "")
    has_answer = ans and ans != "XO" and ans != "sudoku"
    text = "💥 Oyun başarıyla iptal edildi!"
    if has_answer:
        text += f"\n\n📝 Cevap: {ans}"
    
    await state.clear()
    await msg.answer(text)

@router.message(Command("yapayzeka"))
async def cmd_ai(msg: Message):
    text = msg.text.replace("/yapayzeka", "").strip() if msg.text else ""
    if not text:
        await msg.answer(
            "🤖 Kullanım: /yapayzeka [sorunuz]\n"
            "Örnek: /yapayzeka Türkiye'nin cumhurbaşkanı kim?"
        )
        return
    
    if openai_client:
        wait_msg = await msg.answer("🤖 Düşünüyorum...")
        try:
            resp = await openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": text}],
                max_tokens=1000
            )
            answer = resp.choices[0].message.content
            await wait_msg.edit_text(f"🤖 {answer}")
            return
        except Exception:
            await safe_delete(wait_msg)
    
    txt = text.lower()
    resp = None
    for k, v in ai_kw.items():
        if k in txt:
            resp = v
            break
    
    if not resp:
        resp = random.choice(ai_gen)
    
    await msg.answer(f"🤖 {resp}")

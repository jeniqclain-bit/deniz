import random
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.types import InlineKeyboardMarkup as IKM, InlineKeyboardButton as IKB
from aiogram.fsm.context import FSMContext
from config import GS, FARK_PAIRS
from utils import add_score, safe_delete

router = Router()

async def start_fark_bulmaca(msg, state, caller=None):
    pair = random.choice(FARK_PAIRS)
    main_e, diff_e = pair
    diff_pos = random.randint(0, 47)
    rows = []
    idx = 0
    for r in range(6):
        row = []
        for c in range(8):
            e = diff_e if idx == diff_pos else main_e
            row.append(IKB(text=e, callback_data=f"fb_{idx}"))
            idx += 1
        rows.append(row)
    rows.append([IKB(text="⏹ İptal", callback_data="c_cancel")])
    
    await state.set_state(GS.fark_bulmaca)
    await state.update_data(answer=str(diff_pos), game="fark_bulmaca", diff_pos=diff_pos)
    return await msg.answer(
        "🔍 Fark Bulmaca\n\nFarklı olan emojiyi bul!",
        reply_markup=IKM(inline_keyboard=rows)
    )

@router.callback_query(F.data.startswith("fb_"))
async def fb_click(cb: CallbackQuery, state: FSMContext):
    if cb.message.chat.type == "private":
        await cb.answer("🚫 Sadece gruplarda kullanılabilir!", show_alert=True)
        return
    
    cur = await state.get_state()
    if cur != GS.fark_bulmaca.state:
        await cb.answer()
        return
    
    idx = int(cb.data.split("_")[1])
    data = await state.get_data()
    diff_pos = data.get("diff_pos", -1)
    name = cb.from_user.first_name
    
    if idx == diff_pos:
        add_score(cb.message.chat.id, cb.from_user.id, name, 3)
        await safe_delete(cb.message)
        await cb.message.answer(f"🎉 {name} farkı buldu! +3 puan")
        from games import start_game_by_name
        await start_game_by_name(cb.message, state, "fark_bulmaca")
    else:
        await cb.answer("❌ Yanlış! Bu değil, tekrar dene.", show_alert=True)

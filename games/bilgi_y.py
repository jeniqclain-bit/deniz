import random
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.types import InlineKeyboardMarkup as IKM, InlineKeyboardButton as IKB
from aiogram.fsm.context import FSMContext
from config import GS, bilgi_data
from utils import add_score, load_scores, ctrl_kb, safe_delete

router = Router()

async def start_bilgi_y(msg, state, caller=None):
    q = random.choice(bilgi_data)
    opts = q["secenekler"]
    kb = IKM(inline_keyboard=[
        [IKB(text=o, callback_data=f"bilgi_{i}") for i, o in enumerate(opts[:2])],
        [IKB(text=o, callback_data=f"bilgi_{i}") for i, o in enumerate(opts[2:], 2)],
        *ctrl_kb().inline_keyboard
    ])
    await state.set_state(GS.bilgi_y)
    await state.update_data(answer=q["cevap"], game="bilgi_y", opts=opts)
    return await msg.answer(f"❓ Bilgi Yarışması\n\n{q['soru']}", reply_markup=kb)

@router.callback_query(F.data.startswith("bilgi_"))
async def bilgi_ans(cb: CallbackQuery, state: FSMContext):
    if cb.message.chat.type == "private":
        await cb.answer("🚫 Sadece gruplarda kullanılabilir!", show_alert=True)
        return
    
    cur = await state.get_state()
    if cur != GS.bilgi_y.state:
        await cb.answer()
        return
    
    data = await state.get_data()
    idx = int(cb.data.split("_")[1])
    sel = data["opts"][idx]
    name = cb.from_user.first_name
    
    await safe_delete(cb.message)
    
    if sel == data["answer"]:
        add_score(cb.message.chat.id, cb.from_user.id, name)
        await cb.message.answer(f"✅ Doğru! Tebrikler {name}! 🎉")
    else:
        await cb.message.answer(f"❌ Yanlış! Cevap: {data['answer']}")
    
    from games import start_game_by_name
    await start_game_by_name(cb.message, state, "bilgi_y")
    await cb.answer()

import random
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.types import InlineKeyboardMarkup as IKM, InlineKeyboardButton as IKB
from aiogram.fsm.context import FSMContext
from config import GS, dy_data
from utils import add_score, ctrl_kb, safe_delete

router = Router()

async def start_dogru_yanlis(msg, state, caller=None):
    q = random.choice(dy_data)
    ans = "Doğru" if q["cevap"] else "Yanlış"
    kb = IKM(inline_keyboard=[
        [IKB(text="✅ Doğru", callback_data="dy_true"), 
         IKB(text="❌ Yanlış", callback_data="dy_false")],
        *ctrl_kb().inline_keyboard
    ])
    await state.set_state(GS.dogru_yanlis)
    await state.update_data(answer=ans, correct=q["cevap"], game="dogru_yanlis")
    return await msg.answer(f"✅❌ Doğru Yanlış\n\n{q['ifade']}", reply_markup=kb)

@router.callback_query(F.data.in_({"dy_true", "dy_false"}))
async def dy_ans(cb: CallbackQuery, state: FSMContext):
    if cb.message.chat.type == "private":
        await cb.answer("🚫 Sadece gruplarda kullanılabilir!", show_alert=True)
        return
    
    cur = await state.get_state()
    if cur != GS.dogru_yanlis.state:
        await cb.answer()
        return
    
    data = await state.get_data()
    user_ans = (cb.data == "dy_true")
    name = cb.from_user.first_name
    
    await safe_delete(cb.message)
    
    if user_ans == data["correct"]:
        add_score(cb.message.chat.id, cb.from_user.id, name)
        await cb.message.answer(f"✅ Doğru! Tebrikler {name}! 🎉")
    else:
        await cb.message.answer(f"❌ Yanlış! Cevap: {data['answer']}")
    
    from games import start_game_by_name
    await start_game_by_name(cb.message, state, "dogru_yanlis")
    await cb.answer()

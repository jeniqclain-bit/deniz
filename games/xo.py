from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.types import InlineKeyboardMarkup as IKM, InlineKeyboardButton as IKB
from aiogram.fsm.context import FSMContext
from config import GS
from utils import add_score, ctrl_kb

router = Router()

def xo_kb(board):
    rows = []
    for i in range(3):
        row = []
        for j in range(3):
            idx = i * 3 + j
            row.append(IKB(text=board[idx], callback_data=f"xo_{idx}"))
        rows.append(row)
    rows.append([IKB(text="⏹ İptal", callback_data="c_cancel")])
    return IKM(inline_keyboard=rows)

def check_win(board, mark):
    wins = [(0,1,2),(3,4,5),(6,7,8),(0,3,6),(1,4,7),(2,5,8),(0,4,8),(2,4,6)]
    return any(board[a] == board[b] == board[c] == mark for a, b, c in wins)

async def start_xo(msg, state, caller=None):
    board = ["⬜"] * 9
    await state.set_state(GS.xo)
    uid = str(caller.id) if caller else "0"
    uname = caller.first_name if caller else "P1"
    await state.update_data(
        board=board, game="xo", answer="XO",
        p1_id=uid, p1_name=uname, p2_id=None, p2_name=None, turn=uid
    )
    kb = IKM(inline_keyboard=[
        [IKB(text="⚔️ Katıl (⭕)", callback_data="xo_join")],
        [IKB(text="⏹ İptal", callback_data="c_cancel")]
    ])
    return await msg.answer(
        f"❌⭕ XO Oyunu\n\n{uname} (❌) oyunu başlattı!\nBir oyuncu daha katılmalı.",
        reply_markup=kb
    )

@router.callback_query(F.data == "xo_join")
async def xo_join(cb: CallbackQuery, state: FSMContext):
    if cb.message.chat.type == "private":
        await cb.answer("🚫 Sadece gruplarda kullanılabilir!", show_alert=True)
        return
    
    cur = await state.get_state()
    if cur != GS.xo.state:
        await cb.answer()
        return
    
    data = await state.get_data()
    uid = str(cb.from_user.id)
    
    if uid == data.get("p1_id"):
        await cb.answer("Sen zaten oyundasın!", show_alert=True)
        return
    
    if data.get("p2_id"):
        await cb.answer("Oyun dolu!", show_alert=True)
        return
    
    await state.update_data(p2_id=uid, p2_name=cb.from_user.first_name)
    data = await state.get_data()
    board = data["board"]
    
    await cb.message.edit_text(
        f"❌⭕ XO Oyunu\n\n❌ {data['p1_name']} vs ⭕ {cb.from_user.first_name}\n\n"
        f"Sıra: {data['p1_name']} (❌)",
        reply_markup=xo_kb(board)
    )
    await cb.answer()

@router.callback_query(F.data.startswith("xo_"))
async def xo_move(cb: CallbackQuery, state: FSMContext):
    if cb.data == "xo_join":
        return
    
    if cb.message.chat.type == "private":
        await cb.answer("🚫 Sadece gruplarda kullanılabilir!", show_alert=True)
        return
    
    cur = await state.get_state()
    if cur != GS.xo.state:
        await cb.answer()
        return
    
    idx = int(cb.data.split("_")[1])
    data = await state.get_data()
    board = data["board"]
    uid = str(cb.from_user.id)
    p1, p2 = data.get("p1_id"), data.get("p2_id")
    
    if not p2:
        await cb.answer("Oyuncu bekleniyor!")
        return
    
    if uid != data.get("turn"):
        await cb.answer("Senin sıran değil!")
        return
    
    if board[idx] != "⬜":
        await cb.answer("Bu kare dolu!")
        return
    
    mark = "❌" if uid == p1 else "⭕"
    board[idx] = mark
    
    if check_win(board, mark):
        name = cb.from_user.first_name
        add_score(cb.message.chat.id, cb.from_user.id, name, 3)
        await cb.message.edit_text(
            f"🎉 {name} ({mark}) kazandı!",
            reply_markup=xo_kb(board)
        )
        await state.clear()
        await cb.answer()
        return
    
    if "⬜" not in board:
        await cb.message.edit_text("🤝 Berabere!", reply_markup=xo_kb(board))
        await state.clear()
        await cb.answer()
        return
    
    next_turn = p2 if uid == p1 else p1
    next_name = data["p2_name"] if uid == p1 else data["p1_name"]
    next_mark = "⭕" if uid == p1 else "❌"
    
    await state.update_data(board=board, turn=next_turn)
    await cb.message.edit_text(
        f"❌⭕ XO Oyunu\n\n❌ {data['p1_name']} vs ⭕ {data['p2_name']}\n\n"
        f"Sıra: {next_name} ({next_mark})",
        reply_markup=xo_kb(board)
    )
    await cb.answer()

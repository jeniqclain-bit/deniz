from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from config import GS
from utils import add_score, ctrl_kb, generate_sudoku, render_sudoku

router = Router()

async def start_sudoku(msg, state, caller=None):
    board, solution = generate_sudoku()
    await state.set_state(GS.sudoku)
    await state.update_data(board=board, solution=solution, game="sudoku", answer="sudoku")
    return await msg.answer(render_sudoku(board), reply_markup=ctrl_kb())

@router.message(GS.sudoku)
async def sudoku_answer(msg: Message, state: FSMContext):
    if msg.chat.type == "private":
        return
    if not msg.text:
        return
    if msg.text.startswith('/'):
        return
    
    parts = msg.text.strip().split()
    if len(parts) != 3:
        await msg.reply("Format: satır sütun sayı\nÖrnek: 3 5 7")
        return
    
    try:
        r, c, n = int(parts[0])-1, int(parts[1])-1, int(parts[2])
    except ValueError:
        await msg.reply("Lütfen sayı gir! Örnek: 3 5 7")
        return
    
    if not (0 <= r < 9 and 0 <= c < 9 and 1 <= n <= 9):
        await msg.reply("Geçersiz! Satır/sütun 1-9, sayı 1-9 olmalı.")
        return
    
    data = await state.get_data()
    board = data["board"]
    solution = data["solution"]
    
    if board[r][c] != 0:
        await msg.reply("Bu hücre zaten dolu!")
        return
    
    if solution[r][c] == n:
        board[r][c] = n
        await state.update_data(board=board)
        empty = sum(1 for row in board for v in row if v == 0)
        
        if empty == 0:
            name = msg.from_user.first_name
            add_score(msg.chat.id, msg.from_user.id, name, 10)
            await msg.reply(f"🎉 Sudoku tamamlandı! {name} +10 puan!")
            await state.clear()
        else:
            old_mid = data.get("bot_msg_id")
            if old_mid:
                try:
                    await msg.bot.edit_message_text(
                        text=render_sudoku(board), chat_id=msg.chat.id,
                        message_id=old_mid, reply_markup=ctrl_kb())
                except Exception:
                    sent = await msg.answer(render_sudoku(board), reply_markup=ctrl_kb())
                    await state.update_data(bot_msg_id=sent.message_id)
            else:
                sent = await msg.answer(render_sudoku(board), reply_markup=ctrl_kb())
                await state.update_data(bot_msg_id=sent.message_id)
            await msg.reply(f"✅ Doğru! Kalan: {empty} hücre")
    else:
        await msg.reply("❌ Yanlış sayı!")

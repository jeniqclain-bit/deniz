import json
import time
import random
from aiogram.types import InlineKeyboardMarkup as IKM, InlineKeyboardButton as IKB
from config import SCORE_FILE, cooldowns

def load_scores():
    if SCORE_FILE.exists():
        with open(SCORE_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_scores(scores):
    with open(SCORE_FILE, "w", encoding="utf-8") as f:
        json.dump(scores, f, ensure_ascii=False)

def add_score(cid, uid, name, p=1, scores=None):
    if scores is None:
        scores = load_scores()
    k, u = str(cid), str(uid)
    scores.setdefault(k, {})
    scores[k].setdefault(u, {"s": 0, "n": name})
    scores[k][u]["s"] += p
    scores[k][u]["n"] = name
    save_scores(scores)
    return scores

def get_scores_text(cid, scores=None):
    if scores is None:
        scores = load_scores()
    k = str(cid)
    if k not in scores or not scores[k]:
        return "📊 Henüz skor yok!"
    s = sorted(scores[k].items(), key=lambda x: x[1]["s"], reverse=True)
    medals = ["🥇", "🥈", "🥉"]
    t = "📊 Skor Tablosu:\n\n"
    for i, (u, d) in enumerate(s[:10]):
        m = medals[i] if i < 3 else f"{i+1}."
        t += f"{m} {d['n']}: {d['s']} puan\n"
    return t

def flood_ok(uid):
    n = time.time()
    if uid in cooldowns and n - cooldowns[uid] < 3:
        return False
    cooldowns[uid] = n
    return True

async def safe_delete(msg):
    try:
        await msg.delete()
    except Exception:
        pass

def word_similarity(guess, answer):
    g, a = guess.lower(), answer.lower()
    if g == a:
        return 100
    score = 0
    max_len = max(len(g), len(a))
    if max_len == 0:
        return 0
    for i in range(min(len(g), len(a))):
        if g[i] == a[i]:
            score += 1
    common = set(g) & set(a)
    bonus = len(common) * 0.5
    pct = int(((score + bonus) / (max_len + len(set(a)) * 0.5)) * 100)
    return min(pct, 99)

def ctrl_kb():
    return IKM(inline_keyboard=[
        [IKB(text="⏭ Atla", callback_data="c_skip"),
         IKB(text="⏹ İptal", callback_data="c_cancel")],
        [IKB(text="🎮 Yeni Oyun", callback_data="c_new"),
         IKB(text="📊 Skorlar", callback_data="c_scores")]
    ])

def is_valid_answer(text):
    """Tek kelimelik cevap kontrolü - komutları ve boşluk içerenleri reddet"""
    if not text:
        return False
    if text.startswith('/'):
        return False
    if ' ' in text.strip():
        return False
    return True

def games_menu_kb():
    return IKM(inline_keyboard=[
        [IKB(text="📝 Kelime Anlatma", callback_data="g_ka"),
         IKB(text="📝 Boşluk Doldurma", callback_data="g_bd")],
        [IKB(text="🔄 Kelime Sarmalı", callback_data="g_ks"),
         IKB(text="🔢 Hızlı Matematik", callback_data="g_hm")],
        [IKB(text="🔢 Sayı Oyunu", callback_data="g_so"),
         IKB(text="❓ Bilgi Yarışması", callback_data="g_by")],
        [IKB(text="🏴 Bayrak Tahmini", callback_data="g_bt"),
         IKB(text="🔗 Kelime Zinciri", callback_data="g_kz")],
        [IKB(text="🏙 Başkent Tahmini", callback_data="g_bk"),
         IKB(text="🚗 Plaka Oyunu", callback_data="g_pl")],
        [IKB(text="❌⭕ XO Oyunu", callback_data="g_xo"),
         IKB(text="✅❌ Doğru Yanlış", callback_data="g_dy")],
        [IKB(text="🤔 Bilmece", callback_data="g_bi"),
         IKB(text="😀 Emoji Tahmini", callback_data="g_em")],
        [IKB(text="📚 Eser Yazar", callback_data="g_ey"),
         IKB(text="🌡 Sıcak Soğuk", callback_data="g_ss")],
        [IKB(text="⚔️ Duello", callback_data="g_du"),
         IKB(text="🔍 Fark Bulmaca", callback_data="g_fb")],
        [IKB(text="🔢 Sudoku", callback_data="g_su")],
        [IKB(text="🔙 Geri", callback_data="menu_back")]
    ])

def generate_sudoku():
    board = [[0]*9 for _ in range(9)]
    def valid(b, r, c, n):
        if n in b[r]:
            return False
        if n in [b[i][c] for i in range(9)]:
            return False
        br, bc = 3*(r//3), 3*(c//3)
        for i in range(br, br+3):
            for j in range(bc, bc+3):
                if b[i][j] == n:
                    return False
        return True
    def solve(b):
        for r in range(9):
            for c in range(9):
                if b[r][c] == 0:
                    nums = list(range(1, 10))
                    random.shuffle(nums)
                    for n in nums:
                        if valid(b, r, c, n):
                            b[r][c] = n
                            if solve(b):
                                return True
                            b[r][c] = 0
                    return False
        return True
    solve(board)
    solution = [row[:] for row in board]
    cells = [(r, c) for r in range(9) for c in range(9)]
    random.shuffle(cells)
    for r, c in cells[:45]:
        board[r][c] = 0
    return board, solution

def render_sudoku(board):
    t = "🔢 Sudoku\n\n"
    t += "    1 2 3   4 5 6   7 8 9\n"
    for r in range(9):
        if r % 3 == 0 and r > 0:
            t += "   ───────┼───────┼───────\n"
        row_str = f" {r+1} │"
        for c in range(9):
            if c % 3 == 0 and c > 0:
                row_str += "│"
            v = board[r][c]
            row_str += f" {v if v else '·'}"
        t += row_str + "\n"
    t += "\nCevap: satır sütun sayı\nÖrnek: 3 5 7"
    return t

from .kelime_anlatma import router as kelime_anlatma_router
from .bosluk_doldurma import router as bosluk_doldurma_router
from .kelime_sarmali import router as kelime_sarmali_router
from .hizli_mat import router as hizli_mat_router
from .sayi import router as sayi_router
from .bilgi_y import router as bilgi_y_router
from .bayrak import router as bayrak_router
from .kelime_zinciri import router as kelime_zinciri_router
from .baskent import router as baskent_router
from .plaka import router as plaka_router
from .xo import router as xo_router
from .dogru_yanlis import router as dogru_yanlis_router
from .bilmece import router as bilmece_router
from .emoji import router as emoji_router
from .eser import router as eser_router
from .sicak_soguk import router as sicak_soguk_router
from .duello import router as duello_router
from .fark_bulmaca import router as fark_bulmaca_router
from .sudoku import router as sudoku_router

game_routers = [
    kelime_anlatma_router,
    bosluk_doldurma_router,
    kelime_sarmali_router,
    hizli_mat_router,
    sayi_router,
    bilgi_y_router,
    bayrak_router,
    kelime_zinciri_router,
    baskent_router,
    plaka_router,
    xo_router,
    dogru_yanlis_router,
    bilmece_router,
    emoji_router,
    eser_router,
    sicak_soguk_router,
    duello_router,
    fark_bulmaca_router,
    sudoku_router,
]

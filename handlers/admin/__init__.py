from .users import router as users_router
from .products import router as products_router
from .orders import router as orders_router
from .settings import router as settings_router
from .back_button import router as back_button_router

__all__ = [
    "users_router",
    "products_router",
    "orders_router",
    "settings_router",
    "back_button_router",
]
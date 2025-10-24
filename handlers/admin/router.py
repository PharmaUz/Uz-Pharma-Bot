from aiogram import Router
from . import users, products, orders, settings, back_button

router = Router()

# Include all admin-related routers
router.include_router(users.router)
router.include_router(products.router)
router.include_router(orders.router)
router.include_router(settings.router)
router.include_router(back_button.router)
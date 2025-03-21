from .users import router as users_router
from .domains import router as domains_router
from .settings import router as settings_router

__all__ = ["users_router", "domains_router", "settings_router"]

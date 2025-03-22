from .users import router as users_router
from .domains import router as domains_router
from .settings import router as settings_router
from .subscription import router as subscription_router  # بررسی ایمپورت subscription

__all__ = ["users_router", "domains_router", "settings_router", "subscription_router"]

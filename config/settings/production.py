from .base import *

DEBUG = False
ALLOWED_HOSTS = env.list("PRESENTIA_ALLOWED_HOSTS", default=["*"])

# Seguranca
SECURE_SSL_REDIRECT = env.bool("PRESENTIA_SECURE_SSL_REDIRECT", default=False)
SESSION_COOKIE_SECURE = env.bool("PRESENTIA_SESSION_COOKIE_SECURE", default=False)
CSRF_COOKIE_SECURE = env.bool("PRESENTIA_CSRF_COOKIE_SECURE", default=False)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Static
STATIC_ROOT = BASE_DIR / "staticfiles"

# Logging
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "file": {
            "level": "WARNING",
            "class": "logging.FileHandler",
            "filename": BASE_DIR / "logs" / "presentia.log",
        },
    },
    "root": {"handlers": ["file"], "level": "WARNING"},
}

# Sessões no banco (recomendado para produção)
SESSION_ENGINE = "django.contrib.sessions.backends.db"
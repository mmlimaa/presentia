from pathlib import Path
import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent
env = environ.Env(PRESENTIA_DEBUG=(bool, False), PRESENTIA_ALLOWED_HOSTS=(list, []))
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("PRESENTIA_SECRET_KEY", default="django-insecure-dev-key")
DEBUG = env("PRESENTIA_DEBUG")
ALLOWED_HOSTS = env("PRESENTIA_ALLOWED_HOSTS")

INSTALLED_APPS = [ "django.contrib.messages", "django.contrib.staticfiles",
    "rest_framework", "presentia.common", "presentia.accounts",
    "presentia.churches", "presentia.courses", "presentia.attendance",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware", "django.middleware.csrf.CsrfViewMiddleware", "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
TEMPLATES = [{"BACKEND": "django.template.backends.django.DjangoTemplates", "DIRS": [BASE_DIR / "templates"], "APP_DIRS": True, "OPTIONS": {"context_processors": ["django.template.context_processors.debug", "django.template.context_processors.request",  "django.contrib.messages.context_processors.messages"]}}]
WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {"default": env.db("PRESENTIA_DATABASE_URL", default="postgres://PRESENTIA_user:abc%4012345@localhost:5432/Presentia")}
DATABASES["default"]["OPTIONS"] = {"options": "-c search_path=nucleos,public"}
LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'login'


# --- Configuracao do Painel Administrativo (Jazzmin) ---


JAZZMIN_SETTINGS = {
    "site_title": "Presentia - Painel Administrativo",
    "site_header": "Presentia",
    "site_brand": "FVC Presenca",
    "welcome_sign": "Bem-vindo ao Sistema de Frequencia da FVC",
    "copyright": "Faculdade Vitoria em Cristo",
    "show_sidebar": True,
    "navigation_expanded": True,
}

JAZZMIN_UI_TWEAKS = {
    "theme": "flatly",
    "dark_mode_theme": "darkly",
}

SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

MESSAGE_STORAGE = "django.contrib.messages.storage.cookie.CookieStorage"





from .schema import DatabaseConfig

SECRET_KEY = "django-insecure--%dbcahm$h45=qeyio&^8$*iz1!-tnby))#oeowkq0@90c#k!("

DATABASES = {
    "default": DatabaseConfig(
                    ENGINE="django.db.backends.sqlite3",
                    NAME="db.sqlite3",
                )
}


EMAIL_HOST = ''
EMAIL_HOST_USER = ''
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

SYSTEM_EMAIL = ""
NOTIFY_EMAIL_NAME = ""
NOTIFY_EMAIL = ""


ALLOWED_HOSTS =['codev.sinotech.com.tw']


AUTHENTICATION_BACKENDS = [
    'CoDevStudio.backends.sino_remote_user_backend.SinoRemoteUserBackend',
    'django.contrib.auth.backends.ModelBackend',
]

SINO_AUTH_SERVICE_TOKEN = ''
SINO_AUTH_SERVICE_DOMAIN = ''
SINO_AUTH_SERVICE_APP_PATH = 'sas'

STAGE_MIDDLEWARES = [
    "SinoAuth.middlewares.BIMTokenAuthMiddleware",
    "SinoAuth.middlewares.StripTokenMiddleware",  # 選擇使用，可以隱藏網址的 token
]


STAGE_READ_DB_LABELS = [
    'BimAuth',
    'CommonUse',
]
STAGE_WRITE_DB_LABELS = [
    'BimAuth',
]
STAGE_MIGRATE_DB_LABELS = []


GEMINI_API_KEY = ""  
GEMINI_MODEL = "" 


ANYTHINGLLM_KEY = ''


# CORS Settings
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
CORS_TRUSTED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
CORS_ALLOW_CREDENTIALS = True

# CSRF Settings
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

# Feature Toggles
ENABLE_CLASH_CLASSIFIER = False  # 設為 True 以啟用碰撞報告分類 API

# Tiered Storage Settings (可選，schema.py 已有預設值)
# ARCHIVE_ROOT = '/mnt/cold_storage'
# ARCHIVE_URL = '/archive/'
# TMP_ROOT = '/mnt/tmp_data'
# ARCHIVE_MAX_FOLDER_SIZE = 4 * 1024 * 1024 * 1024

# OpenSearch Settings
OPENSEARCH_HOST = 'https://localhost:19200'
OPENSEARCH_USERNAME = 'sino'
OPENSEARCH_PASSWORD = 'sino'
OPENSEARCH_VERIFY_CERTS = False


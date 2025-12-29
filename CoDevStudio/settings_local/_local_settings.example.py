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

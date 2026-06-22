from pathlib import Path
import os
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')

SECRET_KEY = os.environ['DJANGO_SECRET_KEY']

DEBUG = os.environ.get('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = ['localhost', '127.0.0.1']
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'rest_framework',
    'rest_framework_simplejwt.token_blacklist',
    'products',
    'receipts',
    'branches',
    'voicephishing',
    'accounts',
    'docforms',
    'spending',
    'news',
    'stocks',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

AUTH_USER_MODEL = 'accounts.User'

LANGUAGE_CODE = 'ko-kr'
TIME_ZONE = 'Asia/Seoul'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# CORS — Vue dev 서버 허용
CORS_ALLOWED_ORIGINS = [
    'http://localhost:5173',
    'http://127.0.0.1:5173',
]

# FSS API
FSS_API_KEY = os.environ.get('FSS_API_KEY', '')
FSS_BASE_URL = 'https://finlife.fss.or.kr/finlifeapi'

# CLOVA OCR
CLOVA_OCR_INVOKE_URL = os.environ.get('CLOVA_OCR_INVOKE_URL', '')
CLOVA_OCR_SECRET     = os.environ.get('CLOVA_OCR_SECRET', '')

# GMS (Gemini proxy)
GMS_KEY   = os.environ.get('GMS_KEY', '')
GMS_MODEL = os.environ.get('GMS_MODEL', 'gemini-2.5-flash')

# 보이스피싱 탐지 모델 서버 (FastAPI)
MODEL_SERVER_URL = os.environ.get('MODEL_SERVER_URL', 'http://localhost:8001')

# JWT 설정
from datetime import timedelta
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME':  timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=14),
    'ROTATE_REFRESH_TOKENS':  True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.AllowAny',
    ),
}

# Naver Cloud Platform — Dynamic Map, Reverse Geocoding
NCP_MAP_CLIENT_ID     = os.environ.get('NCP_MAP_CLIENT_ID', '')
NCP_MAP_CLIENT_SECRET = os.environ.get('NCP_MAP_CLIENT_SECRET', '')

# Naver Developers — 지역 검색 API
NAVER_SEARCH_CLIENT_ID     = os.environ.get('NAVER_SEARCH_CLIENT_ID', '')
NAVER_SEARCH_CLIENT_SECRET = os.environ.get('NAVER_SEARCH_CLIENT_SECRET', '')

# fixtures 경로 직접 설정
FIXTURE_DIRS = [
    os.path.join(BASE_DIR, 'fixtures'),
]
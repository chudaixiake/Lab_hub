"""
Django settings for lab_hub_project project.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-be+38jo8$d4t!#1b%x*)831wy(hqc%nca5%@d9(*wq-dfz%j4z'

DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '1wo0118io8940.vicp.fun', '*']

CSRF_TRUSTED_ORIGINS = [
    'http://1wo0118io8940.vicp.fun',
    'https://1wo0118io8940.vicp.fun',
    'http://frp-six.com:21652',
    'https://frp-six.com:21652',
]


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'lab_management',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # 'whitenoise.middleware.WhiteNoiseMiddleware',  # 本地开发不需要
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'lab_hub_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'lab_management.context_processors.user_profile',
                'lab_management.context_processors.unread_messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'lab_hub_project.wsgi.application'


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


LANGUAGE_CODE = 'zh-hans'

TIME_ZONE = 'Asia/Shanghai'

USE_I18N = True

USE_TZ = True


STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]
# STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'  # 本地开发不需要

# 静态文件缓存和压缩配置
WHITENOISE_MAX_AGE = 31536000  # 1年缓存
WHITENOISE_GZIP = True
WHITENOISE_BROTLI = True

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/my/'
LOGOUT_REDIRECT_URL = '/'

# 腾讯云 AI 配置（从环境变量读取）
TENCENT_AI_SECRET_ID = os.getenv('TENCENT_AI_SECRET_ID')
TENCENT_AI_SECRET_KEY = os.getenv('TENCENT_AI_SECRET_KEY')
TENCENT_AI_ENDPOINT = os.getenv('TENCENT_AI_ENDPOINT', 'https://hunyuan.tencentcloudapi.com')
TENCENT_AI_VERSION = os.getenv('TENCENT_AI_VERSION', '2023-09-01')
TENCENT_AI_MODEL = os.getenv('TENCENT_AI_MODEL', 'hunyuan-lite')

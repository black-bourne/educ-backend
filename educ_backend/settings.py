import os
from pathlib import Path
from dotenv import load_dotenv
from urllib.parse import urlparse


load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

AUTH_USER_MODEL = 'accounts.User'

CORS_ALLOW_ALL_ORIGINS = True  # For development only
# SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
AUTH_PASSWORD_VALIDATORS = True

# Application definition
INSTALLED_APPS = [
    'corsheaders',
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'accounts.apps.AccountsConfig',
    'academics'
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'educ_backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'educ_backend.wsgi.application'



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


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


STATIC_URL = 'static/'


DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': os.getenv('DB_NAME'),
#         'USER': os.getenv('DB_USER'),
#         'PASSWORD': os.getenv('DB_PASSWORD'),
#         'HOST': os.getenv('DB_HOST'),
#         'PORT': '5432',
#     }
# }
tmpPostgres = urlparse(os.getenv("DATABASE_URL"))

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': tmpPostgres.path.replace('/', ''),
        'USER': tmpPostgres.username,
        'PASSWORD': tmpPostgres.password,
        'HOST': tmpPostgres.hostname,
        'PORT': 5432,
    }
}

# Secret key for JWT (ensure this is secure in production)
SECRET_KEY = os.getenv('SECRET_KEY')

# Email settings (using Gmail)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER') # Your Gmail address
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')  # App Password if 2FA is enabled
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# Redis cache
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Celery settings
CELERY_BROKER_URL = 'redis://127.0.0.1:6379/0'  # Redis as message broker
CELERY_RESULT_BACKEND = 'redis://127.0.0.1:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        '': {
            'handlers': ['console'],
            'level': 'INFO',
        },
    },
}


JAZZMIN_UI_TWEAKS = {
    # Text Sizing
    "navbar_small_text": True,
    "footer_small_text": True,
    "body_small_text": True,
    "brand_small_text": True,
    # Colors and Styling - Education-focused theme
    "brand_colour": "navbar-primary",  # Bold primary color for branding
    "accent": "accent-info",  # Knowledge-focused blue accent
    "navbar": "navbar-dark bg-gradient-primary",  # Gradient navbar for modern look
    "no_navbar_border": True,  # Clean borderless design
    "sidebar": "sidebar-dark-info",  # Info-themed sidebar
    "sidebar_nav_small_text": True,  # Better readability in sidebar

    # Sidebar Navigation - Optimized for education context
    "sidebar_disable_expand": False,  # Allow for expandable sections (courses, classes, etc.)
    "sidebar_nav_child_indent": True,  # Clear hierarchy for educational content
    "sidebar_nav_compact_style": True,  # Efficient space usage
    "sidebar_nav_legacy_style": False,  # Modern appearance
    "sidebar_nav_flat_style": False,  # Dimensional navigation for better UX

    # Theme - Professional education look
    "theme": "flatly",  # Clean, professional theme with good contrast

    # Custom CSS to enhance education dashboard
    "custom_css": "dashboard_styles.css",

    # Button Classes - Intuitive color coding for education actions
    "button_classes": {
        "primary": "btn-primary btn-lg",  # Prominent primary actions
        "secondary": "btn-outline-secondary",  # Secondary options
        "info": "btn-info",  # Informational actions
        "warning": "btn-warning",  # Attention-needed items
        "danger": "btn-outline-danger btn-sm",  # Destructive actions (smaller)
        "success": "btn-success",  # Completion/submission actions
    },

    # Related Modal - For quick reference materials
    "related_modal_active": True,
    "related_modal_background": "primary",
    "custom_links_hover_bg": "primary",

    # Form Styling
    "form_submit_label": "Save and Continue",
    "show_ui_builder": True,

    # Dashboard organization
    "show_fieldsets_as_tabs": True,  # Organized content in tabs
    "show_inlines_as_tabs": True,  # Better organization of inline content
}
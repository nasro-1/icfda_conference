"""
icfda_conference/settings.py
Complete Django settings for ICFDA 2025 Registration System
"""

from pathlib import Path
from decouple import config
import os
from datetime import datetime, date

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='django-insecure-icfda-2025-change-this-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=True, cast=bool)

# Allowed hosts
ALLOWED_HOSTS = config(
    'ALLOWED_HOSTS', 
    default='localhost,127.0.0.1,icfda2025.com,www.icfda2025.com', 
    cast=lambda v: [s.strip() for s in v.split(',')]
)

# Application definition
INSTALLED_APPS = [
    # Django apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',  # For number formatting
    
    # Third party apps
    'rest_framework',
    'corsheaders',
    
    # Local apps
    'registration',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # For static files in production
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'icfda_conference.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'templates',
            BASE_DIR / 'registration' / 'templates',
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
            ],
        },
    },
]

WSGI_APPLICATION = 'icfda_conference.wsgi.application'

# Database Configuration
DATABASES = {
    'default': {
        'ENGINE': config('DB_ENGINE', default='django.db.backends.sqlite3'),
        'NAME': config('DB_NAME', default=str(BASE_DIR / 'db.sqlite3')),
        'USER': config('DB_USER', default=''),
        'PASSWORD': config('DB_PASSWORD', default=''),
        'HOST': config('DB_HOST', default=''),
        'PORT': config('DB_PORT', default=''),
        'OPTIONS': {
            'charset': 'utf8mb4',
        } if config('DB_ENGINE', default='').startswith('mysql') else {},
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = config('TIME_ZONE', default='Africa/Algiers')  # Algeria timezone
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Available languages
LANGUAGES = [
    ('en', 'English'),
    ('fr', 'French'),
    ('ar', 'Arabic'),
]

LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
] if (BASE_DIR / 'static').exists() else []

# Static files storage
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ============================================================================
# EMAIL CONFIGURATION
# ============================================================================

EMAIL_BACKEND = config(
    'EMAIL_BACKEND', 
    default='django.core.mail.backends.smtp.EmailBackend'
)

# Gmail SMTP Configuration
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_USE_SSL = config('EMAIL_USE_SSL', default=False, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='nasr_eddine.mellah@g.enp.edu.dz')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')

# Email addresses
DEFAULT_FROM_EMAIL = config(
    'DEFAULT_FROM_EMAIL', 
    default='ICFDA 2025 <nasr_eddine.mellah@g.enp.edu.dz>'
)
SERVER_EMAIL = DEFAULT_FROM_EMAIL
ADMINS = [
    ('ICFDA 2025 Admin', 'nasro.mellah@gmail.com'),
]
MANAGERS = ADMINS

# ============================================================================
# PAYMENT CONFIGURATION
# ============================================================================

# Stripe Configuration (for international payments)
STRIPE_PUBLIC_KEY = config('STRIPE_PUBLIC_KEY', default='')
STRIPE_SECRET_KEY = config('STRIPE_SECRET_KEY', default='')
STRIPE_WEBHOOK_SECRET = config('STRIPE_WEBHOOK_SECRET', default='')

# Payment settings
STRIPE_LIVE_MODE = config('STRIPE_LIVE_MODE', default=False, cast=bool)

# ============================================================================
# SECURITY SETTINGS
# ============================================================================

# Security settings for production
if not DEBUG:
    SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=True, cast=bool)
    SECURE_HSTS_SECONDS = config('SECURE_HSTS_SECONDS', default=31536000, cast=int)
    SECURE_HSTS_INCLUDE_SUBDOMAINS = config('SECURE_HSTS_INCLUDE_SUBDOMAINS', default=True, cast=bool)
    SECURE_HSTS_PRELOAD = config('SECURE_HSTS_PRELOAD', default=True, cast=bool)
    SECURE_CONTENT_TYPE_NOSNIFF = config('SECURE_CONTENT_TYPE_NOSNIFF', default=True, cast=bool)
    SECURE_BROWSER_XSS_FILTER = config('SECURE_BROWSER_XSS_FILTER', default=True, cast=bool)
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    
    # Cookie security
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    CSRF_COOKIE_SECURE = True
    CSRF_COOKIE_HTTPONLY = True
    CSRF_COOKIE_SAMESITE = 'Strict'
    SESSION_COOKIE_SAMESITE = 'Strict'
    
    # Additional security headers
    X_FRAME_OPTIONS = 'DENY'
    SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
else:
    # Development settings
    SESSION_COOKIE_HTTPONLY = True
    CSRF_COOKIE_HTTPONLY = False  # Allow JavaScript to read CSRF token in development
    CSRF_COOKIE_SAMESITE = 'Lax'

# Session configuration
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = config('SESSION_COOKIE_AGE', default=3600, cast=int)  # 1 hour
SESSION_EXPIRE_AT_BROWSER_CLOSE = config('SESSION_EXPIRE_AT_BROWSER_CLOSE', default=True, cast=bool)

# ============================================================================
# CACHE CONFIGURATION
# ============================================================================

CACHES = {
    'default': {
        'BACKEND': config(
            'CACHE_BACKEND',
            default='django.core.cache.backends.locmem.LocMemCache'
        ),
        'LOCATION': config('CACHE_LOCATION', default='icfda-2025-cache'),
        'TIMEOUT': config('CACHE_TIMEOUT', default=300, cast=int),
        'OPTIONS': {
            'MAX_ENTRIES': config('CACHE_MAX_ENTRIES', default=1000, cast=int),
        }
    }
}

# Cache time to live is 15 minutes
CACHE_TTL = 60 * 15

# ============================================================================
# CORS CONFIGURATION
# ============================================================================

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "https://conferences.ifac-control.org",
]

CORS_ALLOW_CREDENTIALS = True

CORS_ALLOWED_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# ============================================================================
# REST FRAMEWORK CONFIGURATION
# ============================================================================

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
}

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'file': {
            'level': 'INFO',
            'filters': ['require_debug_false'],
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'icfda2025.log',
            'formatter': 'verbose',
        },
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file', 'mail_admins'],
            'level': 'INFO',
        },
        'registration': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    },
}

# Create logs directory if it doesn't exist
log_dir = BASE_DIR / 'logs'
log_dir.mkdir(exist_ok=True)

# ============================================================================
# ICFDA 2025 SPECIFIC CONFIGURATION
# ============================================================================

ICFDA_2025_CONFIG = {
    # Conference Information
    'CONFERENCE_NAME': 'International Conference on Fractional Differentiation and its Applications',
    'CONFERENCE_SHORT_NAME': 'ICFDA 2025',
    'CONFERENCE_YEAR': 2025,
    'CONFERENCE_LOCATION': 'Hotel Mercure Alger Bab Ezzouar, Algiers, Algeria',
    'CONFERENCE_WEBSITE': 'https://conferences.ifac-control.org/icfda2025/',
    
    # Conference Dates
    'CONFERENCE_START_DATE': date(2025, 12, 15),
    'CONFERENCE_END_DATE': date(2025, 12, 18),
    
    # Registration Periods and Deadlines
    'REGISTRATION_PERIODS': {
        'EARLY_DEADLINE': date(2025, 10, 15),
        'NORMAL_DEADLINE': date(2025, 11, 21),
        # Late registration has no deadline
    },
    
    # Registration Limits
    'MAX_TOTAL_REGISTRATIONS': config('MAX_REGISTRATIONS', default=500, cast=int),
    'MAX_PAPERS_PER_REGISTRATION': config('MAX_PAPERS_PER_REG', default=5, cast=int),
    'MAX_ACCOMPANYING_PERSONS': 1,
    
    # Pricing (in respective currencies)
    'PRICING': {
        'ABROAD': {  # Prices in EUR
            'FULL_REGISTRATION': {
                'early': 250, 'normal': 300, 'late': 350
            },
            'STUDENT_REGISTRATION': {
                'early': 150, 'normal': 200, 'late': 250
            },
            'VISITOR_REGISTRATION': {
                'early': 0, 'normal': 0, 'late': 0
            },
            'TUTORIAL_FULL_DAY': {
                'full': {'early': 80, 'normal': 80, 'late': 100},
                'student': {'early': 50, 'normal': 50, 'late': 80}
            },
            'TUTORIAL_PERIOD': {
                'full': {'early': 50, 'normal': 50, 'late': 70},
                'student': {'early': 40, 'normal': 40, 'late': 60}
            },
            'ADDITIONAL_PAPER': 100,
            'MEALS': {
                'gala_dinner': 80,
                'dinner': 40,
                'welcome_dinner': 40,
            },
            'SOCIAL_PROGRAM': 20,
            'ACCOMMODATION': {
                'single_room_per_night': 70,
                'double_room_per_night': 84,
            },
            'ACCOMPANYING_PERSON': {
                'gala_dinner': 80,
                'dinner': 40,
                'welcome_dinner': 40,
                'welcome_lunch': 40,
                'lunch_16': 40,
                'lunch_17': 40,
            }
        },
        'ALGERIA': {  # Prices in DZD
            'FULL_REGISTRATION': {
                'early': 20000, 'normal': 25000, 'late': 30000
            },
            'STUDENT_REGISTRATION': {
                'early': 15000, 'normal': 20000, 'late': 25000
            },
            'VISITOR_REGISTRATION': {
                'early': 0, 'normal': 0, 'late': 0
            },
            'TUTORIAL_FULL_DAY': {
                'full': {'early': 8000, 'normal': 8000, 'late': 10000},
                'student': {'early': 4000, 'normal': 4000, 'late': 7000}
            },
            'TUTORIAL_PERIOD': {
                'full': {'early': 5000, 'normal': 5000, 'late': 8000},
                'student': {'early': 3000, 'normal': 3000, 'late': 5000}
            },
            'MEALS': {
                'gala_dinner': 6000,
                'dinner': 5500,
                'welcome_dinner': 5500,
            },
            'ACCOMMODATION': {
                'single_room_per_night': 10500,
                'double_room_per_night': 12500,
            },
            'ACCOMPANYING_PERSON': {
                'gala_dinner': 5000,  # Updated price
                'dinner': 5500,
                'welcome_dinner': 5500,
                'welcome_lunch': 5500,
                'lunch_16': 5500,
                'lunch_17': 5500,
            }
        }
    },
    
    # Hotel Reservation Email Configuration
'HOTEL_RESERVATION_EMAILS': {
    'TO_EMAILS': [
        'nasro.mellah@gmail.com',  # Hotel responsible person
        # Add other hotel staff emails if needed:
        # 'lynda.kaci@accor.com',
        # 'H3173-re@accor.com',
        # 'Amir.BENSAADA@accor.com'
    ],
    'CC_EMAILS': [
        'samir.ladaci@g.enp.edu.dz',  # Conference organizer
        'nasr_eddine.mellah@g.enp.edu.dz',  # Registration coordinator
    ],
    'REPLY_TO_EMAIL': 'nasr_eddine.mellah@g.enp.edu.dz'
},
    
    # Bank Transfer Details
    'BANK_DETAILS': {
        'BANK_NAME': 'Crédit Populaire d\'Algérie (CPA)',
        'BRANCH': 'Agence 146 Bab Ezzouar',
        'ACCOUNT_HOLDER': 'EGT CENTRE GRAND HOTEL MERCURE',
        'SWIFT_CODE': 'CPALDZAL',
        'IBAN_PREFIX': 'DZ 004',
        
        'ACCOUNTS': {
            'EUR': {
                'RIB': '00400146520817019018',
                'IBAN': 'DZ 00400146520817019018',
                'CURRENCY': 'EUR',
                'DESCRIPTION': 'EUR Account'
            },
            'USD': {
                'RIB': '00400146520817013974',
                'IBAN': 'DZ 00400146520817013974',
                'CURRENCY': 'USD',
                'DESCRIPTION': 'USD Account'
            },
            'DZD': {
                'RIB': '00400146401708170149',
                'IBAN': 'DZ 00400146401708170149',
                'CURRENCY': 'DZD',
                'DESCRIPTION': 'DZD Account'
            }
        }
    },
    
    # Contact Information
    'CONTACT_INFO': {
        'GENERAL_EMAIL': 'samir.ladaci@g.enp.edu.dz',
        'REGISTRATION_EMAIL': 'nasr_eddine.mellah@g.enp.edu.dz',
        'TECHNICAL_EMAIL': 'nasro.mellah@gmail.com',
        'FINANCE_EMAIL': 'samir.ladaci@g.enp.edu.dz',
        'PHONE': '+213 XXX XXX XXX',
        'FAX': '+213 XXX XXX XXX',
    },
    
    # Social Media and External Links
    'SOCIAL_MEDIA': {
        'FACEBOOK': 'https://facebook.com/icfda2025',
        'TWITTER': 'https://twitter.com/icfda2025',
        'LINKEDIN': 'https://linkedin.com/company/icfda2025',
        'YOUTUBE': 'https://youtube.com/icfda2025'
    },
    
    # File Upload Settings
    'FILE_UPLOAD': {
        'MAX_FILE_SIZE': 10 * 1024 * 1024,  # 10MB
        'ALLOWED_EXTENSIONS': ['.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png'],
        'UPLOAD_PATH': 'uploads/registrations/',
    },
    
    # Email Templates
    'EMAIL_TEMPLATES': {
        'CONFIRMATION': 'registration/email_registration.html',
        'PAYMENT_CONFIRMATION': 'registration/email_payment.html',
        'HOTEL_RESERVATION': 'registration/email_hotel_reservation.html',
        'REMINDER': 'registration/email_reminder.html',
        'WELCOME': 'registration/email_welcome.html',
    },
    
    # System Limits and Quotas
    'SYSTEM_LIMITS': {
        'REGISTRATION_RATE_LIMIT': '10/hour',  # Max 10 registrations per IP per hour
        'EMAIL_RATE_LIMIT': '50/day',          # Max 50 emails per day per recipient
        'API_RATE_LIMIT': '100/hour',          # Max 100 API calls per hour
    },
    
    # Feature Flags
    'FEATURES': {
        'ENABLE_ONLINE_PAYMENT': config('ENABLE_ONLINE_PAYMENT', default=True, cast=bool),
        'ENABLE_HOTEL_RESERVATIONS': config('ENABLE_HOTEL_RESERVATIONS', default=True, cast=bool),
        'ENABLE_VISITOR_REGISTRATION': config('ENABLE_VISITOR_REGISTRATION', default=True, cast=bool),
        'ENABLE_TUTORIALS': config('ENABLE_TUTORIALS', default=True, cast=bool),
        'ENABLE_SOCIAL_PROGRAM': config('ENABLE_SOCIAL_PROGRAM', default=True, cast=bool),
        'ENABLE_BULK_REGISTRATION': config('ENABLE_BULK_REGISTRATION', default=False, cast=bool),
        'ENABLE_EARLY_BIRD_PRICING': config('ENABLE_EARLY_BIRD_PRICING', default=True, cast=bool),
        'MAINTENANCE_MODE': config('MAINTENANCE_MODE', default=False, cast=bool),
    },
    
    # Conference Program Schedule
    'PROGRAM_SCHEDULE': {
        'DAY_1': {  # December 15, 2025
            'date': '2025-12-15',
            'events': [
                {'time': '08:00-09:00', 'event': 'Registration and Welcome Coffee'},
                {'time': '09:00-10:00', 'event': 'Opening Ceremony'},
                {'time': '10:00-12:00', 'event': 'Keynote Sessions'},
                {'time': '19:00-22:00', 'event': 'Welcome Dinner'},
            ]
        },
        'DAY_2': {  # December 16, 2025
            'date': '2025-12-16',
            'events': [
                {'time': '09:00-12:00', 'event': 'Technical Sessions'},
                {'time': '14:00-17:00', 'event': 'Paper Presentations'},
                {'time': '19:00-22:00', 'event': 'Conference Dinner'},
            ]
        },
        'DAY_3': {  # December 17, 2025
            'date': '2025-12-17',
            'events': [
                {'time': '09:00-12:00', 'event': 'Technical Sessions'},
                {'time': '14:00-17:00', 'event': 'Panel Discussions'},
                {'time': '19:00-23:00', 'event': 'Gala Dinner'},
            ]
        },
        'DAY_4': {  # December 18, 2025
            'date': '2025-12-18',
            'events': [
                {'time': '09:00-12:00', 'event': 'Final Sessions'},
                {'time': '12:00-13:00', 'event': 'Closing Ceremony'},
                {'time': '14:00-18:00', 'event': 'Cultural Visit of Algiers (Optional)'},
            ]
        }
    }
}

# ============================================================================
# PERFORMANCE SETTINGS
# ============================================================================

# Database connection pooling
if 'postgresql' in DATABASES['default']['ENGINE']:
    DATABASES['default']['OPTIONS'] = {
        'MAX_CONNS': 20,
        'OPTIONS': {
            'MAX_CONNS': 20
        }
    }

# File upload settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
FILE_UPLOAD_PERMISSIONS = 0o644

# ============================================================================
# DEVELOPMENT SETTINGS
# ============================================================================

if DEBUG:
    # Add django-debug-toolbar if available
    try:
        import debug_toolbar
        INSTALLED_APPS.append('debug_toolbar')
        MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')
        
        INTERNAL_IPS = [
            '127.0.0.1',
            'localhost',
        ]
        
        DEBUG_TOOLBAR_CONFIG = {
            'SHOW_TOOLBAR_CALLBACK': lambda request: True,
        }
    except ImportError:
        pass

# ============================================================================
# PRODUCTION OVERRIDES
# ============================================================================

# Load production settings from environment
if not DEBUG:
    # Use environment variables for sensitive data
    SECRET_KEY = config('SECRET_KEY')
    
    # Database configuration
    if config('DATABASE_URL', default=''):
        import dj_database_url
        DATABASES['default'] = dj_database_url.parse(config('DATABASE_URL'))
    
    # Email configuration must be set in production
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    
    # Cache configuration for production
    if config('REDIS_URL', default=''):
        CACHES = {
            'default': {
                'BACKEND': 'django_redis.cache.RedisCache',
                'LOCATION': config('REDIS_URL'),
                'OPTIONS': {
                    'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                }
            }
        }
    
    # Set session engine to cache if Redis is available
    if 'redis' in CACHES['default']['BACKEND'].lower():
        SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
        SESSION_CACHE_ALIAS = 'default'

# ============================================================================
# CUSTOM SETTINGS VALIDATION
# ============================================================================

def validate_icfda_settings():
    """Validate ICFDA specific settings"""
    errors = []
    
    # Check required email settings
    if not DEBUG and not EMAIL_HOST_USER:
        errors.append("EMAIL_HOST_USER must be set in production")
    
    # Check Stripe settings for production
    if not DEBUG and ICFDA_2025_CONFIG['FEATURES']['ENABLE_ONLINE_PAYMENT']:
        if not STRIPE_SECRET_KEY:
            errors.append("STRIPE_SECRET_KEY must be set for online payments")
    
    # Check database configuration
    if not DEBUG and 'sqlite3' in DATABASES['default']['ENGINE']:
        errors.append("SQLite should not be used in production")
    
    return errors

# Validate settings if not in testing environment
if not config('TESTING', default=False, cast=bool):
    validation_errors = validate_icfda_settings()
    if validation_errors and not DEBUG:
        import sys
        print("ICFDA 2025 Configuration Errors:")
        for error in validation_errors:
            print(f"  - {error}")
        if not DEBUG:
            print("Please fix these errors before running in production.")
            sys.exit(1)
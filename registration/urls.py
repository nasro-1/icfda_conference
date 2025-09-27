from django.urls import path
from . import views

app_name = 'registration'

urlpatterns = [
    # Main registration form
    path('', views.RegistrationFormView.as_view(), name='form'),
    
    # API endpoints
    path('api/check-email/', views.check_email, name='check_email'),
    path('api/check-national-id/', views.check_national_id, name='check_national_id'),
    path('api/calculate-price/', views.calculate_price, name='calculate_price'),
    path('api/current-period/', views.get_current_period_info, name='current_period'),
    
    # Payment and success pages
    path('payment/<uuid:registration_id>/', views.PaymentView.as_view(), name='payment'),
    path('success/<uuid:registration_id>/', views.RegistrationSuccessView.as_view(), name='success'),
    
    # Registration status API
    path('api/status/<uuid:registration_id>/', views.get_registration_status, name='registration_status'),
    
    # Webhook for payment processing
    path('webhook/stripe/', views.StripeWebhookView.as_view(), name='stripe_webhook'),
]

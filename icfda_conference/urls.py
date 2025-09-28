# icfda_conference/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse
from django.shortcuts import redirect

def home_redirect(request):
    """Redirect home page to registration form"""
    return redirect('registration:form')

def robots_txt(request):
    """Serve robots.txt"""
    lines = [
        "User-agent: *",
        "Allow: /",
        "Sitemap: https://icfda2025.com/sitemap.xml",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")

def health_check(request):
    """Health check endpoint for monitoring"""
    return HttpResponse("OK", status=200)

urlpatterns = [
    # Admin interface
    path('admin/', admin.site.urls),
    
    # Home page redirects to registration
    path('', home_redirect, name='home'),
    
    # Registration system
    path('registration/', include('registration.urls')),
    
    # Utility endpoints
    path('robots.txt', robots_txt),
    path('health/', health_check, name='health_check'),
]

# Serve media and static files in development
if settings.DEBUG:
    # This is the important part for serving static files
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0] if settings.STATICFILES_DIRS else settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    # Optional: Add debug toolbar if installed
    try:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns
    except ImportError:
        pass
# Import required modules
from django.contrib import admin
from django.urls import path
from myapp.views import *
from django.conf import settings
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf.urls.static import static

# Define URL patterns
urlpatterns = [
    path('home/', home, name="home"),                    # Home page
    path("admin/", admin.site.urls),                     # Admin interface
    path('login/', login_page, name='login_page'),       # Login page
    path('register/', register_page, name='register'),   # Registration page
    path('resume/', upload_resume, name='upload_resume'),# Resume page
]

# Serve media files in development mode
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Serve static files
urlpatterns += staticfiles_urlpatterns()
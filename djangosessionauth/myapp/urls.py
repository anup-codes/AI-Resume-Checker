# Import required modules
from django.contrib import admin
from django.urls import path
from myapp.views import home, auth_page, upload_resume
from django.conf import settings
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf.urls.static import static

# Define URL patterns
urlpatterns = [
    path('admin/', admin.site.urls),                # Admin interface
    path('auth/', auth_page, name='auth'),          # Login + Register (Single Page)
    path('home/', home, name="home"),               # Home page
    path('resume/', upload_resume, name='upload_resume'),  # Resume page
]

# Serve media files in development mode
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Serve static files
urlpatterns += staticfiles_urlpatterns()

# Import required modules
from django.contrib import admin
from django.urls import path
from myapp.views import auth_page, dashboard, upload_resume, logout_view
from django.conf import settings
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # Authentication
    path('auth/', auth_page, name='auth'),
    path('logout/', logout_view, name='logout'),

    # Dashboard
    path('dashboard/', dashboard, name='dashboard'),

    # Resume Upload (AJAX endpoint)
    path('upload-resume/', upload_resume, name='upload_resume'),
]

# Serve media files in development mode
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Serve static files
urlpatterns += staticfiles_urlpatterns()

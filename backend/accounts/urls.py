from django.urls import path
from .views import signup, login_view

urlpatterns = [
    path('signup/', signup),
    path('login/', login_view),
]

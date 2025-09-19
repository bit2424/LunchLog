from django.urls import path

from . import views

app_name = 'users'

urlpatterns = [
    path('auth/signup/', views.CreateUserView.as_view(), name='signup'),
    path('auth/login/', views.LoginView.as_view(), name='login'),
]

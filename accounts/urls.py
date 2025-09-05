from django.urls import path
from django.contrib.auth.views import LogoutView, PasswordChangeDoneView
from django.views.generic import TemplateView
from .views import solicitar_acesso, CustomPasswordChangeView, CustomLoginView


# O app_name é uma boa prática para evitar conflitos de nomes de URL entre apps.
app_name = 'accounts'


urlpatterns = [
    path('login/', CustomLoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', TemplateView.as_view(template_name='registration/logout.html'), name='logout'),
    path('logout/perform/', LogoutView.as_view(next_page='/'), name='logout_perform'),
    path('solicitar_acesso/', solicitar_acesso, name='solicitar_acesso'),
    path('password_change/', CustomPasswordChangeView.as_view(), name='password_change'),
    path('password_change/done/', PasswordChangeDoneView.as_view(template_name='registration/password_change_done.html'), name='password_change_done'),
]
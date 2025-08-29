"""
URL configuration for dashboard_ve project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView
from dashboard.views import dashboard_view, solicitar_acesso
from dashboard.views import CustomPasswordChangeView

from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect

class CustomLoginView(LoginView):
    template_name = 'registration/login.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('/')
        return super().dispatch(request, *args, **kwargs)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', dashboard_view, name='dashboard'),
    path('login/', CustomLoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/confirm/', TemplateView.as_view(template_name='registration/logout.html'), name='logout_confirm'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('solicitar_acesso/', solicitar_acesso, name='solicitar_acesso'),
    path('dashboard/', include('dashboard.urls')),
    path('ubs_consulta/', include('ubs_consulta.urls')),
    path('busca_docs/', include('busca_docs.urls')),
    path('quadro_equipe/', include('quadro_equipe.urls')),
    path('accounts/password_change/', CustomPasswordChangeView.as_view(), name='password_change'),
    path('accounts/password_change/done/', auth_views.PasswordChangeDoneView.as_view(template_name='registration/password_change_done.html'), name='password_change_done'),
    path('controle_oficio/', include('controle_oficio.urls')),
]


# SERVE ARQUIVOS DE MÍDIA (upload de imagens, etc.)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

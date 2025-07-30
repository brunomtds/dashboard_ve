from django.urls import reverse
from django.shortcuts import redirect

class FirstAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            try:
                profile = request.user.profile
                if profile.first_access and request.path not in [reverse('password_change'), reverse('logout')]:
                    return redirect('password_change')
            except Exception:
                # Perfil não existe ou erro no banco — continue normalmente
                pass

        return self.get_response(request)

from django.shortcuts import redirect
from django.urls import reverse
from django.conf import settings


class LoginRequiredMiddleware:
    # Esta classe continua igual à versão que funcionou, sem alterações.
    def __init__(self, get_response):
        self.get_response = get_response
        self.public_url_names = [
            'accounts:login', 'accounts:logout', 'accounts:logout_perform',
            'accounts:solicitar_acesso', 'accounts:password_change', 'accounts:password_change_done',
        ]
        self.public_paths = []
        for name in self.public_url_names:
            try:
                self.public_paths.append(reverse(name))
            except Exception:
                pass
        self.public_paths.append(settings.ADMIN_URL)

    def __call__(self, request):
        if not request.user.is_authenticated:
            is_public = False
            for path in self.public_paths:
                if request.path.startswith(path):
                    is_public = True
                    break
            
            if not is_public:
                login_url = f"{reverse('accounts:login')}?next={request.path}"
                return redirect(login_url)

        return self.get_response(request)
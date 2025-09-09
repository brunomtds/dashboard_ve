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


class FirstAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        # A lógica só se aplica a usuários autenticados.
        if not request.user.is_authenticated:
            return self.get_response(request)

        # Verifica se o usuário tem o perfil e se o 'first_access' está ativo.
        try:
            profile = request.user.profile
            if not profile.first_access:
                return self.get_response(request)
        except AttributeError:
            return self.get_response(request)

        # Se chegamos até aqui, o usuário está autenticado e com first_access=True.

        # Define a lista de URLs que o usuário PODE acessar.
        allowed_paths = [
            reverse('accounts:password_change'),
            reverse('accounts:password_change_done'),
            reverse('accounts:logout'),
            reverse('accounts:logout_perform'),
        ]


        # A verificação principal:
        if request.path not in allowed_paths:
            return redirect('accounts:password_change')

        return self.get_response(request)
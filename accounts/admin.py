from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import SolicitacaoAcesso, UserProfile, Departamento
from django.utils.crypto import get_random_string

# Classe para mostrar o Perfil dentro da página do Usuário (sem alterações)
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Perfil do Usuário'

class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)

admin.site.unregister(User)
admin.site.register(User, UserAdmin)


# ========================================================================
# == NOVA LÓGICA DE CRIAÇÃO AUTOMÁTICA DE USUÁRIO ADICIONADA AQUI ==
# ========================================================================
@admin.register(SolicitacaoAcesso)
class SolicitacaoAcessoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'email', 'departamento', 'aprovado', 'criado_em')
    list_filter = ('aprovado', 'departamento', 'criado_em')
    search_fields = ('nome', 'email')
    list_editable = ('aprovado',)

    def save_model(self, request, obj, form, change):
        if 'aprovado' in form.changed_data and obj.aprovado:
            
            if not User.objects.filter(email=obj.email).exists():
                # ALTERAÇÃO 2: Usamos get_random_string para criar a senha
                # O ideal é uma senha com letras, números e alguns caracteres especiais.
                allowed_chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*(-_=+)'
                temp_password = get_random_string(12, allowed_chars)

                username = obj.email.split('@')[0]
                original_username = username
                counter = 1
                while User.objects.filter(username=username).exists():
                    username = f"{original_username}{counter}"
                    counter += 1
                
                primeiro_nome = obj.nome.split()[0]

                try:
                    departamento = Departamento.objects.get(id=obj.departamento.id)
                    
                    user = User.objects.create_user(
                        username=username,
                        first_name=primeiro_nome,
                        email=obj.email,
                        password=temp_password
                    )

                    UserProfile.objects.create(
                        user=user,
                        ramal=obj.ramal,
                        departamento=departamento,
                        first_access=True
                    )

                    messages.success(request, f"Usuário {username} criado com sucesso! A senha temporária é: {temp_password}")
                
                except Departamento.DoesNotExist:
                    messages.error(request, f"Não foi possível criar o usuário. O departamento selecionado não existe.")
            else:
                messages.warning(request, f"Um usuário com o e-mail {obj.email} já existe. Nenhuma nova conta foi criada.")

        super().save_model(request, obj, form, change)

from django.contrib import admin
from .models import Funcionario, Departamento, Responsabilidade

@admin.register(Departamento)
class DepartamentoAdmin(admin.ModelAdmin):
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "chefe":
            kwargs["queryset"] = Funcionario.objects.filter(is_chefia=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

admin.site.register(Funcionario)
admin.site.register(Responsabilidade)

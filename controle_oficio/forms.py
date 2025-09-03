from django import forms
from .models import Entidade

class EntidadeForm(forms.ModelForm):
    class Meta:
        model = Entidade
        # Liste todos os campos que seu formulário utiliza
        fields = ['tipo', 'tipo_documento', 'numero_documento', 'nome', 'responsavel_tecnico']
        
        # Aqui definimos os atributos para os widgets HTML
        widgets = {
            'tipo': forms.Select(
                attrs={
                    'class': 'form-select',
                    'placeholder': 'Selecione o tipo de entidade'
                }
            ),
            'tipo_documento': forms.Select(
                attrs={
                    'class': 'form-select'
                }
            ),
            'numero_documento': forms.TextInput(
                attrs={
                    'class': 'form-input', 
                    'placeholder': 'Digite o número do documento'
                }
            ),
            'nome': forms.TextInput(
                attrs={
                    'class': 'form-input', 
                    'placeholder': 'Nome completo da entidade ou profissional'
                }
            ),
            'responsavel_tecnico': forms.TextInput(
                attrs={
                    'class': 'form-input', 
                    'placeholder': 'Nome do responsável (opcional)'
                }
            ),
        }
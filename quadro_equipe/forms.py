from django import forms
from .models import Funcionario, Responsabilidade, Departamento


class FuncionarioForm(forms.ModelForm):
    class Meta:
        model = Funcionario
        fields = ['nome', 'departamento', 'ramal', 'responsabilidades', 'is_chefia']  # sem 'chefe'
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'mt-1 block w-full p-2 border rounded-md',
                'placeholder': 'Digite o nome do funcionário'
            }),
            'departamento': forms.Select(attrs={
                'class': 'mt-1 block w-full p-2 border rounded-md'
            }),
            'ramal': forms.TextInput(attrs={
                'class': 'mt-1 block w-full p-2 border rounded-md',
                'placeholder': 'XXXX'
            }),
            'responsabilidades': forms.CheckboxSelectMultiple(attrs={'class': 'peer hidden'}),
            'is_chefia': forms.CheckboxInput(),
        }
        labels = {
            'nome': 'Nome do Funcionário',
            'departamento': 'Departamento',
            'ramal': 'Ramal',
            'responsabilidades': 'Responsabilidades',
            'is_chefia': 'Este funcionário é Chefia?',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['departamento'].queryset = Departamento.objects.order_by('nome')
        self.fields['responsabilidades'].queryset = Responsabilidade.objects.order_by('nome')

        # Tornar categoria opcional
        self.fields['departamento'].empty_label = "Selecione um departamento"


class ResponsabilidadeForm(forms.ModelForm):
    class Meta:
        model = Responsabilidade
        fields = ['nome', 'descricao']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }
        labels = {
            'nome': 'Nome da Responsabilidade',
            'descricao': 'Descrição',
        }

class DepartamentoForm(forms.ModelForm):
    class Meta:
        model = Departamento
        fields = ['nome', 'descricao', 'chefe']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'chefe': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'nome': 'Nome do Departamento',
            'descricao': 'Descrição',
            'chefe': 'Chefe do Departamento',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Limitar o chefe para funcionários que são chefia
        self.fields['chefe'].queryset = Funcionario.objects.filter(is_chefia=True).order_by('nome')

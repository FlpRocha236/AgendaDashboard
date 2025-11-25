from django import forms
from .models import Transacao, Compromisso, Nota 
from django.contrib.auth.models import User

# Estilo padrão do Bootstrap para todos os campos
class BootstrapModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            
            # Ajuste para campos de data (HTML5 Date Picker)
            if 'data' in field_name or 'data_hora' in field_name:
                field.widget.attrs['type'] = 'date' 

class TransacaoForm(BootstrapModelForm):
    class Meta:
        model = Transacao
        fields = ['descricao', 'valor', 'tipo', 'categoria', 'data', 'pago']

class CompromissoForm(BootstrapModelForm):
    class Meta:
        model = Compromisso
        fields = ['titulo', 'data_hora', 'local', 'descricao', 'concluido']
        widgets = {
            'data_hora': forms.DateTimeInput(attrs={'type': 'datetime-local'}), # Picker de data e hora
            'descricao': forms.Textarea(attrs={'rows': 3}),
        }

class NotaForm(BootstrapModelForm):
    class Meta:
        model = Nota
        fields = ['titulo', 'conteudo', 'cor']
        widgets = {
            'conteudo': forms.Textarea(attrs={'rows': 5}),
            'cor': forms.Select(choices=[
                ('white', 'Branco'),
                ('#fff9c4', 'Amarelo'),
                ('#c8e6c9', 'Verde'),
                ('#ffccbc', 'Laranja'),
                ('#bbdefb', 'Azul'),
            ])
        }

class PerfilForm(BootstrapModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'username']
        help_texts = {
            'username': 'Seu nome de usuário para login.',
        }
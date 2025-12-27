from django import forms
from .models import Compromisso, Nota, Transacao, CartaoCredito, DespesaCartao, Ativo, OperacaoInvestimento, Desafio, ContaPagar
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

# --- FORMS DE TRANSAÇÃO ---
class TransacaoForm(forms.ModelForm):
    class Meta:
        model = Transacao
        fields = ['descricao', 'valor', 'tipo', 'data']
        widgets = {
            'data': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'descricao': forms.TextInput(attrs={'class': 'form-control'}),
            'valor': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'tipo': forms.Select(attrs={'class': 'form-control'}),
        }

# --- FORMS DE AGENDA ---
class CompromissoForm(forms.ModelForm):
    class Meta:
        model = Compromisso
        fields = ['titulo', 'data_hora', 'descricao']
        widgets = {
            'data_hora': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'titulo': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

# --- FORMS DE NOTAS ---
class NotaForm(forms.ModelForm):
    class Meta:
        model = Nota
        fields = ['titulo', 'conteudo', 'cor']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control'}),
            'conteudo': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'cor': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
        }

# --- FORMS DE CONFIGURAÇÃO ---
class PerfilForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

# --- FORMS DE CARTÃO E DESPESAS ---
class CartaoForm(forms.ModelForm):
    class Meta:
        model = CartaoCredito
        fields = ['nome', 'limite', 'dia_vencimento', 'cor_cartao']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'limite': forms.NumberInput(attrs={'class': 'form-control'}),
            'dia_vencimento': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 31}),
            'cor_cartao': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
        }

class DespesaCartaoForm(forms.ModelForm):
    class Meta:
        model = DespesaCartao
        fields = ['cartao', 'descricao', 'valor', 'data_compra', 'parcelas']
        widgets = {
            'cartao': forms.Select(attrs={'class': 'form-control'}),
            'descricao': forms.TextInput(attrs={'class': 'form-control'}),
            'valor': forms.NumberInput(attrs={'class': 'form-control'}),
            'data_compra': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'parcelas': forms.NumberInput(attrs={'class': 'form-control'}),
        }

# --- FORMS DE INVESTIMENTOS ---
class AtivoForm(forms.ModelForm):
    class Meta:
        model = Ativo
        fields = ['codigo', 'tipo', 'setor']
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: PETR4'}),
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'setor': forms.TextInput(attrs={'class': 'form-control'}),
        }

class OperacaoInvestimentoForm(forms.ModelForm):
    class Meta:
        model = OperacaoInvestimento
        fields = ['ativo', 'tipo', 'quantidade', 'preco_unitario', 'taxas', 'data']
        widgets = {
            'ativo': forms.Select(attrs={'class': 'form-control'}),
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'quantidade': forms.NumberInput(attrs={'class': 'form-control'}),
            'preco_unitario': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'taxas': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'data': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }

# --- FORM DE DESAFIOS (Metas) ---
class DesafioForm(forms.ModelForm):
    class Meta:
        model = Desafio
        fields = ['objetivo', 'valor_inicial', 'incremento', 'duracao_semanas', 'data_inicio']
        widgets = {
            'objetivo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Comprar Notebook'}),
            'valor_inicial': forms.NumberInput(attrs={'class': 'form-control'}),
            'incremento': forms.NumberInput(attrs={'class': 'form-control'}),
            'duracao_semanas': forms.NumberInput(attrs={'class': 'form-control'}),
            'data_inicio': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }

# --- FORM DE CADASTRO DE USUÁRIO (O CORRIGIDO) ---
class UsuarioRegistroForm(UserCreationForm):
    # CORREÇÃO AQUI: Usamos forms.EmailField, não models.EmailField
    email = forms.EmailField(required=True, label='E-mail')

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

class ContaPagarForm(forms.ModelForm):
    class Meta:
        model = ContaPagar
        fields = ['titulo', 'valor', 'data_vencimento', 'recorrencia']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Seguro do Carro'}),
            'valor': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'data_vencimento': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'recorrencia': forms.Select(attrs={'class': 'form-control'}),
        }
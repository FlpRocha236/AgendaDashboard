from django import forms
from django.contrib.auth.models import User
from .models import (
    Compromisso, Nota, Transacao, CartaoCredito, DespesaCartao, 
    Ativo, OperacaoInvestimento, Desafio, ContaPagar
)

# --- USUÁRIO E PERFIL ---

class UsuarioRegistroForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password != confirm_password:
            raise forms.ValidationError("As senhas não conferem.")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user

class PerfilForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

# --- FINANÇAS E CARTÕES ---

class TransacaoForm(forms.ModelForm):
    class Meta:
        model = Transacao
        fields = ['descricao', 'valor', 'tipo', 'categoria', 'data', 'pago']
        widgets = {
            'descricao': forms.TextInput(attrs={'class': 'form-control'}),
            'valor': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'data': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'pago': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class CartaoForm(forms.ModelForm):
    class Meta:
        model = CartaoCredito
        fields = ['nome', 'limite', 'dia_fechamento', 'dia_vencimento', 'cor_cartao']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Nubank'}),
            'limite': forms.NumberInput(attrs={'class': 'form-control'}),
            'dia_fechamento': forms.NumberInput(attrs={'class': 'form-control'}),
            'dia_vencimento': forms.NumberInput(attrs={'class': 'form-control'}),
            'cor_cartao': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color'}),
        }

class DespesaCartaoForm(forms.ModelForm):
    class Meta:
        model = DespesaCartao
        fields = ['cartao', 'descricao', 'valor', 'parcelas', 'data_compra', 'categoria']
        widgets = {
            'cartao': forms.Select(attrs={'class': 'form-select'}),
            'descricao': forms.TextInput(attrs={'class': 'form-control'}),
            'valor': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'parcelas': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'data_compra': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
        }

# --- INVESTIMENTOS ---

class AtivoForm(forms.ModelForm):
    class Meta:
        model = Ativo
        # CORREÇÃO AQUI: Trocamos 'codigo' por 'ticker' e adicionamos 'setor'
        fields = ['ticker', 'tipo', 'setor']
        widgets = {
            'ticker': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: WEGE3, BTC'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'setor': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Bancos, Tecnologia'}),
        }

class OperacaoInvestimentoForm(forms.ModelForm):
    class Meta:
        model = OperacaoInvestimento
        fields = ['ativo', 'tipo', 'data', 'quantidade', 'preco_unitario', 'taxas']
        widgets = {
            'ativo': forms.Select(attrs={'class': 'form-select'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'data': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'quantidade': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.00000001'}),
            'preco_unitario': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'taxas': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

# --- AGENDA E NOTAS ---

class CompromissoForm(forms.ModelForm):
    class Meta:
        model = Compromisso
        fields = ['titulo', 'data_hora', 'local', 'descricao']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control'}),
            'data_hora': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'local': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class NotaForm(forms.ModelForm):
    class Meta:
        model = Nota
        fields = ['titulo', 'conteudo', 'cor']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control'}),
            'conteudo': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'cor': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color'}),
        }

# --- DESAFIOS ---

class DesafioForm(forms.ModelForm):
    class Meta:
        model = Desafio
        fields = ['objetivo', 'valor_inicial', 'incremento', 'duracao_semanas', 'data_inicio']
        widgets = {
            'objetivo': forms.TextInput(attrs={'class': 'form-control'}),
            'valor_inicial': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'incremento': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'duracao_semanas': forms.NumberInput(attrs={'class': 'form-control'}),
            'data_inicio': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }

# --- CONTAS A PAGAR ---

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
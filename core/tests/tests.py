from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from core.models import Transacao, Compromisso, Nota
from core.forms import TransacaoForm
from datetime import date, datetime, timedelta
from django.utils import timezone

class ModelTest(TestCase):
    def setUp(self):
        # Cria um usuário para os testes (obrigatório pois nossos models dependem de User)
        self.user = User.objects.create_user(username='testuser', password='123')

    def test_transacao_str(self):
        """Teste: O __str__ da Transação deve mostrar sinal e valor corretamente"""
        t = Transacao.objects.create(
            user=self.user,
            descricao="Salário",
            valor=5000.00,
            tipo="receita",
            data=date.today()
        )
        # Verifica se o texto retornado é "+ R$ 5000.0 - Salário"
        self.assertEqual(str(t), "+ R$ 5000.0 - Salário")

    def test_compromisso_criacao(self):
        """Teste: Criação simples de compromisso"""
        agora = timezone.now()
        c = Compromisso.objects.create(
            user=self.user,
            titulo="Reunião",
            data_hora=agora
        )
        self.assertEqual(c.titulo, "Reunião")
        self.assertFalse(c.concluido) # Deve nascer como não concluído

class ViewTest(TestCase):
    def setUp(self):
        # Configura o cliente (navegador simulado) e o usuário
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='123')
        
    def test_acesso_sem_login(self):
        """Teste: Tentar acessar o dashboard sem logar deve redirecionar para login"""
        response = self.client.get(reverse('dashboard'))
        # 302 é o código de redirecionamento
        self.assertEqual(response.status_code, 302) 
        # Verifica se mandou para /accounts/login/
        self.assertIn('/accounts/login/', response.url)

    def test_dashboard_com_login(self):
        """Teste: Com login, o dashboard deve abrir (200 OK) e mostrar o saldo"""
        self.client.force_login(self.user) # Força o login sem precisar digitar senha
        
        # Cria dados fictícios para ver se aparecem na tela
        Transacao.objects.create(user=self.user, descricao="Teste", valor=100, tipo='receita', data=date.today())
        
        response = self.client.get(reverse('dashboard'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard.html')
        # Verifica se o contexto da view calculou o saldo certo (100)
        self.assertEqual(response.context['saldo'], 100)

    def test_dados_de_outro_usuario(self):
        """Teste de Segurança: Eu não posso ver as transações de outro usuário"""
        # Cria um usuário "intruso" e loga com ele
        outro_user = User.objects.create_user(username='intruso', password='123')
        self.client.force_login(outro_user)

        # Cria uma transação para o usuário ORIGINAL (self.user)
        Transacao.objects.create(user=self.user, descricao="Segredo", valor=10000, tipo='receita', data=date.today())

        response = self.client.get(reverse('financas'))
        
        # A lista de transações no contexto deve estar vazia para o intruso
        self.assertEqual(len(response.context['transacoes']), 0)
        # E o HTML não deve conter a palavra "Segredo"
        self.assertNotContains(response, "Segredo")

class FormTest(TestCase):
    def test_transacao_form_valido(self):
        """Teste: Formulário preenchido corretamente deve ser válido"""
        dados = {
            'descricao': 'Compra Teste',
            'valor': 50.00,
            'tipo': 'despesa',
            'categoria': 'lazer',
            'data': date.today(),
            'pago': True
        }
        form = TransacaoForm(data=dados)
        self.assertTrue(form.is_valid())

    def test_transacao_form_invalido(self):
        """Teste: Formulário sem descrição deve falhar"""
        dados = {
            'descricao': '', # Vazio (erro)
            'valor': 50.00,
            'tipo': 'despesa',
            'data': date.today()
        }
        form = TransacaoForm(data=dados)
        self.assertFalse(form.is_valid())
        self.assertIn('descricao', form.errors) # O erro deve estar no campo descrição
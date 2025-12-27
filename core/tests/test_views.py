from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from core.models import Transacao

class DashboardViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='felipe', password='123')
        self.url = reverse('dashboard')

    def test_acesso_sem_login(self):
        """Se tentar entrar sem logar, deve redirecionar para login"""
        response = self.client.get(self.url)
        self.assertNotEqual(response.status_code, 200)
        self.assertEqual(response.status_code, 302)

    def test_acesso_com_login(self):
        """Com login, deve carregar a dashboard"""
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard.html')

class TransacaoViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='felipe', password='123')
        self.client.force_login(self.user)
        self.url_nova = reverse('transacao_nova')

    def test_criar_receita(self):
        """Testa se o formulário cria a transação no banco"""
        dados = {
            'descricao': 'Salário Teste',
            'valor': 5000.00,
            'tipo': 'receita',
            'categoria': 'salario',
            'data': '2025-10-10',
            'pago': True
        }
        response = self.client.post(self.url_nova, dados)
        
        # Deve redirecionar após salvar (302)
        self.assertEqual(response.status_code, 302)
        
        # Verifica se gravou no banco
        existe = Transacao.objects.filter(descricao='Salário Teste').exists()
        self.assertTrue(existe)
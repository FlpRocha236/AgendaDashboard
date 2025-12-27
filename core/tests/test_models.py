from django.test import TestCase
from django.contrib.auth.models import User
from core.models import Ativo, ContaPagar
from django.utils import timezone
from datetime import timedelta

class AtivoModelTest(TestCase):
    def setUp(self):
        # Cria um usuário e ativo para usar nos testes
        self.user = User.objects.create_user(username='testuser', password='123')
        self.ativo = Ativo.objects.create(
            user=self.user,
            ticker='TEST3',
            tipo='ACAO',
            quantidade_atual=10,
            preco_medio=25.50
        )

    def test_calculo_total_investido(self):
        """Verifica se Qtd * Preço Médio está batendo"""
        esperado = 10 * 25.50
        self.assertEqual(self.ativo.total_investido(), esperado)

class ContaPagarModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='123')

    def test_status_vencido(self):
        """Uma conta com data passada deve retornar 'atrasado'"""
        ontem = timezone.now().date() - timedelta(days=1)
        conta = ContaPagar.objects.create(
            user=self.user, titulo="Luz", valor=100, data_vencimento=ontem
        )
        self.assertEqual(conta.status_vencimento, 'atrasado')

    def test_status_hoje(self):
        """Uma conta que vence hoje deve retornar 'hoje'"""
        hoje = timezone.now().date()
        conta = ContaPagar.objects.create(
            user=self.user, titulo="Net", valor=100, data_vencimento=hoje
        )
        self.assertEqual(conta.status_vencimento, 'hoje')

    def test_status_pago(self):
        """Se pago=True, deve retornar 'pago' independente da data"""
        ontem = timezone.now().date() - timedelta(days=1)
        conta = ContaPagar.objects.create(
            user=self.user, titulo="Agua", valor=50, 
            data_vencimento=ontem, pago=True
        )
        self.assertEqual(conta.status_vencimento, 'pago')
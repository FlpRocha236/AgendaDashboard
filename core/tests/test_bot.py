from django.test import TestCase
from unittest.mock import patch, MagicMock
from django.contrib.auth.models import User
from core.models import Ativo, AnaliseBot
from core.bot_logic import executar_analise_carteira

class BotLogicTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='investidor', password='123')
        # Cria uma ação de teste
        self.ativo = Ativo.objects.create(
            user=self.user, ticker='TEST3', tipo='ACAO', quantidade_atual=100
        )

    @patch('core.bot_logic.yf.Ticker')
    def test_analise_acao_graham_aprovada(self, mock_ticker):
        """
        Simula uma ação perfeita que passa em todos os critérios de Graham/Bazin
        """
        # 1. Configura o Mock (Finge ser o Yahoo Finance)
        mock_instance = MagicMock()
        mock_ticker.return_value = mock_instance
        
        # Dados falsos que o Yahoo retornaria para uma empresa PERFEITA
        mock_instance.info = {
            'currentPrice': 20.00,
            'trailingPE': 5.0,        # P/L Barato (<15)
            'priceToBook': 1.0,       # P/VP Justo (<1.5)
            'dividendYield': 0.10,    # DY Alto (10%)
            'returnOnEquity': 0.20,   # ROE Alto (20%)
            'debtToEquity': 50.0      # Dívida Baixa (0.5)
        }

        # 2. Executa a função do Robô
        executar_analise_carteira(self.user)

        # 3. Verifica se o robô salvou a análise no banco
        analise = AnaliseBot.objects.get(ativo=self.ativo)
        
        # 4. Asserts (Validações)
        self.assertTrue(analise.criterio_dy)   # Deve ter passado no DY
        self.assertTrue(analise.criterio_pl)   # Deve ter passado no PL
        self.assertEqual(analise.pontuacao, 5) # Score Máximo
        self.assertIn("APORTAR", analise.recomendacao) # Recomendação de compra

    @patch('core.bot_logic.yf.Ticker')
    def test_analise_acao_ruim(self, mock_ticker):
        """
        Simula uma ação ruim (cara e sem dividendos)
        """
        mock_instance = MagicMock()
        mock_ticker.return_value = mock_instance
        
        # Dados de empresa ruim
        mock_instance.info = {
            'currentPrice': 50.00,
            'trailingPE': 100.0,      # P/L Altíssimo (>15)
            'priceToBook': 5.0,       # P/VP Caro (>1.5)
            'dividendYield': 0.0,     # Sem dividendos
            'returnOnEquity': 0.05,   # ROE Baixo
            'debtToEquity': 200.0     # Dívida Alta
        }

        executar_analise_carteira(self.user)
        
        analise = AnaliseBot.objects.get(ativo=self.ativo)
        self.assertEqual(analise.pontuacao, 0) # Score Zero
        self.assertIn("REVISAR", analise.recomendacao)
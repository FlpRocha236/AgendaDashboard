from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone 

# ==========================================
# 1. AGENDA / COMPROMISSOS
# ==========================================
class Compromisso(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    titulo = models.CharField(max_length=200)
    descricao = models.TextField(blank=True, null=True)
    data_hora = models.DateTimeField()
    local = models.CharField(max_length=200, blank=True, null=True)
    concluido = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.data_hora.strftime('%d/%m %H:%M')} - {self.titulo}"

    class Meta:
        ordering = ['data_hora']

# ==========================================
# 2. BLOCO DE NOTAS
# ==========================================
class Nota(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    titulo = models.CharField(max_length=200)
    conteudo = models.TextField()
    cor = models.CharField(max_length=20, default='#ffffff') 
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.titulo

# ==========================================
# 3. CONTROLE FINANCEIRO (Fluxo de Caixa)
# ==========================================
class Transacao(models.Model):
    TIPO_CHOICES = [
        ('receita', 'Receita (Entrada)'),
        ('despesa', 'Despesa (Saída)'),
    ]
    
    CATEGORIA_CHOICES = [
        ('salario', 'Salário'),
        ('freela', 'Freelance/Extra'),
        ('investimento', 'Investimentos'),
        ('moradia', 'Moradia/Contas'),
        ('alimentacao', 'Alimentação'),
        ('transporte', 'Transporte'),
        ('lazer', 'Lazer'),
        ('saude', 'Saúde'),
        ('educacao', 'Educação'),
        ('outros', 'Outros'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    descricao = models.CharField(max_length=200)
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    categoria = models.CharField(max_length=20, choices=CATEGORIA_CHOICES, default='outros')
    data = models.DateField()
    pago = models.BooleanField(default=True, verbose_name="Efetuado/Recebido")

    def __str__(self):
        sinal = "+" if self.tipo == 'receita' else "-"
        return f"{sinal} R$ {self.valor} - {self.descricao}"

    class Meta:
        verbose_name = "Transação"
        verbose_name_plural = "Transações"

# ==========================================
# 4. CARTÃO DE CRÉDITO
# ==========================================
class CartaoCredito(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    nome = models.CharField(max_length=50, help_text="Ex: Nubank, Visa Platinum")
    limite = models.DecimalField(max_digits=10, decimal_places=2)
    dia_fechamento = models.IntegerField(help_text="Dia que a fatura fecha (1-31)", default=1)
    dia_vencimento = models.IntegerField(help_text="Dia que a fatura vence (1-31)")
    cor_cartao = models.CharField(max_length=7, default='#4e73df', verbose_name="Cor do Cartão")
    
    def __str__(self):
        return self.nome

class DespesaCartao(models.Model):
    cartao = models.ForeignKey(CartaoCredito, on_delete=models.CASCADE, related_name='despesas')
    descricao = models.CharField(max_length=200)
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    data_compra = models.DateField()
    categoria = models.CharField(max_length=20, choices=Transacao.CATEGORIA_CHOICES, default='outros')
    
    # Controle de Parcelas
    parcelas = models.IntegerField(default=1, verbose_name="Qtde Parcelas")
    parcela_atual = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.descricao} ({self.parcela_atual}/{self.parcelas})"

# ==========================================
# 5. INVESTIMENTOS
# ==========================================

class Ativo(models.Model):
    TIPO_CHOICES = [
        ('ACAO', 'Ação B3'),
        ('FII', 'Fundo Imobiliário'),  # <--- ADICIONADO AQUI
        ('ETF', 'ETF'),
        ('CRIPTO', 'Criptomoeda'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    ticker = models.CharField(max_length=20) # Ex: WEGE3, XPLG11
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    setor = models.CharField(max_length=50, blank=True, null=True, help_text="Ex: Bancos, Logística")
    
    # Aumentei casas decimais para suportar frações de Cripto (ex: 0.00045 BTC)
    quantidade_atual = models.DecimalField(max_digits=15, decimal_places=8, default=0)
    preco_medio = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    def total_investido(self):
        return self.quantidade_atual * self.preco_medio

    def __str__(self):
        return f"{self.ticker} ({self.get_tipo_display()})"

# --- O CÉREBRO DO ROBÔ ---
class AnaliseBot(models.Model):
    ativo = models.OneToOneField(Ativo, on_delete=models.CASCADE, related_name='analise')
    data_analise = models.DateTimeField(auto_now=True)
    
    # Dados Coletados
    preco_atual = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    pl = models.DecimalField(max_digits=10, decimal_places=2, null=True) # Preço/Lucro
    pvp = models.DecimalField(max_digits=10, decimal_places=2, null=True) # Preço/VP
    dy = models.DecimalField(max_digits=10, decimal_places=2, null=True) # Dividend Yield
    roe = models.DecimalField(max_digits=10, decimal_places=2, null=True) # ROE
    divida_liquida_pl = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    
    # Critérios (Checklist)
    criterio_dy = models.BooleanField(default=False)
    criterio_pl = models.BooleanField(default=False)
    criterio_pvp = models.BooleanField(default=False)
    criterio_roe = models.BooleanField(default=False)
    criterio_divida = models.BooleanField(default=False)
    
    # Resultado Final
    pontuacao = models.IntegerField(default=0)
    recomendacao = models.CharField(max_length=50, default="AGUARDAR") 

    def __str__(self):
        return f"Análise {self.ativo.ticker}"

class OperacaoInvestimento(models.Model):
    TIPO_OPERACAO = [
        ('C', 'Compra'),
        ('V', 'Venda'),
        ('D', 'Dividendos/Rendimentos'),
    ]
    
    ativo = models.ForeignKey(Ativo, on_delete=models.CASCADE, related_name='operacoes')
    tipo = models.CharField(max_length=1, choices=TIPO_OPERACAO)
    data = models.DateField()
    quantidade = models.DecimalField(max_digits=15, decimal_places=8, default=0)
    preco_unitario = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    taxas = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    def valor_total(self):
        if self.tipo == 'D':
            return self.preco_unitario 
        return (self.quantidade * self.preco_unitario) + self.taxas

    def __str__(self):
        return f"{self.tipo} - {self.ativo.ticker} - {self.data}"

# ==========================================
# 6. DESAFIOS & METAS
# ==========================================

class Desafio(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    objetivo = models.CharField(max_length=100, help_text="Ex: Trocar de Moto, Viagem")
    valor_inicial = models.DecimalField(max_digits=20, decimal_places=2, verbose_name="Depósito da 1ª Semana") # Aumentei digits
    
    # O incremento não é mais usado na lógica de dobrar, mas mantemos para não precisar apagar do banco agora
    incremento = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Aumento por Semana", null=True, blank=True)
    
    duracao_semanas = models.IntegerField(default=12, verbose_name="Duração (Semanas)") # Reduzi default para 12 (mais realista pra dobrar)
    data_inicio = models.DateField(default=timezone.now)
    concluido = models.BooleanField(default=False)

    def total_planejado(self):
        # LÓGICA INTELIGENTE:
        # Se as semanas já foram geradas, somamos elas diretamente do banco.
        # Isso funciona tanto pra lógica antiga (Aritmética) quanto pra nova (Dobrar)
        if self.semanas.exists():
            return self.semanas.aggregate(models.Sum('valor'))['valor__sum'] or 0
        
        # Previsão Matemática (Caso ainda não tenha gerado): PG de razão 2
        # S_n = a1 * (2^n - 1)
        try:
            return self.valor_inicial * (2 ** self.duracao_semanas - 1)
        except:
            return 0

    def total_pago(self):
        return self.semanas.filter(pago=True).aggregate(models.Sum('valor'))['valor__sum'] or 0

    def progresso_percentual(self):
        total = self.total_planejado()
        if total == 0: return 0
        return (self.total_pago() / total) * 100

    def __str__(self):
        return self.objetivo

class SemanaDesafio(models.Model):
    desafio = models.ForeignKey(Desafio, on_delete=models.CASCADE, related_name='semanas')
    numero = models.IntegerField()
    data_prevista = models.DateField()
    # Aumentei max_digits aqui também para aguentar valores exponenciais
    valor = models.DecimalField(max_digits=20, decimal_places=2) 
    pago = models.BooleanField(default=False)
    data_pagamento = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ['numero']

    def __str__(self):
        return f"Semana {self.numero} - R$ {self.valor}"

# ==========================================
# 7. CONTAS A PAGAR & ALERTAS
# ==========================================
class ContaPagar(models.Model):
    RECORRENCIA_CHOICES = [
        ('U', 'Única'),
        ('M', 'Mensal'),
        ('A', 'Anual'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    titulo = models.CharField(max_length=100, help_text="Ex: IPVA, Seguro Carro, Netflix")
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    data_vencimento = models.DateField()
    pago = models.BooleanField(default=False)
    recorrencia = models.CharField(max_length=1, choices=RECORRENCIA_CHOICES, default='M')
    
    class Meta:
        verbose_name = "Conta a Pagar"
        verbose_name_plural = "Contas a Pagar"
        ordering = ['data_vencimento'] 

    def __str__(self):
        return f"{self.titulo} - {self.data_vencimento.strftime('%d/%m')}"
    
    @property
    def status_vencimento(self):
        if self.pago:
            return 'pago'
            
        hoje = timezone.now().date()
        dias_restantes = (self.data_vencimento - hoje).days

        if dias_restantes < 0:
            return 'atrasado' 
        elif dias_restantes == 0:
            return 'hoje'     
        elif dias_restantes <= 5:
            return 'proximo'  
        else:
            return 'longe'
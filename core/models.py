from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone 

# 1. AGENDA / COMPROMISSOS
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

# 2. BLOCO DE NOTAS
class Nota(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    titulo = models.CharField(max_length=200)
    conteudo = models.TextField()
    cor = models.CharField(max_length=20, default='#ffffff') # Ajustado para hex
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.titulo

# 3. CONTROLE FINANCEIRO
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

# === MÓDULO CARTÃO DE CRÉDITO ===

class CartaoCredito(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    nome = models.CharField(max_length=50, help_text="Ex: Nubank, Visa Platinum")
    limite = models.DecimalField(max_digits=10, decimal_places=2)
    dia_fechamento = models.IntegerField(help_text="Dia que a fatura fecha (1-31)", default=1)
    dia_vencimento = models.IntegerField(help_text="Dia que a fatura vence (1-31)")
    
    # --- NOVO CAMPO ADICIONADO ---
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

# === MÓDULO INVESTIMENTOS ===

class Ativo(models.Model):
    TIPO_ATIVO = [
        ('acao', 'Ação'),
        ('fii', 'Fundo Imobiliário (FII)'),
        ('renda_fixa', 'Renda Fixa / Tesouro'),
        ('crypto', 'Criptomoeda'),
        ('fundo', 'Fundo de Investimento'),
        ('exterior', 'Stocks / REITs'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    codigo = models.CharField(max_length=20, help_text="Ex: PETR4, HGLG11, CDB Banco X")
    tipo = models.CharField(max_length=20, choices=TIPO_ATIVO)
    
    # --- NOVO CAMPO ADICIONADO ---
    setor = models.CharField(max_length=50, blank=True, null=True, help_text="Ex: Bancos, Logística, Tecnologia")
    
    # Campos calculados (cache)
    quantidade_atual = models.DecimalField(max_digits=15, decimal_places=8, default=0) 
    preco_medio = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    def __str__(self):
        return f"{self.codigo} ({self.get_tipo_display()})"

    def total_investido(self):
        return self.quantidade_atual * self.preco_medio

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
        return f"{self.tipo} - {self.ativo.codigo} - {self.data}"

class Desafio(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    objetivo = models.CharField(max_length=100, help_text="Ex: Trocar de Moto, Viagem")
    valor_inicial = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Depósito da 1ª Semana")
    incremento = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Aumento por Semana", help_text="Quanto aumenta o depósito a cada semana?")
    duracao_semanas = models.IntegerField(default=52, verbose_name="Duração (Semanas)")
    data_inicio = models.DateField(default=timezone.now)
    concluido = models.BooleanField(default=False)

    def total_planejado(self):
        valor_final = self.valor_inicial + ((self.duracao_semanas - 1) * self.incremento)
        return (self.valor_inicial + valor_final) * self.duracao_semanas / 2

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
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    pago = models.BooleanField(default=False)
    data_pagamento = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ['numero']

    def __str__(self):
        return f"Semana {self.numero} - R$ {self.valor}"

# 4. CONTAS A PAGAR & ALERTAS
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
        ordering = ['data_vencimento'] # Ordena sempre da mais urgente para a mais distante

    def __str__(self):
        return f"{self.titulo} - {self.data_vencimento.strftime('%d/%m')}"
    
    @property
    def status_vencimento(self):
        """
        Retorna o estado da conta para o alerta:
        'atrasado', 'hoje', 'proximo', 'longe'
        """
        if self.pago:
            return 'pago'
            
        hoje = timezone.now().date()
        dias_restantes = (self.data_vencimento - hoje).days

        if dias_restantes < 0:
            return 'atrasado' # Venceu ontem ou antes
        elif dias_restantes == 0:
            return 'hoje'     # Vence hoje
        elif dias_restantes <= 5:
            return 'proximo'  # Vence nos próximos 5 dias
        else:
            return 'longe'    # Tem tempo ainda
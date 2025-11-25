from django.db import models
from django.contrib.auth.models import User

# 1. AGENDA / COMPROMISSOS
class Compromisso(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE) # Cada usuário vê só os seus
    titulo = models.CharField(max_length=200)
    descricao = models.TextField(blank=True, null=True)
    data_hora = models.DateTimeField()
    local = models.CharField(max_length=200, blank=True, null=True)
    concluido = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.data_hora.strftime('%d/%m %H:%M')} - {self.titulo}"

    class Meta:
        ordering = ['data_hora'] # Ordena do mais próximo para o mais distante

# 2. BLOCO DE NOTAS
class Nota(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    titulo = models.CharField(max_length=200)
    conteudo = models.TextField()
    cor = models.CharField(max_length=20, default='white') # Para dar um visual de post-it depois
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
    valor = models.DecimalField(max_digits=10, decimal_places=2) # Ex: 1500.50
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
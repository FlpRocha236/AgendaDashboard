from django.contrib import admin
from .models import (
    Compromisso, Nota, Transacao, CartaoCredito, DespesaCartao, 
    Ativo, OperacaoInvestimento, Desafio, SemanaDesafio, ContaPagar, 
    AnaliseBot
)

# --- CONFIGURAÇÃO DA ADMINISTRAÇÃO ---

@admin.register(Compromisso)
class CompromissoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'data_hora', 'concluido', 'user')
    list_filter = ('concluido', 'data_hora')
    search_fields = ('titulo', 'descricao')

@admin.register(Nota)
class NotaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'atualizado_em', 'user')
    search_fields = ('titulo', 'conteudo')

@admin.register(Transacao)
class TransacaoAdmin(admin.ModelAdmin):
    list_display = ('descricao', 'valor', 'tipo', 'categoria', 'data', 'pago', 'user')
    list_filter = ('tipo', 'categoria', 'pago', 'data')
    search_fields = ('descricao',)

@admin.register(CartaoCredito)
class CartaoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'limite', 'dia_vencimento', 'user')

@admin.register(DespesaCartao)
class DespesaCartaoAdmin(admin.ModelAdmin):
    list_display = ('descricao', 'valor', 'cartao', 'parcela_atual', 'parcelas')
    list_filter = ('cartao',)

# --- INVESTIMENTOS (CORRIGIDO) ---

class AnaliseBotInline(admin.StackedInline):
    model = AnaliseBot
    can_delete = False
    verbose_name_plural = 'Análise do Robô'

@admin.register(Ativo)
class AtivoAdmin(admin.ModelAdmin):
    # AQUI ESTAVA O ERRO: Trocamos 'codigo' por 'ticker'
    list_display = ('ticker', 'tipo', 'setor', 'quantidade_atual', 'preco_medio', 'user')
    list_filter = ('tipo', 'setor')
    search_fields = ('ticker', 'setor')
    inlines = [AnaliseBotInline] # Mostra a análise do robô dentro do ativo

@admin.register(OperacaoInvestimento)
class OperacaoAdmin(admin.ModelAdmin):
    list_display = ('tipo', 'ativo', 'data', 'quantidade', 'preco_unitario', 'valor_total')
    list_filter = ('tipo', 'data')
    # AQUI TAMBÉM: Trocamos 'ativo__codigo' por 'ativo__ticker'
    search_fields = ('ativo__ticker',)

@admin.register(AnaliseBot)
class AnaliseBotAdmin(admin.ModelAdmin):
    list_display = ('ativo', 'recomendacao', 'pontuacao', 'data_analise')
    list_filter = ('recomendacao', 'pontuacao', 'data_analise')

# --- DESAFIOS ---

class SemanaInline(admin.TabularInline):
    model = SemanaDesafio
    extra = 0

@admin.register(Desafio)
class DesafioAdmin(admin.ModelAdmin):
    list_display = ('objetivo', 'progresso_percentual', 'concluido', 'user')
    inlines = [SemanaInline]

# --- CONTAS A PAGAR ---

@admin.register(ContaPagar)
class ContaPagarAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'valor', 'data_vencimento', 'status_vencimento', 'recorrencia', 'user')
    list_filter = ('pago', 'recorrencia', 'data_vencimento')
    search_fields = ('titulo',)
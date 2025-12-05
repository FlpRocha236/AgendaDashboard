from django.contrib import admin
from .models import Compromisso, Nota, Transacao, CartaoCredito, DespesaCartao, Ativo, OperacaoInvestimento

@admin.register(Compromisso)
class CompromissoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'data_hora', 'local', 'concluido')
    list_filter = ('concluido', 'data_hora')

@admin.register(Nota)
class NotaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'criado_em')

@admin.register(Transacao)
class TransacaoAdmin(admin.ModelAdmin):
    list_display = ('descricao', 'tipo', 'valor', 'data', 'categoria', 'pago')
    list_filter = ('tipo', 'categoria', 'pago', 'data')
    search_fields = ('descricao',)

@admin.register(CartaoCredito)
class CartaoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'dia_fechamento', 'dia_vencimento', 'limite')

@admin.register(DespesaCartao)
class DespesaCartaoAdmin(admin.ModelAdmin):
    list_display = ('cartao', 'descricao', 'valor', 'data_compra', 'parcela_atual')
    list_filter = ('cartao', 'data_compra')

@admin.register(Ativo)
class AtivoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'tipo', 'quantidade_atual', 'preco_medio')
    list_filter = ('tipo',)

@admin.register(OperacaoInvestimento)
class OperacaoAdmin(admin.ModelAdmin):
    list_display = ('ativo', 'tipo', 'data', 'quantidade', 'preco_unitario')
    list_filter = ('tipo', 'data')
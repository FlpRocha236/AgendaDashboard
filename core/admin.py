from django.contrib import admin
from .models import Compromisso, Nota, Transacao

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
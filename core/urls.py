from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('financas/', views.financas, name='financas'),
    path('financas/nova/', views.transacao_nova, name='transacao_nova'),
    path('financas/editar/<int:id>/', views.transacao_editar, name='transacao_editar'),
    path('financas/deletar/<int:id>/', views.transacao_deletar, name='transacao_deletar'), 
    path('agenda/', views.agenda, name='agenda'),       
    path('notas/', views.notas, name='notas'),    
    path('agenda/', views.agenda, name='agenda'),
    path('agenda/nova/', views.agenda_nova, name='agenda_nova'),
    path('agenda/editar/<int:id>/', views.agenda_editar, name='agenda_editar'),
    path('agenda/deletar/<int:id>/', views.agenda_deletar, name='agenda_deletar'),
    path('notas/', views.notas, name='notas'),
    path('notas/nova/', views.nota_nova, name='nota_nova'),
    path('notas/editar/<int:id>/', views.nota_editar, name='nota_editar'),
    path('notas/deletar/<int:id>/', views.nota_deletar, name='nota_deletar'), 
    path('configuracoes/', views.configuracoes, name='configuracoes'),
    path('configuracoes/senha/', views.alterar_senha, name='alterar_senha'),
    path('financas/cartao/novo/', views.cartao_novo, name='cartao_novo'),
    path('financas/cartao/despesa/nova/', views.despesa_cartao_nova, name='despesa_cartao_nova'),
    path('financas/ativo/novo/', views.ativo_novo, name='ativo_novo'),
    path('financas/ativo/operacao/', views.operacao_nova, name='operacao_nova'),     
]
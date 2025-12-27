from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from core import views

urlpatterns = [
    # --- ADMINISTRAÇÃO & AUTENTICAÇÃO ---
    path('admin/', admin.site.urls),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('registrar/', views.registrar_usuario, name='registrar_usuario'),

    # --- DASHBOARD (HOME) ---
    path('', views.dashboard, name='dashboard'),

    # --- MÓDULO FINANÇAS (Fluxo & Cartões) ---
    path('financas/', views.financas, name='financas'),
    
    # Transações
    path('financas/nova/', views.transacao_nova, name='transacao_nova'),
    path('financas/editar/<int:id>/', views.transacao_editar, name='transacao_editar'),
    path('financas/deletar/<int:id>/', views.transacao_deletar, name='transacao_deletar'),
    
    # Cartões de Crédito
    path('financas/cartao/novo/', views.cartao_novo, name='cartao_novo'),
    path('financas/cartao/deletar/<int:id>/', views.cartao_deletar, name='cartao_deletar'),
    
    # Despesas de Cartão
    path('financas/cartao/despesa/nova/', views.despesa_cartao_nova, name='despesa_cartao_nova'),
    path('financas/cartao/despesa/editar/<int:id>/', views.despesa_cartao_editar, name='despesa_cartao_editar'),
    path('financas/cartao/despesa/deletar/<int:id>/', views.despesa_cartao_deletar, name='despesa_cartao_deletar'),

    # --- MÓDULO INVESTIMENTOS (Novo & Separado) ---
    path('investimentos/', views.investimentos_dashboard, name='investimentos_dashboard'), # <--- NOVA HOME
    
    # Ativos (Ações, FIIs, etc)
    path('investimentos/ativo/novo/', views.ativo_novo, name='ativo_novo'),
    path('investimentos/ativo/deletar/<int:id>/', views.ativo_deletar, name='ativo_deletar'),
    
    # Operações (Compra/Venda)
    path('investimentos/operacao/', views.operacao_nova, name='operacao_nova'),  
    path('investimentos/operacao/editar/<int:id>/', views.operacao_editar, name='operacao_editar'),
    path('investimentos/operacao/deletar/<int:id>/', views.operacao_deletar, name='operacao_deletar'),   

    # --- MÓDULO AGENDA ---
    path('agenda/', views.agenda, name='agenda'),
    path('agenda/nova/', views.agenda_nova, name='agenda_nova'),
    path('agenda/editar/<int:id>/', views.agenda_editar, name='agenda_editar'),
    path('agenda/deletar/<int:id>/', views.agenda_deletar, name='agenda_deletar'),
    path('agenda/concluir/<int:id>/', views.compromisso_concluir, name='compromisso_concluir'),

    # --- MÓDULO NOTAS ---
    path('notas/', views.notas, name='notas'),    
    path('notas/nova/', views.nota_nova, name='nota_nova'),
    path('notas/editar/<int:id>/', views.nota_editar, name='nota_editar'),
    path('notas/deletar/<int:id>/', views.nota_deletar, name='nota_deletar'), 

    # --- MÓDULO DESAFIOS & METAS ---
    path('desafios/', views.desafios_lista, name='desafios_lista'),
    path('desafios/novo/', views.desafio_novo, name='desafio_novo'),
    path('desafios/pagar/<int:id>/', views.desafio_pagar_semana, name='desafio_pagar_semana'),
    path('desafios/excluir/<int:id>/', views.desafio_excluir, name='desafio_excluir'),

    # --- CONFIGURAÇÕES ---
    path('configuracoes/', views.configuracoes, name='configuracoes'),
    path('configuracoes/senha/', views.alterar_senha, name='alterar_senha'),
]
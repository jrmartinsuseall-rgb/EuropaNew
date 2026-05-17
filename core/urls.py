from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # ── Acesso ──────────────────────────────────────────
    path('login/',               views.login_view,        name='login'),
    path('logout/',              views.logout_view,       name='logout'),
    path('home/',                views.home_view,         name='home'),
    path('selecionar-empresa/',  views.selecionar_empresa, name='selecionar_empresa'),

    # ── Usuários ─────────────────────────────────────────
    path('usuarios/',          views.usuario_list,   name='usuario_list'),
    path('usuarios/novo/',     views.usuario_create, name='usuario_create'),
    path('usuarios/<int:pk>/', views.usuario_edit,   name='usuario_edit'),
    path('senha/',             views.trocar_senha,   name='trocar_senha'),

    # ── Cidades ──────────────────────────────────────────
    path('cidades/',                       views.cidade_list,     name='cidade_list'),
    path('cidades/buscar/',               views.cidade_buscar,   name='cidade_buscar'),
    path('cidades/novo/',                 views.cidade_create,   name='cidade_create'),
    path('cidades/<int:pk>/',             views.cidade_edit,     name='cidade_edit'),
    path('cidades/<int:pk>/inativar/',    views.cidade_inativar, name='cidade_inativar'),

    # ── Bancos ───────────────────────────────────────────
    path('bancos/',                       views.banco_list,     name='banco_list'),
    path('bancos/buscar/',                views.banco_buscar,   name='banco_buscar'),
    path('bancos/novo/',                  views.banco_create,   name='banco_create'),
    path('bancos/<int:pk>/',              views.banco_edit,     name='banco_edit'),
    path('bancos/<int:pk>/inativar/',     views.banco_inativar, name='banco_inativar'),

    # ── CFOP ─────────────────────────────────────────────
    path('cfop/',                         views.cfop_list,     name='cfop_list'),
    path('cfop/buscar/',                  views.cfop_buscar,   name='cfop_buscar'),
    path('cfop/novo/',                    views.cfop_create,   name='cfop_create'),
    path('cfop/<int:pk>/',                views.cfop_edit,     name='cfop_edit'),
    path('cfop/<int:pk>/inativar/',       views.cfop_inativar, name='cfop_inativar'),

    # ── Plano de Contas ──────────────────────────────────────────
    path('contas/',                         views.planoconta_list,     name='planoconta_list'),
    path('contas/buscar/',                  views.planoconta_buscar,   name='planoconta_buscar'),
    path('contas/novo/',                    views.planoconta_create,   name='planoconta_create'),
    path('contas/<int:pk>/',                views.planoconta_edit,     name='planoconta_edit'),
    path('contas/<int:pk>/inativar/',       views.planoconta_inativar, name='planoconta_inativar'),

    # ── Sub-Contas ────────────────────────────────────────────────
    path('subcontas/',                      views.subconta_list,     name='subconta_list'),
    path('subcontas/buscar/',               views.subconta_buscar,   name='subconta_buscar'),
    path('subcontas/novo/',                 views.subconta_create,   name='subconta_create'),
    path('subcontas/<int:pk>/',             views.subconta_edit,     name='subconta_edit'),
    path('subcontas/<int:pk>/inativar/',    views.subconta_inativar, name='subconta_inativar'),

    # ── Empresa ──────────────────────────────────────────
    path('empresa/',                        views.empresa_edit,   name='empresa_edit'),

    # ── Configuração de Caixa ─────────────────────────────
    path('cfg-caixa/',                      views.cfgcaixa_edit,  name='cfgcaixa_edit'),

    # ── Projetos ──────────────────────────────────────────
    path('projetos/',                       views.projeto_list,    name='projeto_list'),
    path('projetos/buscar/',                views.projeto_buscar,  name='projeto_buscar'),
    path('projetos/novo/',                  views.projeto_create,  name='projeto_create'),
    path('projetos/<int:pk>/',              views.projeto_edit,    name='projeto_edit'),
    path('projetos/<int:pk>/inativar/',     views.projeto_inativar,  name='projeto_inativar'),
    path('projetos/<int:pk>/orcamento/',          views.projeto_orcamento,          name='projeto_orcamento'),
    path('projetos/<int:pk>/orcamento/imprimir/', views.projeto_orcamento_imprimir, name='projeto_orcamento_imprimir'),

    # ── Licenças ──────────────────────────────────────────
    path('licencas/',                           views.licenca_list,      name='licenca_list'),
    path('licencas/<int:pk>/',                  views.licenca_edit,      name='licenca_edit'),
    path('licencas/<int:pk>/regenerar/',        views.licenca_regenerar, name='licenca_regenerar'),
    path('licenca-bloqueada/',                  views.licenca_bloqueada, name='licenca_bloqueada'),
]

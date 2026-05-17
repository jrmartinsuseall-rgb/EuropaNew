from django.urls import path
from . import views

app_name = 'servicos'

urlpatterns = [
    path('agenda/',                              views.agenda_view,    name='agenda'),
    path('crm/',                          views.crm_lookup,       name='crm_lookup'),
    path('crm/buscar/',                   views.crm_buscar,       name='crm_buscar'),
    path('crm/cliente/<int:pk>/',         views.crm_ficha,        name='crm_ficha'),
    path('crm/cliente/<int:cli_pk>/contato/salvar/', views.contato_salvar, name='contato_salvar'),
    path('crm/contato/<int:pk>/excluir/',            views.contato_excluir, name='contato_excluir'),
    path('crm/cliente/<int:cli_pk>/fone/salvar/',    views.fone_salvar,    name='fone_salvar'),
    path('crm/fone/<int:pk>/excluir/',               views.fone_excluir,   name='fone_excluir'),

    # ── Roteiros de Instalação ────────────────────────────────
    path('roteiros/',                                views.roteiro_list,           name='roteiro_list'),
    path('roteiros/novo/',                           views.roteiro_create,         name='roteiro_create'),
    path('roteiros/os-pendentes/',                   views.roteiro_os_pendentes,   name='roteiro_os_pendentes'),
    path('roteiros/<int:pk>/',                       views.roteiro_detalhe,        name='roteiro_detalhe'),
    path('roteiros/<int:pk>/retorno/',               views.roteiro_salvar_retorno, name='roteiro_salvar_retorno'),
    path('roteiros/<int:pk>/conferir/',              views.roteiro_conferir,       name='roteiro_conferir'),
    path('roteiros/<int:pk>/cancelar/',              views.roteiro_cancelar,       name='roteiro_cancelar'),

    # ── Ordens de Serviço ─────────────────────────────────────
    path('os/',                                      views.os_list,        name='os_list'),
    path('os/nova/',                                 views.os_create,      name='os_create'),
    path('os/nova/cliente/<int:cli_pk>/',            views.os_create,      name='os_create_cli'),
    path('os/<int:pk>/',                             views.os_detalhe,     name='os_detalhe'),
    path('os/<int:pk>/cancelar/',                    views.os_cancelar,    name='os_cancelar'),
    path('os/<int:pk>/reagendar/',                   views.os_reagendar,   name='os_reagendar'),
    path('os/<int:pk>/status/',                      views.os_mudar_status,name='os_mudar_status'),
    path('os/<int:pk>/espelho/',                     views.os_espelho,     name='os_espelho'),
]

from django.urls import path
from . import views

app_name = 'financeiro'

urlpatterns = [
    # ── Contas a Receber ─────────────────────────────────────
    path('receber/',                       views.contarec_list,     name='contarec_list'),
    path('receber/imprimir/',              views.contarec_imprimir, name='contarec_imprimir'),
    path('receber/buscar/',                views.contarec_buscar,   name='contarec_buscar'),
    path('receber/novo/',                  views.contarec_create,            name='contarec_create'),
    path('receber/assistente/',            views.contarec_assistente,        name='contarec_assistente'),
    path('receber/assistente/preview/',    views.contarec_assistente_preview, name='contarec_assistente_preview'),
    path('receber/assistente/gerar/',      views.contarec_assistente_gerar,  name='contarec_assistente_gerar'),
    path('receber/<int:pk>/',              views.contarec_edit,     name='contarec_edit'),
    path('receber/<int:pk>/cancelar/',     views.contarec_cancelar, name='contarec_cancelar'),

    # ── Contas a Pagar ───────────────────────────────────────
    path('pagar/',                         views.contapag_list,     name='contapag_list'),
    path('pagar/imprimir/',               views.contapag_imprimir, name='contapag_imprimir'),
    path('pagar/buscar/',                  views.contapag_buscar,   name='contapag_buscar'),
    path('pagar/novo/',                    views.contapag_create,   name='contapag_create'),
    path('pagar/<int:pk>/',                views.contapag_edit,     name='contapag_edit'),
    path('pagar/<int:pk>/cancelar/',       views.contapag_cancelar, name='contapag_cancelar'),

    # ── Geração de Boletos ───────────────────────────────────
    path('boletos/',                       views.boletos_view,        name='boletos'),
    path('boletos/gerar/',                 views.boletos_gerar,       name='boletos_gerar'),

    # ── Caixa ─────────────────────────────────────────────────
    path('caixa/',                         views.caixa_view,          name='caixa'),
    path('caixa/abrir/',                   views.caixa_abrir,         name='caixa_abrir'),
    path('caixa/fechar/',                  views.caixa_fechar,        name='caixa_fechar'),
    path('caixa/entrada/',                 views.caixa_entrada,       name='caixa_entrada'),
    path('caixa/saida/',                   views.caixa_saida,         name='caixa_saida'),
    path('caixa/sangria/',                 views.caixa_sangria,       name='caixa_sangria'),
    path('caixa/<int:pk>/cancelar/',       views.caixa_cancelar_mov,  name='caixa_cancelar_mov'),
    path('caixa/projeto/',                 views.caixa_projeto_selecionar,     name='caixa_projeto_selecionar'),
    path('caixa/<int:pk>/relatorio/',      views.caixa_relatorio_fechamento,   name='caixa_relatorio_fechamento'),
    path('caixa/recebimento/',             views.caixa_recebimento,        name='caixa_recebimento'),
    path('caixa/recebimento/buscar/',      views.caixa_recebimento_buscar, name='caixa_recebimento_buscar'),
    path('caixa/pagamento/',               views.caixa_pagamento,          name='caixa_pagamento'),
    path('caixa/pagamento/buscar/',        views.caixa_pagamento_buscar,   name='caixa_pagamento_buscar'),
]

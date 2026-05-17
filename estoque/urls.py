from django.urls import path
from . import views

app_name = 'estoque'

urlpatterns = [
    # ── Requisições ──────────────────────────────────────────
    path('requisicoes/',                      views.req_list,     name='req_list'),
    path('requisicoes/nova/',                 views.req_create,   name='req_create'),
    path('requisicoes/<int:pk>/',             views.req_detalhe,  name='req_detalhe'),
    path('requisicoes/<int:pk>/atender/',     views.req_atender,  name='req_atender'),
    path('requisicoes/<int:pk>/cancelar/',    views.req_cancelar, name='req_cancelar'),
    path('requisicoes/<int:pk>/espelho/',     views.req_espelho,  name='req_espelho'),

    # ── Inventário ───────────────────────────────────────────
    path('inventario/',                       views.inv_list,            name='inv_list'),
    path('inventario/novo/',                  views.inv_create,          name='inv_create'),
    path('inventario/<int:pk>/',              views.inv_detalhe,         name='inv_detalhe'),
    path('inventario/<int:pk>/contagem/',     views.inv_salvar_contagem, name='inv_contagem'),
    path('inventario/<int:pk>/finalizar/',    views.inv_finalizar,       name='inv_finalizar'),
    path('inventario/<int:pk>/cancelar/',     views.inv_cancelar,        name='inv_cancelar'),

    # ── Ajuste Avulso ────────────────────────────────────────
    path('ajuste/',                     views.ajuste_list,    name='ajuste_list'),
    path('ajuste/novo/',                views.ajuste_create,  name='ajuste_create'),
    path('ajuste/<int:pk>/espelho/',    views.ajuste_espelho, name='ajuste_espelho'),

    # ── NF de Entrada ────────────────────────────────────────
    path('nf/',                        views.nf_list,    name='nf_list'),
    path('nf/nova/',                   views.nf_create,  name='nf_create'),
    path('nf/<int:pk>/',               views.nf_detalhe, name='nf_detalhe'),
    path('nf/<int:pk>/editar/',        views.nf_editar,  name='nf_editar'),
    path('nf/<int:pk>/lancar/',        views.nf_lancar,  name='nf_lancar'),
    path('nf/<int:pk>/cancelar/',      views.nf_cancelar,  name='nf_cancelar'),
    path('nf/<int:pk>/espelho/',       views.nf_espelho,   name='nf_espelho'),

    # ── Saldo por Item ───────────────────────────────────────
    path('saldo/',                                views.saldo_list,           name='saldo_list'),
    path('saldo/buscar/',                         views.saldo_buscar,         name='saldo_buscar'),
    path('saldo/imprimir/',                       views.saldo_imprimir,       name='saldo_imprimir'),
    path('saldo/<int:item_pk>/extrato/',           views.item_extrato,         name='item_extrato'),
    path('saldo/<int:item_pk>/extrato/imprimir/',  views.item_extrato_imprimir,name='item_extrato_imprimir'),
]

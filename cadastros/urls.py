from django.urls import path
from . import views

app_name = 'cadastros'

urlpatterns = [
    # ── Clientes / Fornecedores ──────────────────────────────
    path('clientes/',                        views.cliente_list,     name='cliente_list'),
    path('clientes/buscar/',                 views.cliente_buscar,   name='cliente_buscar'),
    path('clientes/novo/',                   views.cliente_create,   name='cliente_create'),
    path('clientes/<int:pk>/',               views.cliente_edit,     name='cliente_edit'),
    path('clientes/<int:pk>/inativar/',      views.cliente_inativar, name='cliente_inativar'),

    # ── Condições de Pagamento ───────────────────────────────
    path('condpag/',                         views.condpag_list,     name='condpag_list'),
    path('condpag/buscar/',                  views.condpag_buscar,   name='condpag_buscar'),
    path('condpag/novo/',                    views.condpag_create,   name='condpag_create'),
    path('condpag/<int:pk>/',                views.condpag_edit,     name='condpag_edit'),
    path('condpag/<int:pk>/inativar/',       views.condpag_inativar, name='condpag_inativar'),

    # ── Grupos ───────────────────────────────────────────────
    path('grupos/',                          views.grupo_list,       name='grupo_list'),
    path('grupos/buscar/',                   views.grupo_buscar,     name='grupo_buscar'),
    path('grupos/novo/',                     views.grupo_create,     name='grupo_create'),
    path('grupos/<int:pk>/',                 views.grupo_edit,       name='grupo_edit'),
    path('grupos/<int:pk>/inativar/',        views.grupo_inativar,   name='grupo_inativar'),

    # ── Itens ─────────────────────────────────────────────────
    path('itens/',                           views.item_list,        name='item_list'),
    path('itens/buscar/',                    views.item_buscar,      name='item_buscar'),
    path('itens/novo/',                      views.item_create,      name='item_create'),
    path('itens/<int:pk>/',                  views.item_edit,        name='item_edit'),
    path('itens/<int:pk>/inativar/',         views.item_inativar,    name='item_inativar'),

    # ── Portadores ───────────────────────────────────────────
    path('portadores/',                        views.portador_list,     name='portador_list'),
    path('portadores/buscar/',                 views.portador_buscar,   name='portador_buscar'),
    path('portadores/novo/',                   views.portador_create,   name='portador_create'),
    path('portadores/<int:pk>/',               views.portador_edit,     name='portador_edit'),
    path('portadores/<int:pk>/inativar/',      views.portador_inativar, name='portador_inativar'),

    # ── Métodos de Pagamento ──────────────────────────────────
    path('metodos/',                           views.metodo_list,       name='metodo_list'),
    path('metodos/buscar/',                    views.metodo_buscar,     name='metodo_buscar'),
    path('metodos/novo/',                      views.metodo_create,     name='metodo_create'),
    path('metodos/<int:pk>/',                  views.metodo_edit,       name='metodo_edit'),
    path('metodos/<int:pk>/inativar/',         views.metodo_inativar,   name='metodo_inativar'),

    # ── Vendedores ───────────────────────────────────────────
    path('vendedores/',                        views.vendedor_list,     name='vendedor_list'),
    path('vendedores/buscar/',                 views.vendedor_buscar,   name='vendedor_buscar'),
    path('vendedores/novo/',                   views.vendedor_create,   name='vendedor_create'),
    path('vendedores/<int:pk>/',               views.vendedor_edit,     name='vendedor_edit'),
    path('vendedores/<int:pk>/inativar/',      views.vendedor_inativar, name='vendedor_inativar'),

    # ── Técnicos / Empregados ────────────────────────────────
    path('tecnicos/',                          views.tecnico_list,      name='tecnico_list'),
    path('tecnicos/buscar/',                   views.tecnico_buscar,    name='tecnico_buscar'),
    path('tecnicos/novo/',                     views.tecnico_create,    name='tecnico_create'),
    path('tecnicos/<int:pk>/',                 views.tecnico_edit,      name='tecnico_edit'),
    path('tecnicos/<int:pk>/inativar/',        views.tecnico_inativar,  name='tecnico_inativar'),

    # ── Tabelas de Preço ─────────────────────────────────────
    path('tabelas/',                              views.tabela_list,         name='tabela_list'),
    path('tabelas/buscar/',                       views.tabela_buscar,       name='tabela_buscar'),
    path('tabelas/nova/',                         views.tabela_create,       name='tabela_create'),
    path('tabelas/<int:pk>/',                     views.tabela_detalhe,      name='tabela_detalhe'),
    path('tabelas/<int:tabela_pk>/item/salvar/',  views.tabela_item_salvar,  name='tabela_item_salvar'),
    path('tabelas/item/<int:pk>/excluir/',        views.tabela_item_excluir, name='tabela_item_excluir'),

    # ── Lookups HTMX ─────────────────────────────────────────
    path('lookup/cidade/',                   views.cidade_lookup,      name='cidade_lookup'),
    path('lookup/item/',                     views.item_lookup,        name='item_lookup'),
    path('lookup/vendedor/',                 views.vendedor_buscar,    name='vendedor_lookup'),
    path('lookup/tecnico/',                  views.tecnico_buscar,     name='tecnico_lookup'),
    path('lookup/tabela-item/',              views.tabela_item_lookup, name='tabela_item_lookup'),
]

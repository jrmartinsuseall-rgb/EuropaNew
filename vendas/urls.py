from django.urls import path
from . import views

app_name = 'vendas'

urlpatterns = [
    path('pedidos/',                   views.pedido_list,    name='pedido_list'),
    path('pedidos/novo/',              views.pedido_create,  name='pedido_create'),
    path('pedidos/<int:pk>/',          views.pedido_detalhe, name='pedido_detalhe'),
    path('pedidos/<int:pk>/faturar/',  views.pedido_faturar, name='pedido_faturar'),
    path('pedidos/<int:pk>/instalar/', views.pedido_instalar,name='pedido_instalar'),
    path('pedidos/<int:pk>/cancelar/', views.pedido_cancelar,  name='pedido_cancelar'),
    path('pedidos/<int:pk>/espelho/',  views.pedido_espelho,   name='pedido_espelho'),

    path('comissoes/config/',             views.comissao_config,  name='comissao_config'),
    path('comissoes/',                    views.acerto_list,      name='acerto_list'),
    path('comissoes/novo/',               views.acerto_create,    name='acerto_create'),
    path('comissoes/<int:pk>/',           views.acerto_detalhe,   name='acerto_detalhe'),
    path('comissoes/<int:pk>/calcular/',  views.acerto_calcular,  name='acerto_calcular'),
    path('comissoes/<int:pk>/confirmar/', views.acerto_confirmar, name='acerto_confirmar'),
    path('comissoes/<int:pk>/cancelar/',  views.acerto_cancelar,  name='acerto_cancelar'),
    path('comissoes/<int:pk>/associar/',                      views.acerto_associar,       name='acerto_associar'),
    path('comissoes/<int:pk>/remover/<int:pedido_pk>/',        views.acerto_remover_pedido, name='acerto_remover_pedido'),
    path('comissoes/<int:pk>/comprovante/', views.acerto_comprovante, name='acerto_comprovante'),
]

from django.urls import path
from campo.views import api, gestor, tecnico

app_name = 'campo'

urlpatterns = [
    # Gestor — painel de monitoramento
    path('gestor/monitoramento/', gestor.monitoramento, name='gestor_monitoramento'),

    # Técnico — interface mobile
    path('',                          tecnico.home,        name='home'),
    path('atividade/<int:pk>/',       tecnico.detalhe,     name='detalhe'),
    path('atividade/<int:pk>/acao/',     tecnico.acao_status, name='acao_status'),
    path('atividade/<int:pk>/concluir/', tecnico.concluir,    name='concluir'),

    # API de integração
    path('api/roteiro/confirmar/', api.confirmar_roteiro, name='api_confirmar_roteiro'),
]

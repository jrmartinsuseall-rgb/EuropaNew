import json

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone

from campo.models import Servico, ServTecnico, ServTempo
from core.decorators import modulo_required


@modulo_required('acesso_televendas')
def monitoramento(request):
    hoje = timezone.localdate()

    tecnicos_hoje = (
        ServTecnico.objects
        .filter(papel='RESPONSAVEL', servico__data_prevista=hoje)
        .values('nome', 'user_id')
        .distinct()
    )

    cards = []
    for t in tecnicos_hoje:
        nome = t['nome']

        qs = Servico.objects.filter(
            tecnicos__nome=nome,
            tecnicos__papel='RESPONSAVEL',
            data_prevista=hoje,
        ).distinct()

        atividade_atual = (
            qs.exclude(status__in=['CONCLUIDO', 'CANCELADO'])
            .order_by('prioridade')
            .first()
        )

        duracao_display = '—'
        if atividade_atual:
            ultimo_tempo = (
                ServTempo.objects
                .filter(servico=atividade_atual)
                .order_by('-timestamp')
                .first()
            )
            if ultimo_tempo:
                delta = timezone.now() - ultimo_tempo.timestamp
                horas   = int(delta.total_seconds() // 3600)
                minutos = int((delta.total_seconds() % 3600) // 60)
                duracao_display = f'{horas}h{minutos:02d}m'

        concluidas_hoje = qs.filter(status='CONCLUIDO').count()
        pendentes       = qs.exclude(status__in=['CONCLUIDO', 'CANCELADO']).count()

        atrasado = (
            atividade_atual is not None
            and atividade_atual.data_prevista
            and atividade_atual.data_prevista < hoje
            and atividade_atual.status not in ['CONCLUIDO', 'CANCELADO']
        )

        iniciais = ''.join([p[0].upper() for p in nome.split()[:2]]) if nome else '?'

        cards.append({
            'nome':            nome,
            'iniciais':        iniciais,
            'atividade_atual': atividade_atual,
            'duracao_display': duracao_display,
            'concluidas_hoje': concluidas_hoje,
            'pendentes':       pendentes,
            'atrasado':        atrasado,
        })

    em_campo       = len(cards)
    em_execucao    = sum(1 for c in cards if c['atividade_atual'] and c['atividade_atual'].status == 'EM_EXECUCAO')
    concluidas_total = Servico.objects.filter(data_prevista=hoje, status='CONCLUIDO').count()
    em_atraso      = sum(1 for c in cards if c['atrasado'])

    return render(request, 'campo/gestor/monitoramento.html', {
        'cards':          cards,
        'kpi_em_campo':   em_campo,
        'kpi_em_execucao': em_execucao,
        'kpi_concluidas': concluidas_total,
        'kpi_em_atraso':  em_atraso,
        'grafico_labels': json.dumps([c['nome'].split()[0] for c in cards], ensure_ascii=False),
        'grafico_dados':  json.dumps([c['concluidas_hoje'] for c in cards]),
        'hoje':           hoje,
    })

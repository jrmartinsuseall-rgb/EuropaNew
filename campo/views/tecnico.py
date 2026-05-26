import re
from datetime import date
from urllib.parse import quote

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from campo.models import Servico, ServApontamento, ServTempo, ScriptMensagem

# status_atual → (novo_status, label_botao, css_botao, evento_tempo)
PROXIMA_ACAO = {
    'AGENDADO':    ('A_CAMINHO',   'A Caminho', 'btn-info',    'A_CAMINHO'),
    'A_CAMINHO':   ('EM_EXECUCAO', 'Iniciar',   'btn-warning', 'INICIO'),
    'EM_EXECUCAO': ('CONCLUIDO',   'Concluir',  'btn-success', 'FIM'),
    'PAUSADO':     ('EM_EXECUCAO', 'Retomar',   'btn-warning', 'RETOMADA'),
    'PENDENTE':    ('EM_EXECUCAO', 'Retomar',   'btn-warning', 'RETOMADA'),
}


def _servicos_do_tecnico(user):
    return Servico.objects.filter(tecnicos__user=user).distinct()


def _cliente(servico):
    if not servico.cliente_id:
        return None
    try:
        from cadastros.models import ClienteFornecedor
        return ClienteFornecedor.objects.filter(pk=servico.cliente_id).first()
    except Exception:
        return None


def _fone_whatsapp(celular):
    if not celular:
        return ''
    digits = re.sub(r'\D', '', celular)
    return f'55{digits}' if digits else ''


def _substituir_variaveis(corpo, servico, user):
    ultimo_laudo = (
        servico.apontamentos.filter(tipo='OBSERVACAO')
        .order_by('-registrado_em').first()
    )
    laudo_texto = ultimo_laudo.descricao if ultimo_laudo else ''

    linhas_mat = []
    for mat in servico.materiais.all():
        qtd = mat.quantidade_realizada if mat.quantidade_realizada is not None else mat.quantidade_prevista
        linhas_mat.append(f'• {mat.item_descricao} — {qtd}')
    materiais_texto = '\n'.join(linhas_mat) or 'Nenhum material registrado'

    variaveis = {
        'cliente':   servico.cliente_nome or '',
        'os':        servico.os_codigo or '',
        'servico':   servico.tipo_atividade or '',
        'local':     servico.local or '',
        'ativo':     servico.ativo or '',
        'data':      servico.data_prevista.strftime('%d/%m/%Y') if servico.data_prevista else '',
        'tecnico':   user.get_full_name() or user.username,
        'laudo':     laudo_texto,
        'materiais': materiais_texto,
    }

    texto = corpo
    for var, valor in variaveis.items():
        texto = texto.replace(f'{{{var}}}', valor)
    return texto


@login_required
def home(request):
    hoje    = date.today()
    ativos  = _servicos_do_tecnico(request.user).exclude(
        status__in=['CONCLUIDO', 'CANCELADO']
    ).order_by('prioridade', 'data_prevista')

    pendentes_hoje = ativos.filter(data_prevista=hoje).count()

    destaque = (
        ativos.filter(status__in=['EM_EXECUCAO', 'PAUSADO']).first()
        or ativos.filter(status='A_CAMINHO').first()
        or ativos.filter(status='AGENDADO').first()
    )

    concluidos = _servicos_do_tecnico(request.user).filter(
        status__in=['CONCLUIDO', 'CANCELADO']
    ).order_by('-atualizado_em')[:50]

    return render(request, 'campo/home.html', {
        'ativos':           ativos,
        'concluidos':       concluidos,
        'pendentes_hoje':   pendentes_hoje,
        'total_fila':       ativos.count(),
        'total_concluidos': _servicos_do_tecnico(request.user).filter(status='CONCLUIDO').count(),
        'destaque':         destaque,
        'hoje':             hoje,
    })


@login_required
def detalhe(request, pk):
    servico   = get_object_or_404(_servicos_do_tecnico(request.user), pk=pk)
    timeline  = servico.tempos.order_by('timestamp')
    acao      = PROXIMA_ACAO.get(servico.status)
    cliente   = _cliente(servico)
    wa_number = _fone_whatsapp(cliente.celular if cliente else '')

    scripts_raw = ScriptMensagem.objects.filter(ativo=True)
    scripts = [
        {
            'titulo': s.titulo,
            'texto':  _substituir_variaveis(s.corpo, servico, request.user),
            'wa_link': (
                f'https://wa.me/{wa_number}?text={quote(_substituir_variaveis(s.corpo, servico, request.user))}'
                if wa_number else ''
            ),
        }
        for s in scripts_raw
    ]

    return render(request, 'campo/detalhe.html', {
        'servico':     servico,
        'timeline':    timeline,
        'acao':        acao,
        'pode_pausar': servico.status == 'EM_EXECUCAO',
        'cliente':     cliente,
        'wa_number':   wa_number,
        'scripts':     scripts,
    })


@login_required
def concluir(request, pk):
    servico = get_object_or_404(_servicos_do_tecnico(request.user), pk=pk)

    if servico.status != 'EM_EXECUCAO':
        return redirect('campo:detalhe', pk=pk)

    materiais = servico.materiais.all()

    if request.method == 'POST':
        laudo = request.POST.get('laudo', '').strip()
        if not laudo:
            return render(request, 'campo/concluir.html', {
                'servico':   servico,
                'materiais': materiais,
                'erro':      'O laudo técnico é obrigatório para concluir o serviço.',
            })

        agora = timezone.now()

        # Salva laudo como apontamento
        ServApontamento.objects.create(
            servico   = servico,
            tipo      = 'OBSERVACAO',
            descricao = laudo,
            user      = request.user,
        )

        # Atualiza quantidades realizadas dos materiais
        for mat in materiais:
            campo_qtd = f'qtd_{mat.pk}'
            valor = request.POST.get(campo_qtd, '').strip()
            if valor:
                try:
                    mat.quantidade_realizada = float(valor.replace(',', '.'))
                    mat.save(update_fields=['quantidade_realizada'])
                except ValueError:
                    pass

        # Conclui o serviço
        servico.status = 'CONCLUIDO'
        servico.save(update_fields=['status', 'atualizado_em'])

        ServTempo.objects.create(
            servico    = servico,
            evento     = 'FIM',
            timestamp  = agora,
            data_ref   = agora.date(),
            user       = request.user,
            observacao = 'Conclusão com relatório técnico',
        )

        return redirect('campo:detalhe', pk=pk)

    return render(request, 'campo/concluir.html', {
        'servico':   servico,
        'materiais': materiais,
        'erro':      None,
    })


@login_required
@require_POST
def acao_status(request, pk):
    servico = get_object_or_404(_servicos_do_tecnico(request.user), pk=pk)
    acao    = request.POST.get('acao')

    transicoes_validas = {
        'avancar': PROXIMA_ACAO.get(servico.status),
        'pausar':  ('PAUSADO', 'Pausar', '', 'PAUSA') if servico.status == 'EM_EXECUCAO' else None,
    }

    transicao = transicoes_validas.get(acao)
    if not transicao:
        return redirect('campo:detalhe', pk=pk)

    novo_status, _, _, evento = transicao

    # Conclusão passa pela tela de relatório técnico
    if novo_status == 'CONCLUIDO':
        return redirect('campo:concluir', pk=pk)

    agora = timezone.now()
    servico.status = novo_status
    servico.save(update_fields=['status', 'atualizado_em'])

    ServTempo.objects.create(
        servico    = servico,
        evento     = evento,
        timestamp  = agora,
        data_ref   = agora.date(),
        user       = request.user,
        observacao = request.POST.get('observacao', ''),
    )

    return redirect('campo:detalhe', pk=pk)

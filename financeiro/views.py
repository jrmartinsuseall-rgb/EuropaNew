from datetime import date, datetime
from django.http import HttpResponse
from core.pagination import paginar
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Q, Sum
from decimal import Decimal
from django.db import transaction
from core.decorators import modulo_required
from core.models import Empresa, Banco, ConfiguracaoCaixa, Projeto, ProjetoOrcamento
from cadastros.models import Portador
from .models import ContaReceber, ContaPagar, AberturaCaixa, MovimentoCaixa
from .forms import (ContaReceberForm, ContaPagarForm,
                    CaixaAberturaForm, CaixaMovimentoForm, CaixaSangriaForm,
                    CaixaRecebimentoForm, CaixaPagamentoForm)
from .relatorios import render_pdf


# ── Contas a Receber ─────────────────────────────────────────

def _totais_contarec(qs):
    """Agrega totais financeiros de um queryset de ContaReceber."""
    agg = qs.aggregate(
        total_valor=Sum('valor'),
        total_juros=Sum('juros'),
        total_descontos=Sum('descontos'),
        total_valorpago=Sum('valorpago'),
    )
    zero = Decimal('0.00')
    return {
        'total_valor':     agg['total_valor']     or zero,
        'total_juros':     agg['total_juros']     or zero,
        'total_descontos': agg['total_descontos'] or zero,
        'total_valorpago': agg['total_valorpago'] or zero,
    }


@modulo_required('acesso_financeiro')
def contarec_list(request):
    status_filtro = request.GET.get('status', 'A')
    q             = request.GET.get('q', '').strip()
    empresa_id    = request.session.get('empresa_id')

    qs = ContaReceber.objects.select_related('cliente', 'portador', 'banco')
    if empresa_id:
        qs = qs.filter(empresa_id=empresa_id)
    if status_filtro and status_filtro != 'TODOS':
        qs = qs.filter(status=status_filtro)
    if q:
        qs = qs.filter(
            Q(cliente__razao__icontains=q) |
            Q(cliente__nome__icontains=q)  |
            Q(numerodoc__icontains=q)
        )
    qs = qs.order_by('vencimento', 'idcontarec')

    base = ContaReceber.objects.filter(empresa_id=empresa_id) if empresa_id else ContaReceber.objects.all()
    counts = {
        'aberto':    base.filter(status='A').count(),
        'vencido':   base.filter(status='A', vencimento__lt=date.today()).count(),
        'baixado':   base.filter(status__in=['B', 'P']).count(),
        'cancelado': base.filter(status__in=['C', 'R']).count(),
    }

    totais               = _totais_contarec(qs)
    page_obj, page_range, query_string = paginar(request, qs)

    return render(request, 'financeiro/contarec_list.html', {
        'titulos':      page_obj.object_list,
        'page_obj':     page_obj,
        'page_range':   page_range,
        'query_string': query_string,
        'status_filtro': status_filtro,
        'q':            q,
        'counts':       counts,
        'hoje':         date.today(),
        **totais,
    })


@modulo_required('acesso_financeiro')
def contarec_imprimir(request):
    STATUS_LABELS = {
        'A': 'Abertos', 'B': 'Baixados / Parciais',
        'C': 'Cancelados / Renegociados', 'TODOS': 'Todos',
    }
    status_filtro = request.GET.get('status', 'A')
    q             = request.GET.get('q', '').strip()
    empresa_id    = request.session.get('empresa_id')
    empresa       = get_object_or_404(Empresa, pk=empresa_id)

    qs = ContaReceber.objects.select_related('cliente', 'portador', 'banco')
    if empresa_id:
        qs = qs.filter(empresa_id=empresa_id)
    if status_filtro and status_filtro != 'TODOS':
        qs = qs.filter(status=status_filtro)
    if q:
        qs = qs.filter(
            Q(cliente__razao__icontains=q) | Q(cliente__nome__icontains=q) |
            Q(numerodoc__icontains=q)
        )
    qs = qs.order_by('vencimento', 'idcontarec')

    totais = _totais_contarec(qs)
    saldo_aberto = (totais['total_valor'] + totais['total_juros']
                    - totais['total_descontos'] - totais['total_valorpago'])

    return render_pdf(
        'relatorios/contarec_lista.html',
        {
            'empresa':       empresa,
            'titulos':       qs,
            'hoje':          date.today(),
            'status_label':  STATUS_LABELS.get(status_filtro, ''),
            'q':             q,
            'saldo_aberto':  saldo_aberto,
            'now':           datetime.now(),
            'usuario':       request.user.username,
            **totais,
        },
        filename='contas-a-receber.pdf',
        request=request,
    )


@modulo_required('acesso_financeiro')
def contarec_buscar(request):
    q             = request.GET.get('q', '').strip()
    status_filtro = request.GET.get('status', 'A')
    empresa_id    = request.session.get('empresa_id')

    qs = ContaReceber.objects.select_related('cliente', 'portador', 'banco')
    if empresa_id:
        qs = qs.filter(empresa_id=empresa_id)

    if status_filtro and status_filtro != 'TODOS':
        qs = qs.filter(status=status_filtro)

    if q:
        qs = qs.filter(
            Q(cliente__razao__icontains=q) |
            Q(cliente__nome__icontains=q)  |
            Q(numerodoc__icontains=q)
        )

    qs = qs.order_by('vencimento', 'idcontarec')

    totais               = _totais_contarec(qs)
    page_obj, page_range, query_string = paginar(request, qs)

    return render(request, 'financeiro/partials/tabela_contarec.html', {
        'titulos':      page_obj.object_list,
        'page_obj':     page_obj,
        'page_range':   page_range,
        'query_string': query_string,
        'hoje':         date.today(),
        **totais,
    })


@modulo_required('acesso_financeiro')
def contarec_create(request):
    empresa_id = request.session.get('empresa_id')
    empresa = get_object_or_404(Empresa, pk=empresa_id) if empresa_id else None

    if request.method == 'POST':
        form = ContaReceberForm(request.POST, empresa_id=empresa_id)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.empresa = empresa
            obj.save()
            messages.success(request, f'Título CR-{obj.idcontarec} lançado com sucesso.')
            if 'salvar_novo' in request.POST:
                return redirect('financeiro:contarec_create')
            return redirect('financeiro:contarec_list')
    else:
        form = ContaReceberForm(initial={'data': date.today(), 'status': 'A'}, empresa_id=empresa_id)

    return render(request, 'financeiro/contarec_form.html', {
        'form':   form,
        'titulo': 'Novo Lançamento — Contas a Receber',
        'objeto': None,
    })


@modulo_required('acesso_financeiro')
def contarec_edit(request, pk):
    empresa_id = request.session.get('empresa_id')
    obj = get_object_or_404(ContaReceber, pk=pk, empresa_id=empresa_id)

    # Título baixado não pode ser editado — apenas visualizado
    bloqueado = obj.status in ('B', 'P')

    if request.method == 'POST' and not bloqueado:
        form = ContaReceberForm(request.POST, instance=obj, empresa_id=empresa_id)
        if form.is_valid():
            form.save()
            messages.success(request, f'Título CR-{obj.idcontarec} atualizado.')
            return redirect('financeiro:contarec_list')
    else:
        form = ContaReceberForm(instance=obj, empresa_id=empresa_id)

    if bloqueado:
        for field in form.fields.values():
            field.disabled = True

    return render(request, 'financeiro/contarec_form.html', {
        'form':      form,
        'titulo':    f'Editar — CR-{obj.idcontarec}',
        'objeto':    obj,
        'bloqueado': bloqueado,
    })


def _next_seq_assistente(empresa_id, cliente_id):
    """Próximo sequencial ASS_ para o cliente na empresa."""
    count = ContaReceber.objects.filter(
        empresa_id=empresa_id,
        cliente_id=cliente_id,
        numerodoc__startswith='ASS_',
    ).count()
    return count + 1


def _clientes_assistente(empresa_id):
    """Clientes ativos com valorreferencia > 0."""
    from cadastros.models import ClienteFornecedor
    return (ClienteFornecedor.objects
            .filter(empresa_id=empresa_id, valorreferencia__gt=0, inativo=False)
            .order_by('razao', 'nome'))


def _duplicados_no_mes(empresa_id, vencimento):
    """IDs de clientes que já têm título ASS_ com vencimento no mesmo mês/ano."""
    return set(
        ContaReceber.objects
        .filter(
            empresa_id=empresa_id,
            numerodoc__startswith='ASS_',
            vencimento__year=vencimento.year,
            vencimento__month=vencimento.month,
        )
        .values_list('cliente_id', flat=True)
    )


@modulo_required('acesso_financeiro')
def contarec_assistente(request):
    from cadastros.models import ClienteFornecedor
    empresa_id = request.session.get('empresa_id')
    empresa    = get_object_or_404(Empresa, pk=empresa_id)
    portadores = Portador.objects.filter(empresa_id=empresa_id, inativo=False).order_by('descricao')
    bancos     = Banco.objects.filter(inativo=False).order_by('descricao')

    return render(request, 'financeiro/contarec_assistente.html', {
        'portadores': portadores,
        'bancos':     bancos,
        'hoje':       date.today(),
    })


@modulo_required('acesso_financeiro')
def contarec_assistente_preview(request):
    """HTMX — carrega tabela de clientes para a competência informada."""
    empresa_id = request.session.get('empresa_id')
    venc_str   = request.POST.get('vencimento', '').strip()

    try:
        from datetime import datetime as dt
        vencimento = dt.strptime(venc_str, '%Y-%m-%d').date()
    except ValueError:
        return HttpResponse('<p class="text-danger">Informe uma data de vencimento válida.</p>')

    clientes   = _clientes_assistente(empresa_id)
    duplicados = _duplicados_no_mes(empresa_id, vencimento)

    linhas = []
    for cli in clientes:
        seq      = _next_seq_assistente(empresa_id, cli.pk)
        numerodoc = f'ASS_{cli.idcliforemp:05d}_{seq:04d}'
        linhas.append({
            'cliente':    cli,
            'numerodoc':  numerodoc,
            'valor':      cli.valorreferencia,
            'duplicado':  cli.pk in duplicados,
        })

    return render(request, 'financeiro/partials/assistente_preview.html', {
        'linhas':     linhas,
        'vencimento': vencimento,
    })


@modulo_required('acesso_financeiro')
def contarec_assistente_gerar(request):
    if request.method != 'POST':
        return redirect('financeiro:contarec_assistente')

    empresa_id = request.session.get('empresa_id')
    empresa    = get_object_or_404(Empresa, pk=empresa_id)
    from cadastros.models import ClienteFornecedor

    venc_str    = request.POST.get('vencimento', '')
    portador_id = request.POST.get('portador') or None
    banco_id    = request.POST.get('banco') or None

    try:
        from datetime import datetime as dt
        vencimento = dt.strptime(venc_str, '%Y-%m-%d').date()
    except ValueError:
        messages.error(request, 'Data de vencimento inválida.')
        return redirect('financeiro:contarec_assistente')

    portador = Portador.objects.filter(pk=portador_id).first() if portador_id else None
    banco    = Banco.objects.filter(pk=banco_id).first()    if banco_id    else None

    selecionados = request.POST.getlist('selecionado')
    duplicados   = _duplicados_no_mes(empresa_id, vencimento)

    novos = []
    for cli_id_str in selecionados:
        try:
            cli_id = int(cli_id_str)
        except ValueError:
            continue
        if cli_id in duplicados:
            continue

        raw_valor = request.POST.get(f'valor_{cli_id}', '').strip().replace(',', '.')
        raw_doc   = request.POST.get(f'doc_{cli_id}', '').strip()
        try:
            valor = Decimal(raw_valor)
        except Exception:
            continue
        if valor <= 0:
            continue

        novos.append(ContaReceber(
            empresa    = empresa,
            data       = date.today(),
            cliente_id = cli_id,
            vencimento = vencimento,
            valor      = valor,
            numerodoc  = raw_doc,
            portador   = portador,
            banco      = banco,
            parcela    = 1,
            status     = 'A',
        ))

    if novos:
        ContaReceber.objects.bulk_create(novos)
        messages.success(request, f'{len(novos)} título(s) gerado(s) pelo assistente com sucesso.')
    else:
        messages.warning(request, 'Nenhum título gerado — verifique a seleção.')

    return redirect('financeiro:contarec_list')


@modulo_required('acesso_financeiro')
def contarec_cancelar(request, pk):
    """HTMX — alterna status Aberto ↔ Cancelado."""
    empresa_id = request.session.get('empresa_id')
    obj = get_object_or_404(ContaReceber, pk=pk, empresa_id=empresa_id)

    if request.method == 'POST' and obj.status in ('A', 'C'):
        obj.status = 'C' if obj.status == 'A' else 'A'
        obj.save(update_fields=['status'])

    return render(request, 'financeiro/partials/linha_contarec.html', {
        't':    obj,
        'hoje': date.today(),
    })


# ── Contas a Pagar ───────────────────────────────────────────

def _totais_contapag(qs):
    """Agrega totais financeiros de um queryset de ContaPagar."""
    agg = qs.aggregate(
        total_valor=Sum('valor'),
        total_juros=Sum('juros'),
        total_descontos=Sum('descontos'),
        total_valorpago=Sum('valorpago'),
    )
    zero = Decimal('0.00')
    return {
        'total_valor':     agg['total_valor']     or zero,
        'total_juros':     agg['total_juros']     or zero,
        'total_descontos': agg['total_descontos'] or zero,
        'total_valorpago': agg['total_valorpago'] or zero,
    }


@modulo_required('acesso_financeiro')
def contapag_list(request):
    status_filtro = request.GET.get('status', 'A')
    q             = request.GET.get('q', '').strip()
    empresa_id    = request.session.get('empresa_id')

    qs = ContaPagar.objects.select_related('fornecedor', 'portador', 'banco')
    if empresa_id:
        qs = qs.filter(empresa_id=empresa_id)
    if status_filtro and status_filtro != 'TODOS':
        qs = qs.filter(status=status_filtro)
    if q:
        qs = qs.filter(
            Q(fornecedor__razao__icontains=q) |
            Q(fornecedor__nome__icontains=q)  |
            Q(numerodoc__icontains=q)
        )
    qs = qs.order_by('vencimento', 'idcontapag')

    base = ContaPagar.objects.filter(empresa_id=empresa_id) if empresa_id else ContaPagar.objects.all()
    counts = {
        'aberto':    base.filter(status='A').count(),
        'vencido':   base.filter(status='A', vencimento__lt=date.today()).count(),
        'baixado':   base.filter(status__in=['B', 'P']).count(),
        'cancelado': base.filter(status='C').count(),
    }

    totais               = _totais_contapag(qs)
    page_obj, page_range, query_string = paginar(request, qs)

    return render(request, 'financeiro/contapag_list.html', {
        'titulos':      page_obj.object_list,
        'page_obj':     page_obj,
        'page_range':   page_range,
        'query_string': query_string,
        'status_filtro': status_filtro,
        'q':            q,
        'counts':       counts,
        'hoje':         date.today(),
        **totais,
    })


@modulo_required('acesso_financeiro')
def contapag_imprimir(request):
    STATUS_LABELS = {
        'A': 'Abertos', 'B': 'Baixados / Parciais',
        'C': 'Cancelados', 'TODOS': 'Todos',
    }
    status_filtro = request.GET.get('status', 'A')
    q             = request.GET.get('q', '').strip()
    empresa_id    = request.session.get('empresa_id')
    empresa       = get_object_or_404(Empresa, pk=empresa_id)

    qs = ContaPagar.objects.select_related('fornecedor', 'portador', 'banco')
    if empresa_id:
        qs = qs.filter(empresa_id=empresa_id)
    if status_filtro and status_filtro != 'TODOS':
        qs = qs.filter(status=status_filtro)
    if q:
        qs = qs.filter(
            Q(fornecedor__razao__icontains=q) | Q(fornecedor__nome__icontains=q) |
            Q(numerodoc__icontains=q)
        )
    qs = qs.order_by('vencimento', 'idcontapag')

    totais = _totais_contapag(qs)
    saldo_aberto = (totais['total_valor'] + totais['total_juros']
                    - totais['total_descontos'] - totais['total_valorpago'])

    return render_pdf(
        'relatorios/contapag_lista.html',
        {
            'empresa':       empresa,
            'titulos':       qs,
            'hoje':          date.today(),
            'status_label':  STATUS_LABELS.get(status_filtro, ''),
            'q':             q,
            'saldo_aberto':  saldo_aberto,
            'now':           datetime.now(),
            'usuario':       request.user.username,
            **totais,
        },
        filename='contas-a-pagar.pdf',
        request=request,
    )


@modulo_required('acesso_financeiro')
def contapag_buscar(request):
    q             = request.GET.get('q', '').strip()
    status_filtro = request.GET.get('status', 'A')
    empresa_id    = request.session.get('empresa_id')

    qs = ContaPagar.objects.select_related('fornecedor', 'portador', 'banco')
    if empresa_id:
        qs = qs.filter(empresa_id=empresa_id)

    if status_filtro and status_filtro != 'TODOS':
        qs = qs.filter(status=status_filtro)

    if q:
        qs = qs.filter(
            Q(fornecedor__razao__icontains=q) |
            Q(fornecedor__nome__icontains=q)  |
            Q(numerodoc__icontains=q)
        )

    qs = qs.order_by('vencimento', 'idcontapag')

    totais               = _totais_contapag(qs)
    page_obj, page_range, query_string = paginar(request, qs)

    return render(request, 'financeiro/partials/tabela_contapag.html', {
        'titulos':      page_obj.object_list,
        'page_obj':     page_obj,
        'page_range':   page_range,
        'query_string': query_string,
        'hoje':         date.today(),
        **totais,
    })


@modulo_required('acesso_financeiro')
def contapag_create(request):
    empresa_id = request.session.get('empresa_id')
    empresa = get_object_or_404(Empresa, pk=empresa_id) if empresa_id else None

    if request.method == 'POST':
        form = ContaPagarForm(request.POST, empresa_id=empresa_id)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.empresa = empresa
            obj.save()
            messages.success(request, f'Título CP-{obj.idcontapag} lançado com sucesso.')
            if 'salvar_novo' in request.POST:
                return redirect('financeiro:contapag_create')
            return redirect('financeiro:contapag_list')
    else:
        form = ContaPagarForm(initial={'data': date.today(), 'status': 'A'}, empresa_id=empresa_id)

    return render(request, 'financeiro/contapag_form.html', {
        'form':   form,
        'titulo': 'Novo Lançamento — Contas a Pagar',
        'objeto': None,
    })


@modulo_required('acesso_financeiro')
def contapag_edit(request, pk):
    empresa_id = request.session.get('empresa_id')
    obj = get_object_or_404(ContaPagar, pk=pk, empresa_id=empresa_id)

    bloqueado = obj.status in ('B', 'P')

    if request.method == 'POST' and not bloqueado:
        form = ContaPagarForm(request.POST, instance=obj, empresa_id=empresa_id)
        if form.is_valid():
            form.save()
            messages.success(request, f'Título CP-{obj.idcontapag} atualizado.')
            return redirect('financeiro:contapag_list')
    else:
        form = ContaPagarForm(instance=obj, empresa_id=empresa_id)

    if bloqueado:
        for field in form.fields.values():
            field.disabled = True

    return render(request, 'financeiro/contapag_form.html', {
        'form':      form,
        'titulo':    f'Editar — CP-{obj.idcontapag}',
        'objeto':    obj,
        'bloqueado': bloqueado,
    })


@modulo_required('acesso_financeiro')
def contapag_cancelar(request, pk):
    """HTMX — alterna status Aberto ↔ Cancelado."""
    empresa_id = request.session.get('empresa_id')
    obj = get_object_or_404(ContaPagar, pk=pk, empresa_id=empresa_id)

    if request.method == 'POST' and obj.status in ('A', 'C'):
        obj.status = 'C' if obj.status == 'A' else 'A'
        obj.save(update_fields=['status'])

    return render(request, 'financeiro/partials/linha_contapag.html', {
        't':    obj,
        'hoje': date.today(),
    })


# ── Geração de Boletos ───────────────────────────────────────

@modulo_required('acesso_financeiro')
def boletos_view(request):
    empresa_id = request.session.get('empresa_id')

    # Defaults do ConfiguracaoCaixa (portador_cheque)
    cfg = ConfiguracaoCaixa.objects.filter(pk=1).first()

    bancos    = Banco.objects.filter(inativo=False).order_by('descricao')
    portadores = Portador.objects.filter(empresa_id=empresa_id, inativo=False).order_by('descricao')

    # Banco e portador selecionados (GET param para persistir entre buscas)
    banco_id    = request.GET.get('banco') or request.POST.get('banco')
    portador_id = request.GET.get('portador') or request.POST.get('portador')

    # Default de portador vem da configuração de caixa
    if not portador_id and cfg and cfg.portador_cheque_id:
        portador_id = str(cfg.portador_cheque_id)

    # Títulos elegíveis: Abertos, sem numerobanco, da empresa
    qs = (ContaReceber.objects
          .select_related('cliente', 'banco', 'portador')
          .filter(status='A', numerobanco=''))
    if empresa_id:
        qs = qs.filter(empresa_id=empresa_id)
    qs = qs.order_by('vencimento', 'idcontarec')

    banco_sel    = None
    portador_sel = None
    if banco_id:
        banco_sel = bancos.filter(pk=banco_id).first()
    if portador_id:
        portador_sel = portadores.filter(pk=portador_id).first()

    return render(request, 'financeiro/boletos.html', {
        'titulos':      qs,
        'bancos':       bancos,
        'portadores':   portadores,
        'banco_sel':    banco_sel,
        'portador_sel': portador_sel,
        'hoje':         date.today(),
    })


@modulo_required('acesso_financeiro')
def boletos_gerar(request):
    """POST — gera numerobanco para os títulos selecionados."""
    if request.method != 'POST':
        return redirect('financeiro:boletos')

    empresa_id   = request.session.get('empresa_id')
    banco_id     = request.POST.get('banco')
    portador_id  = request.POST.get('portador')
    selecionados = request.POST.getlist('selecionados')

    if not banco_id:
        messages.error(request, 'Selecione um banco antes de gerar.')
        return redirect('financeiro:boletos')
    if not selecionados:
        messages.warning(request, 'Nenhum título selecionado.')
        return redirect('financeiro:boletos')

    try:
        with transaction.atomic():
            banco = Banco.objects.select_for_update().get(pk=banco_id)
            portador = Portador.objects.get(pk=portador_id) if portador_id else None

            titulos = (ContaReceber.objects
                       .select_for_update()
                       .filter(pk__in=selecionados,
                               status='A',
                               numerobanco='',
                               empresa_id=empresa_id)
                       .order_by('vencimento', 'idcontarec'))

            proximo = banco.numeroboleto if banco.numeroboleto > 0 else 1
            processados = 0

            for i, titulo in enumerate(titulos):
                titulo.numerobanco = str(proximo + i)
                titulo.banco       = banco
                if portador:
                    titulo.portador = portador
                titulo.save(update_fields=['numerobanco', 'banco', 'portador'])
                processados += 1

            if processados:
                banco.numeroboleto = proximo + processados
                banco.save(update_fields=['numeroboleto'])

        messages.success(
            request,
            f'{processados} boleto(s) gerado(s) — '
            f'numeração {proximo} a {proximo + processados - 1} — '
            f'Banco: {banco.descricao}.'
        )
    except Exception as exc:
        messages.error(request, f'Erro ao gerar boletos: {exc}')

    return redirect('financeiro:boletos')


# ── Caixa ─────────────────────────────────────────────────────

def _sessao_aberta(empresa_id):
    return (AberturaCaixa.objects
            .filter(empresa_id=empresa_id, datafecha__isnull=True)
            .order_by('-dataabre', '-idautenticacao')
            .first())


def _get_saldo_atual(empresa_id):
    ultimo = (MovimentoCaixa.objects
              .filter(empresa_id=empresa_id, data=date.today(), status='A')
              .order_by('id')
              .last())
    return ultimo.saldo if ultimo else Decimal('0.00')


def _get_saldo_dia_anterior(empresa_id):
    """Saldo do último movimento ativo antes de hoje — base para abertura do dia."""
    ultimo = (MovimentoCaixa.objects
              .filter(empresa_id=empresa_id, status='A', data__lt=date.today())
              .order_by('data', 'id')
              .last())
    return ultimo.saldo if ultimo else Decimal('0.00')


_TIPOBAIXA_SEM_PROJETO = {'ABERTURA', 'FECHAMENTO', 'REABERTURA'}


def _criar_movimento(sessao, empresa, tipo, tipobaixa, descricao, valor,
                     documento='', cliforemp=None, idorigem=0,
                     conta=None, subconta=None, banco=None, projeto=None):
    saldo_ant = _get_saldo_atual(empresa.pk)
    novo_saldo = saldo_ant + valor if tipo == 'E' else saldo_ant - valor
    projeto_mov = None if tipobaixa in _TIPOBAIXA_SEM_PROJETO else projeto
    mov = MovimentoCaixa.objects.create(
        idautenticacao=sessao,
        empresa=empresa,
        data=date.today(),
        descricao=descricao,
        tipo=tipo,
        valor=valor,
        documento=documento,
        cliforemp=cliforemp,
        idorigem=idorigem,
        tipobaixa=tipobaixa,
        saldo=novo_saldo,
        conta=conta,
        subconta=subconta,
        banco=banco,
        projeto=projeto_mov,
        status='A',
    )
    sessao.saldo = novo_saldo
    sessao.save(update_fields=['saldo'])
    return mov


def _resumo_movimentos(movimentos):
    from collections import defaultdict
    grupos = defaultdict(lambda: {'creditos': Decimal('0'), 'debitos': Decimal('0')})
    for m in movimentos:
        if m.status != 'A':
            continue
        g = grupos[m.tipobaixa]
        if m.tipo == 'E':
            g['creditos'] += m.valor
        else:
            g['debitos'] += m.valor
    return [
        {'tipobaixa': tb, 'creditos': g['creditos'],
         'debitos': g['debitos'], 'saldo': g['creditos'] - g['debitos']}
        for tb, g in grupos.items()
    ]


@modulo_required('acesso_financeiro')
def caixa_view(request):
    empresa_id = request.session.get('empresa_id')
    empresa = get_object_or_404(Empresa, pk=empresa_id) if empresa_id else None

    sessao = _sessao_aberta(empresa_id)
    cfg = ConfiguracaoCaixa.objects.filter(pk=1).first()

    movimentos = []
    resumo = []
    saldo_atual = Decimal('0.00')
    total_creditos = Decimal('0.00')
    total_debitos  = Decimal('0.00')

    reabrir = MovimentoCaixa.objects.filter(
        empresa_id=empresa_id, data=date.today()
    ).exists()

    projeto_ativo_id = request.session.get('projeto_ativo_id')
    projeto_ativo    = Projeto.objects.filter(pk=projeto_ativo_id, inativo=False).first() if projeto_ativo_id else None
    projetos         = Projeto.objects.filter(empresa_id=empresa_id, inativo=False).order_by('codigo')

    if sessao:
        movimentos = list(
            MovimentoCaixa.objects
            .select_related('cliforemp', 'conta', 'subconta', 'projeto')
            .filter(empresa_id=empresa_id, data=date.today())
            .order_by('id')
        )
        saldo_atual    = _get_saldo_atual(empresa_id)
        resumo         = _resumo_movimentos(movimentos)
        total_creditos = sum(r['creditos'] for r in resumo)
        total_debitos  = sum(r['debitos']  for r in resumo)

    return render(request, 'financeiro/caixa.html', {
        'sessao':          sessao,
        'reabrir':         reabrir,
        'movimentos':      movimentos,
        'resumo':          resumo,
        'cfg':             cfg,
        'saldo_atual':     saldo_atual,
        'total_creditos':  total_creditos,
        'total_debitos':   total_debitos,
        'projetos':        projetos,
        'projeto_ativo':   projeto_ativo,
        'form_abertura':   CaixaAberturaForm(
            initial={'saldo_inicial': _get_saldo_dia_anterior(empresa_id)}
            if not sessao and not reabrir else {}
        ),
        'form_entrada':    CaixaMovimentoForm(prefix='ent', deb_cred='C', empresa_id=empresa_id),
        'form_saida':      CaixaMovimentoForm(prefix='sai', deb_cred='D', empresa_id=empresa_id),
        'form_sangria':    CaixaSangriaForm(prefix='san', empresa_id=empresa_id),
        'hoje':            date.today(),
    })


@modulo_required('acesso_financeiro')
def caixa_projeto_selecionar(request):
    if request.method == 'POST':
        pk = request.POST.get('projeto_id', '').strip()
        if pk:
            request.session['projeto_ativo_id'] = int(pk)
        else:
            request.session.pop('projeto_ativo_id', None)
    return redirect('financeiro:caixa')


@modulo_required('acesso_financeiro')
def caixa_abrir(request):
    if request.method != 'POST':
        return redirect('financeiro:caixa')

    empresa_id = request.session.get('empresa_id')
    empresa = get_object_or_404(Empresa, pk=empresa_id)

    if _sessao_aberta(empresa_id):
        messages.warning(request, 'Já existe uma sessão de caixa aberta.')
        return redirect('financeiro:caixa')

    reabrir = MovimentoCaixa.objects.filter(
        empresa_id=empresa_id, data=date.today()
    ).exists()

    cfg = ConfiguracaoCaixa.objects.filter(pk=1).first()
    hora = datetime.now().strftime('%H:%M:%S')

    if reabrir:
        saldo_inicial = Decimal('0.00')
        with transaction.atomic():
            sessao = AberturaCaixa.objects.create(
                empresa=empresa,
                usuabre=request.user.username,
                dataabre=date.today(),
                horaabre=hora,
                conta=cfg.conta_recebimento if cfg else None,
                subconta=cfg.subconta_recebimento if cfg else None,
                idcontapg=cfg.conta_pagamento_id or 0 if cfg else 0,
                idsubcontapg=cfg.subconta_pagamento_id or 0 if cfg else 0,
                idportadorche=cfg.portador_cheque_id or 0 if cfg else 0,
                idportadordest=cfg.portador_sangria_id or 0 if cfg else 0,
                saldo=_get_saldo_atual(empresa_id),
            )
            _criar_movimento(
                sessao=sessao, empresa=empresa,
                tipo='E', tipobaixa='ABERTURA',
                descricao='REABERTURA DE CAIXA',
                valor=Decimal('0.00'),
            )
        messages.success(request, 'Caixa reaberto — saldo continua do fechamento anterior.')
        return redirect('financeiro:caixa')

    form = CaixaAberturaForm(request.POST)
    if form.is_valid():
        saldo_inicial = form.cleaned_data['saldo_inicial']
        with transaction.atomic():
            sessao = AberturaCaixa.objects.create(
                empresa=empresa,
                usuabre=request.user.username,
                dataabre=date.today(),
                horaabre=hora,
                conta=cfg.conta_recebimento if cfg else None,
                subconta=cfg.subconta_recebimento if cfg else None,
                idcontapg=cfg.conta_pagamento_id or 0 if cfg else 0,
                idsubcontapg=cfg.subconta_pagamento_id or 0 if cfg else 0,
                idportadorche=cfg.portador_cheque_id or 0 if cfg else 0,
                idportadordest=cfg.portador_sangria_id or 0 if cfg else 0,
                saldo=saldo_inicial,
            )
            _criar_movimento(
                sessao=sessao, empresa=empresa,
                tipo='E', tipobaixa='ABERTURA',
                descricao='ABERTURA DE CAIXA',
                valor=saldo_inicial,
                conta=cfg.conta_recebimento if cfg else None,
                subconta=cfg.subconta_recebimento if cfg else None,
            )
        messages.success(request, f'Caixa aberto — saldo inicial R$ {saldo_inicial:.2f}.')
    else:
        messages.error(request, 'Informe um saldo inicial válido.')

    return redirect('financeiro:caixa')


@modulo_required('acesso_financeiro')
def caixa_fechar(request):
    if request.method != 'POST':
        return redirect('financeiro:caixa')

    empresa_id = request.session.get('empresa_id')
    empresa = get_object_or_404(Empresa, pk=empresa_id)
    sessao = _sessao_aberta(empresa_id)

    if not sessao:
        messages.error(request, 'Nenhuma sessão de caixa aberta.')
        return redirect('financeiro:caixa')

    hora = datetime.now().strftime('%H:%M:%S')
    with transaction.atomic():
        saldo_final = _get_saldo_atual(empresa_id)
        _criar_movimento(
            sessao=sessao, empresa=empresa,
            tipo='E', tipobaixa='FECHAMENTO',
            descricao='FECHAMENTO DE CAIXA',
            valor=Decimal('0.00'),
        )
        sessao.usufecha = request.user.username
        sessao.datafecha = date.today()
        sessao.horafecha = hora
        sessao.saldo = saldo_final
        sessao.save(update_fields=['usufecha', 'datafecha', 'horafecha', 'saldo'])

    messages.success(request, f'Caixa fechado — saldo final R$ {saldo_final:.2f}.')
    return redirect('financeiro:caixa')


def _verificar_orcamento(request, projeto, conta, tipo_mov):
    """Emite messages.warning se o total realizado ultrapassou o orçamento do projeto."""
    if not projeto or not conta:
        return
    orcamento = ProjetoOrcamento.objects.filter(projeto=projeto, conta=conta).first()
    if not orcamento or not orcamento.valor_estimado:
        return

    hoje = date.today()
    _SEM_PROJ = {'ABERTURA', 'FECHAMENTO', 'REABERTURA'}
    total = (MovimentoCaixa.objects
             .filter(
                 projeto=projeto,
                 conta=conta,
                 tipo=tipo_mov,
                 data__year=hoje.year,
                 data__month=hoje.month,
                 status='A',
             )
             .exclude(tipobaixa__in=_SEM_PROJ)
             .aggregate(total=Sum('valor'))['total'] or Decimal('0.00'))

    if total > orcamento.valor_estimado:
        excesso = total - orcamento.valor_estimado
        messages.warning(
            request,
            f'Alerta orçamentário — Projeto "{projeto.codigo}" / '
            f'Conta "{conta.descricao}": '
            f'realizado R$ {total:,.2f} excede o orçamento de '
            f'R$ {orcamento.valor_estimado:,.2f} '
            f'(excesso de R$ {excesso:,.2f}) na competência {hoje.month:02d}/{hoje.year}.'
        )


@modulo_required('acesso_financeiro')
def caixa_entrada(request):
    if request.method != 'POST':
        return redirect('financeiro:caixa')

    empresa_id = request.session.get('empresa_id')
    empresa = get_object_or_404(Empresa, pk=empresa_id)
    sessao = _sessao_aberta(empresa_id)

    if not sessao:
        messages.error(request, 'Nenhuma sessão de caixa aberta.')
        return redirect('financeiro:caixa')

    form = CaixaMovimentoForm(request.POST, prefix='ent', deb_cred='C', empresa_id=empresa_id)
    if form.is_valid():
        cfg = ConfiguracaoCaixa.objects.filter(pk=1).first()
        conta = form.cleaned_data.get('conta') or (cfg.conta_recebimento if cfg else None)
        projeto_id = request.session.get('projeto_ativo_id')
        projeto = Projeto.objects.filter(pk=projeto_id).first() if projeto_id else None
        _criar_movimento(
            sessao=sessao, empresa=empresa,
            tipo='E', tipobaixa='ENTRADA',
            descricao=form.cleaned_data['descricao'],
            valor=form.cleaned_data['valor'],
            documento=form.cleaned_data.get('documento', ''),
            conta=conta,
            subconta=cfg.subconta_recebimento if cfg and not form.cleaned_data.get('conta') else None,
            projeto=projeto,
        )
        messages.success(request, 'Entrada registrada.')
        _verificar_orcamento(request, projeto, conta, 'E')
    else:
        messages.error(request, 'Verifique os dados da entrada.')
    return redirect('financeiro:caixa')


@modulo_required('acesso_financeiro')
def caixa_saida(request):
    if request.method != 'POST':
        return redirect('financeiro:caixa')

    empresa_id = request.session.get('empresa_id')
    empresa = get_object_or_404(Empresa, pk=empresa_id)
    sessao = _sessao_aberta(empresa_id)

    if not sessao:
        messages.error(request, 'Nenhuma sessão de caixa aberta.')
        return redirect('financeiro:caixa')

    form = CaixaMovimentoForm(request.POST, prefix='sai', deb_cred='D', empresa_id=empresa_id)
    if form.is_valid():
        cfg = ConfiguracaoCaixa.objects.filter(pk=1).first()
        conta = form.cleaned_data.get('conta') or (cfg.conta_pagamento if cfg else None)
        projeto_id = request.session.get('projeto_ativo_id')
        projeto = Projeto.objects.filter(pk=projeto_id).first() if projeto_id else None
        _criar_movimento(
            sessao=sessao, empresa=empresa,
            tipo='S', tipobaixa='SAIDA',
            descricao=form.cleaned_data['descricao'],
            valor=form.cleaned_data['valor'],
            documento=form.cleaned_data.get('documento', ''),
            conta=conta,
            subconta=cfg.subconta_pagamento if cfg and not form.cleaned_data.get('conta') else None,
            projeto=projeto,
        )
        messages.success(request, 'Saída registrada.')
        _verificar_orcamento(request, projeto, conta, 'S')
    else:
        messages.error(request, 'Verifique os dados da saída.')
    return redirect('financeiro:caixa')


@modulo_required('acesso_financeiro')
def caixa_sangria(request):
    if request.method != 'POST':
        return redirect('financeiro:caixa')

    empresa_id = request.session.get('empresa_id')
    empresa = get_object_or_404(Empresa, pk=empresa_id)
    sessao = _sessao_aberta(empresa_id)

    if not sessao:
        messages.error(request, 'Nenhuma sessão de caixa aberta.')
        return redirect('financeiro:caixa')

    form = CaixaSangriaForm(request.POST, prefix='san', empresa_id=empresa_id)
    if form.is_valid():
        portador = form.cleaned_data.get('portador')
        cfg = ConfiguracaoCaixa.objects.filter(pk=1).first()
        descricao = form.cleaned_data['descricao']
        if portador:
            descricao = f'{descricao} — {portador.descricao}'
        projeto_id = request.session.get('projeto_ativo_id')
        projeto = Projeto.objects.filter(pk=projeto_id).first() if projeto_id else None
        _criar_movimento(
            sessao=sessao, empresa=empresa,
            tipo='S', tipobaixa='SANGRIA',
            descricao=descricao,
            valor=form.cleaned_data['valor'],
            conta=cfg.conta_pagamento if cfg else None,
            subconta=cfg.subconta_pagamento if cfg else None,
            projeto=projeto,
        )
        messages.success(request, 'Sangria registrada.')
    else:
        messages.error(request, 'Verifique os dados da sangria.')
    return redirect('financeiro:caixa')


@modulo_required('acesso_financeiro')
def caixa_cancelar_mov(request, pk):
    if request.method != 'POST':
        return redirect('financeiro:caixa')

    empresa_id = request.session.get('empresa_id')
    empresa = get_object_or_404(Empresa, pk=empresa_id)
    sessao = _sessao_aberta(empresa_id)

    if not sessao:
        messages.error(request, 'Nenhuma sessão de caixa aberta.')
        return redirect('financeiro:caixa')

    mov = get_object_or_404(MovimentoCaixa, pk=pk, idautenticacao=sessao, status='A')

    if mov.tipobaixa in ('ABERTURA', 'FECHAMENTO', 'CANCELAMENTO'):
        messages.error(request, 'Este tipo de movimento não pode ser cancelado.')
        return redirect('financeiro:caixa')

    tipo_contra = 'S' if mov.tipo == 'E' else 'E'

    with transaction.atomic():
        _criar_movimento(
            sessao=sessao, empresa=empresa,
            tipo=tipo_contra, tipobaixa='CANCELAMENTO',
            descricao=f'CANCELAMENTO: {mov.descricao}',
            valor=mov.valor,
            documento=mov.documento,
            cliforemp=mov.cliforemp,
            idorigem=mov.pk,
            conta=mov.conta,
            subconta=mov.subconta,
            projeto=mov.projeto,
        )
        mov.status = 'C'
        mov.save(update_fields=['status'])

        if mov.idorigem > 0:
            if mov.tipobaixa == 'RECEBIMENTO':
                ContaReceber.objects.filter(pk=mov.idorigem).update(
                    status='A', valorpago=Decimal('0'),
                    pagamento=None, juros=Decimal('0'), descontos=Decimal('0'),
                )
            elif mov.tipobaixa == 'PAGAMENTO':
                ContaPagar.objects.filter(pk=mov.idorigem).update(
                    status='A', valorpago=Decimal('0'),
                    pagamento=None, juros=Decimal('0'), descontos=Decimal('0'),
                )

    messages.success(request, f'Movimento #{mov.pk} cancelado.')
    return redirect('financeiro:caixa')


@modulo_required('acesso_financeiro')
def caixa_recebimento(request):
    empresa_id = request.session.get('empresa_id')
    empresa = get_object_or_404(Empresa, pk=empresa_id)
    sessao = _sessao_aberta(empresa_id)

    if not sessao:
        messages.warning(request, 'Abra o caixa antes de registrar recebimentos.')
        return redirect('financeiro:caixa')

    q = request.GET.get('q', '').strip()
    titulos = ContaReceber.objects.none()
    if q:
        titulos = (ContaReceber.objects
                   .select_related('cliente', 'portador')
                   .filter(empresa=empresa, status__in=['A', 'P'])
                   .filter(Q(cliente__razao__icontains=q) |
                           Q(cliente__nome__icontains=q)  |
                           Q(numerodoc__icontains=q)      |
                           Q(numerobanco__icontains=q))
                   .order_by('vencimento')[:50])

    cfg = ConfiguracaoCaixa.objects.filter(pk=1).first()

    if request.method == 'POST':
        form = CaixaRecebimentoForm(request.POST, empresa_id=empresa_id)
        if form.is_valid():
            cr = get_object_or_404(ContaReceber, pk=form.cleaned_data['contarec_pk'], empresa=empresa)
            if cr.status not in ('A', 'P'):
                messages.error(request, 'Título já baixado ou cancelado.')
                return redirect('financeiro:caixa_recebimento')

            juros     = form.cleaned_data['juros']
            descontos = form.cleaned_data['descontos']
            valorpago = form.cleaned_data['valorpago']
            portador  = form.cleaned_data.get('portador')
            metodo    = form.cleaned_data.get('metodo')
            data_pag  = form.cleaned_data['data_pagamento']
            valor_mov = valorpago + juros - descontos

            tipobaixa_cr = (metodo.sigla or metodo.descricao[:20]) if metodo else ''

            with transaction.atomic():
                cr.status    = 'B'
                cr.pagamento = data_pag
                cr.juros     = juros
                cr.descontos = descontos
                cr.valorpago = valorpago
                cr.tipobaixa = tipobaixa_cr
                if portador:
                    cr.portador = portador
                cr.save(update_fields=['status', 'pagamento', 'juros', 'descontos', 'valorpago', 'tipobaixa', 'portador'])

                nome_cli  = cr.cliente.razao or cr.cliente.nome
                desc_rec  = cfg.desc_entrada if cfg else 'RECEBIMENTO'
                label_met = f' [{metodo.sigla or metodo.descricao}]' if metodo else ''
                _criar_movimento(
                    sessao=sessao, empresa=empresa,
                    tipo='E', tipobaixa='RECEBIMENTO',
                    descricao=f'{desc_rec}{label_met} — {nome_cli[:50]}',
                    valor=valor_mov,
                    documento=cr.numerodoc,
                    cliforemp=cr.cliente,
                    idorigem=cr.pk,
                    conta=sessao.conta,
                    subconta=sessao.subconta,
                )

            messages.success(request, f'CR-{cr.pk} baixado — R$ {valorpago:.2f}.')
            return redirect('financeiro:caixa_recebimento')
        else:
            messages.error(request, 'Verifique os dados informados.')
    else:
        initial = {'data_pagamento': date.today(), 'juros': Decimal('0'), 'descontos': Decimal('0')}
        form = CaixaRecebimentoForm(initial=initial, empresa_id=empresa_id)
        if cfg and cfg.portador_dinheiro_id:
            form.fields['portador'].initial = cfg.portador_dinheiro_id

    return render(request, 'financeiro/caixa_recebimento.html', {
        'sessao':  sessao,
        'titulos': titulos,
        'q':       q,
        'form':    form,
        'hoje':    date.today(),
    })


@modulo_required('acesso_financeiro')
def caixa_relatorio_fechamento(request, pk):
    empresa_id = request.session.get('empresa_id')
    empresa    = get_object_or_404(Empresa, pk=empresa_id)
    sessao     = get_object_or_404(AberturaCaixa, pk=pk, empresa_id=empresa_id)

    movimentos = list(
        MovimentoCaixa.objects
        .select_related('cliforemp', 'conta', 'subconta', 'projeto')
        .filter(empresa_id=empresa_id, data=sessao.dataabre)
        .order_by('id')
    )

    resumo         = _resumo_movimentos(movimentos)
    total_creditos = sum(r['creditos'] for r in resumo)
    total_debitos  = sum(r['debitos']  for r in resumo)
    saldo_final    = total_creditos - total_debitos

    # Resumo por projeto (excluindo ABERTURA/FECHAMENTO/REABERTURA)
    from collections import defaultdict
    grupos_proj = defaultdict(lambda: {'creditos': Decimal('0'), 'debitos': Decimal('0'),
                                       'codigo': '', 'descricao': ''})
    for m in movimentos:
        if m.status != 'A' or m.tipobaixa in _TIPOBAIXA_SEM_PROJETO:
            continue
        chave = m.projeto_id or 0
        g = grupos_proj[chave]
        if m.projeto:
            g['codigo']    = m.projeto.codigo
            g['descricao'] = m.projeto.descricao
        if m.tipo == 'E':
            g['creditos'] += m.valor
        else:
            g['debitos'] += m.valor

    resumo_projetos = [
        {**g, 'saldo': g['creditos'] - g['debitos']}
        for g in grupos_proj.values()
        if g['creditos'] or g['debitos']
    ]
    resumo_projetos.sort(key=lambda r: r.get('codigo') or 'ZZZZ')

    return render_pdf(
        'relatorios/caixa_fechamento.html',
        {
            'empresa':         empresa,
            'sessao':          sessao,
            'movimentos':      movimentos,
            'resumo':          resumo,
            'resumo_projetos': resumo_projetos,
            'total_creditos':  total_creditos,
            'total_debitos':   total_debitos,
            'saldo_final':     saldo_final,
            'now':             datetime.now(),
            'usuario':         request.user.username,
        },
        filename=f'caixa-sessao-{sessao.pk}.pdf',
        request=request,
    )


@modulo_required('acesso_financeiro')
def caixa_recebimento_buscar(request):
    empresa_id = request.session.get('empresa_id')
    q = request.GET.get('q', '').strip()
    titulos = ContaReceber.objects.none()
    if q:
        titulos = (ContaReceber.objects
                   .select_related('cliente', 'portador')
                   .filter(empresa_id=empresa_id, status__in=['A', 'P'])
                   .filter(Q(cliente__razao__icontains=q) |
                           Q(cliente__nome__icontains=q)  |
                           Q(numerodoc__icontains=q)      |
                           Q(numerobanco__icontains=q))
                   .order_by('vencimento')[:50])
    return render(request, 'financeiro/partials/caixa_rec_resultados.html', {
        'titulos': titulos, 'q': q,
    })


@modulo_required('acesso_financeiro')
def caixa_pagamento_buscar(request):
    empresa_id = request.session.get('empresa_id')
    q = request.GET.get('q', '').strip()
    titulos = ContaPagar.objects.none()
    if q:
        titulos = (ContaPagar.objects
                   .select_related('fornecedor', 'portador')
                   .filter(empresa_id=empresa_id, status__in=['A', 'P'])
                   .filter(Q(fornecedor__razao__icontains=q) |
                           Q(fornecedor__nome__icontains=q)  |
                           Q(numerodoc__icontains=q))
                   .order_by('vencimento')[:50])
    return render(request, 'financeiro/partials/caixa_pag_resultados.html', {
        'titulos': titulos, 'q': q,
    })


@modulo_required('acesso_financeiro')
def caixa_pagamento(request):
    empresa_id = request.session.get('empresa_id')
    empresa = get_object_or_404(Empresa, pk=empresa_id)
    sessao = _sessao_aberta(empresa_id)

    if not sessao:
        messages.warning(request, 'Abra o caixa antes de registrar pagamentos.')
        return redirect('financeiro:caixa')

    q = request.GET.get('q', '').strip()
    titulos = ContaPagar.objects.none()
    if q:
        titulos = (ContaPagar.objects
                   .select_related('fornecedor', 'portador')
                   .filter(empresa=empresa, status__in=['A', 'P'])
                   .filter(Q(fornecedor__razao__icontains=q) |
                           Q(fornecedor__nome__icontains=q)  |
                           Q(numerodoc__icontains=q))
                   .order_by('vencimento')[:50])

    cfg = ConfiguracaoCaixa.objects.filter(pk=1).first()

    if request.method == 'POST':
        form = CaixaPagamentoForm(request.POST, empresa_id=empresa_id)
        if form.is_valid():
            cp = get_object_or_404(ContaPagar, pk=form.cleaned_data['contapag_pk'], empresa=empresa)
            if cp.status not in ('A', 'P'):
                messages.error(request, 'Título já baixado ou cancelado.')
                return redirect('financeiro:caixa_pagamento')

            juros     = form.cleaned_data['juros']
            descontos = form.cleaned_data['descontos']
            valorpago = form.cleaned_data['valorpago']
            portador  = form.cleaned_data.get('portador')
            metodo    = form.cleaned_data.get('metodo')
            data_pag  = form.cleaned_data['data_pagamento']
            valor_mov = valorpago + juros - descontos

            tipobaixa_cp = (metodo.sigla or metodo.descricao[:20]) if metodo else ''

            with transaction.atomic():
                cp.status    = 'B'
                cp.pagamento = data_pag
                cp.juros     = juros
                cp.descontos = descontos
                cp.valorpago = valorpago
                cp.tipobaixa = tipobaixa_cp
                if portador:
                    cp.portador = portador
                cp.save(update_fields=['status', 'pagamento', 'juros', 'descontos', 'valorpago', 'tipobaixa', 'portador'])

                nome_for  = cp.fornecedor.razao or cp.fornecedor.nome
                desc_pag  = cfg.desc_saida if cfg else 'PAGAMENTO'
                label_met = f' [{metodo.sigla or metodo.descricao}]' if metodo else ''
                _criar_movimento(
                    sessao=sessao, empresa=empresa,
                    tipo='S', tipobaixa='PAGAMENTO',
                    descricao=f'{desc_pag}{label_met} — {nome_for[:50]}',
                    valor=valor_mov,
                    documento=cp.numerodoc,
                    cliforemp=cp.fornecedor,
                    idorigem=cp.pk,
                    conta=None,
                    subconta=None,
                )

            messages.success(request, f'CP-{cp.pk} baixado — R$ {valorpago:.2f}.')
            return redirect('financeiro:caixa_pagamento')
        else:
            messages.error(request, 'Verifique os dados informados.')
    else:
        form = CaixaPagamentoForm(initial={
            'data_pagamento': date.today(),
            'juros': Decimal('0'),
            'descontos': Decimal('0'),
        }, empresa_id=empresa_id)

    return render(request, 'financeiro/caixa_pagamento.html', {
        'sessao':  sessao,
        'titulos': titulos,
        'q':       q,
        'form':    form,
        'hoje':    date.today(),
    })

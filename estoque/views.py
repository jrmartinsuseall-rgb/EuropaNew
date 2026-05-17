import json
from decimal import Decimal
from datetime import date, datetime
from core.pagination import paginar
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db import transaction
from django.db.models import Q, Sum
from django.utils import timezone
from core.decorators import modulo_required
from cadastros.models import Item, Grupo, CondicaoPagamento
from core.models import Empresa
from financeiro.models import ContaPagar
from financeiro.relatorios import render_pdf
from .models import (Requisicao, ItemRequisicao, MovimentoEstoque,
                     Inventario, ItemInventario,
                     NotaFiscalEntrada, ItemNFEntrada, ParcelaNFEntrada)
from .forms import RequisicaoForm, NFEntradaForm

# Fonte única: MovimentoEstoque.ORIGEM_LABELS (definido no modelo)
ORIGEM_LABELS = MovimentoEstoque.ORIGEM_LABELS


# ── Lista ─────────────────────────────────────────────────────────────────────

@modulo_required('acesso_estoque')
def req_list(request):
    empresa_id = request.session.get('empresa_id')
    status     = request.GET.get('status', '')
    q          = request.GET.get('q', '').strip()

    qs = Requisicao.objects.select_related('cliforemp').filter(empresa_id=empresa_id)
    if status:
        qs = qs.filter(status=status)
    if q:
        qs = qs.filter(
            Q(idrequisicao__icontains=q) |
            Q(origem__icontains=q) |
            Q(cliforemp__razao__icontains=q)
        )
    qs = qs.order_by('-data', '-idrequisicao')

    page_obj, page_range, query_string = paginar(request, qs)

    return render(request, 'estoque/req_list.html', {
        'lista':          page_obj.object_list,
        'page_obj':       page_obj,
        'page_range':     page_range,
        'query_string':   query_string,
        'status':         status,
        'q':              q,
        'status_choices': Requisicao.STATUS_CHOICES,
    })


# ── Criação ───────────────────────────────────────────────────────────────────

@modulo_required('acesso_estoque')
def req_create(request):
    empresa_id = request.session.get('empresa_id')

    if request.method == 'POST':
        form = RequisicaoForm(request.POST, empresa_id=empresa_id)
        if form.is_valid():
            itens_raw = json.loads(request.POST.get('itens_json', '[]'))
            if not itens_raw:
                messages.error(request, 'Adicione ao menos um item à requisição.')
            else:
                with transaction.atomic():
                    req = form.save(commit=False)
                    req.empresa_id = empresa_id
                    req.status     = 'A'
                    req.save()

                    for it in itens_raw:
                        qty = Decimal(str(it.get('quantidade', 1)))
                        ItemRequisicao.objects.create(
                            requisicao    = req,
                            identificacao = it.get('identificacao', ''),
                            quantidade    = qty,
                            atendido      = Decimal('0'),
                            saldo         = qty,
                            idorigem      = 0,
                        )

                messages.success(request, f'Requisição #{req.idrequisicao} criada.')
                return redirect('estoque:req_detalhe', pk=req.pk)
    else:
        form = RequisicaoForm(initial={'data': date.today()}, empresa_id=empresa_id)

    return render(request, 'estoque/req_create.html', {'form': form})


# ── Detalhe ───────────────────────────────────────────────────────────────────

@modulo_required('acesso_estoque')
def req_detalhe(request, pk):
    empresa_id = request.session.get('empresa_id')
    req = get_object_or_404(Requisicao, pk=pk, empresa_id=empresa_id)

    itens = list(req.itens.all())

    # Busca saldo atual de estoque para cada identificacao presente na requisição
    idents = {i.identificacao for i in itens if i.identificacao}
    saldo_map = {
        obj.identificacao: obj.saldoestoque
        for obj in Item.objects.filter(empresa_id=empresa_id, identificacao__in=idents)
    }

    # Anexa saldo_estoque e status de atendimento a cada item
    for item in itens:
        est = saldo_map.get(item.identificacao)
        item.saldo_estoque = est  # None = item não encontrado no cadastro
        if item.saldo <= 0:
            item.sit_atend = 'ok'          # já finalizado
        elif est is None or est <= 0:
            item.sit_atend = 'sem_estoque'  # nenhum saldo disponível
        elif est >= item.saldo:
            item.sit_atend = 'total'        # pode atender integralmente
        else:
            item.sit_atend = 'parcial'      # atendimento parcial possível

    movimentos = (MovimentoEstoque.objects
                  .filter(empresa_id=empresa_id, origem='RQ', idorigem=req.pk)
                  .order_by('-data', '-idmovimento'))

    return render(request, 'estoque/req_detalhe.html', {
        'req':        req,
        'itens':      itens,
        'movimentos': movimentos,
        'bloqueada':  req.status in ('F', 'C'),
    })


# ── Atendimento ───────────────────────────────────────────────────────────────

@modulo_required('acesso_estoque')
def req_atender(request, pk):
    empresa_id = request.session.get('empresa_id')
    req = get_object_or_404(Requisicao, pk=pk, empresa_id=empresa_id)

    if req.status in ('F', 'C'):
        messages.error(request, 'Esta requisição não pode ser atendida.')
        return redirect('estoque:req_detalhe', pk=pk)

    if request.method != 'POST':
        return redirect('estoque:req_detalhe', pk=pk)

    with transaction.atomic():
        algum_atendido = False

        for item_req in req.itens.select_for_update().all():
            campo = f'atender_{item_req.pk}'
            val_str = request.POST.get(campo, '').strip()
            if not val_str:
                continue
            try:
                qty_atender = Decimal(val_str)
            except Exception:
                continue

            if qty_atender <= 0:
                continue
            if qty_atender > item_req.saldo:
                qty_atender = item_req.saldo

            # Busca o Item com controle de estoque habilitado
            item_obj = (Item.objects
                        .filter(empresa_id=empresa_id,
                                identificacao=item_req.identificacao,
                                controla_estoque=True)
                        .first())
            if item_obj is None:
                continue  # item não rastreado — não gera movimento

            # Movimento de saída
            MovimentoEstoque.objects.create(
                empresa_id     = empresa_id,
                identificacao  = item_req.identificacao,
                item           = item_obj,
                data           = date.today(),
                ent_sai        = 'S',
                origem         = 'RQ',
                idorigem       = req.pk,
                quantidade     = qty_atender,
                usuariologado  = request.user.username,
            )

            # Atualiza saldo do Item
            if item_obj:
                Item.objects.filter(pk=item_obj.pk).update(
                    saldoestoque=item_obj.saldoestoque - qty_atender
                )

            # Atualiza item da requisição
            novo_atendido = item_req.atendido + qty_atender
            novo_saldo    = item_req.quantidade - novo_atendido
            ItemRequisicao.objects.filter(pk=item_req.pk).update(
                atendido=novo_atendido,
                saldo=novo_saldo,
            )
            algum_atendido = True

        if not algum_atendido:
            messages.warning(request, 'Nenhuma quantidade informada para atendimento.')
            return redirect('estoque:req_detalhe', pk=pk)

        # Reavalia status
        req.refresh_from_db()
        itens_atualizados = list(req.itens.all())
        todos_zero  = all(i.saldo <= 0 for i in itens_atualizados)
        algum_saldo = any(i.atendido > 0 for i in itens_atualizados)

        if todos_zero:
            req.status    = 'F'
            req.dataatendi = date.today()
        elif algum_saldo:
            req.status = 'P'
        req.save(update_fields=['status', 'dataatendi'])

    messages.success(request, 'Atendimento registrado.')
    return redirect('estoque:req_detalhe', pk=pk)


# ── Cancelamento ──────────────────────────────────────────────────────────────

@modulo_required('acesso_estoque')
def req_cancelar(request, pk):
    empresa_id = request.session.get('empresa_id')
    req = get_object_or_404(Requisicao, pk=pk, empresa_id=empresa_id)

    if req.status in ('F', 'C'):
        messages.error(request, 'Esta requisição não pode ser cancelada.')
        return redirect('estoque:req_detalhe', pk=pk)

    if request.method == 'POST':
        # Só cancela se não houver movimentos gerados
        tem_mov = MovimentoEstoque.objects.filter(
            empresa_id=empresa_id, origem='RQ', idorigem=req.pk
        ).exists()
        if tem_mov:
            messages.error(request, 'Requisição com movimentos registrados não pode ser cancelada diretamente.')
            return redirect('estoque:req_detalhe', pk=pk)

        req.status = 'C'
        req.save(update_fields=['status'])
        messages.success(request, f'Requisição #{req.pk} cancelada.')
        return redirect('estoque:req_list')

    return redirect('estoque:req_detalhe', pk=pk)


# ═══════════════════════════════════════════════════════════════════════════════
# Inventário
# ═══════════════════════════════════════════════════════════════════════════════

@modulo_required('acesso_estoque')
def inv_list(request):
    empresa_id = request.session.get('empresa_id')
    status     = request.GET.get('status', '')
    q          = request.GET.get('q', '').strip()

    qs = Inventario.objects.filter(empresa_id=empresa_id)
    if status:
        qs = qs.filter(status=status)
    if q:
        qs = qs.filter(Q(descricao__icontains=q) | Q(idinventario__icontains=q))
    qs = qs.order_by('-data', '-idinventario')[:200]

    return render(request, 'estoque/inv_list.html', {
        'lista':          qs,
        'status':         status,
        'q':              q,
        'status_choices': Inventario.STATUS_CHOICES,
    })


@modulo_required('acesso_estoque')
def inv_create(request):
    empresa_id = request.session.get('empresa_id')

    if request.method == 'POST':
        descricao  = request.POST.get('descricao', '').strip()
        observacao = request.POST.get('observacao', '').strip()

        itens_qs = Item.objects.filter(
            empresa_id=empresa_id, inativo=False, controla_estoque=True
        )

        with transaction.atomic():
            inv = Inventario.objects.create(
                empresa_id  = empresa_id,
                data        = date.today(),
                descricao   = descricao,
                observacao  = observacao,
                status      = 'A',
                usuario     = request.user.username,
            )
            for item in itens_qs.order_by('identificacao', 'descricao'):
                ItemInventario.objects.create(
                    inventario    = inv,
                    item          = item,
                    identificacao = item.identificacao,
                    descricao_item= item.descricao,
                    saldo_sistema = item.saldoestoque,
                    saldo_fisico  = None,
                    diferenca     = Decimal('0'),
                    ajustado      = False,
                )

        messages.success(request, f'Inventário #{inv.pk} aberto com {itens_qs.count()} itens.')
        return redirect('estoque:inv_detalhe', pk=inv.pk)

    return render(request, 'estoque/inv_create.html')


@modulo_required('acesso_estoque')
def inv_detalhe(request, pk):
    empresa_id = request.session.get('empresa_id')
    inv = get_object_or_404(Inventario, pk=pk, empresa_id=empresa_id)
    itens = list(inv.itens.all())

    # Estatísticas para o painel de resumo
    contados    = sum(1 for i in itens if i.saldo_fisico is not None)
    pendentes   = len(itens) - contados
    com_dif     = sum(1 for i in itens if i.saldo_fisico is not None and i.diferenca != 0)
    entradas    = sum(i.diferenca for i in itens if i.diferenca > 0)
    saidas      = sum(abs(i.diferenca) for i in itens if i.diferenca < 0)

    return render(request, 'estoque/inv_detalhe.html', {
        'inv':       inv,
        'itens':     itens,
        'bloqueado': inv.status != 'A',
        'contados':  contados,
        'pendentes': pendentes,
        'com_dif':   com_dif,
        'entradas':  entradas,
        'saidas':    saidas,
        'total':     len(itens),
    })


@modulo_required('acesso_estoque')
def inv_salvar_contagem(request, pk):
    """Salva saldo_fisico digitado para cada item — pode ser chamado várias vezes."""
    empresa_id = request.session.get('empresa_id')
    inv = get_object_or_404(Inventario, pk=pk, empresa_id=empresa_id)

    if inv.status != 'A':
        messages.error(request, 'Este inventário não pode ser editado.')
        return redirect('estoque:inv_detalhe', pk=pk)

    if request.method != 'POST':
        return redirect('estoque:inv_detalhe', pk=pk)

    atualizados = 0
    with transaction.atomic():
        for item in inv.itens.select_for_update().all():
            campo = f'fisico_{item.pk}'
            val_str = request.POST.get(campo, '').strip()
            if val_str == '':
                continue
            try:
                fisico = Decimal(val_str)
            except Exception:
                continue
            if fisico < 0:
                continue
            diferenca = fisico - item.saldo_sistema
            ItemInventario.objects.filter(pk=item.pk).update(
                saldo_fisico=fisico,
                diferenca=diferenca,
            )
            atualizados += 1

    messages.success(request, f'Contagem salva — {atualizados} item(ns) atualizados.')
    return redirect('estoque:inv_detalhe', pk=pk)


@modulo_required('acesso_estoque')
def inv_finalizar(request, pk):
    empresa_id = request.session.get('empresa_id')
    inv = get_object_or_404(Inventario, pk=pk, empresa_id=empresa_id)

    if inv.status != 'A':
        messages.error(request, 'Este inventário já foi finalizado ou cancelado.')
        return redirect('estoque:inv_detalhe', pk=pk)

    if request.method != 'POST':
        return redirect('estoque:inv_detalhe', pk=pk)

    itens = list(inv.itens.all())
    nao_contados = [i for i in itens if i.saldo_fisico is None]
    if nao_contados:
        messages.error(
            request,
            f'Existem {len(nao_contados)} item(ns) sem contagem física. '
            'Registre todos os saldos antes de finalizar.'
        )
        return redirect('estoque:inv_detalhe', pk=pk)

    ajustados = 0
    with transaction.atomic():
        for item_inv in itens:
            if item_inv.diferenca == 0:
                continue

            ent_sai = 'E' if item_inv.diferenca > 0 else 'S'
            qty     = abs(item_inv.diferenca)

            MovimentoEstoque.objects.create(
                empresa_id    = empresa_id,
                identificacao = item_inv.identificacao,
                item          = item_inv.item,
                data          = date.today(),
                ent_sai       = ent_sai,
                origem        = 'AJ',
                idorigem      = inv.pk,
                quantidade    = qty,
                usuariologado = request.user.username,
            )

            # Atualiza saldo do item
            if item_inv.item_id:
                Item.objects.filter(pk=item_inv.item_id).update(
                    saldoestoque=item_inv.saldo_fisico
                )

            ItemInventario.objects.filter(pk=item_inv.pk).update(ajustado=True)
            ajustados += 1

        inv.status          = 'F'
        inv.datafinalizacao = date.today()
        inv.save(update_fields=['status', 'datafinalizacao'])

    messages.success(
        request,
        f'Inventário finalizado. {ajustados} ajuste(s) de estoque registrado(s).'
    )
    return redirect('estoque:inv_detalhe', pk=pk)


@modulo_required('acesso_estoque')
def inv_cancelar(request, pk):
    empresa_id = request.session.get('empresa_id')
    inv = get_object_or_404(Inventario, pk=pk, empresa_id=empresa_id)

    if inv.status != 'A':
        messages.error(request, 'Apenas inventários abertos podem ser cancelados.')
        return redirect('estoque:inv_detalhe', pk=pk)

    if request.method == 'POST':
        inv.status = 'X'
        inv.save(update_fields=['status'])
        messages.success(request, f'Inventário #{inv.pk} cancelado.')
        return redirect('estoque:inv_list')

    return redirect('estoque:inv_detalhe', pk=pk)


# ═══════════════════════════════════════════════════════════════════════════════
# Saldo por Item
# ═══════════════════════════════════════════════════════════════════════════════

def _saldo_qs(empresa_id, q='', grupo_pk='', inativo=''):
    """Queryset base compartilhado entre consulta e impressão."""
    qs = (Item.objects
          .select_related('grupo')
          .filter(empresa_id=empresa_id, controla_estoque=True))
    if not inativo:
        qs = qs.filter(inativo=False)
    if q:
        qs = qs.filter(
            Q(descricao__icontains=q) |
            Q(identificacao__icontains=q) |
            Q(modelo__icontains=q) |
            Q(codforn__icontains=q)
        )
    if grupo_pk:
        qs = qs.filter(grupo__pk=grupo_pk)
    return qs.order_by('identificacao', 'descricao')


@modulo_required('acesso_estoque')
def saldo_list(request):
    empresa_id = request.session.get('empresa_id')
    grupos = Grupo.objects.filter(empresa_id=empresa_id, inativo=False).order_by('descricao')
    itens  = _saldo_qs(empresa_id)
    return render(request, 'estoque/saldo_list.html', {
        'grupos': grupos,
        'itens':  itens,
    })


@modulo_required('acesso_estoque')
def saldo_buscar(request):
    empresa_id = request.session.get('empresa_id')
    q         = request.GET.get('q', '').strip()
    grupo_pk  = request.GET.get('grupo', '').strip()
    inativo   = request.GET.get('inativo', '').strip()
    itens = _saldo_qs(empresa_id, q, grupo_pk, inativo)
    return render(request, 'estoque/partials/tabela_saldo.html', {'itens': itens})


@modulo_required('acesso_estoque')
def saldo_imprimir(request):
    empresa_id = request.session.get('empresa_id')
    empresa    = get_object_or_404(Empresa, pk=empresa_id)
    q          = request.GET.get('q', '').strip()
    grupo_pk   = request.GET.get('grupo', '').strip()
    inativo    = request.GET.get('inativo', '').strip()

    itens = _saldo_qs(empresa_id, q, grupo_pk, inativo)
    total_itens = itens.count()

    subtitulo_parts = []
    if q:
        subtitulo_parts.append(f'Busca: "{q}"')
    if grupo_pk:
        try:
            g = Grupo.objects.get(pk=grupo_pk)
            subtitulo_parts.append(f'Grupo: {g.descricao}')
        except Grupo.DoesNotExist:
            pass
    if inativo:
        subtitulo_parts.append('Incluindo inativos')

    return render_pdf(
        'relatorios/saldo_estoque.html',
        {
            'empresa':     empresa,
            'itens':       itens,
            'total_itens': total_itens,
            'subtitulo':   ' | '.join(subtitulo_parts) if subtitulo_parts else 'Ativos',
            'now':         timezone.localtime(),
            'usuario':     request.user.username,
        },
        filename='saldo_estoque.pdf',
        request=request,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Extrato de Movimentação por Item
# ═══════════════════════════════════════════════════════════════════════════════

def _extrato_context(empresa_id, item, data_base):
    """Calcula saldo inicial e linhas do extrato. Reutilizado na impressão."""
    qs_ant = MovimentoEstoque.objects.filter(
        empresa_id=empresa_id, item=item, data__lt=data_base
    )
    entradas_ant = qs_ant.filter(ent_sai='E').aggregate(t=Sum('quantidade'))['t'] or Decimal('0')
    saidas_ant   = qs_ant.filter(ent_sai='S').aggregate(t=Sum('quantidade'))['t'] or Decimal('0')
    saldo_inicial = entradas_ant - saidas_ant

    movimentos = (MovimentoEstoque.objects
                  .filter(empresa_id=empresa_id, item=item, data__gte=data_base)
                  .order_by('data', 'idmovimento'))

    saldo = saldo_inicial
    linhas = []
    for mov in movimentos:
        if mov.ent_sai == 'E':
            entrada = mov.quantidade
            saida   = Decimal('0')
            saldo  += mov.quantidade
        else:
            entrada = Decimal('0')
            saida   = mov.quantidade
            saldo  -= mov.quantidade
        linhas.append({
            'data':      mov.data,
            'descricao': ORIGEM_LABELS.get(mov.origem, mov.origem),
            'origem':    mov.origem,
            'idorigem':  mov.idorigem,
            'entrada':   entrada,
            'saida':     saida,
            'saldo':     saldo,
        })

    return {
        'saldo_inicial': saldo_inicial,
        'linhas':        linhas,
        'saldo_final':   saldo,
    }


def _parse_data_base(data_base_str):
    if data_base_str:
        try:
            return datetime.strptime(data_base_str, '%Y-%m-%d').date()
        except ValueError:
            pass
    return date.today().replace(day=1)


@modulo_required('acesso_estoque')
def item_extrato(request, item_pk):
    empresa_id = request.session.get('empresa_id')
    item = get_object_or_404(Item, pk=item_pk, empresa_id=empresa_id, controla_estoque=True)

    data_base = _parse_data_base(request.GET.get('data_base', ''))
    ctx = _extrato_context(empresa_id, item, data_base)

    return render(request, 'estoque/item_extrato.html', {
        'item':           item,
        'data_base':      data_base,
        'data_base_str':  data_base.strftime('%Y-%m-%d'),
        **ctx,
    })


@modulo_required('acesso_estoque')
def item_extrato_imprimir(request, item_pk):
    empresa_id = request.session.get('empresa_id')
    empresa    = get_object_or_404(Empresa, pk=empresa_id)
    item = get_object_or_404(Item, pk=item_pk, empresa_id=empresa_id, controla_estoque=True)

    data_base = _parse_data_base(request.GET.get('data_base', ''))
    ctx = _extrato_context(empresa_id, item, data_base)

    return render_pdf(
        'relatorios/extrato_item.html',
        {
            'empresa':    empresa,
            'item':       item,
            'data_base':  data_base,
            'now':        timezone.localtime(),
            'usuario':    request.user.username,
            **ctx,
        },
        filename=f'extrato_item_{item.identificacao or item.pk}.pdf',
        request=request,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Ajuste Avulso de Estoque
# ═══════════════════════════════════════════════════════════════════════════════

@modulo_required('acesso_estoque')
def ajuste_list(request):
    empresa_id = request.session.get('empresa_id')
    qs = (MovimentoEstoque.objects
          .select_related('item')
          .filter(empresa_id=empresa_id, origem='AJ')
          .order_by('-data', '-idmovimento')[:200])
    return render(request, 'estoque/ajuste_list.html', {'lista': qs})


@modulo_required('acesso_estoque')
def ajuste_create(request):
    empresa_id = request.session.get('empresa_id')

    if request.method == 'POST':
        item_pk    = request.POST.get('item_id', '').strip()
        ent_sai    = request.POST.get('ent_sai', '').strip()
        qtd_str    = request.POST.get('quantidade', '').strip()
        motivo     = request.POST.get('observacao', '').strip()
        data_str   = request.POST.get('data', '').strip()

        erros = []
        if not item_pk:
            erros.append('Selecione um item.')
        if ent_sai not in ('E', 'S'):
            erros.append('Informe o tipo: Entrada ou Saída.')
        try:
            quantidade = Decimal(qtd_str)
            if quantidade <= 0:
                raise ValueError
        except Exception:
            erros.append('Quantidade inválida.')
        if not motivo:
            erros.append('O motivo do ajuste é obrigatório.')
        try:
            data_aj = datetime.strptime(data_str, '%Y-%m-%d').date() if data_str else date.today()
        except ValueError:
            data_aj = date.today()

        item_obj = None
        if item_pk:
            item_obj = Item.objects.filter(
                pk=item_pk, empresa_id=empresa_id, controla_estoque=True
            ).first()
            if not item_obj:
                erros.append('Item não encontrado ou não controla estoque.')

        if erros:
            for e in erros:
                messages.error(request, e)
        else:
            with transaction.atomic():
                MovimentoEstoque.objects.create(
                    empresa_id    = empresa_id,
                    identificacao = item_obj.identificacao,
                    item          = item_obj,
                    data          = data_aj,
                    ent_sai       = ent_sai,
                    origem        = 'AJ',
                    idorigem      = 0,
                    quantidade    = quantidade,
                    usuariologado = request.user.username,
                    observacao    = motivo,
                )
                if ent_sai == 'E':
                    Item.objects.filter(pk=item_obj.pk).update(
                        saldoestoque=item_obj.saldoestoque + quantidade
                    )
                else:
                    Item.objects.filter(pk=item_obj.pk).update(
                        saldoestoque=item_obj.saldoestoque - quantidade
                    )

            tipo_label = 'Entrada' if ent_sai == 'E' else 'Saída'
            messages.success(
                request,
                f'Ajuste de {tipo_label} registrado — {item_obj.descricao} | '
                f'Qtd: {quantidade:,.3f} | Motivo: {motivo}'
            )
            return redirect('estoque:ajuste_list')

    return render(request, 'estoque/ajuste_create.html', {
        'data_hoje': date.today().strftime('%Y-%m-%d'),
    })


# ═══════════════════════════════════════════════════════════════════════════════
# NF de Entrada
# ═══════════════════════════════════════════════════════════════════════════════

@modulo_required('acesso_estoque')
def nf_list(request):
    empresa_id = request.session.get('empresa_id')
    status = request.GET.get('status', '')
    q      = request.GET.get('q', '').strip()

    qs = (NotaFiscalEntrada.objects
          .select_related('fornecedor')
          .filter(empresa_id=empresa_id))
    if status:
        qs = qs.filter(status=status)
    if q:
        qs = qs.filter(
            Q(numeronf__icontains=q) |
            Q(fornecedor__razao__icontains=q) |
            Q(fornecedor__nome__icontains=q)
        )
    qs = qs.order_by('-dataentrada', '-idnfentrada')

    page_obj, page_range, query_string = paginar(request, qs)

    return render(request, 'estoque/nf_list.html', {
        'lista':          page_obj.object_list,
        'page_obj':       page_obj,
        'page_range':     page_range,
        'query_string':   query_string,
        'status':         status,
        'q':              q,
        'status_choices': NotaFiscalEntrada.STATUS_CHOICES,
    })


@modulo_required('acesso_estoque')
def nf_create(request):
    empresa_id = request.session.get('empresa_id')

    if request.method == 'POST':
        form = NFEntradaForm(request.POST, empresa_id=empresa_id)
        if form.is_valid():
            itens_raw   = json.loads(request.POST.get('itens_json', '[]'))
            parcelas_raw = json.loads(request.POST.get('parcelas_json', '[]'))

            if not itens_raw:
                messages.error(request, 'Adicione ao menos um item à NF.')
            else:
                with transaction.atomic():
                    nf = form.save(commit=False)
                    nf.empresa_id  = empresa_id
                    nf.status      = 'A'
                    nf.usuariolanc = request.user.username
                    nf.save()

                    qtd_total = Decimal('0')
                    val_total = Decimal('0')

                    for it in itens_raw:
                        qty   = Decimal(str(it.get('quantidade', 1)))
                        vunit = Decimal(str(it.get('valorunitario', 0)))
                        vtot  = Decimal(str(it.get('valortotal', 0)))
                        item_obj = None
                        if it.get('item_id'):
                            item_obj = Item.objects.filter(
                                pk=it['item_id'], empresa_id=empresa_id
                            ).first()
                        ItemNFEntrada.objects.create(
                            nfentrada     = nf,
                            item          = item_obj,
                            identificacao = it.get('identificacao', ''),
                            descricao_item= it.get('descricao', ''),
                            quantidade    = qty,
                            valorunitario = vunit,
                            valortotal    = vtot,
                        )
                        qtd_total += qty
                        val_total += vtot

                    for p in parcelas_raw:
                        ParcelaNFEntrada.objects.create(
                            nfentrada  = nf,
                            parcela    = int(p['parcela']),
                            vencimento = p['vencimento'],
                            valor      = Decimal(str(p['valor'])),
                        )

                    nf.quantidade      = qtd_total
                    nf.valortotalitens = val_total
                    nf.valortotalnf    = val_total
                    nf.save(update_fields=['quantidade', 'valortotalitens', 'valortotalnf'])

                messages.success(request, f'NF {nf.numeronf} registrada.')
                return redirect('estoque:nf_detalhe', pk=nf.pk)
    else:
        form = NFEntradaForm(
            initial={'dataentrada': date.today(), 'dataemissao': date.today()},
            empresa_id=empresa_id,
        )

    condicoes = CondicaoPagamento.objects.filter(empresa_id=empresa_id, inativo=False)
    condicoes_json = json.dumps({
        str(c.idcondpag): {'parcelas': c.parcelas, 'dias': c.dias}
        for c in condicoes
    })

    return render(request, 'estoque/nf_create.html', {
        'form':           form,
        'condicoes_json': condicoes_json,
    })


@modulo_required('acesso_estoque')
def nf_editar(request, pk):
    empresa_id = request.session.get('empresa_id')
    nf = get_object_or_404(NotaFiscalEntrada, pk=pk, empresa_id=empresa_id)

    if nf.status != 'A':
        messages.error(request, 'Esta NF não pode ser editada.')
        return redirect('estoque:nf_detalhe', pk=pk)

    if request.method == 'POST':
        form = NFEntradaForm(request.POST, instance=nf, empresa_id=empresa_id)
        if form.is_valid():
            itens_raw    = json.loads(request.POST.get('itens_json', '[]'))
            parcelas_raw = json.loads(request.POST.get('parcelas_json', '[]'))

            if not itens_raw:
                messages.error(request, 'Adicione ao menos um item à NF.')
            else:
                with transaction.atomic():
                    nf = form.save(commit=False)
                    nf.save()

                    nf.itens.all().delete()
                    nf.parcelas.all().delete()

                    qtd_total = Decimal('0')
                    val_total = Decimal('0')

                    for it in itens_raw:
                        qty   = Decimal(str(it.get('quantidade', 1)))
                        vunit = Decimal(str(it.get('valorunitario', 0)))
                        vtot  = Decimal(str(it.get('valortotal', 0)))
                        item_obj = None
                        if it.get('item_id'):
                            item_obj = Item.objects.filter(
                                pk=it['item_id'], empresa_id=empresa_id
                            ).first()
                        ItemNFEntrada.objects.create(
                            nfentrada     = nf,
                            item          = item_obj,
                            identificacao = it.get('identificacao', ''),
                            descricao_item= it.get('descricao', ''),
                            quantidade    = qty,
                            valorunitario = vunit,
                            valortotal    = vtot,
                        )
                        qtd_total += qty
                        val_total += vtot

                    for p in parcelas_raw:
                        ParcelaNFEntrada.objects.create(
                            nfentrada  = nf,
                            parcela    = int(p['parcela']),
                            vencimento = p['vencimento'],
                            valor      = Decimal(str(p['valor'])),
                        )

                    nf.quantidade      = qtd_total
                    nf.valortotalitens = val_total
                    nf.valortotalnf    = val_total
                    nf.save(update_fields=['quantidade', 'valortotalitens', 'valortotalnf'])

                messages.success(request, f'NF {nf.numeronf} atualizada.')
                return redirect('estoque:nf_detalhe', pk=nf.pk)
    else:
        form = NFEntradaForm(instance=nf, empresa_id=empresa_id)

    itens_init = json.dumps([
        {
            'item_id':       it.item_id,
            'descricao':     it.descricao_item or it.identificacao,
            'identificacao': it.identificacao,
            'quantidade':    float(it.quantidade),
            'valorunitario': float(it.valorunitario),
            'valortotal':    float(it.valortotal),
        }
        for it in nf.itens.all()
    ])

    parcelas_init = json.dumps([
        {
            'parcela':    p.parcela,
            'vencimento': p.vencimento.strftime('%Y-%m-%d'),
            'valor':      float(p.valor),
        }
        for p in nf.parcelas.all()
    ])

    condicoes = CondicaoPagamento.objects.filter(empresa_id=empresa_id, inativo=False)
    condicoes_json = json.dumps({
        str(c.idcondpag): {'parcelas': c.parcelas, 'dias': c.dias}
        for c in condicoes
    })

    return render(request, 'estoque/nf_editar.html', {
        'form':           form,
        'nf':             nf,
        'condicoes_json': condicoes_json,
        'itens_init':     itens_init,
        'parcelas_init':  parcelas_init,
    })


@modulo_required('acesso_estoque')
def nf_detalhe(request, pk):
    empresa_id = request.session.get('empresa_id')
    nf = get_object_or_404(
        NotaFiscalEntrada.objects.select_related('fornecedor', 'condicao', 'metodo'),
        pk=pk, empresa_id=empresa_id,
    )
    itens    = list(nf.itens.select_related('item').all())
    parcelas = list(nf.parcelas.all())

    return render(request, 'estoque/nf_detalhe.html', {
        'nf':       nf,
        'itens':    itens,
        'parcelas': parcelas,
        'bloqueada': nf.status != 'A',
    })


@modulo_required('acesso_estoque')
def nf_lancar(request, pk):
    """Lança a NF: gera MovimentoEstoque + ContaPagar por parcela."""
    empresa_id = request.session.get('empresa_id')
    nf = get_object_or_404(NotaFiscalEntrada, pk=pk, empresa_id=empresa_id)

    if nf.status != 'A':
        messages.error(request, 'Esta NF já foi lançada ou cancelada.')
        return redirect('estoque:nf_detalhe', pk=pk)

    if request.method != 'POST':
        return redirect('estoque:nf_detalhe', pk=pk)

    with transaction.atomic():
        data_ref = nf.dataentrada or date.today()

        # Movimentos de entrada de estoque
        for item_nf in nf.itens.select_related('item').all():
            item_obj = item_nf.item
            if item_obj and item_obj.controla_estoque:
                MovimentoEstoque.objects.create(
                    empresa_id    = empresa_id,
                    identificacao = item_nf.identificacao,
                    item          = item_obj,
                    data          = data_ref,
                    ent_sai       = 'E',
                    origem        = 'NF',
                    idorigem      = nf.pk,
                    quantidade    = item_nf.quantidade,
                    usuariologado = request.user.username,
                )
                Item.objects.filter(pk=item_obj.pk).update(
                    saldoestoque=item_obj.saldoestoque + item_nf.quantidade
                )

        # Parcelas → ContaPagar
        for parcela in nf.parcelas.all():
            cp = ContaPagar.objects.create(
                empresa_id  = empresa_id,
                data        = data_ref,
                fornecedor  = nf.fornecedor,
                parcela     = parcela.parcela,
                valor       = parcela.valor,
                vencimento  = parcela.vencimento,
                numerodoc   = str(nf.numeronf),
                status      = 'A',
                juros       = Decimal('0'),
                descontos   = Decimal('0'),
                valorpago   = Decimal('0'),
            )
            ParcelaNFEntrada.objects.filter(pk=parcela.pk).update(idcontapag=cp.pk)

        nf.status = 'L'
        nf.save(update_fields=['status'])

    messages.success(request, f'NF {nf.numeronf} lançada — movimentos e contas a pagar gerados.')
    return redirect('estoque:nf_detalhe', pk=pk)


@modulo_required('acesso_estoque')
def nf_cancelar(request, pk):
    empresa_id = request.session.get('empresa_id')
    nf = get_object_or_404(NotaFiscalEntrada, pk=pk, empresa_id=empresa_id)

    if nf.status != 'A':
        messages.error(request, 'Apenas NFs abertas podem ser canceladas.')
        return redirect('estoque:nf_detalhe', pk=pk)

    if request.method == 'POST':
        nf.status = 'C'
        nf.save(update_fields=['status'])
        messages.success(request, f'NF {nf.numeronf} cancelada.')
        return redirect('estoque:nf_list')

    return redirect('estoque:nf_detalhe', pk=pk)


# ═══════════════════════════════════════════════════════════════════════════════
# Espelhos PDF
# ═══════════════════════════════════════════════════════════════════════════════

@modulo_required('acesso_estoque')
def nf_espelho(request, pk):
    empresa_id = request.session.get('empresa_id')
    nf       = get_object_or_404(NotaFiscalEntrada, pk=pk, empresa_id=empresa_id)
    empresa  = nf.empresa
    itens    = nf.itens.select_related('item').all()
    parcelas = nf.parcelas.all()

    return render_pdf(
        'espelhos/nf.html',
        {
            'empresa':  empresa,
            'nf':       nf,
            'itens':    itens,
            'parcelas': parcelas,
            'now':      timezone.localtime(),
            'usuario':  request.user.get_full_name() or request.user.username,
        },
        filename=f'NF_{nf.numeronf}.pdf',
        request=request,
    )


@modulo_required('acesso_estoque')
def req_espelho(request, pk):
    empresa_id = request.session.get('empresa_id')
    req     = get_object_or_404(Requisicao, pk=pk, empresa_id=empresa_id)
    empresa = req.empresa
    itens   = req.itens.all()

    return render_pdf(
        'espelhos/req.html',
        {
            'empresa': empresa,
            'req':     req,
            'itens':   itens,
            'now':     timezone.localtime(),
            'usuario': request.user.get_full_name() or request.user.username,
        },
        filename=f'Req_{req.idrequisicao}.pdf',
        request=request,
    )


@modulo_required('acesso_estoque')
def ajuste_espelho(request, pk):
    empresa_id = request.session.get('empresa_id')
    mov     = get_object_or_404(MovimentoEstoque, pk=pk, empresa_id=empresa_id, origem='AJ')
    empresa = mov.empresa

    return render_pdf(
        'espelhos/ajuste.html',
        {
            'empresa': empresa,
            'mov':     mov,
            'now':     timezone.localtime(),
            'usuario': request.user.get_full_name() or request.user.username,
        },
        filename=f'Ajuste_{mov.idmovimento}.pdf',
        request=request,
    )

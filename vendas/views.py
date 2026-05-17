import json
from decimal import Decimal
from datetime import date, datetime
from core.pagination import paginar
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db import transaction
from django.db import models as db_models
from django.db.models import Q, Sum
from core.decorators import modulo_required
from core.models import Empresa
from cadastros.models import Item, CondicaoPagamento, ClienteFornecedor, ItemTabelaPreco
from financeiro.models import ContaReceber, ContaPagar
from financeiro.relatorios import render_pdf
from .models import Pedido, ItemPedido, ParcelaPedido, ConfiguracaoComissao, AcertoComissao, MovimentoComissao
from .forms import PedidoForm

# Mapa de parcelas → campo do ItemTabelaPreco
_PARCELAS_CAMPO = {
    1: 'i_pagto', 2: 'ii_pagto', 3: 'iii_pagto', 4: 'iv_pagto',
    5: 'v_pagto', 6: 'vi_pagto', 7: 'vii_pagto', 8: 'viii_pagto',
    9: 'ix_pagto', 10: 'x_pagto', 11: 'xi_pagto', 12: 'xii_pagto',
}


def _calcular_movimentos(acerto, empresa_id):
    """Calcula movimentos de comissão para um acerto. Retorna lista de dicts."""
    config = ConfiguracaoComissao.objects.first()
    if not config:
        return []

    vendedor = ClienteFornecedor.objects.filter(pk=acerto.idvendrepre).first()
    tipo_mei  = bool(vendedor and ('MEI' in (vendedor.tipovendedor or '').upper()
                                   or vendedor.tipovendedor == '2'))

    pedidos = (Pedido.objects
               .filter(empresa_id=empresa_id,
                       idvendrepre=acerto.idvendrepre,
                       datainstal__gte=acerto.perildoini,
                       datainstal__lte=acerto.periodofim,
                       status='I')
               .exclude(comissaook='S')
               .select_related('condicao', 'tabela', 'cliente'))

    movimentos = []
    for pedido in pedidos:
        cond_desc = (pedido.condicao.condicao if pedido.condicao else '').upper()
        if 'GARANTIA' in cond_desc:
            continue
        num_parcelas = pedido.condicao.parcelas if pedido.condicao else 1

        for it in pedido.itens.select_related('item').all():
            item_obj = it.item
            if item_obj and 'GARANTIA' in (item_obj.descricao or '').upper():
                continue

            # Preço e base da tabela de preços
            c_preco     = Decimal('0')
            base_tabela = Decimal('0')
            if pedido.tabela_id:
                campo = _PARCELAS_CAMPO.get(num_parcelas, 'preco')
                itetabe = ItemTabelaPreco.objects.filter(
                    tabela=pedido.tabela, identificacao=it.identificacao
                ).first()
                if itetabe:
                    c_preco     = getattr(itetabe, campo, itetabe.preco) or Decimal('0')
                    base_tabela = itetabe.basecomissao or Decimal('0')

            if not base_tabela and item_obj:
                base_tabela = item_obj.basecomissao or Decimal('0')

            # Percentual e base conforme tipo (à vista / prazo)
            if num_parcelas == 1:
                perc = config.meiav    if tipo_mei else config.telav
                base = base_tabela if (c_preco and it.valorunitario >= c_preco) else (base_tabela / 2 if base_tabela else it.valorunitario)
            else:
                perc = config.meiprazo if tipo_mei else config.telprazo
                base = base_tabela if (c_preco and it.valorunitario >= c_preco) else (base_tabela / 2 if base_tabela else it.valorunitario)

            base_total  = (base * it.quantidade).quantize(Decimal('0.01'))
            valor_comiss = (base_total * perc / 100).quantize(Decimal('0.01'))
            val_total   = ((it.valortotal or Decimal('0')) - (it.instalacao or Decimal('0'))).quantize(Decimal('0.01'))

            movimentos.append({
                'pedido':       pedido,
                'cliente_id':   pedido.cliente_id,
                'identificacao': it.identificacao,
                'quantidade':   it.quantidade,
                'valorunitario': it.valorunitario,
                'valortotal':   val_total,
                'basecomissao': base_total,
                'perccomiss':   perc,
                'valorcomiss':  valor_comiss,
                'valortabela':  c_preco,
            })
    return movimentos


@modulo_required('acesso_televendas')
def pedido_list(request):
    empresa_id = request.session.get('empresa_id')
    status = request.GET.get('status', '')
    q      = request.GET.get('q', '').strip()

    qs = Pedido.objects.select_related('cliente').filter(empresa_id=empresa_id)
    if status:
        qs = qs.filter(status=status)
    if q:
        qs = qs.filter(
            Q(numero__icontains=q) |
            Q(numgrafico__icontains=q) |
            Q(cliente__razao__icontains=q) |
            Q(cliente__nome__icontains=q)
        )
    qs = qs.order_by('-datavenda', '-idpedido')

    page_obj, page_range, query_string = paginar(request, qs)

    return render(request, 'vendas/pedido_list.html', {
        'lista':          page_obj.object_list,
        'page_obj':       page_obj,
        'page_range':     page_range,
        'query_string':   query_string,
        'status':         status,
        'q':              q,
        'status_choices': Pedido.STATUS_CHOICES,
    })


@modulo_required('acesso_televendas')
def pedido_create(request):
    empresa_id = request.session.get('empresa_id')

    if request.method == 'POST':
        form = PedidoForm(request.POST, empresa_id=empresa_id)
        if form.is_valid():
            itens_raw    = json.loads(request.POST.get('itens_json', '[]'))
            parcelas_raw = json.loads(request.POST.get('parcelas_json', '[]'))

            if not itens_raw:
                messages.error(request, 'Adicione ao menos um item ao pedido.')
            else:
                with transaction.atomic():
                    pedido = form.save(commit=False)
                    pedido.empresa_id = empresa_id
                    pedido.status     = 'A'
                    pedido.datagrav   = date.today()
                    vend_pk = request.POST.get('vendedor', '').strip()
                    pedido.idvendrepre = int(vend_pk) if vend_pk else 0
                    pedido.save()

                    val_total = Decimal('0')
                    for it in itens_raw:
                        qty   = Decimal(str(it.get('quantidade', 1)))
                        vunit = Decimal(str(it.get('valorunitario', 0)))
                        vins  = Decimal(str(it.get('instalacao', 0)))
                        vtot  = Decimal(str(it.get('valortotal', 0)))
                        item_obj = None
                        if it.get('item_id'):
                            item_obj = Item.objects.filter(
                                pk=it['item_id'], empresa_id=empresa_id
                            ).first()
                        ItemPedido.objects.create(
                            pedido        = pedido,
                            item          = item_obj,
                            identificacao = it.get('identificacao', ''),
                            quantidade    = qty,
                            valorunitario = vunit,
                            instalacao    = vins,
                            valortotal    = vtot,
                        )
                        val_total += vtot

                    for p in parcelas_raw:
                        ParcelaPedido.objects.create(
                            pedido     = pedido,
                            parcela    = int(p['parcela']),
                            vencimento = p['vencimento'],
                            valor      = Decimal(str(p['valor'])),
                        )

                    pedido.valortotal = val_total
                    pedido.save(update_fields=['valortotal'])

                messages.success(request, f'Pedido #{pedido.pk} criado.')
                return redirect('vendas:pedido_detalhe', pk=pedido.pk)
    else:
        form = PedidoForm(initial={'datavenda': date.today()}, empresa_id=empresa_id)

    condicoes = CondicaoPagamento.objects.filter(empresa_id=empresa_id, inativo=False)
    condicoes_json = json.dumps({
        str(c.idcondpag): {'parcelas': c.parcelas, 'dias': c.dias}
        for c in condicoes
    })

    return render(request, 'vendas/pedido_create.html', {
        'form':           form,
        'condicoes_json': condicoes_json,
    })


@modulo_required('acesso_televendas')
def pedido_detalhe(request, pk):
    empresa_id = request.session.get('empresa_id')
    pedido = get_object_or_404(
        Pedido.objects.select_related('cliente', 'condicao', 'tabela', 'metodo'),
        pk=pk, empresa_id=empresa_id,
    )
    itens    = list(pedido.itens.select_related('item').all())
    parcelas = list(pedido.parcelas.all())
    vendedor = (
        ClienteFornecedor.objects.filter(pk=pedido.idvendrepre).first()
        if pedido.idvendrepre else None
    )

    tecnicos = ClienteFornecedor.objects.filter(
        empresa_id=empresa_id, tipocliforemp='E', inativo=False
    ).order_by('razao', 'nome')
    tecnico_atual = (
        ClienteFornecedor.objects.filter(pk=pedido.idtecnico).first()
        if pedido.idtecnico else None
    )

    return render(request, 'vendas/pedido_detalhe.html', {
        'pedido':        pedido,
        'itens':         itens,
        'parcelas':      parcelas,
        'vendedor':      vendedor,
        'tecnicos':      tecnicos,
        'tecnico_atual': tecnico_atual,
        'today':         date.today(),
        'bloqueado':     pedido.status in ('F', 'I', 'C'),
    })


@modulo_required('acesso_televendas')
def pedido_faturar(request, pk):
    empresa_id = request.session.get('empresa_id')
    pedido = get_object_or_404(Pedido, pk=pk, empresa_id=empresa_id)

    if pedido.status != 'I':
        messages.error(request, 'Apenas pedidos instalados podem ser faturados.')
        return redirect('vendas:pedido_detalhe', pk=pk)

    if request.method != 'POST':
        return redirect('vendas:pedido_detalhe', pk=pk)

    with transaction.atomic():
        data_ref = pedido.datavenda or date.today()
        for parcela in pedido.parcelas.all():
            ContaReceber.objects.create(
                empresa_id = empresa_id,
                data       = data_ref,
                cliente    = pedido.cliente,
                idpedido   = pedido.pk,
                parcela    = parcela.parcela,
                valor      = parcela.valor,
                vencimento = parcela.vencimento,
                numerodoc  = str(pedido.numero or pedido.pk),
                status     = 'A',
                juros      = Decimal('0'),
                descontos  = Decimal('0'),
                valorpago  = Decimal('0'),
            )

        pedido.status  = 'F'
        pedido.datafat = date.today()
        pedido.save(update_fields=['status', 'datafat'])

    messages.success(request, f'Pedido #{pedido.pk} faturado — contas a receber geradas.')
    return redirect('vendas:pedido_detalhe', pk=pk)


@modulo_required('acesso_televendas')
def pedido_instalar(request, pk):
    empresa_id = request.session.get('empresa_id')
    pedido = get_object_or_404(Pedido, pk=pk, empresa_id=empresa_id)

    if pedido.status != 'A':
        messages.error(request, 'Apenas pedidos abertos podem ser instalados.')
        return redirect('vendas:pedido_detalhe', pk=pk)

    if request.method == 'POST':
        datainstal_raw = request.POST.get('datainstal', '').strip()
        idtecnico_raw  = request.POST.get('idtecnico', '').strip()
        observacao     = request.POST.get('observacao', '').strip()

        try:
            datainstal = datetime.strptime(datainstal_raw, '%Y-%m-%d').date()
        except ValueError:
            datainstal = date.today()

        pedido.status     = 'I'
        pedido.datainstal = datainstal
        pedido.idtecnico  = int(idtecnico_raw) if idtecnico_raw else 0
        if observacao:
            pedido.observacao = observacao
        pedido.save(update_fields=['status', 'datainstal', 'idtecnico', 'observacao'])
        messages.success(request, f'Pedido #{pedido.pk} instalado em {datainstal.strftime("%d/%m/%Y")}.')
        return redirect('vendas:pedido_detalhe', pk=pk)

    return redirect('vendas:pedido_detalhe', pk=pk)


@modulo_required('acesso_televendas')
def pedido_cancelar(request, pk):
    empresa_id = request.session.get('empresa_id')
    pedido = get_object_or_404(Pedido, pk=pk, empresa_id=empresa_id)

    if pedido.status in ('F', 'C'):
        messages.error(request, 'Este pedido não pode ser cancelado.')
        return redirect('vendas:pedido_detalhe', pk=pk)

    if request.method == 'POST':
        motivo = request.POST.get('motivo', '').strip()
        if not motivo:
            messages.error(request, 'Informe o motivo do cancelamento.')
            return redirect('vendas:pedido_detalhe', pk=pk)

        if pedido.status == 'F':
            ContaReceber.objects.filter(
                empresa_id=empresa_id, idpedido=pedido.pk, status='A'
            ).update(status='C')

        pedido.status        = 'C'
        pedido.datacancela   = date.today()
        pedido.motivocancela = motivo
        pedido.save(update_fields=['status', 'datacancela', 'motivocancela'])
        messages.success(request, f'Pedido #{pedido.pk} cancelado.')
        return redirect('vendas:pedido_list')

    return redirect('vendas:pedido_detalhe', pk=pk)


# ─── Comissões ───────────────────────────────────────────────────────────────

@modulo_required('acesso_televendas')
def comissao_config(request):
    empresa_id = request.session.get('empresa_id')
    config = ConfiguracaoComissao.objects.first()

    if request.method == 'POST':
        fields = [
            'telprazo', 'telav', 'telpremio',
            'meiprazo', 'meiav', 'meipremio',
        ]
        data = {f: Decimal(request.POST.get(f, '0') or '0') for f in fields}
        if config:
            for f, v in data.items():
                setattr(config, f, v)
            config.save(update_fields=fields)
        else:
            ConfiguracaoComissao.objects.create(**data)
        messages.success(request, 'Configuração salva.')
        return redirect('vendas:comissao_config')

    return render(request, 'vendas/comissao_config.html', {'config': config})


@modulo_required('acesso_televendas')
def acerto_list(request):
    empresa_id = request.session.get('empresa_id')
    status = request.GET.get('status', '')
    q      = request.GET.get('q', '').strip()

    qs = AcertoComissao.objects.filter(empresa_id=empresa_id)
    if status:
        qs = qs.filter(status=status)

    acertos = []
    for a in qs[:200]:
        vend = ClienteFornecedor.objects.filter(pk=a.idvendrepre).first()
        nome = (vend.razao or vend.nome) if vend else f'#{a.idvendrepre}'
        if q and q.lower() not in nome.lower():
            continue
        acertos.append({'obj': a, 'vendedor': nome})

    return render(request, 'vendas/acerto_list.html', {
        'acertos':        acertos,
        'status':         status,
        'q':              q,
        'status_choices': AcertoComissao.STATUS_CHOICES,
    })


@modulo_required('acesso_televendas')
def acerto_create(request):
    empresa_id = request.session.get('empresa_id')

    if request.method == 'POST':
        idvend   = request.POST.get('idvendrepre', '').strip()
        periini  = request.POST.get('perildoini', '').strip()
        perifim  = request.POST.get('periodofim', '').strip()
        obs      = request.POST.get('observacao', '').strip()

        if not (idvend and periini and perifim):
            messages.error(request, 'Preencha vendedor e período.')
        else:
            acerto = AcertoComissao.objects.create(
                empresa_id   = empresa_id,
                idvendrepre  = int(idvend),
                emissao      = date.today(),
                perildoini   = periini,
                periodofim   = perifim,
                observacao   = obs,
                status       = 'A',
            )
            messages.success(request, f'Acerto #{acerto.pk} criado.')
            return redirect('vendas:acerto_detalhe', pk=acerto.pk)

    vendedores = ClienteFornecedor.objects.filter(
        empresa_id=empresa_id, tipocliforemp='V', inativo=False
    ).order_by('razao', 'nome')

    return render(request, 'vendas/acerto_create.html', {'vendedores': vendedores})


@modulo_required('acesso_televendas')
def acerto_detalhe(request, pk):
    empresa_id = request.session.get('empresa_id')
    acerto = get_object_or_404(AcertoComissao, pk=pk, empresa_id=empresa_id)
    movimentos = list(acerto.movimentos.select_related('pedido', 'cliente').all())
    vendedor   = ClienteFornecedor.objects.filter(pk=acerto.idvendrepre).first()

    sem_vendedor = []
    if acerto.status == 'A' and acerto.perildoini and acerto.periodofim:
        sem_vendedor = list(
            Pedido.objects
            .filter(
                empresa_id=empresa_id,
                idvendrepre=0,
                datainstal__gte=acerto.perildoini,
                datainstal__lte=acerto.periodofim,
                status='I',
            )
            .exclude(comissaook='S')
            .select_related('cliente')
            .order_by('datainstal')
        )

    return render(request, 'vendas/acerto_detalhe.html', {
        'acerto':       acerto,
        'movimentos':   movimentos,
        'vendedor':     vendedor,
        'sem_vendedor': sem_vendedor,
        'bloqueado':    acerto.status in ('F', 'C'),
    })


@modulo_required('acesso_televendas')
def acerto_calcular(request, pk):
    empresa_id = request.session.get('empresa_id')
    acerto = get_object_or_404(AcertoComissao, pk=pk, empresa_id=empresa_id)

    if acerto.status != 'A':
        messages.error(request, 'Apenas acertos abertos podem ser calculados.')
        return redirect('vendas:acerto_detalhe', pk=pk)

    if request.method != 'POST':
        return redirect('vendas:acerto_detalhe', pk=pk)

    movs = _calcular_movimentos(acerto, empresa_id)
    if not movs:
        messages.warning(request, 'Nenhum movimento encontrado para o período.')
        return redirect('vendas:acerto_detalhe', pk=pk)

    with transaction.atomic():
        acerto.movimentos.all().delete()
        total_vendido  = Decimal('0')
        total_base     = Decimal('0')
        total_comissao = Decimal('0')

        for m in movs:
            cliente_obj = ClienteFornecedor.objects.filter(pk=m['cliente_id']).first()
            if not cliente_obj:
                continue
            MovimentoComissao.objects.create(
                acerto         = acerto,
                empresa_id     = empresa_id,
                cliente        = cliente_obj,
                pedido         = m['pedido'],
                identificacao  = m['identificacao'],
                quantidade     = m['quantidade'],
                valorunitario  = m['valorunitario'],
                valortotal     = m['valortotal'],
                basecomissao   = m['basecomissao'],
                perccomiss     = m['perccomiss'],
                valorcomiss    = m['valorcomiss'],
                valortabela    = m['valortabela'],
            )
            total_vendido  += m['valortotal']
            total_base     += m['basecomissao']
            total_comissao += m['valorcomiss']

        acerto.totalvendido  = total_vendido.quantize(Decimal('0.01'))
        acerto.totalbase     = total_base.quantize(Decimal('0.01'))
        acerto.totalcomissao = total_comissao.quantize(Decimal('0.01'))
        acerto.save(update_fields=['totalvendido', 'totalbase', 'totalcomissao'])

    messages.success(request, f'{len(movs)} movimentos calculados.')
    return redirect('vendas:acerto_detalhe', pk=pk)


@modulo_required('acesso_televendas')
def acerto_confirmar(request, pk):
    empresa_id = request.session.get('empresa_id')
    acerto = get_object_or_404(AcertoComissao, pk=pk, empresa_id=empresa_id)

    if acerto.status != 'A':
        messages.error(request, 'Apenas acertos abertos podem ser confirmados.')
        return redirect('vendas:acerto_detalhe', pk=pk)

    if not acerto.movimentos.exists():
        messages.error(request, 'Calcule os movimentos antes de confirmar.')
        return redirect('vendas:acerto_detalhe', pk=pk)

    if request.method != 'POST':
        return redirect('vendas:acerto_detalhe', pk=pk)

    vendedor = ClienteFornecedor.objects.filter(pk=acerto.idvendrepre).first()
    if not vendedor:
        messages.error(request, 'Vendedor não encontrado.')
        return redirect('vendas:acerto_detalhe', pk=pk)

    with transaction.atomic():
        ContaPagar.objects.create(
            empresa_id     = empresa_id,
            data           = date.today(),
            fornecedor     = vendedor,
            parcela        = 1,
            valor          = acerto.totalcomissao,
            vencimento     = date.today(),
            numerodoc      = f'COMIS-{acerto.pk}',
            status         = 'A',
            juros          = Decimal('0'),
            descontos      = Decimal('0'),
            valorpago      = Decimal('0'),
            idacertocomiss = acerto.pk,
        )

        pedido_ids = acerto.movimentos.values_list('pedido_id', flat=True).distinct()
        Pedido.objects.filter(pk__in=pedido_ids).update(comissaook='S')

        acerto.status = 'F'
        acerto.save(update_fields=['status'])

    messages.success(request, f'Acerto #{acerto.pk} confirmado — conta a pagar gerada.')
    return redirect('vendas:acerto_detalhe', pk=pk)


@modulo_required('acesso_televendas')
def acerto_cancelar(request, pk):
    empresa_id = request.session.get('empresa_id')
    acerto = get_object_or_404(AcertoComissao, pk=pk, empresa_id=empresa_id)

    if acerto.status == 'F':
        messages.error(request, 'Acerto finalizado não pode ser cancelado.')
        return redirect('vendas:acerto_detalhe', pk=pk)

    if request.method != 'POST':
        return redirect('vendas:acerto_detalhe', pk=pk)

    with transaction.atomic():
        acerto.movimentos.all().delete()
        acerto.totalvendido  = Decimal('0')
        acerto.totalbase     = Decimal('0')
        acerto.totalcomissao = Decimal('0')
        acerto.status        = 'C'
        acerto.save(update_fields=['totalvendido', 'totalbase', 'totalcomissao', 'status'])

    messages.success(request, f'Acerto #{acerto.pk} cancelado.')
    return redirect('vendas:acerto_list')


@modulo_required('acesso_televendas')
def acerto_associar(request, pk):
    """Associa pedidos sem vendedor (idvendrepre=0) ao vendedor do acerto."""
    empresa_id = request.session.get('empresa_id')
    acerto = get_object_or_404(AcertoComissao, pk=pk, empresa_id=empresa_id)

    if acerto.status != 'A':
        messages.error(request, 'Apenas acertos abertos permitem associação de pedidos.')
        return redirect('vendas:acerto_detalhe', pk=pk)

    if request.method != 'POST':
        return redirect('vendas:acerto_detalhe', pk=pk)

    ids_raw = request.POST.getlist('pedidos_assoc')
    if not ids_raw:
        messages.warning(request, 'Nenhum pedido selecionado.')
        return redirect('vendas:acerto_detalhe', pk=pk)

    ids = [int(i) for i in ids_raw if i.isdigit()]
    updated = Pedido.objects.filter(
        pk__in=ids, empresa_id=empresa_id, idvendrepre=0
    ).update(idvendrepre=acerto.idvendrepre)

    messages.success(request, f'{updated} pedido(s) associado(s) ao vendedor.')
    return redirect('vendas:acerto_detalhe', pk=pk)


@modulo_required('acesso_televendas')
def acerto_remover_pedido(request, pk, pedido_pk):
    """Remove um pedido do acerto: apaga seus movimentos, zera idvendrepre e recalcula totais."""
    empresa_id = request.session.get('empresa_id')
    acerto = get_object_or_404(AcertoComissao, pk=pk, empresa_id=empresa_id)

    if acerto.status != 'A':
        messages.error(request, 'Apenas acertos abertos permitem remoção de pedidos.')
        return redirect('vendas:acerto_detalhe', pk=pk)

    if request.method != 'POST':
        return redirect('vendas:acerto_detalhe', pk=pk)

    with transaction.atomic():
        acerto.movimentos.filter(pedido_id=pedido_pk).delete()

        Pedido.objects.filter(
            pk=pedido_pk, empresa_id=empresa_id, idvendrepre=acerto.idvendrepre
        ).update(idvendrepre=0)

        totais = acerto.movimentos.aggregate(
            tv=Sum('valortotal'),
            tb=Sum('basecomissao'),
            tc=Sum('valorcomiss'),
        )
        acerto.totalvendido  = (totais['tv'] or Decimal('0')).quantize(Decimal('0.01'))
        acerto.totalbase     = (totais['tb'] or Decimal('0')).quantize(Decimal('0.01'))
        acerto.totalcomissao = (totais['tc'] or Decimal('0')).quantize(Decimal('0.01'))
        acerto.save(update_fields=['totalvendido', 'totalbase', 'totalcomissao'])

    messages.success(request, f'Pedido #{pedido_pk} removido do acerto.')
    return redirect('vendas:acerto_detalhe', pk=pk)


@modulo_required('acesso_televendas')
def acerto_comprovante(request, pk):
    empresa_id = request.session.get('empresa_id')
    acerto = get_object_or_404(AcertoComissao, pk=pk, empresa_id=empresa_id)

    if acerto.status != 'F':
        messages.error(request, 'O comprovante só está disponível para acertos finalizados.')
        return redirect('vendas:acerto_detalhe', pk=pk)

    movimentos = list(acerto.movimentos.select_related('cliente').all())
    vendedor   = ClienteFornecedor.objects.filter(pk=acerto.idvendrepre).first()
    empresa    = Empresa.objects.filter(pk=empresa_id).first()

    nome_vend  = (vendedor.razao or vendedor.nome) if vendedor else str(acerto.idvendrepre)
    filename   = f'comissao-acerto-{acerto.pk}-{nome_vend[:20].replace(" ", "_")}.pdf'

    return render_pdf(
        'vendas/acerto_comprovante_pdf.html',
        {
            'acerto':     acerto,
            'movimentos': movimentos,
            'vendedor':   vendedor,
            'empresa':    empresa,
            'usuario':    request.user.get_full_name() or request.user.username,
        },
        filename=filename,
        request=request,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Espelhos PDF
# ═══════════════════════════════════════════════════════════════════════════════

@modulo_required('acesso_televendas')
def pedido_espelho(request, pk):
    from django.utils import timezone
    empresa_id = request.session.get('empresa_id')
    pedido   = get_object_or_404(Pedido, pk=pk, empresa_id=empresa_id)
    empresa  = pedido.empresa
    itens    = pedido.itens.select_related('item').all()
    parcelas = pedido.parcelas.all()
    vendedor = ClienteFornecedor.objects.filter(pk=pedido.idvendrepre).first() if pedido.idvendrepre else None
    tecnico  = ClienteFornecedor.objects.filter(pk=pedido.idtecnico).first()   if pedido.idtecnico  else None

    return render_pdf(
        'espelhos/pedido.html',
        {
            'empresa':  empresa,
            'pedido':   pedido,
            'itens':    itens,
            'parcelas': parcelas,
            'vendedor': vendedor,
            'tecnico':  tecnico,
            'now':      timezone.localtime(),
            'usuario':  request.user.get_full_name() or request.user.username,
        },
        filename=f'Pedido_{pedido.pk}.pdf',
        request=request,
    )

import json
import calendar as cal_module
from decimal import Decimal
from datetime import date, timedelta
from core.pagination import paginar
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db import transaction
from django.db.models import Q, Exists, OuterRef
from django.http import JsonResponse
from django.utils import timezone
from core.decorators import modulo_required
from core.models import Empresa
from financeiro.relatorios import render_pdf
from cadastros.models import ClienteFornecedor, HistoricoCliente, TelefoneAdicional, CondicaoPagamento, Item
from financeiro.models import ContaReceber, ContaPagar
from vendas.models import Pedido, ItemPedido, ParcelaPedido
from estoque.models import Requisicao, ItemRequisicao
from campo.services import criar_servicos_roteiro
from campo.models import Servico as ServicoCampo
from .models import (ContatoCliente, TeleVenda, ItemTeleVenda, ParcelaTeleVenda,
                     Roteiro, OSRoteiro)
from .forms import ContatoForm, TelefoneForm, TeleVendaForm

COL_DEFS = [
    ('codigo', '#'),
    ('cpfcnpj', 'CNPJ/CPF'),
    ('nome',   'Nome'),
    ('fone',   'Fone'),
    ('fone',   'Celular'),
    ('bairro', 'Bairro'),
    ('cidade', 'Cidade'),
    ('proxcontato', 'Próx. Contato'),
]

ORDEM_CAMPOS = {
    'codigo': 'idcliforemp',
    'nome':   'razao',
    'cpfcnpj':'cnpjcpf',
    'cidade': 'cidade__descricao',
    'bairro': 'bairro',
    'fone':   'fone',
}

REF_FILTROS = {
    'nome':   'razao__icontains',
    'cpfcnpj':'cnpjcpf__icontains',
    'cidade': 'cidade__descricao__icontains',
    'bairro': 'bairro__icontains',
    'fone':   'fone__icontains',
}


def _qs_clientes(empresa_id, ref, q, order, direction):
    qs = (ClienteFornecedor.objects
          .select_related('cidade')
          .filter(tipocliforemp='C'))
    if empresa_id:
        qs = qs.filter(empresa_id=empresa_id)

    if q and q != '*':
        if ref == 'codigo':
            try:
                qs = qs.filter(idcliforemp=int(q))
            except ValueError:
                qs = qs.none()
        elif ref == 'nome':
            qs = qs.filter(Q(razao__icontains=q) | Q(nome__icontains=q))
        else:
            filtro = REF_FILTROS.get(ref, 'razao__icontains')
            qs = qs.filter(**{filtro: q})

    qs = qs.annotate(
        inadimplente=Exists(
            ContaReceber.objects.filter(
                empresa_id=empresa_id,
                cliente=OuterRef('pk'), status='A', vencimento__lt=date.today()
            )
        ),
        os_andamento=Exists(
            TeleVenda.objects.filter(
                empresa_id=empresa_id,
                cliente=OuterRef('pk'), status__in=['A', 'P']
            )
        ),
        tem_pedido=Exists(
            TeleVenda.objects.filter(empresa_id=empresa_id, cliente=OuterRef('pk'))
        ),
    )

    campo = ORDEM_CAMPOS.get(order, 'razao')
    if direction == 'desc':
        campo = f'-{campo}'
    return qs.order_by(campo)


@modulo_required('acesso_televendas')
def crm_lookup(request):
    empresa_id = request.session.get('empresa_id')
    ref       = request.GET.get('ref', 'nome')
    q         = request.GET.get('q', '').strip()
    order     = request.GET.get('order', 'nome')
    direction = request.GET.get('dir', 'asc')

    clientes = _qs_clientes(empresa_id, ref, q, order, direction)[:300] if q else []

    return render(request, 'servicos/crm_lookup.html', {
        'clientes': clientes, 'ref': ref, 'q': q,
        'order': order, 'direction': direction,
        'col_defs': COL_DEFS,
        'total': len(clientes) if q else 0,
    })


@modulo_required('acesso_televendas')
def crm_buscar(request):
    empresa_id = request.session.get('empresa_id')
    ref       = request.GET.get('ref', 'nome')
    q         = request.GET.get('q', '').strip()
    order     = request.GET.get('order', 'nome')
    direction = request.GET.get('dir', 'asc')

    clientes = _qs_clientes(empresa_id, ref, q, order, direction)[:300] if q else []

    return render(request, 'servicos/partials/tabela_clientes.html', {
        'clientes': clientes, 'ref': ref, 'q': q,
        'order': order, 'direction': direction,
        'col_defs': COL_DEFS,
    })


@modulo_required('acesso_televendas')
def crm_ficha(request, pk):
    empresa_id = request.session.get('empresa_id')

    cli = get_object_or_404(ClienteFornecedor, pk=pk)

    cr_abertos  = ContaReceber.objects.filter(empresa_id=empresa_id, cliente=cli, status='A').order_by('vencimento')
    cr_vencidos = cr_abertos.filter(vencimento__lt=date.today())
    cp_abertos  = ContaPagar.objects.filter(empresa_id=empresa_id, fornecedor=cli, status='A').order_by('vencimento')

    historico   = HistoricoCliente.objects.filter(empresa_id=empresa_id, cliforemp=cli).order_by('-datavenda')[:20]
    ultimo_hist = historico.first()

    os_lista    = TeleVenda.objects.filter(empresa_id=empresa_id, cliente=cli).order_by('-dataprevisao')[:10]

    contatos    = ContatoCliente.objects.filter(empresa_id=empresa_id, cliforemp=cli).order_by('-datacontato')[:30]
    telefones   = TelefoneAdicional.objects.filter(cliforemp=cli)

    proximo_contato = (
        ContatoCliente.objects
        .filter(empresa_id=empresa_id, cliforemp=cli, proximocontato__isnull=False)
        .order_by('proximocontato')
        .filter(proximocontato__gte=date.today())
        .values_list('proximocontato', flat=True)
        .first()
    )

    inadimplente = cr_vencidos.exists()
    os_andamento = TeleVenda.objects.filter(empresa_id=empresa_id, cliente=cli, status__in=['A', 'P']).exists()

    form_contato = ContatoForm(initial={'datacontato': date.today()})
    form_fone    = TelefoneForm()

    return render(request, 'servicos/crm_ficha.html', {
        'cli':          cli,
        'cr_abertos':   cr_abertos,
        'cr_vencidos':  cr_vencidos,
        'cp_abertos':   cp_abertos,
        'historico':    historico,
        'ultimo_hist':  ultimo_hist,
        'os_lista':     os_lista,
        'contatos':     contatos,
        'inadimplente': inadimplente,
        'os_andamento': os_andamento,
        'form_contato':    form_contato,
        'form_fone':       form_fone,
        'telefones':       telefones,
        'proximo_contato': proximo_contato,
        'hoje':            date.today(),
    })


@modulo_required('acesso_televendas')
def contato_salvar(request, cli_pk):
    cli = get_object_or_404(ClienteFornecedor, pk=cli_pk)
    empresa_id = request.session.get('empresa_id')

    contato_pk = request.POST.get('contato_pk')
    if contato_pk:
        obj  = get_object_or_404(ContatoCliente, pk=contato_pk, cliforemp=cli)
        form = ContatoForm(request.POST, instance=obj)
        acao = 'atualizado'
    else:
        form = ContatoForm(request.POST)
        acao = 'registrado'

    if form.is_valid():
        c = form.save(commit=False)
        c.cliforemp    = cli
        c.empresa_id   = empresa_id
        c.usuario      = request.user.username
        c.save()
        messages.success(request, f'Contato {acao}.')
    else:
        messages.error(request, 'Verifique os dados do contato.')

    return redirect('servicos:crm_ficha', pk=cli_pk)


@modulo_required('acesso_televendas')
def contato_excluir(request, pk):
    contato = get_object_or_404(ContatoCliente, pk=pk)
    cli_pk  = contato.cliforemp_id
    if request.method == 'POST':
        contato.delete()
        messages.success(request, 'Contato removido.')
    return redirect('servicos:crm_ficha', pk=cli_pk)


MESES_PT = [
    'Janeiro','Fevereiro','Março','Abril','Maio','Junho',
    'Julho','Agosto','Setembro','Outubro','Novembro','Dezembro',
]
STATUS_AGENDA = ['Pendente', 'Agendado', 'Em andamento']


@modulo_required('acesso_televendas')
def agenda_view(request):
    empresa_id = request.session.get('empresa_id')
    today  = date.today()
    year   = int(request.GET.get('ano', today.year))
    month  = int(request.GET.get('mes', today.month))
    month  = max(1, min(12, month))
    desc   = request.GET.get('desc', '').strip()

    contatos = (
        ContatoCliente.objects
        .filter(empresa_id=empresa_id,
                proximocontato__year=year, proximocontato__month=month,
                status__in=STATUS_AGENDA)
        .select_related('cliforemp')
        .order_by('proximocontato', 'cliforemp__razao')
    )
    if desc:
        contatos = contatos.filter(descricao__icontains=desc)

    por_dia = {}
    for c in contatos:
        por_dia.setdefault(c.proximocontato.day, []).append(c)

    # Grade com domingo como primeiro dia
    calendario = cal_module.Calendar(firstweekday=6)
    semanas_raw = calendario.monthdayscalendar(year, month)
    semanas = [
        [{'day': d, 'contatos': por_dia.get(d, []) if d else []} for d in semana]
        for semana in semanas_raw
    ]

    prev_month = month - 1 or 12
    prev_year  = year - 1 if month == 1 else year
    next_month = month % 12 + 1
    next_year  = year + 1 if month == 12 else year

    return render(request, 'servicos/agenda.html', {
        'semanas':    semanas,
        'year':       year,
        'month':      month,
        'mes_nome':   MESES_PT[month - 1],
        'today':      today,
        'prev_year':  prev_year,  'prev_month': prev_month,
        'next_year':  next_year,  'next_month': next_month,
        'desc':       desc,
        'total':      contatos.count(),
    })


@modulo_required('acesso_televendas')
def fone_salvar(request, cli_pk):
    cli = get_object_or_404(ClienteFornecedor, pk=cli_pk)
    fone_pk = request.POST.get('fone_pk')
    if fone_pk:
        obj  = get_object_or_404(TelefoneAdicional, pk=fone_pk, cliforemp=cli)
        form = TelefoneForm(request.POST, instance=obj)
        acao = 'atualizado'
    else:
        form = TelefoneForm(request.POST)
        acao = 'registrado'

    if form.is_valid():
        f = form.save(commit=False)
        f.cliforemp = cli
        f.save()
        messages.success(request, f'Telefone {acao}.')
    else:
        messages.error(request, 'Verifique os dados do telefone.')

    return redirect('servicos:crm_ficha', pk=cli_pk)


@modulo_required('acesso_televendas')
def fone_excluir(request, pk):
    fone   = get_object_or_404(TelefoneAdicional, pk=pk)
    cli_pk = fone.cliforemp_id
    if request.method == 'POST':
        fone.delete()
        messages.success(request, 'Telefone removido.')
    return redirect('servicos:crm_ficha', pk=cli_pk)


# ── Ordem de Serviço ──────────────────────────────────────────────────────────

def _gerar_numero_os(empresa_id):
    """Sequencial por empresa: OS-0001, OS-0002..."""
    ultimo = (TeleVenda.objects
              .filter(empresa_id=empresa_id)
              .order_by('-idtelvenda')
              .values_list('idtelvenda', flat=True)
              .first()) or 0
    return f'OS-{ultimo + 1:04d}'


@modulo_required('acesso_televendas')
def os_list(request):
    empresa_id = request.session.get('empresa_id')
    status     = request.GET.get('status', '')
    q          = request.GET.get('q', '').strip()

    qs = TeleVenda.objects.select_related('cliente').filter(empresa_id=empresa_id)
    if status:
        qs = qs.filter(status=status)
    if q:
        qs = qs.filter(
            Q(numero__icontains=q) |
            Q(cliente__razao__icontains=q) |
            Q(cliente__nome__icontains=q)
        )
    qs = qs.order_by('-dataprevisao', '-idtelvenda')

    page_obj, page_range, query_string = paginar(request, qs)

    return render(request, 'servicos/os_list.html', {
        'lista':          page_obj.object_list,
        'page_obj':       page_obj,
        'page_range':     page_range,
        'query_string':   query_string,
        'status':         status,
        'q':              q,
        'status_choices': TeleVenda.STATUS_CHOICES,
    })


@modulo_required('acesso_televendas')
def os_create(request, cli_pk=None):
    empresa_id = request.session.get('empresa_id')
    cli = get_object_or_404(ClienteFornecedor, pk=cli_pk) if cli_pk else None

    if request.method == 'POST':
        form = TeleVendaForm(request.POST, empresa_id=empresa_id)
        if form.is_valid():
            with transaction.atomic():
                os = form.save(commit=False)
                os.empresa_id   = empresa_id
                os.dataemissao  = date.today()
                os.usuariolanc  = request.user.username
                os.idusuario    = request.user.pk
                os.status       = 'A'

                vendedor = form.cleaned_data.get('vendedor')
                tecnico  = form.cleaned_data.get('tecnico')
                os.idvendrepre = vendedor.pk if vendedor else 0
                os.idtecnico   = tecnico.pk  if tecnico  else 0

                os.save()
                os.numero = f'OS-{os.idtelvenda:04d}'
                os.save(update_fields=['numero'])

                # Itens — first pass: create, track temp-id → pk
                itens_raw  = json.loads(request.POST.get('itens_json', '[]'))
                qtd_total  = Decimal('0')
                val_total  = Decimal('0')
                tid_to_pk  = {}
                for it in itens_raw:
                    qty    = Decimal(str(it.get('quantidade', 1)))
                    preco  = Decimal(str(it.get('valorunitario', 0)))
                    instal = Decimal(str(it.get('instalacao', 0)))
                    total  = qty * preco + instal
                    obj = ItemTeleVenda.objects.create(
                        telvenda      = os,
                        item_id       = it['item_id'],
                        identificacao = it.get('identificacao', ''),
                        quantidade    = qty,
                        valorunitario = preco,
                        instalacao    = instal,
                        valortotal    = total,
                        tipo_item     = it.get('tipo_item', ''),
                    )
                    tid_to_pk[it.get('_tid', 0)] = obj.pk
                    qtd_total += qty
                    val_total += total
                # Second pass: resolve servico_pai
                for it in itens_raw:
                    pai_tid = int(it.get('servico_pai_tid', 0))
                    if pai_tid and pai_tid in tid_to_pk:
                        pk = tid_to_pk.get(it.get('_tid', 0))
                        if pk:
                            ItemTeleVenda.objects.filter(pk=pk).update(
                                servico_pai=tid_to_pk[pai_tid]
                            )

                os.quantidadetotal = qtd_total
                os.valortotal      = val_total
                os.save(update_fields=['quantidadetotal', 'valortotal'])

                # Parcelas
                parcelas_raw = json.loads(request.POST.get('parcelas_json', '[]'))
                for i, p in enumerate(parcelas_raw):
                    ParcelaTeleVenda.objects.create(
                        telvenda   = os,
                        parcela    = i + 1,
                        vencimento = p['vencimento'],
                        valor      = Decimal(str(p['valor'])),
                    )

                messages.success(request, f'{os.numero} lançada com sucesso.')
                return redirect('servicos:os_detalhe', pk=os.pk)
        # form inválido — re-renderiza
    else:
        initial = {'cliente': cli} if cli else {}
        form = TeleVendaForm(initial=initial, empresa_id=empresa_id)

    condicoes = CondicaoPagamento.objects.filter(empresa_id=empresa_id, inativo=False).order_by('descricao')
    condicoes_json = json.dumps({
        str(c.idcondpag): {'parcelas': c.parcelas, 'dias': c.dias}
        for c in condicoes
    })

    return render(request, 'servicos/os_create.html', {
        'form':           form,
        'cli':            cli,
        'condicoes_json': condicoes_json,
    })


@modulo_required('acesso_televendas')
def os_detalhe(request, pk):
    empresa_id = request.session.get('empresa_id')
    os = get_object_or_404(TeleVenda, pk=pk, empresa_id=empresa_id)

    vendedor = (ClienteFornecedor.objects.filter(pk=os.idvendrepre).first()
                if os.idvendrepre else None)
    tecnico  = (ClienteFornecedor.objects.filter(pk=os.idtecnico).first()
                if os.idtecnico else None)

    itens_qs = list(os.itens.select_related('item').all())

    # Build hierarchical groups for display
    servicos  = {it.pk: it for it in itens_qs if it.tipo_item == 'S'}
    children  = {pk: [] for pk in servicos}
    standalone = []
    for it in itens_qs:
        if it.tipo_item != 'S':
            if it.servico_pai in servicos:
                children[it.servico_pai].append(it)
            else:
                standalone.append(it)
    grupos = [{'servico': sv, 'filhos': children[sv.pk]} for sv in servicos.values()]
    if standalone:
        grupos.append({'servico': None, 'filhos': standalone})

    return render(request, 'servicos/os_detalhe.html', {
        'os':       os,
        'itens':    itens_qs,
        'grupos':   grupos,
        'parcelas': os.parcelas.all(),
        'vendedor': vendedor,
        'tecnico':  tecnico,
        'bloqueada': os.status in ('F', 'C'),
    })


@modulo_required('acesso_televendas')
def os_cancelar(request, pk):
    empresa_id = request.session.get('empresa_id')
    os = get_object_or_404(TeleVenda, pk=pk, empresa_id=empresa_id)

    if os.status in ('F', 'C'):
        messages.error(request, 'Esta OS não pode ser cancelada.')
        return redirect('servicos:os_detalhe', pk=pk)

    if request.method == 'POST':
        motivo = request.POST.get('motivo', '').strip()
        if not motivo:
            messages.error(request, 'Informe o motivo do cancelamento.')
            return redirect('servicos:os_detalhe', pk=pk)
        os.status       = 'C'
        os.motivocancel = motivo
        os.save(update_fields=['status', 'motivocancel'])
        messages.success(request, f'{os.numero} cancelada.')
        return redirect('servicos:os_detalhe', pk=pk)

    return redirect('servicos:os_detalhe', pk=pk)


@modulo_required('acesso_televendas')
def os_reagendar(request, pk):
    empresa_id = request.session.get('empresa_id')
    os = get_object_or_404(TeleVenda, pk=pk, empresa_id=empresa_id)

    if os.status in ('F', 'C'):
        messages.error(request, 'Esta OS não pode ser reagendada.')
        return redirect('servicos:os_detalhe', pk=pk)

    if request.method == 'POST':
        nova_data   = request.POST.get('dataprevisao', '').strip()
        periodo     = request.POST.get('atend_periodo', '').strip()
        hora        = request.POST.get('atend_hora', '').strip()
        retorno     = request.POST.get('retornar_agendada', '0')

        if not nova_data:
            messages.error(request, 'Informe a nova data de previsão.')
            return redirect('servicos:os_detalhe', pk=pk)

        try:
            os.dataprevisao = date.fromisoformat(nova_data)
        except ValueError:
            messages.error(request, 'Data inválida.')
            return redirect('servicos:os_detalhe', pk=pk)

        os.atend_periodo = periodo
        os.atend_hora    = hora
        fields = ['dataprevisao', 'atend_periodo', 'atend_hora']

        if retorno == '1' and os.status == 'P':
            os.status = 'A'
            fields.append('status')

        os.save(update_fields=fields)
        messages.success(request, f'{os.numero} reagendada para {os.dataprevisao.strftime("%d/%m/%Y")}.')

    return redirect('servicos:os_detalhe', pk=pk)


@modulo_required('acesso_televendas')
def os_mudar_status(request, pk):
    empresa_id = request.session.get('empresa_id')
    os = get_object_or_404(TeleVenda, pk=pk, empresa_id=empresa_id)

    TRANSICOES = {
        'A': ('P', 'R'),
        'P': ('R',),
        'R': ('F',),
    }
    novo = request.POST.get('status', '')
    permitidos = TRANSICOES.get(os.status, ())

    if request.method == 'POST' and novo in permitidos:
        os.status = novo
        os.save(update_fields=['status'])
        messages.success(request, f'Status atualizado para {os.get_status_display()}.')
    else:
        messages.error(request, 'Transição de status não permitida.')

    return redirect('servicos:os_detalhe', pk=pk)


# ═══════════════════════════════════════════════════════════════════════════════
# Roteiro de Instalação
# ═══════════════════════════════════════════════════════════════════════════════

EXEC_CHOICES = [('A', 'Aberto'), ('E', 'Executado'), ('C', 'Cancelar')]
REC_CHOICES  = [('', '—'), ('S', 'Recebido'), ('P', 'Pendente')]


@modulo_required('acesso_televendas')
def roteiro_list(request):
    empresa_id = request.session.get('empresa_id')
    status = request.GET.get('status', '')
    q      = request.GET.get('q', '').strip()

    qs = Roteiro.objects.filter(empresa_id=empresa_id)
    if status:
        qs = qs.filter(status=status)
    if q:
        qs = qs.filter(Q(idassroteiro__icontains=q) | Q(destino__icontains=q))
    qs = qs.order_by('-dateemissao', '-idassroteiro')[:200]

    return render(request, 'servicos/roteiro_list.html', {
        'lista':          qs,
        'status':         status,
        'q':              q,
        'status_choices': Roteiro.STATUS_CHOICES,
    })


@modulo_required('acesso_televendas')
def roteiro_os_pendentes(request):
    """JSON — OS pendentes ainda não alocadas em roteiro."""
    empresa_id = request.session.get('empresa_id')
    data_ini   = request.GET.get('data_ini', '').strip()
    data_fim   = request.GET.get('data_fim', '').strip()
    q          = request.GET.get('q', '').strip()

    qs = (TeleVenda.objects
          .select_related('cliente')
          .filter(empresa_id=empresa_id, status__in=['A', 'P'], idassroteiro=0))

    if data_ini:
        qs = qs.filter(dataprevisao__gte=data_ini)
    if data_fim:
        qs = qs.filter(dataprevisao__lte=data_fim)
    if q:
        qs = qs.filter(
            Q(numero__icontains=q) |
            Q(cliente__razao__icontains=q) |
            Q(cliente__nome__icontains=q)
        )

    data = [
        {
            'id':               os.idtelvenda,
            'numero':           os.numero or str(os.idtelvenda),
            'cliente':          os.cliente.razao or os.cliente.nome,
            'fone':             os.cliente.celular or os.cliente.fone or '',
            'dataprevisao':     os.dataprevisao.strftime('%Y-%m-%d') if os.dataprevisao else '',
            'dataprevisao_fmt': os.dataprevisao.strftime('%d/%m/%Y') if os.dataprevisao else '—',
            'periodo':          os.get_atend_periodo_display() if os.atend_periodo else '—',
            'valortotal':       float(os.valortotal),
        }
        for os in qs.order_by('dataprevisao', 'cliente__razao')[:300]
    ]
    return JsonResponse(data, safe=False)


@modulo_required('acesso_televendas')
def roteiro_create(request):
    empresa_id = request.session.get('empresa_id')

    if request.method == 'POST':
        data_exec  = request.POST.get('data_execucao', '').strip()
        destino    = request.POST.get('destino', '').strip()
        observacao = request.POST.get('observacao', '').strip()
        os_json    = request.POST.get('os_json', '[]')

        try:
            os_list = json.loads(os_json)
        except (json.JSONDecodeError, ValueError):
            os_list = []

        if not os_list:
            messages.error(request, 'Selecione ao menos uma OS para o roteiro.')
        else:
            try:
                data_exec_date = date.fromisoformat(data_exec) if data_exec else date.today()
            except ValueError:
                data_exec_date = date.today()

            with transaction.atomic():
                roteiro = Roteiro.objects.create(
                    empresa_id      = empresa_id,
                    dateemissao     = data_exec_date,
                    destino         = destino,
                    status          = 'A',
                    qtdassistencias = len(os_list),
                )

                alocadas = 0
                for item in os_list:
                    os_id      = item.get('os_id')
                    tecnico_id = item.get('tecnico_id')
                    tv = TeleVenda.objects.filter(
                        pk=os_id, empresa_id=empresa_id
                    ).first()
                    tecnico = ClienteFornecedor.objects.filter(
                        pk=tecnico_id, empresa_id=empresa_id, tipocliforemp='E'
                    ).first() if tecnico_id else None

                    if tv and tv.status in ('A', 'P') and tv.idassroteiro == 0:
                        OSRoteiro.objects.create(
                            roteiro     = roteiro,
                            cliente     = tecnico or tv.cliente,
                            telvenda    = tv,
                            execucao    = 'A',
                            recebimento = '',
                        )
                        tv.idassroteiro = roteiro.pk
                        tv.save(update_fields=['idassroteiro'])
                        alocadas += 1

                roteiro.qtdassistencias = alocadas
                roteiro.save(update_fields=['qtdassistencias'])

                # Gera requisição de materiais para o roteiro
                primeiro_osrot = (roteiro.ordens_servico
                                  .select_related('cliente')
                                  .filter(cliente__tipocliforemp='E')
                                  .first())
                tecnico_req = primeiro_osrot.cliente if primeiro_osrot else None

                req = Requisicao.objects.create(
                    empresa_id  = empresa_id,
                    cliforemp   = tecnico_req,
                    data        = date.today(),
                    status      = 'A',
                    origem      = 'Roteiro',
                    idorigem    = roteiro.pk,
                    observacao  = f'Requisição gerada por roteiro técnico nº {roteiro.pk}',
                )
                for osrot in roteiro.ordens_servico.select_related('telvenda').all():
                    tv = osrot.telvenda
                    if not tv:
                        continue
                    for it in tv.itens.select_related('item').all():
                        item_obj = it.item
                        if item_obj and item_obj.tipoitem == 0 and item_obj.controla_estoque:
                            ItemRequisicao.objects.create(
                                requisicao    = req,
                                identificacao = it.identificacao,
                                quantidade    = it.quantidade,
                                atendido      = 0,
                                saldo         = it.quantidade,
                                idorigem      = tv.pk,
                            )
                roteiro.idrequisicao = req.pk
                roteiro.requisicaook = True
                roteiro.save(update_fields=['idrequisicao', 'requisicaook'])

                # ── Integração campo: cria Servico para cada OS do roteiro ──
                for osrot in roteiro.ordens_servico.select_related(
                    'telvenda', 'telvenda__cliente', 'cliente'
                ).all():
                    tv = osrot.telvenda
                    if not tv:
                        continue

                    # osrot.cliente armazena o técnico (tipocliforemp='E') quando atribuído
                    tecnico = (
                        osrot.cliente
                        if osrot.cliente and osrot.cliente.tipocliforemp == 'E'
                        else None
                    )
                    cliente = tv.cliente

                    local_parts = [
                        getattr(cliente, 'endereco', ''),
                        getattr(cliente, 'bairro', ''),
                        getattr(cliente, 'nomecidade', ''),
                    ]
                    local = ', '.join(p for p in local_parts if p)

                    materiais = []
                    for it in tv.itens.select_related('item').all():
                        descricao = it.identificacao or (
                            it.item.descricao if it.item else ''
                        )
                        if not descricao:
                            continue
                        materiais.append({
                            'item_id':        it.item_id,
                            'item_codigo':    it.identificacao or '',
                            'item_descricao': descricao,
                            'quantidade':     float(it.quantidade),
                        })

                    criar_servicos_roteiro({
                        'roteiro_id': roteiro.pk,
                        'os_codigo':  str(tv.numero),
                        'tecnicos': [{
                            'id':    tecnico.pk,
                            'nome':  tecnico.razao or tecnico.nome or '',
                            'papel': 'RESPONSAVEL',
                        }] if tecnico else [],
                        'servicos': [{
                            'tipo_atividade': (tv.atend_obs or 'Assistência Técnica')[:100],
                            'cliente_id':     cliente.pk if cliente else None,
                            'cliente_nome':   (cliente.razao or cliente.nome or '') if cliente else '',
                            'local':          local,
                            'ativo':          '',
                            'descricao':      tv.atend_obs or '',
                            'data_prevista':  tv.dataprevisao.isoformat() if tv.dataprevisao else None,
                            'materiais':      materiais,
                        }],
                    })

            messages.success(request, f'Roteiro #{roteiro.pk} criado com {alocadas} OS(s).')
            return redirect('servicos:roteiro_detalhe', pk=roteiro.pk)

    tecnicos = (ClienteFornecedor.objects
                .filter(empresa_id=empresa_id, tipocliforemp='E', inativo=False)
                .order_by('nome', 'razao'))

    return render(request, 'servicos/roteiro_create.html', {
        'tecnicos':  tecnicos,
        'data_hoje': date.today().strftime('%Y-%m-%d'),
    })


# ═══════════════════════════════════════════════════════════════════════════════
# Espelhos PDF
# ═══════════════════════════════════════════════════════════════════════════════

@modulo_required('acesso_televendas')
def os_espelho(request, pk):
    empresa_id = request.session.get('empresa_id')
    os = get_object_or_404(TeleVenda, pk=pk, empresa_id=empresa_id)
    empresa  = os.empresa
    itens_qs = list(os.itens.select_related('item').all())
    parcelas = os.parcelas.all()
    vendedor = ClienteFornecedor.objects.filter(pk=os.idvendrepre).first() if os.idvendrepre else None
    tecnico  = ClienteFornecedor.objects.filter(pk=os.idtecnico).first()  if os.idtecnico  else None

    servicos  = {it.pk: it for it in itens_qs if it.tipo_item == 'S'}
    children  = {pk: [] for pk in servicos}
    standalone = []
    for it in itens_qs:
        if it.tipo_item != 'S':
            if it.servico_pai in servicos:
                children[it.servico_pai].append(it)
            else:
                standalone.append(it)
    grupos = [{'servico': sv, 'filhos': children[sv.pk]} for sv in servicos.values()]
    if standalone:
        grupos.append({'servico': None, 'filhos': standalone})

    return render_pdf(
        'espelhos/os.html',
        {
            'empresa':  empresa,
            'os':       os,
            'itens':    itens_qs,
            'grupos':   grupos,
            'parcelas': parcelas,
            'vendedor': vendedor,
            'tecnico':  tecnico,
            'now':      timezone.localtime(),
            'usuario':  request.user.get_full_name() or request.user.username,
        },
        filename=f'OS_{os.numero}.pdf',
        request=request,
    )


@modulo_required('acesso_televendas')
def roteiro_detalhe(request, pk):
    empresa_id = request.session.get('empresa_id')
    roteiro = get_object_or_404(Roteiro, pk=pk, empresa_id=empresa_id)
    ordens  = list(roteiro.ordens_servico.select_related(
        'telvenda__cliente__cidade', 'cliente'
    ).all())

    # Monta URL do Google Maps com os endereços dos clientes das OS
    from urllib.parse import quote_plus
    paradas = []
    for ord in ordens:
        cli = ord.telvenda.cliente if ord.telvenda else None
        if cli and cli.endereco:
            partes = [cli.endereco]
            if cli.numero:   partes.append(cli.numero)
            if cli.bairro:   partes.append(cli.bairro)
            if cli.cidade:   partes.append(str(cli.cidade))
            if cli.cep:      partes.append(cli.cep)
            paradas.append(quote_plus(' '.join(partes)))
    maps_rota_url = None
    if paradas:
        maps_rota_url = 'https://www.google.com/maps/dir/' + '/'.join(paradas[:10])

    return render(request, 'servicos/roteiro_detalhe.html', {
        'roteiro':       roteiro,
        'ordens':        ordens,
        'exec_choices':  EXEC_CHOICES,
        'rec_choices':   REC_CHOICES,
        'bloqueado':     roteiro.status in ('F', 'C'),
        'maps_rota_url': maps_rota_url,
    })


@modulo_required('acesso_televendas')
def roteiro_salvar_retorno(request, pk):
    empresa_id = request.session.get('empresa_id')
    roteiro = get_object_or_404(Roteiro, pk=pk, empresa_id=empresa_id)

    if roteiro.status in ('F', 'C'):
        messages.error(request, 'Este roteiro não pode ser editado.')
        return redirect('servicos:roteiro_detalhe', pk=pk)

    if request.method != 'POST':
        return redirect('servicos:roteiro_detalhe', pk=pk)

    with transaction.atomic():
        for ordem in roteiro.ordens_servico.select_for_update().all():
            exec_val = request.POST.get(f'exec_{ordem.pk}', '').strip()
            rec_val  = request.POST.get(f'rec_{ordem.pk}', '').strip()
            update = {}
            if exec_val in ('A', 'E', 'C'):
                update['execucao'] = exec_val
            if rec_val in ('', 'S', 'P'):
                update['recebimento'] = rec_val
            if update:
                OSRoteiro.objects.filter(pk=ordem.pk).update(**update)

        roteiro.refresh_from_db()
        if roteiro.status == 'A':
            if roteiro.ordens_servico.exclude(execucao='A').exists():
                roteiro.status = 'E'
                roteiro.save(update_fields=['status'])

    messages.success(request, 'Retorno salvo.')
    return redirect('servicos:roteiro_detalhe', pk=pk)


@modulo_required('acesso_televendas')
def roteiro_conferir(request, pk):
    """Finaliza o roteiro: gera Pedido+CR dos executados, cancela os cancelados."""
    empresa_id = request.session.get('empresa_id')
    roteiro = get_object_or_404(Roteiro, pk=pk, empresa_id=empresa_id)

    if roteiro.status in ('F', 'C'):
        messages.error(request, 'Este roteiro já foi finalizado ou cancelado.')
        return redirect('servicos:roteiro_detalhe', pk=pk)

    if request.method != 'POST':
        return redirect('servicos:roteiro_detalhe', pk=pk)

    executados = cancelados = liberados = 0

    with transaction.atomic():
        for ordem in roteiro.ordens_servico.select_related(
            'telvenda__cliente', 'telvenda__condicao',
            'telvenda__tabela', 'telvenda__metodo', 'cliente',
        ).select_for_update(of=('self',)).all():
            tv = ordem.telvenda
            if not tv:
                continue

            if ordem.execucao == 'E' and tv.status not in ('F', 'C'):
                data_ref = tv.dataprevisao or date.today()

                pedido = Pedido.objects.create(
                    empresa_id   = empresa_id,
                    numgrafico   = tv.numero,
                    datagrav     = date.today(),
                    datavenda    = tv.dataemissao or date.today(),
                    previnstal   = tv.dataprevisao,
                    datafat      = date.today(),
                    datainstal   = date.today(),
                    cliente      = tv.cliente,
                    idvendrepre  = tv.idvendrepre,
                    idtecnico    = ordem.cliente_id,
                    condicao     = tv.condicao,
                    tabela       = tv.tabela,
                    metodo       = tv.metodo,
                    valortotal   = tv.valortotal,
                    status       = 'I',
                    observacao   = f'Roteiro #{roteiro.pk}',
                    control_conf = 'S',
                )

                for it in tv.itens.all():
                    ItemPedido.objects.create(
                        pedido        = pedido,
                        item          = it.item,
                        identificacao = it.identificacao,
                        quantidade    = it.quantidade,
                        valorunitario = it.valorunitario,
                        instalacao    = it.instalacao,
                        valortotal    = it.valortotal,
                    )

                for p in tv.parcelas.all():
                    ParcelaPedido.objects.create(
                        pedido     = pedido,
                        parcela    = p.parcela,
                        vencimento = p.vencimento,
                        valor      = p.valor,
                    )
                    ContaReceber.objects.create(
                        empresa_id = empresa_id,
                        data       = data_ref,
                        cliente    = tv.cliente,
                        idpedido   = pedido.pk,
                        parcela    = p.parcela,
                        valor      = p.valor,
                        vencimento = p.vencimento,
                        numerodoc  = tv.numero or str(pedido.pk),
                        status     = 'A',
                        juros      = Decimal('0'),
                        descontos  = Decimal('0'),
                        valorpago  = Decimal('0'),
                    )

                tv.status   = 'F'
                tv.idpedido = pedido.pk
                tv.save(update_fields=['status', 'idpedido'])
                executados += 1

            elif ordem.execucao == 'C' and tv.status not in ('F', 'C'):
                tv.status       = 'C'
                tv.motivocancel = f'Cancelado no roteiro #{roteiro.pk}'
                tv.idassroteiro = 0
                tv.save(update_fields=['status', 'motivocancel', 'idassroteiro'])
                cancelados += 1

            else:
                if tv.idassroteiro == roteiro.pk and tv.status not in ('F', 'C'):
                    tv.idassroteiro = 0
                    tv.save(update_fields=['idassroteiro'])
                liberados += 1

        roteiro.status = 'F'
        roteiro.save(update_fields=['status'])

    messages.success(
        request,
        f'Roteiro #{roteiro.pk} finalizado — '
        f'{executados} executado(s), {cancelados} cancelado(s), {liberados} liberado(s).'
    )
    return redirect('servicos:roteiro_detalhe', pk=pk)


@modulo_required('acesso_televendas')
def roteiro_cancelar(request, pk):
    empresa_id = request.session.get('empresa_id')
    roteiro = get_object_or_404(Roteiro, pk=pk, empresa_id=empresa_id)

    if roteiro.status in ('F', 'C'):
        messages.error(request, 'Este roteiro não pode ser cancelado.')
        return redirect('servicos:roteiro_detalhe', pk=pk)

    # Bloqueia cancelamento se algum serviço de campo já foi iniciado
    iniciados = ServicoCampo.objects.filter(
        roteiro_id=roteiro.pk
    ).exclude(
        status__in=['AGENDADO', 'CANCELADO']
    ).select_related()

    if iniciados.exists():
        nomes = ', '.join(
            f'{s.tipo_atividade} ({s.get_status_display()})' for s in iniciados[:3]
        )
        messages.error(
            request,
            f'Cancelamento bloqueado — serviço(s) já iniciado(s) em campo: {nomes}.'
        )
        return redirect('servicos:roteiro_detalhe', pk=pk)

    if request.method == 'POST':
        with transaction.atomic():
            for ordem in roteiro.ordens_servico.select_related('telvenda').all():
                tv = ordem.telvenda
                if tv and tv.status not in ('F', 'C') and tv.idassroteiro == roteiro.pk:
                    tv.idassroteiro = 0
                    tv.save(update_fields=['idassroteiro'])
            roteiro.status = 'C'
            roteiro.save(update_fields=['status'])
        messages.success(request, f'Roteiro #{roteiro.pk} cancelado — OS liberadas.')
        return redirect('servicos:roteiro_list')

    return redirect('servicos:roteiro_detalhe', pk=pk)

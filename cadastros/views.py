import json
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db.models import Q
from core.decorators import modulo_required
from .models import ClienteFornecedor, CondicaoPagamento, Grupo, Item, Portador, Metodo, TabelaPreco, ItemTabelaPreco
from .forms import (ClienteFornecedorForm, CondicaoPagamentoForm, GrupoForm,
                    ItemForm, PortadorForm, MetodoForm, VendedorForm, TecnicoForm,
                    TabelaPrecoForm, ItemTabelaPrecoForm, PARCELAS_FIELDS)


@modulo_required('acesso_cadastro')
def cliente_list(request):
    empresa_id = request.session.get('empresa_id')
    clientes = ClienteFornecedor.objects.filter(empresa_id=empresa_id).select_related('cidade').order_by('razao', 'nome')
    return render(request, 'cadastros/cliente_list.html', {'clientes': clientes})


@modulo_required('acesso_cadastro')
def cliente_buscar(request):
    """Partial HTMX — retorna só a tabela filtrada."""
    empresa_id = request.session.get('empresa_id')
    q = request.GET.get('q', '').strip()
    tipo = request.GET.get('tipo', '')

    clientes = ClienteFornecedor.objects.filter(empresa_id=empresa_id).select_related('cidade')

    if q:
        clientes = clientes.filter(
            Q(razao__icontains=q) |
            Q(nome__icontains=q)  |
            Q(fantasia__icontains=q) |
            Q(cnpjcpf__icontains=q) |
            Q(fone__icontains=q)  |
            Q(celular__icontains=q)
        )

    if tipo:
        clientes = clientes.filter(tipocliforemp=tipo)

    clientes = clientes.order_by('razao', 'nome')[:100]

    return render(request, 'cadastros/partials/tabela_clientes.html', {'clientes': clientes})


@modulo_required('acesso_cadastro')
def cliente_create(request):
    empresa_id = request.session.get('empresa_id')
    if request.method == 'POST':
        form = ClienteFornecedorForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.empresa_id = empresa_id
            obj.save()
            messages.success(request, f'"{obj.nome_exibicao}" salvo com sucesso.')
            if 'salvar_novo' in request.POST:
                return redirect('cadastros:cliente_create')
            return redirect('cadastros:cliente_list')
    else:
        form = ClienteFornecedorForm()

    return render(request, 'cadastros/cliente_form.html', {
        'form': form,
        'titulo': 'Novo Cliente / Fornecedor',
        'objeto': None,
    })


@modulo_required('acesso_cadastro')
def cliente_edit(request, pk):
    empresa_id = request.session.get('empresa_id')
    obj = get_object_or_404(ClienteFornecedor, pk=pk, empresa_id=empresa_id)

    if request.method == 'POST':
        form = ClienteFornecedorForm(request.POST, instance=obj)
        if form.is_valid():
            obj = form.save()
            messages.success(request, f'"{obj.nome_exibicao}" atualizado com sucesso.')
            if 'salvar_novo' in request.POST:
                return redirect('cadastros:cliente_create')
            return redirect('cadastros:cliente_list')
    else:
        form = ClienteFornecedorForm(instance=obj)

    return render(request, 'cadastros/cliente_form.html', {
        'form': form,
        'titulo': f'Editar — {obj.nome_exibicao}',
        'objeto': obj,
    })


@modulo_required('acesso_cadastro')
def cliente_inativar(request, pk):
    """HTMX — alterna inativo e retorna a linha atualizada."""
    empresa_id = request.session.get('empresa_id')
    obj = get_object_or_404(ClienteFornecedor, pk=pk, empresa_id=empresa_id)
    if request.method == 'POST':
        obj.inativo = not obj.inativo
        obj.save(update_fields=['inativo'])

    return render(request, 'cadastros/partials/linha_cliente.html', {'c': obj})


# ── Helper compartilhado Vendedor / Técnico ──────────────────────────────────

def _pessoa_list(request, tipo, template):
    empresa_id = request.session.get('empresa_id')
    pessoas = (ClienteFornecedor.objects
               .filter(tipocliforemp=tipo, empresa_id=empresa_id)
               .order_by('razao', 'nome'))
    return render(request, template, {'pessoas': pessoas})


def _pessoa_buscar(request, tipo, template_partial):
    empresa_id = request.session.get('empresa_id')
    q = request.GET.get('q', '').strip()
    qs = ClienteFornecedor.objects.filter(tipocliforemp=tipo, empresa_id=empresa_id)
    if q:
        qs = qs.filter(Q(razao__icontains=q) | Q(nome__icontains=q) |
                       Q(fone__icontains=q) | Q(celular__icontains=q))
    return render(request, template_partial, {'pessoas': qs.order_by('razao', 'nome')[:100]})


def _pessoa_create(request, tipo, form_class, template, url_list):
    empresa_id = request.session.get('empresa_id')
    if request.method == 'POST':
        form = form_class(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.tipocliforemp = tipo
            obj.empresa_id = empresa_id
            obj.save()
            messages.success(request, f'"{obj.nome_exibicao}" salvo com sucesso.')
            if 'salvar_novo' in request.POST:
                return redirect(url_list)
            return redirect(url_list)
    else:
        form = form_class()
    return render(request, template, {'form': form, 'objeto': None})


def _pessoa_edit(request, pk, tipo, form_class, template, url_list):
    empresa_id = request.session.get('empresa_id')
    obj = get_object_or_404(ClienteFornecedor, pk=pk, tipocliforemp=tipo, empresa_id=empresa_id)
    if request.method == 'POST':
        form = form_class(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, f'"{obj.nome_exibicao}" atualizado com sucesso.')
            return redirect(url_list)
    else:
        form = form_class(instance=obj)
    return render(request, template, {'form': form, 'objeto': obj})


def _pessoa_inativar(request, pk, tipo, template_linha):
    empresa_id = request.session.get('empresa_id')
    obj = get_object_or_404(ClienteFornecedor, pk=pk, tipocliforemp=tipo, empresa_id=empresa_id)
    if request.method == 'POST':
        obj.inativo = not obj.inativo
        obj.save(update_fields=['inativo'])
    return render(request, template_linha, {'p': obj})


# ── Vendedor ─────────────────────────────────────────────────────────────────

@modulo_required('acesso_cadastro')
def vendedor_list(request):
    return _pessoa_list(request, 'V', 'cadastros/vendedor_list.html')


@modulo_required('acesso_cadastro')
def vendedor_buscar(request):
    return _pessoa_buscar(request, 'V', 'cadastros/partials/tabela_vendedores.html')


@modulo_required('acesso_cadastro')
def vendedor_create(request):
    return _pessoa_create(request, 'V', VendedorForm,
                          'cadastros/vendedor_form.html', 'cadastros:vendedor_list')


@modulo_required('acesso_cadastro')
def vendedor_edit(request, pk):
    return _pessoa_edit(request, pk, 'V', VendedorForm,
                        'cadastros/vendedor_form.html', 'cadastros:vendedor_list')


@modulo_required('acesso_cadastro')
def vendedor_inativar(request, pk):
    return _pessoa_inativar(request, pk, 'V', 'cadastros/partials/linha_vendedor.html')


# ── Técnico / Empregado ───────────────────────────────────────────────────────

@modulo_required('acesso_cadastro')
def tecnico_list(request):
    return _pessoa_list(request, 'E', 'cadastros/tecnico_list.html')


@modulo_required('acesso_cadastro')
def tecnico_buscar(request):
    return _pessoa_buscar(request, 'E', 'cadastros/partials/tabela_tecnicos.html')


@modulo_required('acesso_cadastro')
def tecnico_create(request):
    return _pessoa_create(request, 'E', TecnicoForm,
                          'cadastros/tecnico_form.html', 'cadastros:tecnico_list')


@modulo_required('acesso_cadastro')
def tecnico_edit(request, pk):
    return _pessoa_edit(request, pk, 'E', TecnicoForm,
                        'cadastros/tecnico_form.html', 'cadastros:tecnico_list')


@modulo_required('acesso_cadastro')
def tecnico_inativar(request, pk):
    return _pessoa_inativar(request, pk, 'E', 'cadastros/partials/linha_tecnico.html')


# ─────────────────────────────────────────────────────────────────────────────

@modulo_required('acesso_cadastro')
def cidade_lookup(request):
    """HTMX — autocomplete de cidades."""
    q = request.GET.get('q', '').strip()
    from core.models import Cidade
    cidades = Cidade.objects.filter(
        Q(descricao__icontains=q) | Q(uf__icontains=q)
    ).filter(inativo=False).order_by('descricao')[:15] if q else []

    return render(request, 'cadastros/partials/lookup_cidade.html', {'cidades': cidades})


# ── Condições de Pagamento ───────────────────────────────────

@modulo_required('acesso_cadastro')
def condpag_list(request):
    empresa_id = request.session.get('empresa_id')
    condpags = CondicaoPagamento.objects.filter(empresa_id=empresa_id).order_by('descricao')
    return render(request, 'cadastros/condpag_list.html', {'condpags': condpags})


@modulo_required('acesso_cadastro')
def condpag_buscar(request):
    empresa_id = request.session.get('empresa_id')
    q = request.GET.get('q', '').strip()
    condpags = CondicaoPagamento.objects.filter(empresa_id=empresa_id)
    if q:
        condpags = condpags.filter(
            Q(descricao__icontains=q) | Q(condicao__icontains=q)
        )
    condpags = condpags.order_by('descricao')[:100]
    return render(request, 'cadastros/partials/tabela_condpag.html', {'condpags': condpags})


@modulo_required('acesso_cadastro')
def condpag_create(request):
    empresa_id = request.session.get('empresa_id')
    if request.method == 'POST':
        form = CondicaoPagamentoForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.empresa_id = empresa_id
            obj.save()
            messages.success(request, f'"{obj}" salvo com sucesso.')
            if 'salvar_novo' in request.POST:
                return redirect('cadastros:condpag_create')
            return redirect('cadastros:condpag_list')
    else:
        form = CondicaoPagamentoForm()
    return render(request, 'cadastros/condpag_form.html', {
        'form': form, 'titulo': 'Nova Condição de Pagamento', 'objeto': None,
    })


@modulo_required('acesso_cadastro')
def condpag_edit(request, pk):
    empresa_id = request.session.get('empresa_id')
    obj = get_object_or_404(CondicaoPagamento, pk=pk, empresa_id=empresa_id)
    if request.method == 'POST':
        form = CondicaoPagamentoForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, f'"{obj}" atualizado.')
            return redirect('cadastros:condpag_list')
    else:
        form = CondicaoPagamentoForm(instance=obj)
    return render(request, 'cadastros/condpag_form.html', {
        'form': form, 'titulo': f'Editar — {obj}', 'objeto': obj,
    })


@modulo_required('acesso_cadastro')
def condpag_inativar(request, pk):
    empresa_id = request.session.get('empresa_id')
    obj = get_object_or_404(CondicaoPagamento, pk=pk, empresa_id=empresa_id)
    if request.method == 'POST':
        obj.inativo = not obj.inativo
        obj.save(update_fields=['inativo'])
    return render(request, 'cadastros/partials/linha_condpag.html', {'c': obj})


# ── Grupos ───────────────────────────────────────────────────

@modulo_required('acesso_cadastro')
def grupo_list(request):
    empresa_id = request.session.get('empresa_id')
    grupos = Grupo.objects.filter(empresa_id=empresa_id).select_related('idgrupopai').order_by('descricao')
    return render(request, 'cadastros/grupo_list.html', {'grupos': grupos})


@modulo_required('acesso_cadastro')
def grupo_buscar(request):
    empresa_id = request.session.get('empresa_id')
    q = request.GET.get('q', '').strip()
    grupos = Grupo.objects.filter(empresa_id=empresa_id).select_related('idgrupopai')
    if q:
        grupos = grupos.filter(
            Q(descricao__icontains=q) | Q(classificacao__icontains=q)
        )
    grupos = grupos.order_by('descricao')[:100]
    return render(request, 'cadastros/partials/tabela_grupos.html', {'grupos': grupos})


@modulo_required('acesso_cadastro')
def grupo_create(request):
    empresa_id = request.session.get('empresa_id')
    if request.method == 'POST':
        form = GrupoForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.empresa_id = empresa_id
            obj.save()
            messages.success(request, f'Grupo "{obj}" salvo com sucesso.')
            if 'salvar_novo' in request.POST:
                return redirect('cadastros:grupo_create')
            return redirect('cadastros:grupo_list')
    else:
        form = GrupoForm()
    return render(request, 'cadastros/grupo_form.html', {
        'form': form, 'titulo': 'Novo Grupo', 'objeto': None,
    })


@modulo_required('acesso_cadastro')
def grupo_edit(request, pk):
    empresa_id = request.session.get('empresa_id')
    obj = get_object_or_404(Grupo, pk=pk, empresa_id=empresa_id)
    if request.method == 'POST':
        form = GrupoForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, f'Grupo "{obj}" atualizado.')
            return redirect('cadastros:grupo_list')
    else:
        form = GrupoForm(instance=obj)
    return render(request, 'cadastros/grupo_form.html', {
        'form': form, 'titulo': f'Editar — {obj}', 'objeto': obj,
    })


@modulo_required('acesso_cadastro')
def grupo_inativar(request, pk):
    empresa_id = request.session.get('empresa_id')
    obj = get_object_or_404(Grupo, pk=pk, empresa_id=empresa_id)
    if request.method == 'POST':
        obj.inativo = not obj.inativo
        obj.save(update_fields=['inativo'])
    return render(request, 'cadastros/partials/linha_grupo.html', {'g': obj})


# ── Itens ────────────────────────────────────────────────────

@modulo_required('acesso_cadastro')
def item_list(request):
    empresa_id = request.session.get('empresa_id')
    itens = Item.objects.filter(empresa_id=empresa_id).select_related('grupo').order_by('descricao')
    grupos = Grupo.objects.filter(empresa_id=empresa_id, inativo=False).order_by('descricao')
    return render(request, 'cadastros/item_list.html', {'itens': itens, 'grupos': grupos})


@modulo_required('acesso_cadastro')
def item_buscar(request):
    empresa_id = request.session.get('empresa_id')
    q = request.GET.get('q', '').strip()
    grupo_pk = request.GET.get('grupo', '').strip()
    itens = Item.objects.filter(empresa_id=empresa_id).select_related('grupo')
    if q:
        itens = itens.filter(
            Q(descricao__icontains=q) |
            Q(identificacao__icontains=q) |
            Q(modelo__icontains=q) |
            Q(codforn__icontains=q)
        )
    if grupo_pk:
        itens = itens.filter(grupo__pk=grupo_pk)
    itens = itens.order_by('descricao')[:100]
    return render(request, 'cadastros/partials/tabela_itens.html', {'itens': itens})


@modulo_required('acesso_cadastro')
def item_create(request):
    empresa_id = request.session.get('empresa_id')
    if request.method == 'POST':
        form = ItemForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.empresa_id = empresa_id
            obj.save()
            messages.success(request, f'Item "{obj}" salvo com sucesso.')
            if 'salvar_novo' in request.POST:
                return redirect('cadastros:item_create')
            return redirect('cadastros:item_list')
    else:
        form = ItemForm()
    return render(request, 'cadastros/item_form.html', {
        'form': form, 'titulo': 'Novo Item', 'objeto': None,
    })


@modulo_required('acesso_cadastro')
def item_edit(request, pk):
    empresa_id = request.session.get('empresa_id')
    obj = get_object_or_404(Item, pk=pk, empresa_id=empresa_id)
    if request.method == 'POST':
        form = ItemForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, f'Item "{obj}" atualizado.')
            return redirect('cadastros:item_list')
    else:
        form = ItemForm(instance=obj)
    return render(request, 'cadastros/item_form.html', {
        'form': form, 'titulo': f'Editar — {obj}', 'objeto': obj,
    })


@modulo_required('acesso_cadastro')
def item_inativar(request, pk):
    empresa_id = request.session.get('empresa_id')
    obj = get_object_or_404(Item, pk=pk, empresa_id=empresa_id)
    if request.method == 'POST':
        obj.inativo = not obj.inativo
        obj.save(update_fields=['inativo'])
    return render(request, 'cadastros/partials/linha_item.html', {'i': obj})


# ── Portadores ───────────────────────────────────────────────

@modulo_required('acesso_cadastro')
def portador_list(request):
    empresa_id = request.session.get('empresa_id')
    portadores = Portador.objects.filter(empresa_id=empresa_id).order_by('descricao')
    return render(request, 'cadastros/portador_list.html', {'portadores': portadores})


@modulo_required('acesso_cadastro')
def portador_buscar(request):
    empresa_id = request.session.get('empresa_id')
    q = request.GET.get('q', '').strip()
    portadores = Portador.objects.filter(empresa_id=empresa_id)
    if q:
        portadores = portadores.filter(descricao__icontains=q)
    portadores = portadores.order_by('descricao')[:100]
    return render(request, 'cadastros/partials/tabela_portadores.html', {'portadores': portadores})


@modulo_required('acesso_cadastro')
def portador_create(request):
    empresa_id = request.session.get('empresa_id')
    if request.method == 'POST':
        form = PortadorForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.empresa_id = empresa_id
            obj.save()
            messages.success(request, f'Portador "{obj}" salvo com sucesso.')
            if 'salvar_novo' in request.POST:
                return redirect('cadastros:portador_create')
            return redirect('cadastros:portador_list')
    else:
        form = PortadorForm()
    return render(request, 'cadastros/portador_form.html', {
        'form': form, 'titulo': 'Novo Portador', 'objeto': None,
    })


@modulo_required('acesso_cadastro')
def portador_edit(request, pk):
    empresa_id = request.session.get('empresa_id')
    obj = get_object_or_404(Portador, pk=pk, empresa_id=empresa_id)
    if request.method == 'POST':
        form = PortadorForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, f'Portador "{obj}" atualizado.')
            return redirect('cadastros:portador_list')
    else:
        form = PortadorForm(instance=obj)
    return render(request, 'cadastros/portador_form.html', {
        'form': form, 'titulo': f'Editar — {obj}', 'objeto': obj,
    })


@modulo_required('acesso_cadastro')
def portador_inativar(request, pk):
    empresa_id = request.session.get('empresa_id')
    obj = get_object_or_404(Portador, pk=pk, empresa_id=empresa_id)
    if request.method == 'POST':
        obj.inativo = not obj.inativo
        obj.save(update_fields=['inativo'])
    return render(request, 'cadastros/partials/linha_portador.html', {'p': obj})


# ── Métodos de Pagamento ─────────────────────────────────────

@modulo_required('acesso_cadastro')
def metodo_list(request):
    empresa_id = request.session.get('empresa_id')
    metodos = Metodo.objects.filter(empresa_id=empresa_id).order_by('descricao')
    return render(request, 'cadastros/metodo_list.html', {'metodos': metodos})


@modulo_required('acesso_cadastro')
def metodo_buscar(request):
    empresa_id = request.session.get('empresa_id')
    q = request.GET.get('q', '').strip()
    metodos = Metodo.objects.filter(empresa_id=empresa_id)
    if q:
        metodos = metodos.filter(
            Q(descricao__icontains=q) | Q(sigla__icontains=q)
        )
    metodos = metodos.order_by('descricao')[:100]
    return render(request, 'cadastros/partials/tabela_metodos.html', {'metodos': metodos})


@modulo_required('acesso_cadastro')
def metodo_create(request):
    empresa_id = request.session.get('empresa_id')
    if request.method == 'POST':
        form = MetodoForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.empresa_id = empresa_id
            obj.save()
            messages.success(request, f'Método "{obj}" salvo com sucesso.')
            if 'salvar_novo' in request.POST:
                return redirect('cadastros:metodo_create')
            return redirect('cadastros:metodo_list')
    else:
        form = MetodoForm(initial={'movcaixa': True})
    return render(request, 'cadastros/metodo_form.html', {
        'form': form, 'titulo': 'Novo Método de Pagamento', 'objeto': None,
    })


@modulo_required('acesso_cadastro')
def metodo_edit(request, pk):
    empresa_id = request.session.get('empresa_id')
    obj = get_object_or_404(Metodo, pk=pk, empresa_id=empresa_id)
    if request.method == 'POST':
        form = MetodoForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, f'Método "{obj}" atualizado.')
            return redirect('cadastros:metodo_list')
    else:
        form = MetodoForm(instance=obj)
    return render(request, 'cadastros/metodo_form.html', {
        'form': form, 'titulo': f'Editar — {obj}', 'objeto': obj,
    })


@modulo_required('acesso_cadastro')
def metodo_inativar(request, pk):
    empresa_id = request.session.get('empresa_id')
    obj = get_object_or_404(Metodo, pk=pk, empresa_id=empresa_id)
    if request.method == 'POST':
        obj.inativo = not obj.inativo
        obj.save(update_fields=['inativo'])
    return render(request, 'cadastros/partials/linha_metodo.html', {'m': obj})


@modulo_required('acesso_cadastro')
def item_lookup(request):
    """Autocomplete de itens — HTML (HTMX) ou JSON (Alpine.js fetch).
    Parâmetro opcional ?controla_estoque=1 limita aos itens com estoque controlado.
    """
    empresa_id = request.session.get('empresa_id')
    q = request.GET.get('q', '').strip()
    qs = Item.objects.filter(empresa_id=empresa_id, inativo=False)
    if request.GET.get('controla_estoque') == '1':
        qs = qs.filter(controla_estoque=True)
    itens = (qs.filter(
        Q(descricao__icontains=q) | Q(identificacao__icontains=q)
    ).order_by('descricao')[:15]) if q else []

    if request.GET.get('formato') == 'json':
        data = [{'id': it.pk, 'descricao': it.descricao,
                 'identificacao': it.identificacao,
                 'tipo_item': it.tipo_item,
                 'saldoestoque': float(it.saldoestoque)} for it in itens]
        return JsonResponse(data, safe=False)

    return render(request, 'cadastros/partials/lookup_item.html', {'itens': itens})


# ── Tabela de Preço ───────────────────────────────────────────────────────────

@modulo_required('acesso_cadastro')
def tabela_list(request):
    empresa_id = request.session.get('empresa_id')
    tabelas = TabelaPreco.objects.filter(empresa_id=empresa_id)
    return render(request, 'cadastros/tabela_list.html', {'tabelas': tabelas})


@modulo_required('acesso_cadastro')
def tabela_buscar(request):
    empresa_id = request.session.get('empresa_id')
    q = request.GET.get('q', '').strip()
    qs = TabelaPreco.objects.filter(empresa_id=empresa_id)
    if q:
        qs = qs.filter(descricao__icontains=q)
    return render(request, 'cadastros/partials/tabela_tabelas.html', {'tabelas': qs.order_by('descricao')})


@modulo_required('acesso_cadastro')
def tabela_create(request):
    empresa_id = request.session.get('empresa_id')
    if request.method == 'POST':
        form = TabelaPrecoForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.empresa_id = empresa_id
            obj.save()
            messages.success(request, f'Tabela "{obj.descricao}" criada.')
            return redirect('cadastros:tabela_detalhe', pk=obj.pk)
    else:
        form = TabelaPrecoForm()
    return render(request, 'cadastros/tabela_form.html', {'form': form, 'objeto': None})


@modulo_required('acesso_cadastro')
def tabela_detalhe(request, pk):
    empresa_id = request.session.get('empresa_id')
    tabela = get_object_or_404(TabelaPreco, pk=pk, empresa_id=empresa_id)
    if request.method == 'POST':
        form = TabelaPrecoForm(request.POST, instance=tabela)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tabela atualizada.')
            return redirect('cadastros:tabela_detalhe', pk=pk)
    else:
        form = TabelaPrecoForm(instance=tabela)

    itens_qs  = tabela.itens.select_related('item').order_by('item__descricao')
    # Resolve valores de parcela para o template (evita filtros custom)
    itens = []
    for it in itens_qs:
        precos_dict = {f: getattr(it, f) for f, _ in PARCELAS_FIELDS}
        # JSON-safe string para o Alpine.js no botão editar
        edit_json = json.dumps({
            'item_id':      it.item_id,
            'identificacao': it.identificacao,
            'preco':        str(it.preco),
            'basecomissao': str(it.basecomissao),
            **{f: str(getattr(it, f)) for f, _ in PARCELAS_FIELDS},
        })
        itens.append({
            'obj':       it,
            'precos':    list(precos_dict.values()),
            'edit_json': edit_json,
        })
    form_item = ItemTabelaPrecoForm()
    return render(request, 'cadastros/tabela_detalhe.html', {
        'tabela':    tabela,
        'form':      form,
        'itens':     itens,
        'form_item': form_item,
        'parcelas':  PARCELAS_FIELDS,
        'total_itens': len(itens),
    })


@modulo_required('acesso_cadastro')
def tabela_item_salvar(request, tabela_pk):
    tabela  = get_object_or_404(TabelaPreco, pk=tabela_pk)
    item_pk = request.POST.get('item_pk')

    if item_pk:
        obj  = get_object_or_404(ItemTabelaPreco, pk=item_pk, tabela=tabela)
        form = ItemTabelaPrecoForm(request.POST, instance=obj)
        acao = 'atualizado'
    else:
        form = ItemTabelaPrecoForm(request.POST)
        acao = 'adicionado'

    if form.is_valid():
        it        = form.save(commit=False)
        it.tabela = tabela
        it.save()
        messages.success(request, f'Item {acao}.')
    else:
        messages.error(request, 'Verifique os dados do item.')

    return redirect('cadastros:tabela_detalhe', pk=tabela_pk)


@modulo_required('acesso_cadastro')
def tabela_item_excluir(request, pk):
    it        = get_object_or_404(ItemTabelaPreco, pk=pk)
    tabela_pk = it.tabela_id
    if request.method == 'POST':
        it.delete()
        messages.success(request, 'Item removido.')
    return redirect('cadastros:tabela_detalhe', pk=tabela_pk)


def tabela_item_lookup(request):
    """JSON — retorna preço para (tabela, item, parcelas). Consumido por OS/Pedido."""
    tabela_pk = request.GET.get('tabela')
    item_pk   = request.GET.get('item')
    parcelas  = int(request.GET.get('parcelas', 1))

    PARCELA_MAP = {i + 1: f for i, (f, _) in enumerate(PARCELAS_FIELDS)}
    campo = PARCELA_MAP.get(parcelas, 'i_pagto')

    try:
        it    = ItemTabelaPreco.objects.get(tabela_id=tabela_pk, item_id=item_pk)
        preco = float(getattr(it, campo) or it.preco)
        return JsonResponse({
            'preco':        preco,
            'basecomissao': float(it.basecomissao),
            'identificacao': it.identificacao,
        })
    except ItemTabelaPreco.DoesNotExist:
        return JsonResponse({'preco': 0, 'basecomissao': 0, 'identificacao': ''})

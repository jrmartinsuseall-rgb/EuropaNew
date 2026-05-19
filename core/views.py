import hmac, hashlib, base64, secrets
from datetime import date
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import (
    authenticate, login, logout,
    update_session_auth_hash,
)
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.views.decorators.http import require_POST

from .models import PerfilUsuario, Cidade, Banco, Cfop, Empresa, ConfiguracaoCaixa, Projeto, ProjetoOrcamento, Licenca
from .forms import (
    LoginForm, EmpresaSelecaoForm, UsuarioForm, PerfilUsuarioForm, TrocaSenhaForm,
    CidadeForm, BancoForm, CfopForm, EmpresaForm,
    PlanoContaForm, SubContaForm, ConfiguracaoCaixaForm, ProjetoForm, LicencaForm,
)
from financeiro.models import PlanoConta, SubConta
from .decorators import modulo_required, admin_required


# ── Home ────────────────────────────────────────────────────

@login_required
def home_view(request):
    return render(request, 'core/home.html')


# ── Login / Logout ──────────────────────────────────────────

def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    form = LoginForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        login(request, user)

        if not user.is_superuser:
            # Usuário comum: empresa definida no perfil
            try:
                if user.perfil.empresa_id:
                    request.session['empresa_id'] = user.perfil.empresa_id
                # Inicia contagem de expiração de senha no primeiro acesso
                if user.perfil.password_changed_at is None:
                    user.perfil.password_changed_at = date.today()
                    user.perfil.save(update_fields=['password_changed_at'])
            except Exception:
                pass

        # Superusuário sem empresa na sessão → tela de seleção pós-login
        next_url = request.GET.get('next') or 'home'
        return redirect(next_url)

    return render(request, 'login.html', {'form': form})


@login_required
def selecionar_empresa(request):
    """Tela pós-login para superusuários escolherem a empresa de trabalho."""
    if not request.user.is_superuser:
        return redirect('home')

    if request.method == 'POST':
        form = EmpresaSelecaoForm(request.POST)
        if form.is_valid():
            empresa = form.cleaned_data['empresa']
            request.session['empresa_id'] = empresa.pk
            return redirect('home')
    else:
        # Pré-seleciona a empresa atual se já houver uma na sessão
        empresa_id = request.session.get('empresa_id')
        form = EmpresaSelecaoForm(initial={'empresa': empresa_id})

    return render(request, 'core/selecionar_empresa.html', {'form': form})


@require_POST
def logout_view(request):
    logout(request)
    return redirect('core:login')


# ── Usuários — CRUD ─────────────────────────────────────────

@login_required
def usuario_list(request):
    if not request.user.is_superuser:
        try:
            if request.user.perfil.nivel_adm < 9:
                messages.error(request, 'Acesso negado.')
                return redirect('home')
        except Exception:
            messages.error(request, 'Acesso negado.')
            return redirect('home')

    usuarios = User.objects.select_related('perfil').order_by('username')
    return render(request, 'core/usuario_list.html', {'usuarios': usuarios})


@login_required
def usuario_create(request):
    if not request.user.is_superuser:
        try:
            if request.user.perfil.nivel_adm < 9:
                messages.error(request, 'Acesso negado.')
                return redirect('home')
        except Exception:
            messages.error(request, 'Acesso negado.')
            return redirect('home')

    if request.method == 'POST':
        user_form = UsuarioForm(request.POST)
        perfil_form = PerfilUsuarioForm(request.POST)
        if user_form.is_valid() and perfil_form.is_valid():
            user = user_form.save()
            # O signal já criou o PerfilUsuario; basta atualizar
            perfil = user.perfil
            for field in perfil_form.cleaned_data:
                setattr(perfil, field, perfil_form.cleaned_data[field])
            perfil.save()
            messages.success(request, f'Usuário "{user.username}" criado com sucesso.')
            return redirect('core:usuario_list')
    else:
        user_form = UsuarioForm()
        perfil_form = PerfilUsuarioForm()

    return render(request, 'core/usuario_form.html', {
        'user_form': user_form,
        'perfil_form': perfil_form,
        'titulo': 'Novo Usuário',
        'objeto': None,
    })


@login_required
def usuario_edit(request, pk):
    if not request.user.is_superuser:
        try:
            if request.user.perfil.nivel_adm < 9:
                messages.error(request, 'Acesso negado.')
                return redirect('home')
        except Exception:
            messages.error(request, 'Acesso negado.')
            return redirect('home')

    obj = get_object_or_404(User, pk=pk)
    perfil, _ = PerfilUsuario.objects.get_or_create(usuario=obj)

    if request.method == 'POST':
        user_form = UsuarioForm(request.POST, instance=obj)
        perfil_form = PerfilUsuarioForm(request.POST, instance=perfil)
        if user_form.is_valid() and perfil_form.is_valid():
            user_form.save()
            perfil_form.save()
            messages.success(request, f'Usuário "{obj.username}" atualizado.')
            return redirect('core:usuario_list')
    else:
        user_form = UsuarioForm(instance=obj)
        perfil_form = PerfilUsuarioForm(instance=perfil)

    return render(request, 'core/usuario_form.html', {
        'user_form': user_form,
        'perfil_form': perfil_form,
        'titulo': f'Editar — {obj.username}',
        'objeto': obj,
    })


# ── Troca de Senha ──────────────────────────────────────────

@login_required
def trocar_senha(request):
    senha_expirada = request.GET.get('expired') == '1'
    if request.method == 'POST':
        form = TrocaSenhaForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            try:
                perfil = user.perfil
                perfil.password_changed_at = date.today()
                perfil.save(update_fields=['password_changed_at'])
            except Exception:
                pass
            messages.success(request, 'Senha alterada com sucesso.')
            return redirect('home')
    else:
        form = TrocaSenhaForm(request.user)

    return render(request, 'core/senha_form.html', {
        'form': form,
        'senha_expirada': senha_expirada,
    })


# ── Cidades ─────────────────────────────────────────────────

@admin_required
def cidade_list(request):
    cidades = Cidade.objects.order_by('descricao')
    return render(request, 'core/cidade_list.html', {'cidades': cidades})


@admin_required
def cidade_buscar(request):
    q = request.GET.get('q', '').strip()
    uf = request.GET.get('uf', '').strip()
    cidades = Cidade.objects.all()
    if q:
        cidades = cidades.filter(
            Q(descricao__icontains=q) | Q(codibge__icontains=q)
        )
    if uf:
        cidades = cidades.filter(uf__iexact=uf)
    cidades = cidades.order_by('descricao')[:100]
    return render(request, 'core/partials/tabela_cidades.html', {'cidades': cidades})


@admin_required
def cidade_create(request):
    if request.method == 'POST':
        form = CidadeForm(request.POST)
        if form.is_valid():
            obj = form.save()
            messages.success(request, f'Cidade "{obj}" salva com sucesso.')
            if 'salvar_novo' in request.POST:
                return redirect('core:cidade_create')
            return redirect('core:cidade_list')
    else:
        form = CidadeForm()
    return render(request, 'core/cidade_form.html', {
        'form': form, 'titulo': 'Nova Cidade', 'objeto': None,
    })


@admin_required
def cidade_edit(request, pk):
    obj = get_object_or_404(Cidade, pk=pk)
    if request.method == 'POST':
        form = CidadeForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, f'Cidade "{obj}" atualizada.')
            return redirect('core:cidade_list')
    else:
        form = CidadeForm(instance=obj)
    return render(request, 'core/cidade_form.html', {
        'form': form, 'titulo': f'Editar — {obj}', 'objeto': obj,
    })


@admin_required
def cidade_inativar(request, pk):
    obj = get_object_or_404(Cidade, pk=pk)
    if request.method == 'POST':
        obj.inativo = not obj.inativo
        obj.save(update_fields=['inativo'])
    return render(request, 'core/partials/linha_cidade.html', {'c': obj})


# ── Bancos ───────────────────────────────────────────────────

@admin_required
def banco_list(request):
    bancos = Banco.objects.order_by('descricao')
    return render(request, 'core/banco_list.html', {'bancos': bancos})


@admin_required
def banco_buscar(request):
    q = request.GET.get('q', '').strip()
    bancos = Banco.objects.all()
    if q:
        bancos = bancos.filter(
            Q(descricao__icontains=q) | Q(numero__icontains=q)
        )
    bancos = bancos.order_by('descricao')[:50]
    return render(request, 'core/partials/tabela_bancos.html', {'bancos': bancos})


@admin_required
def banco_create(request):
    if request.method == 'POST':
        form = BancoForm(request.POST)
        if form.is_valid():
            obj = form.save()
            messages.success(request, f'Banco "{obj}" salvo com sucesso.')
            if 'salvar_novo' in request.POST:
                return redirect('core:banco_create')
            return redirect('core:banco_list')
    else:
        form = BancoForm()
    return render(request, 'core/banco_form.html', {
        'form': form, 'titulo': 'Novo Banco', 'objeto': None,
    })


@admin_required
def banco_edit(request, pk):
    obj = get_object_or_404(Banco, pk=pk)
    if request.method == 'POST':
        form = BancoForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, f'Banco "{obj}" atualizado.')
            return redirect('core:banco_list')
    else:
        form = BancoForm(instance=obj)
    return render(request, 'core/banco_form.html', {
        'form': form, 'titulo': f'Editar — {obj}', 'objeto': obj,
    })


@admin_required
def banco_inativar(request, pk):
    obj = get_object_or_404(Banco, pk=pk)
    if request.method == 'POST':
        obj.inativo = not obj.inativo
        obj.save(update_fields=['inativo'])
    return render(request, 'core/partials/linha_banco.html', {'b': obj})


# ── CFOP ─────────────────────────────────────────────────────

@admin_required
def cfop_list(request):
    cfops = Cfop.objects.order_by('descricao')
    return render(request, 'core/cfop_list.html', {'cfops': cfops})


@admin_required
def cfop_buscar(request):
    q = request.GET.get('q', '').strip()
    tipo = request.GET.get('tipo', '').strip()
    cfops = Cfop.objects.all()
    if q:
        cfops = cfops.filter(
            Q(descricao__icontains=q) | Q(observacao__icontains=q)
        )
    if tipo:
        cfops = cfops.filter(tipo=tipo)
    cfops = cfops.order_by('descricao')[:100]
    return render(request, 'core/partials/tabela_cfop.html', {'cfops': cfops})


@admin_required
def cfop_create(request):
    if request.method == 'POST':
        form = CfopForm(request.POST)
        if form.is_valid():
            obj = form.save()
            messages.success(request, f'CFOP "{obj}" salvo com sucesso.')
            if 'salvar_novo' in request.POST:
                return redirect('core:cfop_create')
            return redirect('core:cfop_list')
    else:
        form = CfopForm()
    return render(request, 'core/cfop_form.html', {
        'form': form, 'titulo': 'Novo CFOP', 'objeto': None,
    })


@admin_required
def cfop_edit(request, pk):
    obj = get_object_or_404(Cfop, pk=pk)
    if request.method == 'POST':
        form = CfopForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, f'CFOP "{obj}" atualizado.')
            return redirect('core:cfop_list')
    else:
        form = CfopForm(instance=obj)
    return render(request, 'core/cfop_form.html', {
        'form': form, 'titulo': f'Editar — {obj}', 'objeto': obj,
    })


@admin_required
def cfop_inativar(request, pk):
    obj = get_object_or_404(Cfop, pk=pk)
    if request.method == 'POST':
        obj.inativo = not obj.inativo
        obj.save(update_fields=['inativo'])
    return render(request, 'core/partials/linha_cfop.html', {'c': obj})


# ── Plano de Contas ──────────────────────────────────────────

@admin_required
def planoconta_list(request):
    empresa_id = request.session.get('empresa_id')
    contas = PlanoConta.objects.filter(empresa_id=empresa_id).order_by('descricao')
    return render(request, 'core/planoconta_list.html', {'contas': contas})


@admin_required
def planoconta_buscar(request):
    empresa_id = request.session.get('empresa_id')
    q = request.GET.get('q', '').strip()
    contas = PlanoConta.objects.filter(empresa_id=empresa_id)
    if q:
        contas = contas.filter(
            Q(descricao__icontains=q) | Q(descrigrupo__icontains=q)
        )
    contas = contas.order_by('descricao')[:100]
    return render(request, 'core/partials/tabela_planocontas.html', {'contas': contas})


@admin_required
def planoconta_create(request):
    empresa_id = request.session.get('empresa_id')
    if request.method == 'POST':
        form = PlanoContaForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.empresa_id = empresa_id
            obj.save()
            messages.success(request, f'Conta "{obj}" salva com sucesso.')
            if 'salvar_novo' in request.POST:
                return redirect('core:planoconta_create')
            return redirect('core:planoconta_list')
    else:
        form = PlanoContaForm()
    return render(request, 'core/planoconta_form.html', {
        'form': form, 'titulo': 'Nova Conta', 'objeto': None,
    })


@admin_required
def planoconta_edit(request, pk):
    empresa_id = request.session.get('empresa_id')
    obj = get_object_or_404(PlanoConta, pk=pk, empresa_id=empresa_id)
    if request.method == 'POST':
        form = PlanoContaForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, f'Conta "{obj}" atualizada.')
            return redirect('core:planoconta_list')
    else:
        form = PlanoContaForm(instance=obj)
    return render(request, 'core/planoconta_form.html', {
        'form': form, 'titulo': f'Editar — {obj}', 'objeto': obj,
    })


@admin_required
def planoconta_inativar(request, pk):
    empresa_id = request.session.get('empresa_id')
    obj = get_object_or_404(PlanoConta, pk=pk, empresa_id=empresa_id)
    if request.method == 'POST':
        obj.inativo = not obj.inativo
        obj.save(update_fields=['inativo'])
    return render(request, 'core/partials/linha_planoconta.html', {'c': obj})


# ── Sub-Contas ────────────────────────────────────────────────

@admin_required
def subconta_list(request):
    empresa_id = request.session.get('empresa_id')
    subcontas = SubConta.objects.filter(empresa_id=empresa_id).select_related('conta').order_by('conta__descricao', 'descricao')
    contas = PlanoConta.objects.filter(empresa_id=empresa_id, inativo=False).order_by('descricao')
    return render(request, 'core/subconta_list.html', {
        'subcontas': subcontas, 'contas': contas,
    })


@admin_required
def subconta_buscar(request):
    empresa_id = request.session.get('empresa_id')
    q = request.GET.get('q', '').strip()
    conta_pk = request.GET.get('conta', '').strip()
    subcontas = SubConta.objects.filter(empresa_id=empresa_id).select_related('conta')
    if q:
        subcontas = subcontas.filter(
            Q(descricao__icontains=q) | Q(conta__descricao__icontains=q)
        )
    if conta_pk:
        subcontas = subcontas.filter(conta__pk=conta_pk)
    subcontas = subcontas.order_by('conta__descricao', 'descricao')[:100]
    return render(request, 'core/partials/tabela_subcontas.html', {'subcontas': subcontas})


@admin_required
def subconta_create(request):
    empresa_id = request.session.get('empresa_id')
    if request.method == 'POST':
        form = SubContaForm(request.POST, empresa_id=empresa_id)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.empresa_id = empresa_id
            obj.save()
            messages.success(request, f'Sub-conta "{obj.descricao}" salva com sucesso.')
            if 'salvar_novo' in request.POST:
                return redirect('core:subconta_create')
            return redirect('core:subconta_list')
    else:
        form = SubContaForm(empresa_id=empresa_id)
    return render(request, 'core/subconta_form.html', {
        'form': form, 'titulo': 'Nova Sub-Conta', 'objeto': None,
    })


@admin_required
def subconta_edit(request, pk):
    empresa_id = request.session.get('empresa_id')
    obj = get_object_or_404(SubConta, pk=pk, empresa_id=empresa_id)
    if request.method == 'POST':
        form = SubContaForm(request.POST, instance=obj, empresa_id=empresa_id)
        if form.is_valid():
            form.save()
            messages.success(request, f'Sub-conta "{obj.descricao}" atualizada.')
            return redirect('core:subconta_list')
    else:
        form = SubContaForm(instance=obj, empresa_id=empresa_id)
    return render(request, 'core/subconta_form.html', {
        'form': form, 'titulo': f'Editar — {obj.descricao}', 'objeto': obj,
    })


@admin_required
def subconta_inativar(request, pk):
    empresa_id = request.session.get('empresa_id')
    obj = get_object_or_404(SubConta, pk=pk, empresa_id=empresa_id)
    if request.method == 'POST':
        obj.inativo = not obj.inativo
        obj.save(update_fields=['inativo'])
    return render(request, 'core/partials/linha_subconta.html', {'s': obj})


# ── Empresa ──────────────────────────────────────────────────

@admin_required
def empresa_edit(request):
    empresa_id = request.session.get('empresa_id')
    obj = get_object_or_404(Empresa, pk=empresa_id)
    if request.method == 'POST':
        form = EmpresaForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Dados da empresa salvos.')
            return redirect('core:empresa_edit')
    else:
        form = EmpresaForm(instance=obj)
    return render(request, 'core/empresa_form.html', {'form': form, 'objeto': obj})


# ── Configuração de Caixa ────────────────────────────────────

@admin_required
def cfgcaixa_edit(request):
    empresa_id = request.session.get('empresa_id')
    obj, _ = ConfiguracaoCaixa.objects.get_or_create(empresa_id=empresa_id)
    if request.method == 'POST':
        form = ConfiguracaoCaixaForm(request.POST, instance=obj, empresa_id=empresa_id)
        if form.is_valid():
            form.save()
            messages.success(request, 'Configurações de Caixa salvas com sucesso.')
            return redirect('core:cfgcaixa_edit')
    else:
        form = ConfiguracaoCaixaForm(instance=obj, empresa_id=empresa_id)
    return render(request, 'core/cfgcaixa_form.html', {'form': form})


# ── Projetos ─────────────────────────────────────────────────

@admin_required
def projeto_list(request):
    empresa_id = request.session.get('empresa_id')
    projetos = Projeto.objects.filter(empresa_id=empresa_id).order_by('codigo')
    return render(request, 'core/projeto_list.html', {'projetos': projetos})


@admin_required
def projeto_buscar(request):
    empresa_id = request.session.get('empresa_id')
    q = request.GET.get('q', '').strip()
    qs = Projeto.objects.filter(empresa_id=empresa_id)
    if q:
        qs = qs.filter(Q(codigo__icontains=q) | Q(descricao__icontains=q))
    qs = qs.order_by('codigo')[:50]
    return render(request, 'core/partials/tabela_projetos.html', {'projetos': qs})


@admin_required
def projeto_create(request):
    empresa_id = request.session.get('empresa_id')
    if request.method == 'POST':
        form = ProjetoForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.empresa_id = empresa_id
            obj.save()
            messages.success(request, f'Projeto "{obj}" salvo com sucesso.')
            if 'salvar_novo' in request.POST:
                return redirect('core:projeto_create')
            return redirect('core:projeto_list')
    else:
        form = ProjetoForm()
    return render(request, 'core/projeto_form.html', {
        'form': form, 'titulo': 'Novo Projeto', 'objeto': None,
    })


@admin_required
def projeto_edit(request, pk):
    empresa_id = request.session.get('empresa_id')
    obj = get_object_or_404(Projeto, pk=pk, empresa_id=empresa_id)
    if request.method == 'POST':
        form = ProjetoForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, f'Projeto "{obj}" atualizado.')
            return redirect('core:projeto_list')
    else:
        form = ProjetoForm(instance=obj)
    return render(request, 'core/projeto_form.html', {
        'form': form, 'titulo': f'Editar — {obj}', 'objeto': obj,
    })


@admin_required
def projeto_inativar(request, pk):
    empresa_id = request.session.get('empresa_id')
    obj = get_object_or_404(Projeto, pk=pk, empresa_id=empresa_id)
    if request.method == 'POST':
        obj.inativo = not obj.inativo
        obj.save(update_fields=['inativo'])
    return render(request, 'core/partials/linha_projeto.html', {'p': obj})


# ── Licenças ─────────────────────────────────────────────────

def _license_secret():
    from django.conf import settings
    return getattr(settings, 'LICENSE_SECRET_KEY', 'insecure-default-key').encode()


def _gerar_chave(cnpj: str, valid_until: str, max_usuarios: int) -> str:
    cnpj_digits = ''.join(c for c in cnpj if c.isdigit())
    nonce = secrets.token_hex(8)
    payload_str = f"{cnpj_digits}|{valid_until}|{max_usuarios}|{nonce}"
    payload_b64 = base64.urlsafe_b64encode(payload_str.encode()).decode().rstrip('=')
    sig = hmac.new(_license_secret(), payload_b64.encode(), hashlib.sha256).hexdigest()
    return f"{payload_b64}.{sig}"


def licenca_bloqueada(request):
    return render(request, 'core/licenca_bloqueada.html', {}, status=403)


@login_required
def licenca_list(request):
    if not request.user.is_superuser:
        messages.error(request, 'Acesso negado.')
        return redirect('home')
    empresas = Empresa.objects.filter(inativo=False).prefetch_related('licenca').order_by('razao')
    lista = []
    for emp in empresas:
        try:
            lic = emp.licenca
        except Licenca.DoesNotExist:
            lic = None
        lista.append({'empresa': emp, 'licenca': lic})
    return render(request, 'core/licenca_list.html', {'lista': lista})


@login_required
def licenca_edit(request, pk):
    if not request.user.is_superuser:
        messages.error(request, 'Acesso negado.')
        return redirect('home')
    empresa = get_object_or_404(Empresa, pk=pk)
    try:
        obj = empresa.licenca
    except Licenca.DoesNotExist:
        obj = None

    chave_gerada = None

    if request.method == 'POST':
        form = LicencaForm(request.POST, instance=obj)
        if form.is_valid():
            lic = form.save(commit=False)
            lic.empresa = empresa
            chave = _gerar_chave(
                empresa.cnpj,
                lic.valid_until.isoformat(),
                lic.max_usuarios,
            )
            lic.chave = chave
            lic.save()
            chave_gerada = chave
            messages.success(request, f'Licença para "{empresa.razao}" salva. Copie a chave abaixo.')
    else:
        form = LicencaForm(instance=obj)

    return render(request, 'core/licenca_form.html', {
        'form': form,
        'empresa': empresa,
        'licenca': obj,
        'chave_gerada': chave_gerada,
    })


@login_required
def licenca_regenerar(request, pk):
    """Regenera a chave mantendo os parâmetros da licença existente."""
    if not request.user.is_superuser:
        messages.error(request, 'Acesso negado.')
        return redirect('home')
    if request.method != 'POST':
        return redirect('core:licenca_edit', pk=pk)
    empresa = get_object_or_404(Empresa, pk=pk)
    try:
        lic = empresa.licenca
    except Licenca.DoesNotExist:
        messages.error(request, 'Nenhuma licença cadastrada para esta empresa.')
        return redirect('core:licenca_edit', pk=pk)

    chave = _gerar_chave(empresa.cnpj, lic.valid_until.isoformat(), lic.max_usuarios)
    lic.chave = chave
    lic.save(update_fields=['chave', 'atualizado_em'])
    messages.success(request, 'Chave de licença regenerada com sucesso.')
    return redirect('core:licenca_edit', pk=pk)


def _realizado_por_conta(projeto, empresa_id, mes, ano):
    """Retorna dict {conta_id: valor_realizado} para o projeto/período."""
    from financeiro.models import MovimentoCaixa
    from django.db.models import Sum, Case, When, DecimalField as Df
    _SEM_PROJ = {'ABERTURA', 'FECHAMENTO', 'REABERTURA'}
    qs = (MovimentoCaixa.objects
          .filter(
              empresa_id=empresa_id,
              projeto=projeto,
              data__year=ano,
              data__month=mes,
              status='A',
          )
          .exclude(tipobaixa__in=_SEM_PROJ)
          .values('conta_id')
          .annotate(
              total_entrada=Sum(Case(When(tipo='E', then='valor'),
                                    default=0, output_field=Df())),
              total_saida=Sum(Case(When(tipo='S', then='valor'),
                                   default=0, output_field=Df())),
          ))
    resultado = {}
    for row in qs:
        resultado[row['conta_id']] = {
            'entrada': row['total_entrada'] or Decimal('0.00'),
            'saida':   row['total_saida']   or Decimal('0.00'),
        }
    return resultado


def _monta_linhas(contas, valores_orc, realizado):
    """Combina orçamento + realizado em lista de dicts para o template."""
    zero = Decimal('0.00')
    linhas = []
    for c in contas:
        estimado = valores_orc.get(c.pk, zero)
        mov      = realizado.get(c.pk, {})
        if c.deb_cred == 'C':
            realiz = mov.get('entrada', zero)
        elif c.deb_cred == 'D':
            realiz = mov.get('saida', zero)
        else:
            realiz = mov.get('entrada', zero) - mov.get('saida', zero)
        linhas.append({
            'conta':     c,
            'estimado':  estimado,
            'realizado': realiz,
            'diferenca': estimado - realiz,
        })
    return linhas


def _grupo(nome, icon, cor, linhas):
    zero = Decimal('0.00')
    return {
        'nome':          nome,
        'icon':          icon,
        'cor':           cor,
        'linhas':        linhas,
        'tot_estimado':  sum((l['estimado']  for l in linhas), zero),
        'tot_realizado': sum((l['realizado'] for l in linhas), zero),
        'tot_diferenca': sum((l['diferenca'] for l in linhas), zero),
    }


def _agrupar_linhas(linhas):
    """Agrupa linhas por conta.descrigrupo retornando lista de subgrupos com totais."""
    from itertools import groupby
    zero = Decimal('0.00')
    subgrupos = []
    key = lambda l: l['conta'].descrigrupo or '—'
    for nome_sg, items in groupby(sorted(linhas, key=key), key=key):
        itens = list(items)
        subgrupos.append({
            'nome':          nome_sg,
            'linhas':        itens,
            'tot_estimado':  sum((l['estimado']  for l in itens), zero),
            'tot_realizado': sum((l['realizado'] for l in itens), zero),
            'tot_diferenca': sum((l['diferenca'] for l in itens), zero),
        })
    return subgrupos


@admin_required
def projeto_orcamento(request, pk):
    empresa_id = request.session.get('empresa_id')
    projeto    = get_object_or_404(Projeto, pk=pk, empresa_id=empresa_id)
    hoje       = date.today()
    mes        = int(request.GET.get('mes', hoje.month))
    ano        = int(request.GET.get('ano', hoje.year))
    contas     = PlanoConta.objects.filter(empresa_id=empresa_id, inativo=False).order_by('deb_cred', 'descrigrupo', 'descricao')

    if request.method == 'POST':
        objs_existentes = {
            o.conta_id: o
            for o in ProjetoOrcamento.objects.filter(projeto=projeto)
        }
        to_create, to_update = [], []
        for conta in contas:
            raw = request.POST.get(f'valor_{conta.pk}', '').strip().replace(',', '.')
            try:
                valor = Decimal(raw) if raw else Decimal('0.00')
            except Exception:
                valor = Decimal('0.00')

            if conta.pk in objs_existentes:
                obj = objs_existentes[conta.pk]
                if obj.valor_estimado != valor:
                    obj.valor_estimado = valor
                    to_update.append(obj)
            else:
                if valor:
                    to_create.append(ProjetoOrcamento(
                        projeto=projeto, conta=conta, valor_estimado=valor
                    ))

        if to_update:
            ProjetoOrcamento.objects.bulk_update(to_update, ['valor_estimado'])
        if to_create:
            ProjetoOrcamento.objects.bulk_create(to_create)

        messages.success(request, f'Orçamento do projeto "{projeto}" salvo com sucesso.')
        return redirect(f"{request.path}?mes={mes}&ano={ano}")

    valores_orc = {
        o.conta_id: o.valor_estimado
        for o in ProjetoOrcamento.objects.filter(projeto=projeto)
    }
    realizado = _realizado_por_conta(projeto, empresa_id, mes, ano)
    linhas    = _monta_linhas(contas, valores_orc, realizado)

    MESES = ['Janeiro','Fevereiro','Março','Abril','Maio','Junho',
             'Julho','Agosto','Setembro','Outubro','Novembro','Dezembro']

    grupos = [
        _grupo('Receitas', 'bi-arrow-down-circle', 'success',
               [l for l in linhas if l['conta'].deb_cred == 'C']),
        _grupo('Despesas', 'bi-arrow-up-circle', 'danger',
               [l for l in linhas if l['conta'].deb_cred == 'D']),
        _grupo('Sem Classificação', 'bi-dash-circle', 'secondary',
               [l for l in linhas if l['conta'].deb_cred not in ('C', 'D')]),
    ]

    return render(request, 'core/projeto_orcamento.html', {
        'projeto':     projeto,
        'grupos':      grupos,
        'mes':         mes,
        'ano':         ano,
        'mes_label':   MESES[mes - 1],
        'anos_range':  range(hoje.year - 3, hoje.year + 2),
        'meses_lista': list(enumerate(MESES, 1)),
    })


@admin_required
def projeto_orcamento_imprimir(request, pk):
    from financeiro.relatorios import render_pdf
    from datetime import datetime
    empresa_id = request.session.get('empresa_id')
    projeto    = get_object_or_404(Projeto, pk=pk, empresa_id=empresa_id)
    empresa    = get_object_or_404(Empresa, pk=empresa_id)
    hoje       = date.today()
    mes        = int(request.GET.get('mes', hoje.month))
    ano        = int(request.GET.get('ano', hoje.year))
    contas     = PlanoConta.objects.filter(empresa_id=empresa_id, inativo=False).order_by('deb_cred', 'descrigrupo', 'descricao')

    MESES = ['Janeiro','Fevereiro','Março','Abril','Maio','Junho',
             'Julho','Agosto','Setembro','Outubro','Novembro','Dezembro']

    valores_orc = {
        o.conta_id: o.valor_estimado
        for o in ProjetoOrcamento.objects.filter(projeto=projeto)
    }
    realizado = _realizado_por_conta(projeto, empresa_id, mes, ano)
    linhas    = _monta_linhas(contas, valores_orc, realizado)

    grupos_base = [
        _grupo('Receitas', 'bi-arrow-down-circle', 'success',
               [l for l in linhas if l['conta'].deb_cred == 'C']),
        _grupo('Despesas', 'bi-arrow-up-circle', 'danger',
               [l for l in linhas if l['conta'].deb_cred == 'D']),
        _grupo('Sem Classificação', 'bi-dash-circle', 'secondary',
               [l for l in linhas if l['conta'].deb_cred not in ('C', 'D')]),
    ]
    grupos = [dict(g, subgrupos=_agrupar_linhas(g['linhas'])) for g in grupos_base]

    return render_pdf(
        'relatorios/projeto_orcamento.html',
        {
            'empresa':   empresa,
            'projeto':   projeto,
            'grupos':    grupos,
            'mes':       mes,
            'ano':       ano,
            'mes_label': MESES[mes - 1],
            'hoje':      hoje,
            'now':       datetime.now(),
            'usuario':   request.user.username,
        },
        filename=f'orcamento-{projeto.codigo}-{ano}-{mes:02d}.pdf',
        request=request,
    )

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordChangeForm as DjangoPasswordChangeForm,
)
from .models import PerfilUsuario, Cidade, Banco, Cfop, Empresa, ConfiguracaoCaixa, Projeto, Licenca
from financeiro.models import PlanoConta, SubConta
from cadastros.models import Portador

CSS = 'form-control form-control-sm'
CSS_CHECK = 'form-check-input'
CSS_SELECT = 'form-select form-select-sm'


class LoginForm(AuthenticationForm):
    """Formulário de login — apenas usuário e senha."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': CSS, 'placeholder': 'Usuário', 'autofocus': True,
        })
        self.fields['password'].widget.attrs.update({
            'class': CSS, 'placeholder': 'Senha',
        })


class EmpresaSelecaoForm(forms.Form):
    """Seleção de empresa pós-login para superusuários."""
    empresa = forms.ModelChoiceField(
        queryset=Empresa.objects.filter(inativo=False).order_by('razao'),
        label='Empresa',
        empty_label='— Selecione a empresa —',
        widget=forms.Select(attrs={'class': CSS_SELECT}),
    )


class UsuarioForm(forms.ModelForm):
    """Dados básicos do User do Django."""
    password1 = forms.CharField(
        label='Senha', widget=forms.PasswordInput(attrs={'class': CSS}),
        required=False, help_text='Deixe em branco para manter a senha atual.'
    )
    password2 = forms.CharField(
        label='Confirme a senha', widget=forms.PasswordInput(attrs={'class': CSS}),
        required=False,
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'is_active', 'is_superuser']
        widgets = {
            'username':   forms.TextInput(attrs={'class': CSS}),
            'first_name': forms.TextInput(attrs={'class': CSS}),
            'last_name':  forms.TextInput(attrs={'class': CSS}),
            'email':      forms.EmailInput(attrs={'class': CSS}),
            'is_active':  forms.CheckboxInput(attrs={'class': CSS_CHECK}),
            'is_superuser': forms.CheckboxInput(attrs={'class': CSS_CHECK}),
        }

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('password1')
        p2 = cleaned.get('password2')
        if p1 or p2:
            if p1 != p2:
                self.add_error('password2', 'As senhas não coincidem.')
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        p1 = self.cleaned_data.get('password1')
        if p1:
            user.set_password(p1)
        if commit:
            user.save()
        return user


class PerfilUsuarioForm(forms.ModelForm):
    """Permissões e configurações do perfil."""
    class Meta:
        model = PerfilUsuario
        fields = [
            'empresa',
            'nivel_adm', 'idvendedor',
            'acesso_cadastro', 'acesso_administrativo',
            'acesso_televendas', 'acesso_financeiro', 'acesso_estoque',
            'inativo',
        ]
        widgets = {
            'empresa':     forms.Select(attrs={'class': CSS_SELECT}),
            'nivel_adm':   forms.NumberInput(attrs={'class': CSS}),
            'idvendedor':  forms.NumberInput(attrs={'class': CSS}),
            'acesso_cadastro':       forms.CheckboxInput(attrs={'class': CSS_CHECK}),
            'acesso_administrativo': forms.CheckboxInput(attrs={'class': CSS_CHECK}),
            'acesso_televendas':     forms.CheckboxInput(attrs={'class': CSS_CHECK}),
            'acesso_financeiro':     forms.CheckboxInput(attrs={'class': CSS_CHECK}),
            'acesso_estoque':        forms.CheckboxInput(attrs={'class': CSS_CHECK}),
            'inativo':               forms.CheckboxInput(attrs={'class': CSS_CHECK}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['empresa'].queryset = Empresa.objects.filter(inativo=False).order_by('razao')
        self.fields['empresa'].empty_label = '— Selecione a empresa —'
        self.fields['empresa'].required = True


class TrocaSenhaForm(DjangoPasswordChangeForm):
    """Formulário de troca de senha com classes Bootstrap."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': CSS})


# ── Formulários de configuração do sistema ───────────────────

class CidadeForm(forms.ModelForm):
    class Meta:
        model = Cidade
        fields = ['descricao', 'uf', 'codibge', 'inativo']
        widgets = {
            'descricao': forms.TextInput(attrs={'class': CSS}),
            'uf':        forms.TextInput(attrs={'class': CSS, 'maxlength': 2, 'style': 'text-transform:uppercase'}),
            'codibge':   forms.TextInput(attrs={'class': CSS}),
            'inativo':   forms.CheckboxInput(attrs={'class': CSS_CHECK}),
        }


class BancoForm(forms.ModelForm):
    class Meta:
        model = Banco
        fields = ['descricao', 'numero', 'agencia', 'conta', 'convenio',
                  'numeroboleto', 'jurosmora', 'inativo']
        widgets = {
            'descricao':    forms.TextInput(attrs={'class': CSS}),
            'numero':       forms.TextInput(attrs={'class': CSS}),
            'agencia':      forms.TextInput(attrs={'class': CSS}),
            'conta':        forms.TextInput(attrs={'class': CSS}),
            'convenio':     forms.TextInput(attrs={'class': CSS}),
            'numeroboleto': forms.NumberInput(attrs={'class': CSS}),
            'jurosmora':    forms.NumberInput(attrs={'class': CSS, 'step': '0.01'}),
            'inativo':      forms.CheckboxInput(attrs={'class': CSS_CHECK}),
        }


class ProjetoForm(forms.ModelForm):
    class Meta:
        model = Projeto
        fields = ['codigo', 'descricao', 'dataencerramento', 'inativo']
        widgets = {
            'codigo':           forms.TextInput(attrs={'class': CSS}),
            'descricao':        forms.TextInput(attrs={'class': CSS}),
            'dataencerramento': forms.DateInput(attrs={'class': CSS, 'type': 'date'}, format='%Y-%m-%d'),
            'inativo':          forms.CheckboxInput(attrs={'class': CSS_CHECK}),
        }


class CfopForm(forms.ModelForm):
    class Meta:
        model = Cfop
        fields = ['descricao', 'tipo', 'observacao', 'inativo']
        widgets = {
            'descricao':  forms.TextInput(attrs={'class': CSS}),
            'tipo':       forms.Select(attrs={'class': CSS_SELECT}),
            'observacao': forms.Textarea(attrs={'class': CSS, 'rows': 3}),
            'inativo':    forms.CheckboxInput(attrs={'class': CSS_CHECK}),
        }


class EmpresaForm(forms.ModelForm):
    class Meta:
        model = Empresa
        fields = [
            'razao', 'cnpj', 'ie', 'inativo',
            'fone', 'celular', 'foneass', 'fonewhats', 'email',
            'endereco', 'numero', 'bairro', 'cep', 'cidade',
            'set_baixadireta', 'set_baixafat',
            'senha_expiry_days',
            'cor_cad', 'cor_adm', 'cor_tel', 'cor_fin', 'cor_est',
            'maps_api_key',
        ]
        widgets = {
            'razao':    forms.TextInput(attrs={'class': CSS}),
            'cnpj':     forms.TextInput(attrs={'class': CSS, 'data-mask': 'cnpj'}),
            'ie':       forms.TextInput(attrs={'class': CSS}),
            'fone':     forms.TextInput(attrs={'class': CSS, 'data-mask': 'fone'}),
            'celular':  forms.TextInput(attrs={'class': CSS, 'data-mask': 'fone'}),
            'foneass':  forms.TextInput(attrs={'class': CSS, 'data-mask': 'fone'}),
            'fonewhats':forms.TextInput(attrs={'class': CSS, 'data-mask': 'fone'}),
            'email':    forms.EmailInput(attrs={'class': CSS}),
            'endereco': forms.TextInput(attrs={'class': CSS}),
            'numero':   forms.TextInput(attrs={'class': CSS}),
            'bairro':   forms.TextInput(attrs={'class': CSS}),
            'cep':      forms.TextInput(attrs={'class': CSS, 'data-mask': 'cep'}),
            'cidade':   forms.Select(attrs={'class': CSS_SELECT}),
            'set_baixadireta': forms.CheckboxInput(attrs={'class': CSS_CHECK}),
            'set_baixafat':    forms.CheckboxInput(attrs={'class': CSS_CHECK}),
            'cor_cad':  forms.NumberInput(attrs={'class': CSS}),
            'cor_adm':  forms.NumberInput(attrs={'class': CSS}),
            'cor_tel':  forms.NumberInput(attrs={'class': CSS}),
            'cor_fin':  forms.NumberInput(attrs={'class': CSS}),
            'cor_est':  forms.NumberInput(attrs={'class': CSS}),
            'inativo':  forms.CheckboxInput(attrs={'class': CSS_CHECK}),
            'maps_api_key':      forms.TextInput(attrs={'class': CSS, 'placeholder': 'Deixe em branco para usar links simples (Fase 1)'}),
            'senha_expiry_days': forms.NumberInput(attrs={'class': CSS, 'min': 0}),
        }


# ── Plano de Contas ──────────────────────────────────────────

class PlanoContaForm(forms.ModelForm):
    class Meta:
        model = PlanoConta
        fields = ['descricao', 'deb_cred', 'descrigrupo', 'inativo']
        widgets = {
            'descricao':   forms.TextInput(attrs={'class': CSS}),
            'deb_cred':    forms.Select(attrs={'class': CSS_SELECT}),
            'descrigrupo': forms.TextInput(attrs={'class': CSS}),
            'inativo':     forms.CheckboxInput(attrs={'class': CSS_CHECK}),
        }


class SubContaForm(forms.ModelForm):
    class Meta:
        model = SubConta
        fields = ['descricao', 'conta', 'inativo']
        widgets = {
            'descricao': forms.TextInput(attrs={'class': CSS}),
            'conta':     forms.Select(attrs={'class': CSS_SELECT}),
            'inativo':   forms.CheckboxInput(attrs={'class': CSS_CHECK}),
        }

    def __init__(self, *args, empresa_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        qs = PlanoConta.objects.filter(inativo=False)
        if empresa_id:
            qs = qs.filter(empresa_id=empresa_id)
        self.fields['conta'].queryset = qs.order_by('descricao')
        self.fields['conta'].empty_label = '— Selecione a conta —'


# ── Configuração de Caixa ────────────────────────────────────

class ConfiguracaoCaixaForm(forms.ModelForm):

    class Meta:
        model = ConfiguracaoCaixa
        fields = [
            'conta_recebimento', 'subconta_recebimento',
            'conta_pagamento',   'subconta_pagamento',
            'portador_cheque',   'portador_sangria',
            'portador_dinheiro', 'portador_cartao_deb',
            'portador_cartao_cred', 'portador_pix',
            'banco_padrao',
            'desc_entrada', 'desc_saida', 'desc_sangria', 'desc_suprimento',
        ]
        widgets = {
            'conta_recebimento':    forms.Select(attrs={'class': CSS_SELECT}),
            'subconta_recebimento': forms.Select(attrs={'class': CSS_SELECT}),
            'conta_pagamento':      forms.Select(attrs={'class': CSS_SELECT}),
            'subconta_pagamento':   forms.Select(attrs={'class': CSS_SELECT}),
            'portador_cheque':      forms.Select(attrs={'class': CSS_SELECT}),
            'portador_sangria':     forms.Select(attrs={'class': CSS_SELECT}),
            'portador_dinheiro':    forms.Select(attrs={'class': CSS_SELECT}),
            'portador_cartao_deb':  forms.Select(attrs={'class': CSS_SELECT}),
            'portador_cartao_cred': forms.Select(attrs={'class': CSS_SELECT}),
            'portador_pix':         forms.Select(attrs={'class': CSS_SELECT}),
            'banco_padrao':         forms.Select(attrs={'class': CSS_SELECT}),
            'desc_entrada':         forms.TextInput(attrs={'class': CSS}),
            'desc_saida':           forms.TextInput(attrs={'class': CSS}),
            'desc_sangria':         forms.TextInput(attrs={'class': CSS}),
            'desc_suprimento':      forms.TextInput(attrs={'class': CSS}),
        }

    def __init__(self, *args, empresa_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        planos = PlanoConta.objects.filter(inativo=False)
        subcontas = SubConta.objects.filter(inativo=False)
        portadores = Portador.objects.filter(inativo=False)
        if empresa_id:
            planos = planos.filter(empresa_id=empresa_id)
            subcontas = subcontas.filter(empresa_id=empresa_id)
            portadores = portadores.filter(empresa_id=empresa_id)

        planos = planos.order_by('descricao')
        subcontas = subcontas.order_by('conta__descricao', 'descricao')
        portadores = portadores.order_by('descricao')

        for f in ('conta_recebimento', 'conta_pagamento'):
            self.fields[f].queryset   = planos
            self.fields[f].empty_label = '— não definido —'
            self.fields[f].required   = False

        for f in ('subconta_recebimento', 'subconta_pagamento'):
            self.fields[f].queryset   = subcontas
            self.fields[f].empty_label = '— não definido —'
            self.fields[f].required   = False

        for f in ('portador_cheque', 'portador_sangria', 'portador_dinheiro',
                  'portador_cartao_deb', 'portador_cartao_cred', 'portador_pix'):
            self.fields[f].queryset   = portadores
            self.fields[f].empty_label = '— não definido —'
            self.fields[f].required   = False

        self.fields['banco_padrao'].queryset   = Banco.objects.filter(inativo=False).order_by('descricao')
        self.fields['banco_padrao'].empty_label = '— não definido —'
        self.fields['banco_padrao'].required   = False


# ── Licença de Uso ───────────────────────────────────────────

class LicencaForm(forms.ModelForm):
    class Meta:
        model = Licenca
        fields = ['valid_from', 'valid_until', 'max_usuarios', 'ativa']
        widgets = {
            'valid_from':   forms.DateInput(attrs={'class': CSS, 'type': 'date'}, format='%Y-%m-%d'),
            'valid_until':  forms.DateInput(attrs={'class': CSS, 'type': 'date'}, format='%Y-%m-%d'),
            'max_usuarios': forms.NumberInput(attrs={'class': CSS, 'min': 1}),
            'ativa':        forms.CheckboxInput(attrs={'class': CSS_CHECK}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['valid_from'].input_formats  = ['%Y-%m-%d']
        self.fields['valid_until'].input_formats = ['%Y-%m-%d']

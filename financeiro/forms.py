from django import forms
from .models import ContaReceber, ContaPagar, PlanoConta
from cadastros.models import ClienteFornecedor, Portador, Metodo
from core.models import Banco

CSS        = 'form-control form-control-sm'
CSS_CHECK  = 'form-check-input'
CSS_SELECT = 'form-select form-select-sm'
CSS_DATE   = 'form-control form-control-sm'
_BRL       = {'class': CSS, 'data-mask': 'brl', 'inputmode': 'decimal'}


class ContaReceberForm(forms.ModelForm):

    class Meta:
        model = ContaReceber
        fields = [
            'numerodoc', 'data', 'cliente', 'parcela',
            'valor', 'vencimento', 'portador', 'banco', 'status',
        ]
        widgets = {
            'numerodoc': forms.TextInput(attrs={'class': CSS}),
            'data':      forms.DateInput(attrs={'class': CSS_DATE, 'type': 'date'}, format='%Y-%m-%d'),
            'cliente':   forms.Select(attrs={'class': CSS_SELECT}),
            'parcela':   forms.NumberInput(attrs={'class': CSS, 'min': 1}),
            'valor':     forms.TextInput(attrs=_BRL),
            'vencimento':forms.DateInput(attrs={'class': CSS_DATE, 'type': 'date'}, format='%Y-%m-%d'),
            'portador':  forms.Select(attrs={'class': CSS_SELECT}),
            'banco':     forms.Select(attrs={'class': CSS_SELECT}),
            'status':    forms.Select(attrs={'class': CSS_SELECT}),
        }

    def __init__(self, *args, empresa_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        cli_qs = ClienteFornecedor.objects.filter(tipocliforemp='C', inativo=False)
        por_qs = Portador.objects.filter(inativo=False)
        if empresa_id:
            cli_qs = cli_qs.filter(empresa_id=empresa_id)
            por_qs = por_qs.filter(empresa_id=empresa_id)
        self.fields['cliente'].queryset = cli_qs.order_by('razao', 'nome')
        self.fields['cliente'].empty_label = '— Selecione o cliente —'
        self.fields['portador'].queryset = por_qs.order_by('descricao')
        self.fields['portador'].empty_label = '— Portador —'
        self.fields['portador'].required = False
        self.fields['banco'].queryset = Banco.objects.filter(inativo=False).order_by('descricao')
        self.fields['banco'].empty_label = '— Banco / Conta —'
        self.fields['banco'].required = False
        self.fields['status'].choices = [
            ('A', 'Aberto'),
            ('C', 'Cancelado'),
        ]


# ── Contas a Pagar ───────────────────────────────────────────

class ContaPagarForm(forms.ModelForm):

    class Meta:
        model = ContaPagar
        fields = [
            'numerodoc', 'data', 'fornecedor', 'parcela',
            'valor', 'vencimento', 'portador', 'banco', 'status',
        ]
        widgets = {
            'numerodoc':  forms.TextInput(attrs={'class': CSS}),
            'data':       forms.DateInput(attrs={'class': CSS_DATE, 'type': 'date'}, format='%Y-%m-%d'),
            'fornecedor': forms.Select(attrs={'class': CSS_SELECT}),
            'parcela':    forms.NumberInput(attrs={'class': CSS, 'min': 1}),
            'valor':      forms.TextInput(attrs=_BRL),
            'vencimento': forms.DateInput(attrs={'class': CSS_DATE, 'type': 'date'}, format='%Y-%m-%d'),
            'portador':   forms.Select(attrs={'class': CSS_SELECT}),
            'banco':      forms.Select(attrs={'class': CSS_SELECT}),
            'status':     forms.Select(attrs={'class': CSS_SELECT}),
        }

    def __init__(self, *args, empresa_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        forn_qs = ClienteFornecedor.objects.filter(tipocliforemp='F', inativo=False)
        por_qs  = Portador.objects.filter(inativo=False)
        if empresa_id:
            forn_qs = forn_qs.filter(empresa_id=empresa_id)
            por_qs  = por_qs.filter(empresa_id=empresa_id)
        self.fields['fornecedor'].queryset = forn_qs.order_by('razao', 'nome')
        self.fields['fornecedor'].empty_label = '— Selecione o fornecedor —'
        self.fields['portador'].queryset = por_qs.order_by('descricao')
        self.fields['portador'].empty_label = '— Portador —'
        self.fields['portador'].required = False
        self.fields['banco'].queryset = Banco.objects.filter(inativo=False).order_by('descricao')
        self.fields['banco'].empty_label = '— Banco / Conta —'
        self.fields['banco'].required = False
        self.fields['status'].choices = [
            ('A', 'Aberto'),
            ('C', 'Cancelado'),
        ]


# ── Caixa ─────────────────────────────────────────────────────

class CaixaAberturaForm(forms.Form):
    saldo_inicial = forms.DecimalField(
        label='Saldo Inicial (R$)', min_value=0, decimal_places=2, initial=0,
        widget=forms.TextInput(attrs=_BRL),
    )


class CaixaMovimentoForm(forms.Form):
    descricao = forms.CharField(
        label='Descrição', max_length=200,
        widget=forms.TextInput(attrs={'class': CSS}),
    )
    valor = forms.DecimalField(
        label='Valor (R$)', min_value=0.01, decimal_places=2,
        widget=forms.TextInput(attrs=_BRL),
    )
    documento = forms.CharField(
        label='Documento', max_length=30, required=False,
        widget=forms.TextInput(attrs={'class': CSS}),
    )
    conta = forms.ModelChoiceField(
        label='Plano de Conta', queryset=None, required=False,
        empty_label='— Selecione —',
        widget=forms.Select(attrs={'class': CSS_SELECT}),
    )

    def __init__(self, *args, deb_cred=None, empresa_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        qs = PlanoConta.objects.filter(inativo=False)
        if empresa_id:
            qs = qs.filter(empresa_id=empresa_id)
        if deb_cred:
            qs = qs.filter(deb_cred=deb_cred)
        self.fields['conta'].queryset = qs.order_by('descricao')


class CaixaSangriaForm(forms.Form):
    descricao = forms.CharField(
        label='Descrição', max_length=200,
        widget=forms.TextInput(attrs={'class': CSS}),
    )
    valor = forms.DecimalField(
        label='Valor (R$)', min_value=0.01, decimal_places=2,
        widget=forms.TextInput(attrs=_BRL),
    )
    portador = forms.ModelChoiceField(
        label='Destino (Portador)', queryset=None, required=False,
        empty_label='— Destino —',
        widget=forms.Select(attrs={'class': CSS_SELECT}),
    )

    def __init__(self, *args, empresa_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        por_qs = Portador.objects.filter(inativo=False)
        if empresa_id:
            por_qs = por_qs.filter(empresa_id=empresa_id)
        self.fields['portador'].queryset = por_qs.order_by('descricao')


class CaixaRecebimentoForm(forms.Form):
    contarec_pk = forms.IntegerField(widget=forms.HiddenInput)
    data_pagamento = forms.DateField(
        label='Data Pagamento',
        widget=forms.DateInput(attrs={'class': CSS_DATE, 'type': 'date'}, format='%Y-%m-%d'),
    )
    metodo = forms.ModelChoiceField(
        label='Método de Recebimento', queryset=None, required=False,
        empty_label='— Método —',
        widget=forms.Select(attrs={'class': CSS_SELECT}),
    )
    juros = forms.DecimalField(
        label='Juros (R$)', min_value=0, decimal_places=2, initial=0,
        widget=forms.TextInput(attrs=_BRL),
    )
    descontos = forms.DecimalField(
        label='Descontos (R$)', min_value=0, decimal_places=2, initial=0,
        widget=forms.TextInput(attrs=_BRL),
    )
    valorpago = forms.DecimalField(
        label='Valor Pago (R$)', min_value=0.01, decimal_places=2,
        widget=forms.TextInput(attrs=_BRL),
    )
    portador = forms.ModelChoiceField(
        label='Portador', queryset=None, required=False,
        empty_label='— Portador —',
        widget=forms.Select(attrs={'class': CSS_SELECT}),
    )

    def __init__(self, *args, empresa_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        met_qs = Metodo.objects.filter(inativo=False)
        por_qs = Portador.objects.filter(inativo=False)
        if empresa_id:
            met_qs = met_qs.filter(empresa_id=empresa_id)
            por_qs = por_qs.filter(empresa_id=empresa_id)
        self.fields['metodo'].queryset   = met_qs.order_by('descricao')
        self.fields['portador'].queryset = por_qs.order_by('descricao')


class CaixaPagamentoForm(forms.Form):
    contapag_pk = forms.IntegerField(widget=forms.HiddenInput)
    data_pagamento = forms.DateField(
        label='Data Pagamento',
        widget=forms.DateInput(attrs={'class': CSS_DATE, 'type': 'date'}, format='%Y-%m-%d'),
    )
    metodo = forms.ModelChoiceField(
        label='Método de Pagamento', queryset=None, required=False,
        empty_label='— Método —',
        widget=forms.Select(attrs={'class': CSS_SELECT}),
    )
    juros = forms.DecimalField(
        label='Juros (R$)', min_value=0, decimal_places=2, initial=0,
        widget=forms.TextInput(attrs=_BRL),
    )
    descontos = forms.DecimalField(
        label='Descontos (R$)', min_value=0, decimal_places=2, initial=0,
        widget=forms.TextInput(attrs=_BRL),
    )
    valorpago = forms.DecimalField(
        label='Valor Pago (R$)', min_value=0.01, decimal_places=2,
        widget=forms.TextInput(attrs=_BRL),
    )
    portador = forms.ModelChoiceField(
        label='Portador', queryset=None, required=False,
        empty_label='— Portador —',
        widget=forms.Select(attrs={'class': CSS_SELECT}),
    )

    def __init__(self, *args, empresa_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        met_qs = Metodo.objects.filter(inativo=False)
        por_qs = Portador.objects.filter(inativo=False)
        if empresa_id:
            met_qs = met_qs.filter(empresa_id=empresa_id)
            por_qs = por_qs.filter(empresa_id=empresa_id)
        self.fields['metodo'].queryset   = met_qs.order_by('descricao')
        self.fields['portador'].queryset = por_qs.order_by('descricao')

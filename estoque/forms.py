from django import forms
from .models import Requisicao, NotaFiscalEntrada
from cadastros.models import ClienteFornecedor, CondicaoPagamento, Metodo

CSS        = 'form-control form-control-sm'
CSS_SELECT = 'form-select form-select-sm'
CSS_DATE   = 'form-control form-control-sm'

ORIGEM_CHOICES = [
    ('',          '— Selecione —'),
    ('Manual',    'Manual'),
    ('Faturamento', 'Faturamento'),
    ('Consumo',   'Consumo'),
]


class RequisicaoForm(forms.ModelForm):
    origem = forms.ChoiceField(
        choices=ORIGEM_CHOICES,
        label='Origem',
        widget=forms.Select(attrs={'class': CSS_SELECT}),
    )

    class Meta:
        model  = Requisicao
        fields = ['data', 'origem', 'cliforemp', 'observacao']
        widgets = {
            'data':       forms.DateInput(attrs={'class': CSS_DATE, 'type': 'date'}, format='%Y-%m-%d'),
            'cliforemp':  forms.Select(attrs={'class': CSS_SELECT}),
            'observacao': forms.Textarea(attrs={'class': CSS, 'rows': 2}),
        }

    def __init__(self, *args, empresa_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        cli_qs = ClienteFornecedor.objects.filter(inativo=False)
        if empresa_id:
            cli_qs = cli_qs.filter(empresa_id=empresa_id)
        self.fields['cliforemp'].queryset   = cli_qs.order_by('razao', 'nome')
        self.fields['cliforemp'].empty_label = '— Nenhum (opcional) —'
        self.fields['cliforemp'].required   = False
        self.fields['data'].required        = True


class NFEntradaForm(forms.ModelForm):
    class Meta:
        model  = NotaFiscalEntrada
        fields = ['fornecedor', 'numeronf', 'serie', 'dataemissao', 'dataentrada',
                  'chaveacesso', 'condicao', 'metodo', 'observacao']
        widgets = {
            'fornecedor':  forms.Select(attrs={'class': CSS_SELECT}),
            'numeronf':    forms.NumberInput(attrs={'class': CSS}),
            'serie':       forms.TextInput(attrs={'class': CSS, 'placeholder': 'Ex.: 001'}),
            'dataemissao': forms.DateInput(attrs={'class': CSS_DATE, 'type': 'date'}, format='%Y-%m-%d'),
            'dataentrada': forms.DateInput(attrs={'class': CSS_DATE, 'type': 'date'}, format='%Y-%m-%d'),
            'chaveacesso': forms.TextInput(attrs={
                'class': 'form-control form-control-sm font-monospace',
                'placeholder': '44 dígitos — chave de acesso da NF-e',
                'maxlength': '44',
            }),
            'condicao':    forms.Select(attrs={'class': CSS_SELECT, '@change': 'onCondicaoChange($event)'}),
            'metodo':      forms.Select(attrs={'class': CSS_SELECT}),
            'observacao':  forms.Textarea(attrs={'class': CSS, 'rows': 2}),
        }

    def __init__(self, *args, empresa_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        base_forn  = ClienteFornecedor.objects.filter(tipocliforemp='F', inativo=False)
        base_cond  = CondicaoPagamento.objects.filter(inativo=False)
        base_metod = Metodo.objects.filter(inativo=False)
        if empresa_id:
            base_forn  = base_forn.filter(empresa_id=empresa_id)
            base_cond  = base_cond.filter(empresa_id=empresa_id)
            base_metod = base_metod.filter(empresa_id=empresa_id)

        self.fields['fornecedor'].queryset   = base_forn.order_by('razao', 'nome')
        self.fields['fornecedor'].empty_label = '— Selecione o fornecedor —'
        self.fields['condicao'].queryset     = base_cond.order_by('descricao')
        self.fields['condicao'].empty_label  = '— Condição de Pgto (opcional) —'
        self.fields['condicao'].required     = False
        self.fields['metodo'].queryset       = base_metod.order_by('descricao')
        self.fields['metodo'].empty_label    = '— Método de Pgto (opcional) —'
        self.fields['metodo'].required       = False
        self.fields['serie'].required        = False

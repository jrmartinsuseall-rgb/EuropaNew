from django import forms
from .models import ContatoCliente, TeleVenda
from cadastros.models import TelefoneAdicional, ClienteFornecedor, TabelaPreco, CondicaoPagamento, Metodo

CSS        = 'form-control form-control-sm'
CSS_DATE   = 'form-control form-control-sm'
CSS_SELECT = 'form-select form-select-sm'

IDENTIFICACAO_FONE = [
    ('Principal',   'Principal'),
    ('Secundário',  'Secundário'),
    ('Celular',     'Celular'),
    ('WhatsApp',    'WhatsApp'),
    ('Comercial',   'Comercial'),
    ('Residencial', 'Residencial'),
    ('Recado',      'Recado'),
]

RELACAO_FONE = [
    ('Titular',     'Titular'),
    ('Cônjuge',     'Cônjuge'),
    ('Filho/Filha', 'Filho/Filha'),
    ('Responsável', 'Responsável'),
    ('Contato',     'Contato'),
    ('Outro',       'Outro'),
]

STATUS_CONTATO = [
    ('',              '— Selecione —'),
    ('Realizado',     'Realizado'),
    ('Pendente',      'Pendente'),
    ('Agendado',      'Agendado'),
    ('Em andamento',  'Em andamento'),
    ('Sem retorno',   'Sem retorno'),
    ('Cancelado',     'Cancelado'),
]


class ContatoForm(forms.ModelForm):
    status = forms.ChoiceField(
        choices=STATUS_CONTATO,
        required=False,
        widget=forms.Select(attrs={'class': CSS_SELECT}),
    )

    class Meta:
        model  = ContatoCliente
        fields = ['datacontato', 'descricao', 'status', 'proximocontato', 'observacao']
        widgets = {
            'datacontato':    forms.DateInput(attrs={'class': CSS_DATE, 'type': 'date'}, format='%Y-%m-%d'),
            'descricao':      forms.TextInput(attrs={'class': CSS}),
            'proximocontato': forms.DateInput(attrs={'class': CSS_DATE, 'type': 'date'}, format='%Y-%m-%d'),
            'observacao':     forms.Textarea(attrs={'class': CSS, 'rows': 3}),
        }


class TelefoneForm(forms.ModelForm):
    identificacao = forms.ChoiceField(
        label='Identificação',
        choices=IDENTIFICACAO_FONE,
        widget=forms.Select(attrs={'class': CSS_SELECT}),
    )
    relacao = forms.ChoiceField(
        label='Relação',
        choices=RELACAO_FONE,
        widget=forms.Select(attrs={'class': CSS_SELECT}),
    )

    class Meta:
        model  = TelefoneAdicional
        fields = ['numero', 'identificacao', 'relacao', 'descricao']
        widgets = {
            'numero':    forms.TextInput(attrs={'class': CSS}),
            'descricao': forms.TextInput(attrs={'class': CSS}),
        }


# ── Ordem de Serviço / TeleVenda ──────────────────────────────

class TeleVendaForm(forms.ModelForm):
    vendedor = forms.ModelChoiceField(
        queryset=ClienteFornecedor.objects.none(),
        required=False, label='Vendedor',
        widget=forms.Select(attrs={'class': CSS_SELECT}),
    )
    tecnico = forms.ModelChoiceField(
        queryset=ClienteFornecedor.objects.none(),
        required=False, label='Técnico',
        widget=forms.Select(attrs={'class': CSS_SELECT}),
    )

    class Meta:
        model  = TeleVenda
        fields = ['cliente', 'dataprevisao', 'atend_periodo', 'atend_hora',
                  'tabela', 'condicao', 'metodo', 'atend_obs']
        widgets = {
            'cliente':       forms.Select(attrs={'class': CSS_SELECT}),
            'dataprevisao':  forms.DateInput(attrs={'class': CSS_DATE, 'type': 'date'}, format='%Y-%m-%d'),
            'atend_periodo': forms.Select(attrs={'class': CSS_SELECT}),
            'atend_hora':    forms.TextInput(attrs={'class': CSS, 'placeholder': '08:00'}),
            'tabela':        forms.Select(attrs={'class': CSS_SELECT}),
            'condicao':      forms.Select(attrs={'class': CSS_SELECT}),
            'metodo':        forms.Select(attrs={'class': CSS_SELECT}),
            'atend_obs':     forms.Textarea(attrs={'class': CSS, 'rows': 2}),
        }

    def __init__(self, *args, empresa_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        cli_qs = ClienteFornecedor.objects.filter(tipocliforemp='C', inativo=False)
        ven_qs = ClienteFornecedor.objects.filter(tipocliforemp='V', inativo=False)
        tec_qs = ClienteFornecedor.objects.filter(tipocliforemp='E', inativo=False)
        tab_qs = TabelaPreco.objects.filter(inativo=False)
        con_qs = CondicaoPagamento.objects.filter(inativo=False)
        met_qs = Metodo.objects.filter(inativo=False)
        if empresa_id:
            cli_qs = cli_qs.filter(empresa_id=empresa_id)
            ven_qs = ven_qs.filter(empresa_id=empresa_id)
            tec_qs = tec_qs.filter(empresa_id=empresa_id)
            tab_qs = tab_qs.filter(empresa_id=empresa_id)
            con_qs = con_qs.filter(empresa_id=empresa_id)
            met_qs = met_qs.filter(empresa_id=empresa_id)
        self.fields['cliente'].queryset  = cli_qs.order_by('razao', 'nome')
        self.fields['vendedor'].queryset = ven_qs.order_by('razao', 'nome')
        self.fields['tecnico'].queryset  = tec_qs.order_by('razao', 'nome')
        self.fields['tabela'].queryset   = tab_qs.order_by('descricao')
        self.fields['condicao'].queryset = con_qs.order_by('descricao')
        self.fields['metodo'].queryset   = met_qs.order_by('descricao')
        self.fields['cliente'].empty_label  = '— Selecione o cliente —'
        self.fields['tabela'].empty_label   = '— Selecione a tabela —'
        self.fields['tabela'].required      = False
        self.fields['condicao'].empty_label = '— Selecione —'
        self.fields['condicao'].required    = False
        self.fields['metodo'].empty_label   = '— Selecione —'
        self.fields['metodo'].required      = False
        self.fields['vendedor'].empty_label = '— Selecione —'
        self.fields['tecnico'].empty_label  = '— Selecione —'

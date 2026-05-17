from django import forms
from .models import ClienteFornecedor, CondicaoPagamento, Grupo, Item, Portador, Metodo, TabelaPreco, ItemTabelaPreco

CSS        = 'form-control form-control-sm'
CSS_CHECK  = 'form-check-input'
CSS_SELECT = 'form-select form-select-sm'
_BRL       = {'class': CSS, 'data-mask': 'brl', 'inputmode': 'decimal'}
_BRL_SM    = {'class': CSS, 'data-mask': 'brl', 'inputmode': 'decimal', 'style': 'width:90px;'}


class ClienteFornecedorForm(forms.ModelForm):

    class Meta:
        model = ClienteFornecedor
        fields = [
            # Aba 1 — Dados Principais
            'tipocliforemp', 'tipopessoa', 'empresa', 'classificacao',
            'razao', 'fantasia', 'nome', 'cnpjcpf', 'identinscr', 'estadocivil',
            'datacadastro', 'inativo',
            # Aba 2 — Contato
            'fone', 'celular', 'email',
            'convfone', 'convcelular', 'convcelular1', 'convcelular2',
            # Aba 3 — Endereço
            'cep', 'endereco', 'numero', 'bairro', 'cidade',
            'edificio', 'apto', 'referencia',
            # Aba 4 — Dados Pessoais (PF)
            'fdatanasc', 'fdataexpid', 'fufexpid',
            'fnomepai', 'fnomemae',
            'fempregador', 'fcargo', 'ffoneempre',
            'favalista', 'responsavel',
            # Aba 5 — Comercial
            'idvendrepre', 'nomevendedor', 'limitecredito',
            'perccomiss', 'perccomissp', 'valorreferencia', 'tipovendedor',
            # Aba 6 — Observações
            'observacao', 'obscobranca',
        ]
        widgets = {
            # Selects
            'tipocliforemp': forms.Select(attrs={'class': 'form-select'}),
            'tipopessoa':    forms.Select(attrs={'class': 'form-select'}),
            'estadocivil':   forms.Select(attrs={'class': 'form-select'}),
            'empresa':       forms.Select(attrs={'class': 'form-select'}),
            'cidade':        forms.Select(attrs={'class': 'form-select'}),
            # Textos comuns
            'razao':         forms.TextInput(attrs={'class': 'form-control'}),
            'fantasia':      forms.TextInput(attrs={'class': 'form-control'}),
            'nome':          forms.TextInput(attrs={'class': 'form-control'}),
            'cnpjcpf':       forms.TextInput(attrs={'class': 'form-control font-monospace', 'data-mask': 'cpfcnpj'}),
            'identinscr':    forms.TextInput(attrs={'class': 'form-control'}),
            'classificacao': forms.TextInput(attrs={'class': 'form-control'}),
            # Contato
            'fone':          forms.TextInput(attrs={'class': 'form-control', 'data-mask': 'fone'}),
            'celular':       forms.TextInput(attrs={'class': 'form-control', 'data-mask': 'fone'}),
            'email':         forms.EmailInput(attrs={'class': 'form-control'}),
            'convfone':      forms.TextInput(attrs={'class': 'form-control', 'data-mask': 'fone'}),
            'convcelular':   forms.TextInput(attrs={'class': 'form-control', 'data-mask': 'fone'}),
            'convcelular1':  forms.TextInput(attrs={'class': 'form-control', 'data-mask': 'fone'}),
            'convcelular2':  forms.TextInput(attrs={'class': 'form-control', 'data-mask': 'fone'}),
            # Endereço
            'cep':           forms.TextInput(attrs={'class': 'form-control font-monospace', 'data-mask': 'cep', 'autocomplete': 'off'}),
            'endereco':      forms.TextInput(attrs={'class': 'form-control'}),
            'numero':        forms.TextInput(attrs={'class': 'form-control'}),
            'bairro':        forms.TextInput(attrs={'class': 'form-control'}),
            'edificio':      forms.TextInput(attrs={'class': 'form-control'}),
            'apto':          forms.TextInput(attrs={'class': 'form-control'}),
            'referencia':    forms.TextInput(attrs={'class': 'form-control'}),
            # Datas
            'datacadastro':  forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'fdatanasc':     forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'fdataexpid':    forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            # Dados pessoais
            'fufexpid':      forms.TextInput(attrs={'class': 'form-control text-uppercase', 'maxlength': '2'}),
            'fnomepai':      forms.TextInput(attrs={'class': 'form-control'}),
            'fnomemae':      forms.TextInput(attrs={'class': 'form-control'}),
            'fempregador':   forms.TextInput(attrs={'class': 'form-control'}),
            'fcargo':        forms.TextInput(attrs={'class': 'form-control'}),
            'ffoneempre':    forms.TextInput(attrs={'class': 'form-control', 'data-mask': 'fone'}),
            'favalista':     forms.TextInput(attrs={'class': 'form-control'}),
            'responsavel':   forms.TextInput(attrs={'class': 'form-control'}),
            # Comercial
            'idvendrepre':   forms.NumberInput(attrs={'class': 'form-control'}),
            'nomevendedor':  forms.TextInput(attrs={'class': 'form-control'}),
            'limitecredito':   forms.TextInput(attrs={'class': 'form-control', 'data-mask': 'brl', 'inputmode': 'decimal'}),
            'perccomiss':      forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'perccomissp':     forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'valorreferencia': forms.TextInput(attrs={'class': 'form-control', 'data-mask': 'brl', 'inputmode': 'decimal'}),
            'tipovendedor':   forms.TextInput(attrs={'class': 'form-control'}),
            # Observações
            'observacao':    forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'obscobranca':   forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }


# ── Vendedor ─────────────────────────────────────────────────

class VendedorForm(forms.ModelForm):
    class Meta:
        model  = ClienteFornecedor
        fields = ['tipopessoa', 'nome', 'razao', 'cnpjcpf',
                  'fone', 'celular', 'email',
                  'perccomiss', 'perccomissp', 'tipovendedor', 'equipe',
                  'observacao', 'inativo']
        widgets = {
            'tipopessoa':   forms.Select(attrs={'class': CSS_SELECT}),
            'nome':         forms.TextInput(attrs={'class': CSS}),
            'razao':        forms.TextInput(attrs={'class': CSS}),
            'cnpjcpf':      forms.TextInput(attrs={'class': f'{CSS} font-monospace', 'data-mask': 'cpfcnpj'}),
            'fone':         forms.TextInput(attrs={'class': CSS, 'data-mask': 'fone'}),
            'celular':      forms.TextInput(attrs={'class': CSS, 'data-mask': 'fone'}),
            'email':        forms.EmailInput(attrs={'class': CSS}),
            'perccomiss':   forms.NumberInput(attrs={'class': CSS, 'step': '0.01'}),
            'perccomissp':  forms.NumberInput(attrs={'class': CSS, 'step': '0.01'}),
            'tipovendedor': forms.TextInput(attrs={'class': CSS}),
            'equipe':       forms.NumberInput(attrs={'class': CSS}),
            'observacao':   forms.Textarea(attrs={'class': CSS, 'rows': 3}),
            'inativo':      forms.CheckboxInput(attrs={'class': CSS_CHECK}),
        }


# ── Empregado / Técnico ───────────────────────────────────────

class TecnicoForm(forms.ModelForm):
    class Meta:
        model  = ClienteFornecedor
        fields = ['tipopessoa', 'nome', 'razao', 'cnpjcpf',
                  'fone', 'celular', 'email',
                  'equipe', 'observacao', 'inativo']
        widgets = {
            'tipopessoa': forms.Select(attrs={'class': CSS_SELECT}),
            'nome':       forms.TextInput(attrs={'class': CSS}),
            'razao':      forms.TextInput(attrs={'class': CSS}),
            'cnpjcpf':    forms.TextInput(attrs={'class': f'{CSS} font-monospace', 'data-mask': 'cpfcnpj'}),
            'fone':       forms.TextInput(attrs={'class': CSS, 'data-mask': 'fone'}),
            'celular':    forms.TextInput(attrs={'class': CSS, 'data-mask': 'fone'}),
            'email':      forms.EmailInput(attrs={'class': CSS}),
            'equipe':     forms.NumberInput(attrs={'class': CSS}),
            'observacao': forms.Textarea(attrs={'class': CSS, 'rows': 3}),
            'inativo':    forms.CheckboxInput(attrs={'class': CSS_CHECK}),
        }


# ── Condição de Pagamento ────────────────────────────────────

class CondicaoPagamentoForm(forms.ModelForm):
    class Meta:
        model = CondicaoPagamento
        fields = ['descricao', 'tipo', 'condicao', 'dias', 'parcelas', 'inativo']
        widgets = {
            'descricao': forms.TextInput(attrs={'class': CSS}),
            'tipo':      forms.NumberInput(attrs={'class': CSS}),
            'condicao':  forms.TextInput(attrs={'class': CSS}),
            'dias':      forms.NumberInput(attrs={'class': CSS}),
            'parcelas':  forms.NumberInput(attrs={'class': CSS}),
            'inativo':   forms.CheckboxInput(attrs={'class': CSS_CHECK}),
        }


# ── Grupo ────────────────────────────────────────────────────

class GrupoForm(forms.ModelForm):
    class Meta:
        model = Grupo
        fields = ['descricao', 'idgrupopai', 'classificacao', 'corlista', 'inativo']
        widgets = {
            'descricao':    forms.TextInput(attrs={'class': CSS}),
            'idgrupopai':   forms.Select(attrs={'class': CSS_SELECT}),
            'classificacao':forms.TextInput(attrs={'class': CSS}),
            'corlista':     forms.NumberInput(attrs={'class': CSS}),
            'inativo':      forms.CheckboxInput(attrs={'class': CSS_CHECK}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Exclui o próprio grupo da lista de pais (evita auto-referência)
        if self.instance.pk:
            self.fields['idgrupopai'].queryset = Grupo.objects.exclude(pk=self.instance.pk)
        self.fields['idgrupopai'].empty_label = '— Sem grupo pai —'


# ── Item ─────────────────────────────────────────────────────

class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = [
            'identificacao', 'descricao', 'modelo', 'unidade',
            'grupo', 'tipo_item', 'tipoitem', 'precobase', 'basecomissao',
            'saldoestoque', 'tempotroca', 'codforn',
            'controla_estoque', 'corlista', 'inativo',
        ]
        widgets = {
            'identificacao':    forms.TextInput(attrs={'class': CSS}),
            'descricao':        forms.TextInput(attrs={'class': CSS}),
            'modelo':           forms.TextInput(attrs={'class': CSS}),
            'unidade':          forms.TextInput(attrs={'class': CSS}),
            'grupo':            forms.Select(attrs={'class': CSS_SELECT}),
            'tipo_item':        forms.Select(attrs={'class': CSS_SELECT}),
            'tipoitem':         forms.HiddenInput(),
            'precobase':        forms.TextInput(attrs=_BRL),
            'basecomissao':     forms.TextInput(attrs=_BRL),
            'saldoestoque':     forms.NumberInput(attrs={'class': CSS, 'step': '0.001', 'readonly': True}),
            'tempotroca':       forms.NumberInput(attrs={'class': CSS}),
            'codforn':          forms.TextInput(attrs={'class': CSS}),
            'controla_estoque': forms.CheckboxInput(attrs={'class': CSS_CHECK}),
            'corlista':         forms.NumberInput(attrs={'class': CSS}),
            'inativo':          forms.CheckboxInput(attrs={'class': CSS_CHECK}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['grupo'].empty_label = '— Sem grupo —'


# ── Portador ─────────────────────────────────────────────────

class PortadorForm(forms.ModelForm):
    class Meta:
        model = Portador
        fields = ['descricao', 'inativo']
        widgets = {
            'descricao': forms.TextInput(attrs={'class': CSS}),
            'inativo':   forms.CheckboxInput(attrs={'class': CSS_CHECK}),
        }


# ── Método de Pagamento ───────────────────────────────────────

class MetodoForm(forms.ModelForm):
    class Meta:
        model = Metodo
        fields = ['descricao', 'sigla', 'movcaixa', 'mensagem', 'inativo']
        widgets = {
            'descricao': forms.TextInput(attrs={'class': CSS}),
            'sigla':     forms.TextInput(attrs={'class': CSS, 'maxlength': '10', 'style': 'text-transform:uppercase;'}),
            'movcaixa':  forms.CheckboxInput(attrs={'class': CSS_CHECK}),
            'mensagem':  forms.TextInput(attrs={'class': CSS}),
            'inativo':   forms.CheckboxInput(attrs={'class': CSS_CHECK}),
        }


# ── Tabela de Preço ───────────────────────────────────────────

class TabelaPrecoForm(forms.ModelForm):
    class Meta:
        model  = TabelaPreco
        fields = ['descricao', 'tipo', 'datavalidade', 'observacao', 'inativo']
        widgets = {
            'descricao':    forms.TextInput(attrs={'class': CSS}),
            'tipo':         forms.NumberInput(attrs={'class': CSS}),
            'datavalidade': forms.DateInput(attrs={'class': CSS, 'type': 'date'}, format='%Y-%m-%d'),
            'observacao':   forms.Textarea(attrs={'class': CSS, 'rows': 2}),
            'inativo':      forms.CheckboxInput(attrs={'class': CSS_CHECK}),
        }


# Campos de parcela em ordem para uso no form e template
PARCELAS_FIELDS = [
    ('i_pagto',    '1x'),
    ('ii_pagto',   '2x'),
    ('iii_pagto',  '3x'),
    ('iv_pagto',   '4x'),
    ('v_pagto',    '5x'),
    ('vi_pagto',   '6x'),
    ('vii_pagto',  '7x'),
    ('viii_pagto', '8x'),
    ('ix_pagto',   '9x'),
    ('x_pagto',    '10x'),
    ('xi_pagto',   '11x'),
    ('xii_pagto',  '12x'),
]

_NUM = _BRL_SM


class ItemTabelaPrecoForm(forms.ModelForm):
    class Meta:
        model  = ItemTabelaPreco
        fields = (['item', 'identificacao', 'preco', 'basecomissao'] +
                  [f for f, _ in PARCELAS_FIELDS])
        widgets = {
            'item':         forms.Select(attrs={'class': CSS_SELECT}),
            'identificacao':forms.TextInput(attrs={'class': CSS}),
            'preco':        forms.NumberInput(attrs={**_NUM}),
            'basecomissao': forms.NumberInput(attrs={**_NUM}),
            **{f: forms.NumberInput(attrs={**_NUM}) for f, _ in PARCELAS_FIELDS},
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['item'].queryset = Item.objects.filter(inativo=False).order_by('descricao')
        self.fields['item'].empty_label = '— Selecione o item —'
        self.fields['identificacao'].required = False

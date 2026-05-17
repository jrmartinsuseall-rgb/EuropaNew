from django import forms
from .models import Pedido
from cadastros.models import ClienteFornecedor, CondicaoPagamento, TabelaPreco, Metodo

CSS        = 'form-control form-control-sm'
CSS_SELECT = 'form-select form-select-sm'
CSS_DATE   = 'form-control form-control-sm'


class PedidoForm(forms.ModelForm):
    class Meta:
        model  = Pedido
        fields = ['datavenda', 'previnstal', 'numgrafico', 'cliente', 'condicao', 'tabela', 'metodo', 'observacao']
        widgets = {
            'datavenda':   forms.DateInput(attrs={'class': CSS_DATE, 'type': 'date'}, format='%Y-%m-%d'),
            'previnstal':  forms.DateInput(attrs={'class': CSS_DATE, 'type': 'date'}, format='%Y-%m-%d'),
            'numgrafico':  forms.TextInput(attrs={'class': CSS, 'maxlength': '20', 'placeholder': 'Ex: OS-0001'}),
            'cliente':     forms.Select(attrs={'class': CSS_SELECT}),
            'condicao':    forms.Select(attrs={'class': CSS_SELECT, '@change': 'onCondicaoChange($event)'}),
            'tabela':      forms.Select(attrs={'class': CSS_SELECT}),
            'metodo':      forms.Select(attrs={'class': CSS_SELECT}),
            'observacao':  forms.Textarea(attrs={'class': CSS, 'rows': 2}),
        }

    vendedor = forms.ChoiceField(
        label='Vendedor',
        required=False,
        widget=forms.Select(attrs={'class': CSS_SELECT}),
    )

    def __init__(self, *args, empresa_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        base_cli   = ClienteFornecedor.objects.filter(tipocliforemp='C', inativo=False)
        base_cond  = CondicaoPagamento.objects.filter(inativo=False)
        base_tab   = TabelaPreco.objects.filter(inativo=False)
        base_metod = Metodo.objects.filter(inativo=False)
        base_vend  = ClienteFornecedor.objects.filter(tipocliforemp='V', inativo=False)
        if empresa_id:
            base_cli   = base_cli.filter(empresa_id=empresa_id)
            base_cond  = base_cond.filter(empresa_id=empresa_id)
            base_tab   = base_tab.filter(empresa_id=empresa_id)
            base_metod = base_metod.filter(empresa_id=empresa_id)
            base_vend  = base_vend.filter(empresa_id=empresa_id)

        self.fields['cliente'].queryset    = base_cli.order_by('razao', 'nome')
        self.fields['cliente'].empty_label = '— Selecione o cliente —'
        self.fields['condicao'].queryset   = base_cond.order_by('descricao')
        self.fields['condicao'].empty_label = '— Condição (opcional) —'
        self.fields['condicao'].required   = False
        self.fields['tabela'].queryset     = base_tab.order_by('descricao')
        self.fields['tabela'].empty_label  = '— Tabela de Preço (opcional) —'
        self.fields['tabela'].required     = False
        self.fields['metodo'].queryset     = base_metod.order_by('descricao')
        self.fields['metodo'].empty_label  = '— Método de Pgto (opcional) —'
        self.fields['metodo'].required     = False
        self.fields['previnstal'].required = False

        vendedores = [('', '— Vendedor (opcional) —')]
        vendedores += [
            (str(v.pk), v.razao or v.nome)
            for v in base_vend.order_by('razao', 'nome')
        ]
        self.fields['vendedor'].choices = vendedores

        # pre-fill from instance
        if self.instance and self.instance.pk and self.instance.idvendrepre:
            self.fields['vendedor'].initial = str(self.instance.idvendrepre)

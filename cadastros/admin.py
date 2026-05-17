from django.contrib import admin
from .models import (
    Grupo, Item, Portador, Metodo, CondicaoPagamento,
    TabelaPreco, ItemTabelaPreco,
    ClienteFornecedor, TelefoneAdicional, HistoricoCliente,
)


@admin.register(Grupo)
class GrupoAdmin(admin.ModelAdmin):
    list_display = ('idgrupo', 'descricao', 'idgrupopai', 'classificacao', 'inativo')
    list_filter = ('inativo',)
    search_fields = ('descricao',)


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('iditem', 'identificacao', 'descricao', 'unidade', 'grupo', 'precobase', 'saldoestoque', 'inativo')
    list_filter = ('grupo', 'inativo', 'tipoitem')
    search_fields = ('descricao', 'identificacao', 'modelo')
    fieldsets = (
        ('Dados Principais', {
            'fields': ('identificacao', 'descricao', 'modelo', 'unidade', 'grupo', 'tipoitem', 'inativo')
        }),
        ('Preço e Comissão', {
            'fields': ('precobase', 'basecomissao', 'codforn')
        }),
        ('Estoque', {
            'fields': ('saldoestoque', 'tempotroca', 'mpestoque')
        }),
    )


@admin.register(Portador)
class PortadorAdmin(admin.ModelAdmin):
    list_display = ('idportador', 'descricao', 'inativo')
    list_filter = ('inativo',)
    search_fields = ('descricao',)


@admin.register(Metodo)
class MetodoAdmin(admin.ModelAdmin):
    list_display = ('idmetodo', 'sigla', 'descricao', 'movcaixa', 'inativo')
    list_filter = ('movcaixa', 'inativo')
    search_fields = ('descricao', 'sigla')


@admin.register(CondicaoPagamento)
class CondicaoPagamentoAdmin(admin.ModelAdmin):
    list_display = ('idcondpag', 'descricao', 'parcelas', 'dias', 'inativo')
    list_filter = ('inativo',)
    search_fields = ('descricao',)


class ItemTabelaPrecoInline(admin.TabularInline):
    model = ItemTabelaPreco
    extra = 0
    fields = ('item', 'identificacao', 'preco', 'i_pagto', 'ii_pagto', 'iii_pagto')


@admin.register(TabelaPreco)
class TabelaPrecoAdmin(admin.ModelAdmin):
    list_display = ('idtabela', 'descricao', 'datavalidade', 'empresa', 'inativo')
    list_filter = ('inativo', 'empresa')
    search_fields = ('descricao',)
    inlines = [ItemTabelaPrecoInline]


class TelefoneAdicionalInline(admin.TabularInline):
    model = TelefoneAdicional
    extra = 0
    fields = ('numero', 'identificacao', 'relacao', 'descricao')


class HistoricoClienteInline(admin.TabularInline):
    model = HistoricoCliente
    extra = 0
    readonly_fields = ('datavenda', 'descricao', 'quantidade', 'valorunit', 'valortotal', 'vendedor')
    fields = ('datavenda', 'descricao', 'quantidade', 'valortotal', 'vendedor')
    can_delete = False


@admin.register(ClienteFornecedor)
class ClienteFornecedorAdmin(admin.ModelAdmin):
    list_display = ('idcliforemp', 'nome_exibicao', 'tipocliforemp', 'tipopessoa', 'cnpjcpf', 'fone', 'celular', 'inativo')
    list_filter = ('tipocliforemp', 'tipopessoa', 'inativo', 'empresa')
    search_fields = ('razao', 'nome', 'fantasia', 'cnpjcpf', 'fone', 'celular')
    inlines = [TelefoneAdicionalInline, HistoricoClienteInline]
    fieldsets = (
        ('Identificação', {
            'fields': ('tipocliforemp', 'tipopessoa', 'empresa', 'classificacao', 'inativo')
        }),
        ('Dados Cadastrais', {
            'fields': ('razao', 'fantasia', 'nome', 'cnpjcpf', 'identinscr', 'estadocivil', 'datacadastro')
        }),
        ('Endereço', {
            'fields': ('endereco', 'numero', 'bairro', 'cep', 'cidade', 'edificio', 'apto', 'referencia')
        }),
        ('Contato', {
            'fields': ('fone', 'celular', 'email', 'convfone', 'convcelular', 'convcelular1', 'convcelular2')
        }),
        ('Dados Pessoais (PF)', {
            'fields': ('fdatanasc', 'fdataexpid', 'fufexpid', 'fnomepai', 'fnomemae',
                       'fempregador', 'fcargo', 'ffoneempre', 'favalista', 'responsavel'),
            'classes': ('collapse',)
        }),
        ('Comercial', {
            'fields': ('idvendrepre', 'nomevendedor', 'limitecredito', 'perccomiss',
                       'perccomissp', 'tipovendedor', 'equipe', 'dataultvenda', 'dtproximaTroca'),
            'classes': ('collapse',)
        }),
        ('Observações', {
            'fields': ('observacao', 'obscobranca'),
            'classes': ('collapse',)
        }),
    )

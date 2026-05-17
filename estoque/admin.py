from django.contrib import admin
from .models import (
    NotaFiscalEntrada, ItemNFEntrada,
    MovimentoEstoque,
    Requisicao, ItemRequisicao,
)


class ItemNFEntradaInline(admin.TabularInline):
    model = ItemNFEntrada
    extra = 0
    fields = ('identificacao', 'quantidade', 'valorunitario', 'ipi', 'icms', 'cfop', 'valortotal')


@admin.register(NotaFiscalEntrada)
class NotaFiscalEntradaAdmin(admin.ModelAdmin):
    list_display = ('idnfentrada', 'numeronf', 'serie', 'fornecedor', 'dataentrada', 'valortotalnf', 'status')
    list_filter = ('status', 'empresa', 'dataentrada')
    search_fields = ('numeronf', 'chaveacesso', 'fornecedor__razao', 'fornecedor__nome')
    date_hierarchy = 'dataentrada'
    inlines = [ItemNFEntradaInline]
    fieldsets = (
        ('Identificação', {
            'fields': ('empresa', 'fornecedor', 'numeronf', 'serie', 'chaveacesso', 'status')
        }),
        ('Datas', {
            'fields': ('dataemissao', 'dataentrada')
        }),
        ('Fiscal', {
            'fields': ('cfop', 'condicao', 'metodo', 'tipofrete', 'idtransporte')
        }),
        ('Totais', {
            'fields': ('quantidade', 'valortotalitens', 'valorfrete',
                       'valoracrecimo', 'valordesconto', 'valoripi', 'valoricms', 'valortotalnf')
        }),
        ('Observação', {
            'fields': ('observacao',),
            'classes': ('collapse',)
        }),
    )


@admin.register(MovimentoEstoque)
class MovimentoEstoqueAdmin(admin.ModelAdmin):
    list_display = ('idmovimento', 'item', 'data', 'ent_sai', 'quantidade', 'origem', 'idorigem', 'usuariologado')
    list_filter = ('ent_sai', 'origem', 'empresa', 'data')
    search_fields = ('item__descricao', 'item__identificacao', 'usuariologado')
    date_hierarchy = 'data'


class ItemRequisicaoInline(admin.TabularInline):
    model = ItemRequisicao
    extra = 0
    fields = ('identificacao', 'quantidade', 'atendido', 'saldo')


@admin.register(Requisicao)
class RequisicaoAdmin(admin.ModelAdmin):
    list_display = ('idrequisicao', 'empresa', 'cliforemp', 'data', 'status', 'dataatendi')
    list_filter = ('status', 'empresa', 'data')
    search_fields = ('cliforemp__razao', 'cliforemp__nome', 'observacao')
    date_hierarchy = 'data'
    inlines = [ItemRequisicaoInline]
    fieldsets = (
        ('Cabeçalho', {
            'fields': ('empresa', 'cliforemp', 'data', 'status', 'dataatendi')
        }),
        ('Origem', {
            'fields': ('origem', 'idorigem')
        }),
        ('Observação', {
            'fields': ('observacao',),
            'classes': ('collapse',)
        }),
    )

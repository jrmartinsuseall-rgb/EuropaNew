from django.contrib import admin
from .models import (
    Pedido, ItemPedido, ParcelaPedido,
    ConfiguracaoComissao, AcertoComissao, MovimentoComissao,
    Resumo, LogSistema,
)


# ─── Pedido ───────────────────────────────────────────────────────────────────

class ItemPedidoInline(admin.TabularInline):
    model = ItemPedido
    extra = 0
    fields = ('identificacao', 'item', 'quantidade', 'valorunitario', 'instalacao', 'valortotal', 'estoqueok')
    readonly_fields = ('valortotal',)


class ParcelaPedidoInline(admin.TabularInline):
    model = ParcelaPedido
    extra = 0
    fields = ('parcela', 'vencimento', 'valor')


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ('numero', 'cliente', 'datavenda', 'valortotal', 'status', 'idvendrepre', 'datafat')
    list_filter = ('status', 'empresa', 'datavenda', 'condicao', 'metodo')
    search_fields = ('numero', 'numgrafico', 'cliente__razao', 'cliente__nome')
    date_hierarchy = 'datavenda'
    inlines = [ItemPedidoInline, ParcelaPedidoInline]
    fieldsets = (
        ('Identificação', {
            'fields': ('empresa', 'numero', 'numgrafico', 'status')
        }),
        ('Cliente / Vendedor', {
            'fields': ('cliente', 'idvendrepre', 'idtecnico', 'idcliente_conv')
        }),
        ('Datas', {
            'fields': ('datagrav', 'datavenda', 'previnstal', 'datafat', 'datainstal', 'datacancela')
        }),
        ('Pagamento', {
            'fields': ('condicao', 'tabela', 'metodo', 'valortotal')
        }),
        ('Cancelamento', {
            'fields': ('motivocancela',),
            'classes': ('collapse',)
        }),
        ('Observação', {
            'fields': ('observacao',),
            'classes': ('collapse',)
        }),
        ('Controles Internos', {
            'fields': ('control_conf', 'comissaook', 'marca', 'idorigem'),
            'classes': ('collapse',)
        }),
    )


# ─── Comissão ─────────────────────────────────────────────────────────────────

@admin.register(ConfiguracaoComissao)
class ConfiguracaoComissaoAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Televendas', {
            'fields': ('telprazo', 'telav', 'telpremio')
        }),
        ('Meios de Pagamento', {
            'fields': ('meiprazo', 'meiav', 'meipremio')
        }),
        ('Revendas — Faixas de Volume', {
            'fields': ('revfaixa1', 'revfaixa2', 'revfaixa3', 'revfaixa4')
        }),
        ('Revendas — % Naturais', {
            'fields': ('revpercnat1', 'revpercnat2', 'revpercnat3', 'revpercnat4')
        }),
        ('Revendas — % Elétricos', {
            'fields': ('revpercele1', 'revpercele2', 'revpercele3', 'revpercele4')
        }),
    )


class MovimentoComissaoInline(admin.TabularInline):
    model = MovimentoComissao
    extra = 0
    fields = ('cliente', 'pedido', 'identificacao', 'valortotal', 'perccomiss', 'valorcomiss')
    readonly_fields = ('valorcomiss',)


@admin.register(AcertoComissao)
class AcertoComissaoAdmin(admin.ModelAdmin):
    list_display = ('idacertocomiss', 'idvendrepre', 'emissao', 'perildoini', 'periodofim',
                    'totalvendido', 'totalcomissao', 'status')
    list_filter = ('status', 'empresa', 'emissao')
    search_fields = ('idvendrepre',)
    date_hierarchy = 'emissao'
    inlines = [MovimentoComissaoInline]
    fieldsets = (
        ('Identificação', {
            'fields': ('empresa', 'idvendrepre', 'emissao', 'status')
        }),
        ('Período', {
            'fields': ('perildoini', 'periodofim')
        }),
        ('Totais', {
            'fields': ('totalvendido', 'totalbase', 'totalcomissao', 'percpremio')
        }),
        ('Observação', {
            'fields': ('observacao',),
            'classes': ('collapse',)
        }),
    )


# ─── Resumo / Log ─────────────────────────────────────────────────────────────

@admin.register(Resumo)
class ResumoAdmin(admin.ModelAdmin):
    list_display = ('id', 'empresa', 'seq', 'descricao', 'valor')
    list_filter = ('empresa',)
    search_fields = ('descricao',)


@admin.register(LogSistema)
class LogSistemaAdmin(admin.ModelAdmin):
    list_display = ('id', 'date', 'time', 'description')
    list_filter = ('date',)
    search_fields = ('description',)
    date_hierarchy = 'date'

from django.contrib import admin
from .models import (
    TeleVenda, ItemTeleVenda, ParcelaTeleVenda,
    Roteiro, OSRoteiro, TecnicoRoteiro,
    BoletoRoteiro, CobrancaRoteiro,
)


# ─── TeleVenda / OS ───────────────────────────────────────────────────────────

class ItemTeleVendaInline(admin.TabularInline):
    model = ItemTeleVenda
    extra = 0
    fields = ('identificacao', 'item', 'quantidade', 'valorunitario', 'instalacao', 'valortotal')
    readonly_fields = ('valortotal',)


class ParcelaTeleVendaInline(admin.TabularInline):
    model = ParcelaTeleVenda
    extra = 0
    fields = ('parcela', 'vencimento', 'valor')


@admin.register(TeleVenda)
class TeleVendaAdmin(admin.ModelAdmin):
    list_display = ('numero', 'cliente', 'dataprevisao', 'atend_periodo',
                    'idtecnico', 'valortotal', 'status', 'impresso')
    list_filter = ('status', 'empresa', 'dataprevisao', 'atend_periodo', 'equipe')
    search_fields = ('numero', 'cliente__razao', 'cliente__nome', 'usuariolanc')
    date_hierarchy = 'dataprevisao'
    inlines = [ItemTeleVendaInline, ParcelaTeleVendaInline]
    fieldsets = (
        ('Identificação', {
            'fields': ('empresa', 'numero', 'status', 'impresso')
        }),
        ('Cliente / Equipe', {
            'fields': ('cliente', 'idvendrepre', 'idtecnico', 'equipe', 'idusuario', 'usuariolanc')
        }),
        ('Datas', {
            'fields': ('dataemissao', 'dataprevisao', 'datainstal', 'datahora')
        }),
        ('Atendimento', {
            'fields': ('atend_periodo', 'atend_hora', 'atend_obs')
        }),
        ('Pagamento', {
            'fields': ('tabela', 'condicao', 'metodo', 'quantidadetotal', 'valortotal')
        }),
        ('Cancelamento', {
            'fields': ('motivocancel',),
            'classes': ('collapse',)
        }),
        ('Controles', {
            'fields': ('marca', 'idassroteiro'),
            'classes': ('collapse',)
        }),
    )


# ─── Roteiro de Assistência ───────────────────────────────────────────────────

class OSRoteiroInline(admin.TabularInline):
    model = OSRoteiro
    extra = 0
    fields = ('cliente', 'telvenda', 'execucao', 'recebimento')


class TecnicoRoteiroInline(admin.TabularInline):
    model = TecnicoRoteiro
    extra = 0
    fields = ('tecnico', 'mat_capacidade', 'ves_capacidade', 'destino')


class BoletoRoteiroInline(admin.TabularInline):
    model = BoletoRoteiro
    extra = 0
    fields = ('cliente', 'contarec', 'status')


class CobrancaRoteiroInline(admin.TabularInline):
    model = CobrancaRoteiro
    extra = 0
    fields = ('cliente', 'contarec', 'valor', 'valoratualizado', 'mesesatraso', 'status')
    readonly_fields = ('valoratualizado',)


@admin.register(Roteiro)
class RoteiroAdmin(admin.ModelAdmin):
    list_display = ('idassroteiro', 'dateemissao', 'empresa', 'qtdassistencias',
                    'qtde_matutino', 'qtde_vespertino', 'status', 'requisicaook')
    list_filter = ('status', 'empresa', 'dateemissao')
    search_fields = ('destino', 'cliforemp__razao')
    date_hierarchy = 'dateemissao'
    inlines = [TecnicoRoteiroInline, OSRoteiroInline, BoletoRoteiroInline, CobrancaRoteiroInline]
    fieldsets = (
        ('Identificação', {
            'fields': ('empresa', 'dateemissao', 'status', 'destino')
        }),
        ('Capacidade', {
            'fields': ('qtdassistencias', 'qtde_matutino', 'qtde_vespertino')
        }),
        ('Vinculações', {
            'fields': ('cliforemp', 'idrequisicao', 'requisicaook')
        }),
    )

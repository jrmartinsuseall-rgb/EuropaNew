from django.contrib import admin
from .models import (
    PlanoConta, SubConta,
    OperadoraCartao,
    ContaReceber, ContaPagar,
    AberturaCaixa, MovimentoCaixa,
    Cheque, MovimentoCartao,
    Renegociacao, ParcelaRenegociacao,
    ReceitaMorta,
)


# ─── Plano de Contas ─────────────────────────────────────────────────────────

class SubContaInline(admin.TabularInline):
    model = SubConta
    extra = 0
    fields = ('descricao', 'inativo')


@admin.register(PlanoConta)
class PlanoContaAdmin(admin.ModelAdmin):
    list_display = ('idconta', 'descricao', 'deb_cred', 'descrigrupo', 'inativo')
    list_filter = ('deb_cred', 'inativo')
    search_fields = ('descricao', 'descrigrupo')
    inlines = [SubContaInline]


@admin.register(SubConta)
class SubContaAdmin(admin.ModelAdmin):
    list_display = ('idsubconta', 'conta', 'descricao', 'inativo')
    list_filter = ('inativo', 'conta')
    search_fields = ('descricao',)


# ─── Operadora de Cartão ─────────────────────────────────────────────────────

@admin.register(OperadoraCartao)
class OperadoraCartaoAdmin(admin.ModelAdmin):
    list_display = ('idopercard', 'descricao', 'banco', 'taxa', 'diavencto', 'inativo')
    list_filter = ('inativo', 'empresa')
    search_fields = ('descricao', 'contrato')


# ─── Contas a Receber ─────────────────────────────────────────────────────────

@admin.register(ContaReceber)
class ContaReceberAdmin(admin.ModelAdmin):
    list_display = ('idcontarec', 'cliente', 'parcela', 'valor', 'vencimento', 'pagamento', 'status')
    list_filter = ('status', 'empresa', 'vencimento', 'portador')
    search_fields = ('cliente__razao', 'cliente__nome', 'numerodoc')
    date_hierarchy = 'vencimento'
    fieldsets = (
        ('Identificação', {
            'fields': ('empresa', 'cliente', 'data', 'parcela', 'numerodoc', 'status')
        }),
        ('Valores', {
            'fields': ('valor', 'valorpago', 'juros', 'descontos', 'vencimento', 'pagamento')
        }),
        ('Pagamento', {
            'fields': ('portador', 'banco', 'tipobaixa', 'numerobanco', 'reccheque')
        }),
        ('Cartão', {
            'fields': ('operadora', 'parcelascard'),
            'classes': ('collapse',)
        }),
        ('Outros', {
            'fields': ('idpedido', 'idassroteiro', 'idtecnico', 'cliente_conv', 'movcadok', 'marca'),
            'classes': ('collapse',)
        }),
    )


# ─── Contas a Pagar ───────────────────────────────────────────────────────────

@admin.register(ContaPagar)
class ContaPagarAdmin(admin.ModelAdmin):
    list_display = ('idcontapag', 'fornecedor', 'parcela', 'valor', 'vencimento', 'pagamento', 'status')
    list_filter = ('status', 'empresa', 'vencimento', 'portador')
    search_fields = ('fornecedor__razao', 'fornecedor__nome', 'numerodoc')
    date_hierarchy = 'vencimento'
    fieldsets = (
        ('Identificação', {
            'fields': ('empresa', 'fornecedor', 'data', 'parcela', 'numerodoc', 'status')
        }),
        ('Valores', {
            'fields': ('valor', 'valorpago', 'juros', 'descontos', 'vencimento', 'pagamento')
        }),
        ('Pagamento', {
            'fields': ('portador', 'banco', 'tipobaixa')
        }),
    )


# ─── Caixa ────────────────────────────────────────────────────────────────────

@admin.register(AberturaCaixa)
class AberturaCaixaAdmin(admin.ModelAdmin):
    list_display = ('idautenticacao', 'usuabre', 'dataabre', 'horaabre', 'usufecha', 'datafecha', 'saldo')
    list_filter = ('dataabre',)
    search_fields = ('usuabre', 'usufecha')
    date_hierarchy = 'dataabre'


@admin.register(MovimentoCaixa)
class MovimentoCaixaAdmin(admin.ModelAdmin):
    list_display = ('id', 'data', 'descricao', 'tipo', 'valor', 'saldo', 'status', 'empresa')
    list_filter = ('tipo', 'status', 'empresa', 'data')
    search_fields = ('descricao', 'documento', 'cliforemp__razao')
    date_hierarchy = 'data'


# ─── Cheques ──────────────────────────────────────────────────────────────────

@admin.register(Cheque)
class ChequeAdmin(admin.ModelAdmin):
    list_display = ('idcheque', 'numero', 'emitente', 'valor', 'vencimento', 'bompara', 'status', 'portador')
    list_filter = ('status', 'empresa', 'portador')
    search_fields = ('emitente', 'cnpjcpf', 'numero')
    date_hierarchy = 'vencimento'
    fieldsets = (
        ('Cheque', {
            'fields': ('empresa', 'numero', 'emitente', 'cnpjcpf', 'valor', 'status')
        }),
        ('Datas', {
            'fields': ('dataemissao', 'vencimento', 'bompara', 'baixa')
        }),
        ('Banco do Cheque', {
            'fields': ('bancocheq', 'agencia', 'conta')
        }),
        ('Destino', {
            'fields': ('portador', 'banco', 'destino', 'cliforemp')
        }),
    )


# ─── Cartão ───────────────────────────────────────────────────────────────────

@admin.register(MovimentoCartao)
class MovimentoCartaoAdmin(admin.ModelAdmin):
    list_display = ('id', 'operadora', 'contarec', 'parcela', 'vencimento', 'valor', 'encargos', 'saldo')
    list_filter = ('operadora', 'empresa')
    date_hierarchy = 'vencimento'


# ─── Renegociação ─────────────────────────────────────────────────────────────

class ParcelaRenegociacaoInline(admin.TabularInline):
    model = ParcelaRenegociacao
    extra = 0
    fields = ('contarec', 'selecionados')


@admin.register(Renegociacao)
class RenegociacaoAdmin(admin.ModelAdmin):
    list_display = ('idreneg', 'cliente', 'data', 'valorreneg', 'valorfinal', 'parcelas', 'status')
    list_filter = ('status', 'empresa', 'data')
    search_fields = ('cliente__razao', 'cliente__nome')
    date_hierarchy = 'data'
    inlines = [ParcelaRenegociacaoInline]
    fieldsets = (
        ('Cabeçalho', {
            'fields': ('empresa', 'cliente', 'data', 'idusuario', 'status')
        }),
        ('Valores', {
            'fields': ('valorreneg', 'valoracre', 'valordesc', 'valorfinal', 'parcelas', 'pvencimento')
        }),
        ('Observação', {
            'fields': ('observacao',),
            'classes': ('collapse',)
        }),
    )


# ─── Arquivo Morto ────────────────────────────────────────────────────────────

@admin.register(ReceitaMorta)
class ReceitaMortaAdmin(admin.ModelAdmin):
    list_display = ('id', 'idcontarec', 'cliforemp', 'valor', 'vencimento', 'pagamento', 'status')
    list_filter = ('status', 'empresa')
    search_fields = ('cliforemp__razao', 'cliforemp__nome', 'numerodoc')
    date_hierarchy = 'vencimento'

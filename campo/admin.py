from django.contrib import admin
from campo.models import Servico, ServTecnico, ServMaterial, ServApontamento, ServTempo, ScriptMensagem


class ServTecnicoInline(admin.TabularInline):
    model = ServTecnico
    extra = 0
    fields = ['nome', 'origem', 'papel', 'user', 'crm_id']
    readonly_fields = ['nome']


class ServMaterialInline(admin.TabularInline):
    model = ServMaterial
    extra = 0
    fields = ['item_codigo', 'item_descricao', 'quantidade_prevista', 'quantidade_realizada', 'origem']


class ServApontamentoInline(admin.TabularInline):
    model = ServApontamento
    extra = 0
    fields = ['tipo', 'descricao', 'arquivo', 'user', 'registrado_em']
    readonly_fields = ['registrado_em']


class ServTempoInline(admin.TabularInline):
    model = ServTempo
    extra = 0
    fields = ['evento', 'timestamp', 'user', 'observacao']


@admin.register(Servico)
class ServicoAdmin(admin.ModelAdmin):
    list_display  = ['id', 'tipo_atividade', 'cliente_nome', 'status', 'origem', 'data_prevista', 'prioridade']
    list_filter   = ['status', 'origem', 'data_prevista']
    search_fields = ['os_codigo', 'cliente_nome', 'tipo_atividade']
    ordering      = ['prioridade', 'data_prevista']
    inlines       = [ServTecnicoInline, ServMaterialInline, ServApontamentoInline, ServTempoInline]


@admin.register(ScriptMensagem)
class ScriptMensagemAdmin(admin.ModelAdmin):
    list_display       = ['ordem', 'titulo', 'ativo']
    list_display_links = ['titulo']
    list_editable      = ['ordem', 'ativo']
    ordering           = ['ordem', 'titulo']
    fields             = ['titulo', 'corpo', 'ativo', 'ordem']

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['corpo'].help_text = (
            'Variáveis disponíveis: {cliente} · {os} · {servico} · {local} · '
            '{ativo} · {data} · {tecnico} · {laudo} · {materiais}'
        )
        return form

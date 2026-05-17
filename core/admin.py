from django.contrib import admin
from .models import Cidade, Empresa, Banco, Cfop, PerfilUsuario, Controle


@admin.register(Cidade)
class CidadeAdmin(admin.ModelAdmin):
    list_display = ('idcidade', 'descricao', 'uf', 'codibge', 'inativo')
    list_filter = ('uf', 'inativo')
    search_fields = ('descricao', 'codibge')
    list_per_page = 50


@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ('idempresa', 'razao', 'cnpj', 'fone', 'email', 'inativo')
    list_filter = ('inativo',)
    search_fields = ('razao', 'cnpj')
    fieldsets = (
        ('Dados Principais', {
            'fields': ('razao', 'cnpj', 'ie', 'inativo')
        }),
        ('Contato', {
            'fields': ('fone', 'celular', 'foneass', 'fonewhats', 'email')
        }),
        ('Endereço', {
            'fields': ('endereco', 'numero', 'bairro', 'cep', 'cidade')
        }),
        ('Parâmetros', {
            'fields': ('set_baixadireta', 'set_baixafat',
                       'cor_cad', 'cor_adm', 'cor_tel', 'cor_fin', 'cor_est'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Banco)
class BancoAdmin(admin.ModelAdmin):
    list_display = ('idbanco', 'numero', 'descricao', 'agencia', 'conta', 'inativo')
    list_filter = ('inativo',)
    search_fields = ('descricao', 'numero')


@admin.register(Cfop)
class CfopAdmin(admin.ModelAdmin):
    list_display = ('idcfop', 'descricao', 'tipo', 'inativo')
    list_filter = ('tipo', 'inativo')
    search_fields = ('descricao',)


@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'nivel_adm', 'ultimo_acesso', 'ultimo_modulo', 'inativo')
    list_filter = ('inativo', 'acesso_cadastro', 'acesso_financeiro', 'acesso_estoque')
    search_fields = ('usuario__username', 'usuario__first_name')
    fieldsets = (
        ('Usuário', {
            'fields': ('usuario', 'nivel_adm', 'idvendedor', 'inativo')
        }),
        ('Último Acesso', {
            'fields': ('ultimo_acesso', 'ultimo_hora', 'ultimo_modulo')
        }),
        ('Permissões por Módulo', {
            'fields': ('acesso_cadastro', 'acesso_administrativo',
                       'acesso_televendas', 'acesso_financeiro', 'acesso_estoque')
        }),
    )


@admin.register(Controle)
class ControleAdmin(admin.ModelAdmin):
    list_display = ('id', 'idempresa', 'idusuario', 'idpedido', 'idcontarec', 'idcontapag')

from django.db import models
from django.contrib.auth.models import User


class Cidade(models.Model):
    idcidade = models.AutoField(primary_key=True)
    descricao = models.CharField('Cidade', max_length=100)
    uf = models.CharField('UF', max_length=2)
    codibge = models.CharField('Cód. IBGE', max_length=10, blank=True)
    inativo = models.BooleanField('Inativo', default=False)

    class Meta:
        db_table = 'cidades'
        ordering = ['descricao']
        verbose_name = 'Cidade'
        verbose_name_plural = 'Cidades'

    def __str__(self):
        return f'{self.descricao} - {self.uf}'


class Empresa(models.Model):
    idempresa = models.AutoField(primary_key=True)
    razao = models.CharField('Razão Social', max_length=150)
    cnpj = models.CharField('CNPJ', max_length=18, unique=True)
    ie = models.CharField('Insc. Estadual', max_length=20, blank=True)
    fone = models.CharField('Telefone', max_length=20, blank=True)
    celular = models.CharField('Celular', max_length=20, blank=True)
    foneass = models.CharField('Fone Assistência', max_length=20, blank=True)
    fonewhats = models.CharField('WhatsApp', max_length=20, blank=True)
    email = models.EmailField('E-mail', blank=True)
    endereco = models.CharField('Endereço', max_length=200, blank=True)
    bairro = models.CharField('Bairro', max_length=100, blank=True)
    numero = models.CharField('Número', max_length=10, blank=True)
    cep = models.CharField('CEP', max_length=10, blank=True)
    cidade = models.ForeignKey(
        Cidade, on_delete=models.PROTECT,
        null=True, blank=True, verbose_name='Cidade'
    )
    inativo = models.BooleanField('Inativo', default=False)
    # Cores dos módulos (configuração visual)
    cor_cad = models.IntegerField('Cor Cadastro', default=0)
    cor_adm = models.IntegerField('Cor Admin', default=0)
    cor_tel = models.IntegerField('Cor TeleVendas', default=0)
    cor_fin = models.IntegerField('Cor Financeiro', default=0)
    cor_est = models.IntegerField('Cor Estoque', default=0)
    # Parâmetros operacionais
    set_baixadireta = models.BooleanField('Baixa Direta', default=False)
    set_baixafat    = models.BooleanField('Baixa Faturamento', default=False)
    # Integrações externas
    maps_api_key    = models.CharField('Google Maps API Key', max_length=200, blank=True)
    # Controle de acesso
    senha_expiry_days = models.IntegerField('Expiração de Senha (dias)', default=0,
                                            help_text='0 = nunca expira')

    class Meta:
        db_table = 'empresas'
        ordering = ['razao']
        verbose_name = 'Empresa'
        verbose_name_plural = 'Empresas'

    def __str__(self):
        return self.razao


class Banco(models.Model):
    idbanco = models.AutoField(primary_key=True)
    descricao = models.CharField('Descrição', max_length=100)
    numero = models.CharField('Número', max_length=10)
    agencia = models.CharField('Agência', max_length=20, blank=True)
    conta = models.CharField('Conta', max_length=30, blank=True)
    convenio = models.CharField('Convênio', max_length=30, blank=True)
    numeroboleto = models.IntegerField('Próx. Nº Boleto', default=0)
    jurosmora = models.DecimalField('Juros Mora %', max_digits=5, decimal_places=2, default=0)
    inativo = models.BooleanField('Inativo', default=False)

    class Meta:
        db_table = 'bancos'
        ordering = ['descricao']
        verbose_name = 'Banco'
        verbose_name_plural = 'Bancos'

    def __str__(self):
        return f'{self.numero} - {self.descricao}'


class Cfop(models.Model):
    TIPO_CHOICES = [('E', 'Entrada'), ('S', 'Saída')]

    idcfop = models.AutoField(primary_key=True)
    descricao = models.CharField('Descrição', max_length=200)
    tipo = models.CharField('Tipo', max_length=1, choices=TIPO_CHOICES)
    observacao = models.TextField('Observação', blank=True)
    inativo = models.BooleanField('Inativo', default=False)

    class Meta:
        db_table = 'cfop'
        ordering = ['descricao']
        verbose_name = 'CFOP'
        verbose_name_plural = 'CFOPs'

    def __str__(self):
        return f'{self.idcfop} - {self.descricao}'


class PerfilUsuario(models.Model):
    """Estende o User do Django com campos do VDF (usuarios.fd)."""
    usuario = models.OneToOneField(
        User, on_delete=models.CASCADE,
        related_name='perfil', verbose_name='Usuário'
    )
    empresa = models.ForeignKey(
        Empresa, on_delete=models.PROTECT,
        null=True, blank=True, verbose_name='Empresa'
    )
    nivel_adm = models.IntegerField('Nível Admin', default=0)
    idvendedor = models.IntegerField('ID Vendedor', default=0)
    ultimo_acesso = models.DateField('Último Acesso', null=True, blank=True)
    ultimo_hora = models.CharField('Última Hora', max_length=8, blank=True)
    ultimo_modulo = models.CharField('Último Módulo', max_length=30, blank=True)
    inativo = models.BooleanField('Inativo', default=False)
    password_changed_at = models.DateField('Última Troca de Senha', null=True, blank=True)
    # Permissões por módulo (mapeado de usuarios.fd)
    acesso_cadastro = models.BooleanField('Cadastro', default=False)
    acesso_administrativo = models.BooleanField('Administrativo', default=False)
    acesso_televendas = models.BooleanField('TeleVendas', default=False)
    acesso_financeiro = models.BooleanField('Financeiro', default=False)
    acesso_estoque = models.BooleanField('Estoque', default=False)

    class Meta:
        db_table = 'perfil_usuario'
        verbose_name = 'Perfil de Usuário'
        verbose_name_plural = 'Perfis de Usuários'

    def __str__(self):
        return f'Perfil: {self.usuario.username}'


class ConfiguracaoCaixa(models.Model):
    """Parâmetros padrão do módulo de Caixa — um registro por empresa."""

    empresa = models.OneToOneField(
        Empresa, on_delete=models.CASCADE,
        null=True, blank=True, verbose_name='Empresa',
        related_name='cfg_caixa',
    )

    # ── Padrão para recebimento ──────────────────────────────
    conta_recebimento = models.ForeignKey(
        'financeiro.PlanoConta', on_delete=models.PROTECT,
        null=True, blank=True, related_name='+',
        verbose_name='Conta Recebimento'
    )
    subconta_recebimento = models.ForeignKey(
        'financeiro.SubConta', on_delete=models.PROTECT,
        null=True, blank=True, related_name='+',
        verbose_name='Sub-Conta Recebimento'
    )

    # ── Padrão para pagamento ────────────────────────────────
    conta_pagamento = models.ForeignKey(
        'financeiro.PlanoConta', on_delete=models.PROTECT,
        null=True, blank=True, related_name='+',
        verbose_name='Conta Pagamento'
    )
    subconta_pagamento = models.ForeignKey(
        'financeiro.SubConta', on_delete=models.PROTECT,
        null=True, blank=True, related_name='+',
        verbose_name='Sub-Conta Pagamento'
    )

    # ── Portadores de caixa (cheque + sangria/cofre) ─────────
    portador_cheque = models.ForeignKey(
        'cadastros.Portador', on_delete=models.PROTECT,
        null=True, blank=True, related_name='+',
        verbose_name='Portador Cheques'
    )
    portador_sangria = models.ForeignKey(
        'cadastros.Portador', on_delete=models.PROTECT,
        null=True, blank=True, related_name='+',
        verbose_name='Portador Sangria (Cofre)'
    )

    # ── Portadores por forma de pagamento ────────────────────
    portador_dinheiro = models.ForeignKey(
        'cadastros.Portador', on_delete=models.PROTECT,
        null=True, blank=True, related_name='+',
        verbose_name='Portador Dinheiro'
    )
    portador_cartao_deb = models.ForeignKey(
        'cadastros.Portador', on_delete=models.PROTECT,
        null=True, blank=True, related_name='+',
        verbose_name='Portador Cartão Débito'
    )
    portador_cartao_cred = models.ForeignKey(
        'cadastros.Portador', on_delete=models.PROTECT,
        null=True, blank=True, related_name='+',
        verbose_name='Portador Cartão Crédito'
    )
    portador_pix = models.ForeignKey(
        'cadastros.Portador', on_delete=models.PROTECT,
        null=True, blank=True, related_name='+',
        verbose_name='Portador PIX / Transferência'
    )

    # ── Banco padrão ─────────────────────────────────────────
    banco_padrao = models.ForeignKey(
        'core.Banco', on_delete=models.PROTECT,
        null=True, blank=True, related_name='+',
        verbose_name='Banco Padrão'
    )

    # ── Descrições padrão de lançamento ──────────────────────
    desc_entrada    = models.CharField('Descrição Entrada',    max_length=100, default='RECEBIMENTO')
    desc_saida      = models.CharField('Descrição Saída',      max_length=100, default='PAGAMENTO')
    desc_sangria    = models.CharField('Descrição Sangria',    max_length=100, default='SANGRIA DE CAIXA')
    desc_suprimento = models.CharField('Descrição Suprimento', max_length=100, default='SUPRIMENTO DE CAIXA')

    class Meta:
        db_table = 'cfgcaixa'
        verbose_name = 'Configuração de Caixa'
        verbose_name_plural = 'Configurações de Caixa'

    def __str__(self):
        return 'Configuração de Caixa'


class Projeto(models.Model):
    idprojeto = models.AutoField(primary_key=True)
    empresa = models.ForeignKey(
        Empresa, on_delete=models.PROTECT,
        null=True, blank=True, verbose_name='Empresa'
    )
    codigo = models.CharField('Código', max_length=20)
    descricao = models.CharField('Descrição', max_length=100)
    dataencerramento = models.DateField('Data Encerramento', null=True, blank=True)
    inativo = models.BooleanField('Inativo', default=False)

    class Meta:
        db_table = 'projetos'
        ordering = ['codigo']
        verbose_name = 'Projeto'
        verbose_name_plural = 'Projetos'

    def __str__(self):
        return f'{self.codigo} — {self.descricao}'


class ProjetoOrcamento(models.Model):
    idorcamento    = models.AutoField(primary_key=True)
    projeto        = models.ForeignKey(
        Projeto, on_delete=models.CASCADE,
        related_name='orcamentos', verbose_name='Projeto'
    )
    conta          = models.ForeignKey(
        'financeiro.PlanoConta', on_delete=models.PROTECT,
        verbose_name='Conta'
    )
    valor_estimado = models.DecimalField(
        'Valor Estimado', max_digits=12, decimal_places=2, default=0
    )

    class Meta:
        db_table     = 'projeto_orcamento'
        unique_together = [('projeto', 'conta')]
        ordering     = ['conta__deb_cred', 'conta__descrigrupo', 'conta__descricao']
        verbose_name = 'Orçamento do Projeto'


class Licenca(models.Model):
    """Licença de uso por empresa — gerada e gerenciada pelo superusuário."""
    empresa     = models.OneToOneField(
        Empresa, on_delete=models.CASCADE,
        related_name='licenca', verbose_name='Empresa'
    )
    chave       = models.TextField('Chave de Licença', blank=True)
    valid_from  = models.DateField('Válida de')
    valid_until = models.DateField('Válida até')
    max_usuarios = models.IntegerField('Máx. Usuários', default=5)
    ativa       = models.BooleanField('Ativa', default=True)
    criado_em   = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'licencas'
        ordering = ['empresa__razao']
        verbose_name = 'Licença'
        verbose_name_plural = 'Licenças'

    def __str__(self):
        return f'{self.empresa.razao} — até {self.valid_until}'

    @property
    def dias_para_expirar(self):
        from datetime import date
        return (self.valid_until - date.today()).days

    @property
    def is_valid(self):
        from datetime import date
        today = date.today()
        return self.ativa and self.valid_from <= today <= self.valid_until


class Controle(models.Model):
    """
    Tabela de controle de sequências do VDF.
    Mantida para compatibilidade na importação dos dados legados.
    Em produção Django usa sequences nativas do PostgreSQL.
    """
    idempresa = models.IntegerField(default=0)
    idusuario = models.IntegerField(default=0)
    idcidade = models.IntegerField(default=0)
    idtipoitem = models.IntegerField(default=0)
    idgrupo = models.IntegerField(default=0)
    iditem = models.IntegerField(default=0)
    idcondpag = models.IntegerField(default=0)
    idtabela = models.IntegerField(default=0)
    idtelvenda = models.IntegerField(default=0)
    idpedido = models.IntegerField(default=0)
    idmovitem = models.IntegerField(default=0)
    idmovcaixa = models.IntegerField(default=0)
    idcontarec = models.IntegerField(default=0)
    idcontapag = models.IntegerField(default=0)
    idappajuda = models.IntegerField(default=0)
    idmetodo = models.IntegerField(default=0)
    idportador = models.IntegerField(default=0)
    idbanco = models.IntegerField(default=0)
    idconta = models.IntegerField(default=0)
    idsubconta = models.IntegerField(default=0)
    idcliforemp = models.IntegerField(default=0)
    idcheque = models.IntegerField(default=0)
    idassroteiro = models.IntegerField(default=0)
    codigo_conv = models.IntegerField(default=0)
    numero = models.IntegerField(default=0)
    idopercard = models.IntegerField(default=0)
    idacertocomiss = models.IntegerField(default=0)
    idmovimento = models.IntegerField(default=0)
    idrequisicao = models.IntegerField(default=0)
    idnfentrada = models.IntegerField(default=0)
    idreneg = models.IntegerField(default=0)

    class Meta:
        db_table = 'controle'
        verbose_name = 'Controle de Sequências'

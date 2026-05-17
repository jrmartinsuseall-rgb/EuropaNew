from django.db import models
from core.models import Empresa, Banco
from cadastros.models import ClienteFornecedor, Portador


# ─── Plano de Contas ────────────────────────────────────────────────────────

class PlanoConta(models.Model):
    DEB_CRED_CHOICES = [('D', 'Débito'), ('C', 'Crédito')]

    idconta = models.AutoField(primary_key=True)
    empresa = models.ForeignKey(
        Empresa, on_delete=models.PROTECT,
        null=True, blank=True, verbose_name='Empresa'
    )
    descricao = models.CharField('Descrição', max_length=100)
    deb_cred = models.CharField('D/C', max_length=1, choices=DEB_CRED_CHOICES, blank=True)
    descrigrupo = models.CharField('Grupo', max_length=100, blank=True)
    inativo = models.BooleanField('Inativo', default=False)

    class Meta:
        db_table = 'tabconta'
        ordering = ['descricao']
        verbose_name = 'Plano de Conta'
        verbose_name_plural = 'Plano de Contas'

    def __str__(self):
        return self.descricao


class SubConta(models.Model):
    idsubconta = models.AutoField(primary_key=True)
    empresa = models.ForeignKey(
        Empresa, on_delete=models.PROTECT,
        null=True, blank=True, verbose_name='Empresa'
    )
    descricao = models.CharField('Descrição', max_length=100)
    conta = models.ForeignKey(
        PlanoConta, on_delete=models.PROTECT, verbose_name='Conta'
    )
    inativo = models.BooleanField('Inativo', default=False)

    class Meta:
        db_table = 'subconta'
        ordering = ['conta', 'descricao']
        verbose_name = 'Sub-Conta'
        verbose_name_plural = 'Sub-Contas'

    def __str__(self):
        return f'{self.conta} / {self.descricao}'


# ─── Operadora de Cartão ────────────────────────────────────────────────────

class OperadoraCartao(models.Model):
    idopercard = models.AutoField(primary_key=True)
    empresa = models.ForeignKey(
        Empresa, on_delete=models.PROTECT, verbose_name='Empresa'
    )
    banco = models.ForeignKey(
        Banco, on_delete=models.PROTECT,
        null=True, blank=True, verbose_name='Banco'
    )
    descricao = models.CharField('Descrição', max_length=100)
    contrato = models.CharField('Contrato', max_length=50, blank=True)
    diavencto = models.IntegerField('Dia Vencimento', default=0)
    taxa = models.DecimalField('Taxa %', max_digits=5, decimal_places=2, default=0)
    obs = models.TextField('Observação', blank=True)
    inativo = models.BooleanField('Inativo', default=False)

    class Meta:
        db_table = 'cadcard'
        ordering = ['descricao']
        verbose_name = 'Operadora de Cartão'
        verbose_name_plural = 'Operadoras de Cartão'

    def __str__(self):
        return self.descricao


# ─── Contas a Receber ───────────────────────────────────────────────────────

class ContaReceber(models.Model):
    STATUS_CHOICES = [
        ('A', 'Aberto'),
        ('B', 'Baixado'),
        ('P', 'Parcial'),
        ('C', 'Cancelado'),
        ('R', 'Renegociado'),
    ]

    idcontarec = models.AutoField(primary_key=True)
    empresa = models.ForeignKey(
        Empresa, on_delete=models.PROTECT, verbose_name='Empresa'
    )
    data = models.DateField('Data Emissão')
    cliente = models.ForeignKey(
        ClienteFornecedor, on_delete=models.PROTECT,
        verbose_name='Cliente'
    )
    idpedido = models.IntegerField('ID Pedido', default=0)
    banco = models.ForeignKey(
        Banco, on_delete=models.PROTECT,
        null=True, blank=True, verbose_name='Banco'
    )
    parcela = models.IntegerField('Parcela', default=1)
    valor = models.DecimalField('Valor', max_digits=12, decimal_places=2)
    vencimento = models.DateField('Vencimento')
    pagamento = models.DateField('Pagamento', null=True, blank=True)
    portador = models.ForeignKey(
        Portador, on_delete=models.PROTECT,
        null=True, blank=True, verbose_name='Portador'
    )
    tipobaixa = models.CharField('Tipo Baixa', max_length=20, blank=True)
    juros = models.DecimalField('Juros', max_digits=12, decimal_places=2, default=0)
    descontos = models.DecimalField('Descontos', max_digits=12, decimal_places=2, default=0)
    valorpago = models.DecimalField('Valor Pago', max_digits=12, decimal_places=2, default=0)
    numerodoc = models.CharField('Nº Documento', max_length=30, blank=True)
    numerobanco = models.CharField('Nº Banco', max_length=30, blank=True)
    reccheque = models.CharField('Rec. Cheque', max_length=20, blank=True)
    status = models.CharField('Status', max_length=1, choices=STATUS_CHOICES, default='A')
    marca = models.CharField('Marca', max_length=20, blank=True)
    idusumarca = models.IntegerField('ID Usu. Marca', default=0)
    movcadok = models.CharField('Mov. Cad OK', max_length=1, blank=True)
    cliente_conv = models.IntegerField('Cliente Conv.', default=0)
    operadora = models.ForeignKey(
        OperadoraCartao, on_delete=models.PROTECT,
        null=True, blank=True, verbose_name='Operadora Cartão'
    )
    parcelascard = models.IntegerField('Parcelas Cartão', default=0)
    idassroteiro = models.IntegerField('ID Rot. Assistência', default=0)
    idtecnico = models.IntegerField('ID Técnico', default=0)

    class Meta:
        db_table = 'contarec'
        ordering = ['vencimento', 'idcontarec']
        verbose_name = 'Conta a Receber'
        verbose_name_plural = 'Contas a Receber'

    def __str__(self):
        return f'CR {self.idcontarec} | {self.cliente} | {self.vencimento} | R$ {self.valor}'

    @property
    def em_aberto(self):
        return self.status == 'A'

    @property
    def saldo(self):
        return self.valor - self.valorpago

    @property
    def vencido(self):
        from datetime import date
        return self.status == 'A' and self.vencimento < date.today()


# ─── Contas a Pagar ─────────────────────────────────────────────────────────

class ContaPagar(models.Model):
    STATUS_CHOICES = [
        ('A', 'Aberto'),
        ('B', 'Baixado'),
        ('P', 'Parcial'),
        ('C', 'Cancelado'),
    ]

    idcontapag = models.AutoField(primary_key=True)
    empresa = models.ForeignKey(
        Empresa, on_delete=models.PROTECT, verbose_name='Empresa'
    )
    data = models.DateField('Data Emissão')
    fornecedor = models.ForeignKey(
        ClienteFornecedor, on_delete=models.PROTECT,
        verbose_name='Fornecedor'
    )
    banco = models.ForeignKey(
        Banco, on_delete=models.PROTECT,
        null=True, blank=True, verbose_name='Banco'
    )
    parcela = models.IntegerField('Parcela', default=1)
    valor = models.DecimalField('Valor', max_digits=12, decimal_places=2)
    vencimento = models.DateField('Vencimento')
    pagamento = models.DateField('Pagamento', null=True, blank=True)
    portador = models.ForeignKey(
        Portador, on_delete=models.PROTECT,
        null=True, blank=True, verbose_name='Portador'
    )
    tipobaixa = models.CharField('Tipo Baixa', max_length=20, blank=True)
    juros = models.DecimalField('Juros', max_digits=12, decimal_places=2, default=0)
    descontos = models.DecimalField('Descontos', max_digits=12, decimal_places=2, default=0)
    valorpago = models.DecimalField('Valor Pago', max_digits=12, decimal_places=2, default=0)
    numerodoc = models.CharField('Nº Documento', max_length=30, blank=True)
    status = models.CharField('Status', max_length=1, choices=STATUS_CHOICES, default='A')
    idacertocomiss = models.IntegerField('ID Acerto Comissão', default=0)

    class Meta:
        db_table = 'contapag'
        ordering = ['vencimento', 'idcontapag']
        verbose_name = 'Conta a Pagar'
        verbose_name_plural = 'Contas a Pagar'

    def __str__(self):
        return f'CP {self.idcontapag} | {self.fornecedor} | {self.vencimento} | R$ {self.valor}'

    @property
    def saldo(self):
        return self.valor - self.valorpago

    @property
    def vencido(self):
        from datetime import date
        return self.status == 'A' and self.vencimento < date.today()


# ─── Caixa ──────────────────────────────────────────────────────────────────

class AberturaCaixa(models.Model):
    idautenticacao = models.AutoField(primary_key=True)
    empresa = models.ForeignKey(
        Empresa, on_delete=models.PROTECT,
        null=True, blank=True, verbose_name='Empresa'
    )
    usuabre = models.CharField('Usuário Abertura', max_length=50)
    dataabre = models.DateField('Data Abertura', null=True, blank=True)
    horaabre = models.CharField('Hora Abertura', max_length=8, blank=True)
    usufecha = models.CharField('Usuário Fechamento', max_length=50, blank=True)
    datafecha = models.DateField('Data Fechamento', null=True, blank=True)
    horafecha = models.CharField('Hora Fechamento', max_length=8, blank=True)
    conta = models.ForeignKey(
        PlanoConta, on_delete=models.PROTECT,
        null=True, blank=True, related_name='aberturas_caixa',
        verbose_name='Conta'
    )
    subconta = models.ForeignKey(
        SubConta, on_delete=models.PROTECT,
        null=True, blank=True, related_name='aberturas_caixa',
        verbose_name='Sub-Conta'
    )
    idcontapg = models.IntegerField('ID Conta Pgto', default=0)
    idsubcontapg = models.IntegerField('ID Sub-Conta Pgto', default=0)
    idportadorche = models.IntegerField('ID Portador Cheque', default=0)
    idportadordest = models.IntegerField('ID Portador Destino', default=0)
    idsangriacheque = models.IntegerField('ID Sangria Cheque', default=0)
    saldo = models.DecimalField('Saldo', max_digits=12, decimal_places=2, default=0)

    class Meta:
        db_table = 'syscaixa'
        ordering = ['-dataabre']
        verbose_name = 'Abertura de Caixa'
        verbose_name_plural = 'Aberturas de Caixa'

    def __str__(self):
        return f'Caixa {self.dataabre} | {self.usuabre}'


class MovimentoCaixa(models.Model):
    TIPO_CHOICES = [('E', 'Entrada'), ('S', 'Saída')]
    STATUS_CHOICES = [('A', 'Ativo'), ('C', 'Cancelado')]

    idautenticacao = models.ForeignKey(
        AberturaCaixa, on_delete=models.PROTECT,
        db_column='idautenticacao', verbose_name='Sessão Caixa'
    )
    empresa = models.ForeignKey(
        Empresa, on_delete=models.PROTECT, verbose_name='Empresa'
    )
    data = models.DateField('Data')
    descricao = models.CharField('Descrição', max_length=200)
    tipo = models.CharField('Tipo', max_length=1, choices=TIPO_CHOICES)
    valor = models.DecimalField('Valor', max_digits=12, decimal_places=2)
    documento = models.CharField('Documento', max_length=30, blank=True)
    cliforemp = models.ForeignKey(
        ClienteFornecedor, on_delete=models.PROTECT,
        null=True, blank=True, verbose_name='Cliente/Forn.'
    )
    status = models.CharField('Status', max_length=1, choices=STATUS_CHOICES, default='A')
    conta = models.ForeignKey(
        PlanoConta, on_delete=models.PROTECT,
        null=True, blank=True, verbose_name='Conta'
    )
    subconta = models.ForeignKey(
        SubConta, on_delete=models.PROTECT,
        null=True, blank=True, verbose_name='Sub-Conta'
    )
    idorigem = models.IntegerField('ID Origem', default=0)
    tipobaixa = models.CharField('Tipo Baixa', max_length=20, blank=True)
    saldo = models.DecimalField('Saldo', max_digits=12, decimal_places=2, default=0)
    banco = models.ForeignKey(
        Banco, on_delete=models.PROTECT,
        null=True, blank=True, verbose_name='Banco'
    )
    projeto = models.ForeignKey(
        'core.Projeto', on_delete=models.SET_NULL,
        null=True, blank=True, verbose_name='Projeto'
    )

    class Meta:
        db_table = 'movcaixa'
        ordering = ['-data', '-id']
        verbose_name = 'Movimento de Caixa'
        verbose_name_plural = 'Movimentos de Caixa'

    def __str__(self):
        return f'{self.data} | {self.descricao} | R$ {self.valor}'


# ─── Cheques ─────────────────────────────────────────────────────────────────

class Cheque(models.Model):
    STATUS_CHOICES = [
        ('C', 'Em Carteira'),
        ('D', 'Depositado'),
        ('B', 'Compensado'),
        ('V', 'Devolvido'),
        ('R', 'Repassado'),
    ]

    idcheque = models.AutoField(primary_key=True)
    empresa = models.ForeignKey(
        Empresa, on_delete=models.PROTECT, verbose_name='Empresa'
    )
    cliforemp = models.ForeignKey(
        ClienteFornecedor, on_delete=models.PROTECT,
        null=True, blank=True, verbose_name='Cliente'
    )
    portador = models.ForeignKey(
        Portador, on_delete=models.PROTECT,
        null=True, blank=True, verbose_name='Portador'
    )
    banco = models.ForeignKey(
        Banco, on_delete=models.PROTECT,
        null=True, blank=True, verbose_name='Banco Destino'
    )
    dataemissao = models.DateField('Data Emissão', null=True, blank=True)
    numero = models.IntegerField('Número', default=0)
    emitente = models.CharField('Emitente', max_length=150, blank=True)
    cnpjcpf = models.CharField('CPF/CNPJ', max_length=18, blank=True)
    valor = models.DecimalField('Valor', max_digits=12, decimal_places=2, default=0)
    vencimento = models.DateField('Vencimento', null=True, blank=True)
    bompara = models.DateField('Bom Para', null=True, blank=True)
    baixa = models.DateField('Baixa', null=True, blank=True)
    bancocheq = models.CharField('Banco do Cheque', max_length=50, blank=True)
    agencia = models.CharField('Agência', max_length=20, blank=True)
    conta = models.CharField('Conta', max_length=30, blank=True)
    destino = models.CharField('Destino', max_length=50, blank=True)
    idpedido = models.IntegerField('ID Pedido', default=0)
    status = models.CharField('Status', max_length=1, choices=STATUS_CHOICES, default='C')
    banco_str = models.CharField('Banco (texto)', max_length=50, blank=True, db_column='banco')
    marca = models.CharField('Marca', max_length=20, blank=True)
    idusumarca = models.IntegerField('ID Usu. Marca', default=0)
    idsangriacheque = models.IntegerField('ID Sangria', default=0)

    class Meta:
        db_table = 'cheques'
        ordering = ['-dataemissao', '-idcheque']
        verbose_name = 'Cheque'
        verbose_name_plural = 'Cheques'

    def __str__(self):
        return f'Cheque {self.numero} | {self.emitente} | R$ {self.valor}'


# ─── Movimento de Cartão ─────────────────────────────────────────────────────

class MovimentoCartao(models.Model):
    empresa = models.ForeignKey(
        Empresa, on_delete=models.PROTECT, verbose_name='Empresa'
    )
    operadora = models.ForeignKey(
        OperadoraCartao, on_delete=models.PROTECT, verbose_name='Operadora'
    )
    contarec = models.ForeignKey(
        ContaReceber, on_delete=models.PROTECT, verbose_name='Conta a Receber'
    )
    parcela = models.IntegerField('Parcela', default=1)
    vencimento = models.DateField('Vencimento', null=True, blank=True)
    valor = models.DecimalField('Valor', max_digits=12, decimal_places=2, default=0)
    encargos = models.DecimalField('Encargos', max_digits=12, decimal_places=2, default=0)
    saldo = models.DecimalField('Saldo', max_digits=12, decimal_places=2, default=0)

    class Meta:
        db_table = 'movcard'
        ordering = ['vencimento']
        verbose_name = 'Movimento de Cartão'
        verbose_name_plural = 'Movimentos de Cartão'

    def __str__(self):
        return f'{self.operadora} | Parcela {self.parcela} | R$ {self.valor}'


# ─── Renegociação ────────────────────────────────────────────────────────────

class Renegociacao(models.Model):
    STATUS_CHOICES = [
        ('A', 'Aberta'),
        ('F', 'Finalizada'),
        ('C', 'Cancelada'),
    ]

    idreneg = models.AutoField(primary_key=True)
    empresa = models.ForeignKey(
        Empresa, on_delete=models.PROTECT, verbose_name='Empresa'
    )
    data = models.DateField('Data')
    cliente = models.ForeignKey(
        ClienteFornecedor, on_delete=models.PROTECT, verbose_name='Cliente'
    )
    idusuario = models.IntegerField('ID Usuário', default=0)
    valorreneg = models.DecimalField('Valor Renegociado', max_digits=12, decimal_places=2, default=0)
    valoracre = models.DecimalField('Acréscimo', max_digits=12, decimal_places=2, default=0)
    valordesc = models.DecimalField('Desconto', max_digits=12, decimal_places=2, default=0)
    valorfinal = models.DecimalField('Valor Final', max_digits=12, decimal_places=2, default=0)
    parcelas = models.IntegerField('Parcelas', default=1)
    pvencimento = models.DateField('1º Vencimento', null=True, blank=True)
    status = models.CharField('Status', max_length=1, choices=STATUS_CHOICES, default='A')
    observacao = models.TextField('Observação', blank=True)

    class Meta:
        db_table = 'reneg'
        ordering = ['-data', '-idreneg']
        verbose_name = 'Renegociação'
        verbose_name_plural = 'Renegociações'

    def __str__(self):
        return f'Reneg. {self.idreneg} | {self.cliente} | R$ {self.valorfinal}'


class ParcelaRenegociacao(models.Model):
    renegociacao = models.ForeignKey(
        Renegociacao, on_delete=models.CASCADE,
        related_name='parcelas_reneg', verbose_name='Renegociação'
    )
    contarec = models.ForeignKey(
        ContaReceber, on_delete=models.PROTECT,
        verbose_name='Conta a Receber'
    )
    selecionados = models.CharField('Selecionados', max_length=1, blank=True)

    class Meta:
        db_table = 'renegpg'
        verbose_name = 'Parcela de Renegociação'
        verbose_name_plural = 'Parcelas de Renegociação'

    def __str__(self):
        return f'{self.renegociacao} / CR {self.contarec_id}'


# ─── Arquivo Morto ───────────────────────────────────────────────────────────

class ReceitaMorta(models.Model):
    """Histórico de contas a receber baixadas/canceladas (arquivo morto)."""
    idcontarec = models.IntegerField('ID Conta Rec. Original')
    empresa = models.ForeignKey(
        Empresa, on_delete=models.PROTECT, verbose_name='Empresa'
    )
    data = models.DateField('Data Emissão')
    cliforemp = models.ForeignKey(
        ClienteFornecedor, on_delete=models.PROTECT, verbose_name='Cliente'
    )
    idpedido = models.IntegerField('ID Pedido', default=0)
    banco = models.ForeignKey(
        Banco, on_delete=models.PROTECT,
        null=True, blank=True, verbose_name='Banco'
    )
    parcela = models.IntegerField('Parcela', default=1)
    valor = models.DecimalField('Valor', max_digits=12, decimal_places=2)
    vencimento = models.DateField('Vencimento')
    pagamento = models.DateField('Pagamento', null=True, blank=True)
    portador = models.ForeignKey(
        Portador, on_delete=models.PROTECT,
        null=True, blank=True, verbose_name='Portador'
    )
    tipobaixa = models.CharField('Tipo Baixa', max_length=20, blank=True)
    juros = models.DecimalField('Juros', max_digits=12, decimal_places=2, default=0)
    descontos = models.DecimalField('Descontos', max_digits=12, decimal_places=2, default=0)
    numerobanco = models.CharField('Nº Banco', max_length=30, blank=True)
    status = models.CharField('Status', max_length=1, blank=True)
    numerodoc = models.CharField('Nº Documento', max_length=30, blank=True)
    valorpago = models.DecimalField('Valor Pago', max_digits=12, decimal_places=2, default=0)
    reccheque = models.CharField('Rec. Cheque', max_length=20, blank=True)
    cliente_conv = models.IntegerField('Cliente Conv.', default=0)
    movcadok = models.CharField('Mov. Cad OK', max_length=1, blank=True)
    operadora = models.ForeignKey(
        OperadoraCartao, on_delete=models.PROTECT,
        null=True, blank=True, verbose_name='Operadora Cartão'
    )
    parcelascard = models.IntegerField('Parcelas Cartão', default=0)
    marca = models.CharField('Marca', max_length=20, blank=True)
    idusumarca = models.IntegerField('ID Usu. Marca', default=0)

    class Meta:
        db_table = 'recmorto'
        ordering = ['-vencimento']
        verbose_name = 'Receita Morta'
        verbose_name_plural = 'Receitas Mortas'

    def __str__(self):
        return f'Morto CR {self.idcontarec} | {self.cliforemp} | R$ {self.valor}'

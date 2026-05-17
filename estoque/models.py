from django.db import models
from core.models import Empresa, Cfop
from cadastros.models import Item, ClienteFornecedor, CondicaoPagamento, Metodo


class NotaFiscalEntrada(models.Model):
    STATUS_CHOICES = [
        ('A', 'Em Digitação'),
        ('L', 'Lançada'),
        ('C', 'Cancelada'),
    ]
    FRETE_CHOICES = [
        ('C', 'CIF - Por conta do emitente'),
        ('F', 'FOB - Por conta do destinatário'),
        ('S', 'Sem frete'),
    ]

    idnfentrada = models.AutoField(primary_key=True)
    empresa = models.ForeignKey(
        Empresa, on_delete=models.PROTECT, verbose_name='Empresa'
    )
    fornecedor = models.ForeignKey(
        ClienteFornecedor, on_delete=models.PROTECT,
        verbose_name='Fornecedor'
    )
    numeronf = models.IntegerField('Número NF')
    serie = models.CharField('Série', max_length=5, blank=True)
    chaveacesso = models.CharField('Chave de Acesso', max_length=50, blank=True)
    dataemissao = models.DateField('Data Emissão', null=True, blank=True)
    dataentrada = models.DateField('Data Entrada', null=True, blank=True)
    cfop = models.ForeignKey(
        Cfop, on_delete=models.PROTECT,
        null=True, blank=True, verbose_name='CFOP'
    )
    condicao = models.ForeignKey(
        CondicaoPagamento, on_delete=models.PROTECT,
        null=True, blank=True, verbose_name='Condição Pgto'
    )
    metodo = models.ForeignKey(
        Metodo, on_delete=models.PROTECT,
        null=True, blank=True, verbose_name='Método Pgto'
    )
    idtransporte = models.IntegerField('ID Transportadora', default=0)
    tipofrete = models.CharField('Tipo Frete', max_length=1, choices=FRETE_CHOICES, default='S')
    status = models.CharField('Status', max_length=1, choices=STATUS_CHOICES, default='A')
    quantidade = models.DecimalField('Qtd. Total', max_digits=12, decimal_places=3, default=0)
    valortotalitens = models.DecimalField('Total Itens', max_digits=12, decimal_places=2, default=0)
    valorfrete = models.DecimalField('Frete', max_digits=12, decimal_places=2, default=0)
    valoracrecimo = models.DecimalField('Acréscimo', max_digits=12, decimal_places=2, default=0)
    valordesconto = models.DecimalField('Desconto', max_digits=12, decimal_places=2, default=0)
    valoripi = models.DecimalField('IPI', max_digits=12, decimal_places=2, default=0)
    valoricms = models.DecimalField('ICMS', max_digits=12, decimal_places=2, default=0)
    valortotalnf = models.DecimalField('Total NF', max_digits=12, decimal_places=2, default=0)
    observacao = models.TextField('Observação', blank=True)
    usuariolanc = models.CharField('Usuário Lanç.', max_length=50, blank=True)

    class Meta:
        db_table = 'nfcompra'
        ordering = ['-dataentrada', '-idnfentrada']
        verbose_name = 'NF de Entrada'
        verbose_name_plural = 'NFs de Entrada'

    def __str__(self):
        return f'NF {self.numeronf} | {self.fornecedor} | {self.dataentrada}'


class ItemNFEntrada(models.Model):
    nfentrada = models.ForeignKey(
        NotaFiscalEntrada, on_delete=models.CASCADE,
        related_name='itens', verbose_name='NF Entrada'
    )
    item = models.ForeignKey(
        Item, on_delete=models.SET_NULL,
        null=True, blank=True, verbose_name='Item'
    )
    identificacao = models.CharField('Identificação', max_length=50, blank=True)
    descricao_item = models.CharField('Descrição', max_length=200, blank=True)
    quantidade = models.DecimalField('Quantidade', max_digits=12, decimal_places=3, default=0)
    valorunitario = models.DecimalField('Valor Unit.', max_digits=12, decimal_places=4, default=0)
    ipi = models.DecimalField('IPI %', max_digits=7, decimal_places=4, default=0)
    icms = models.DecimalField('ICMS %', max_digits=7, decimal_places=4, default=0)
    cfop = models.ForeignKey(
        Cfop, on_delete=models.PROTECT,
        null=True, blank=True, verbose_name='CFOP'
    )
    valortotal = models.DecimalField('Total', max_digits=12, decimal_places=2, default=0)

    class Meta:
        db_table = 'itecompr'
        verbose_name = 'Item da NF de Entrada'
        verbose_name_plural = 'Itens da NF de Entrada'

    def __str__(self):
        return f'{self.nfentrada} / {self.identificacao}'


class ParcelaNFEntrada(models.Model):
    nfentrada = models.ForeignKey(
        NotaFiscalEntrada, on_delete=models.CASCADE,
        related_name='parcelas', verbose_name='NF Entrada'
    )
    parcela = models.IntegerField('Parcela')
    vencimento = models.DateField('Vencimento')
    valor = models.DecimalField('Valor', max_digits=12, decimal_places=2)
    idcontapag = models.IntegerField('ID Conta Pagar', default=0)

    class Meta:
        db_table = 'parcnfentrada'
        ordering = ['nfentrada', 'parcela']
        verbose_name = 'Parcela da NF de Entrada'
        verbose_name_plural = 'Parcelas da NF de Entrada'

    def __str__(self):
        return f'{self.nfentrada} / Parcela {self.parcela}'


class MovimentoEstoque(models.Model):
    ENT_SAI_CHOICES = [('E', 'Entrada'), ('S', 'Saída')]
    ORIGEM_CHOICES = [
        ('NF', 'NF de Entrada'),
        ('PD', 'Pedido'),
        ('RQ', 'Requisição'),
        ('OS', 'Ordem de Serviço'),
        ('AJ', 'Ajuste de Estoque'),
    ]
    # Mapeamento legível para extrato e relatórios
    ORIGEM_LABELS = {
        'NF': 'NF de Entrada',
        'PD': 'Pedido',
        'RQ': 'Atendimento de Requisição',
        'OS': 'Ordem de Serviço',
        'AJ': 'Ajuste de Estoque',
    }

    idmovimento = models.AutoField(primary_key=True)
    empresa = models.ForeignKey(
        Empresa, on_delete=models.PROTECT, verbose_name='Empresa'
    )
    # VDF armazena a identificação (código) do item como string
    identificacao = models.CharField('Identificação Item', max_length=50)
    item = models.ForeignKey(
        Item, on_delete=models.SET_NULL,
        null=True, blank=True, verbose_name='Item'
    )
    data = models.DateField('Data')
    ent_sai = models.CharField('Ent./Saída', max_length=1, choices=ENT_SAI_CHOICES)
    origem = models.CharField('Origem', max_length=2, choices=ORIGEM_CHOICES, blank=True)
    idorigem = models.IntegerField('ID Origem', default=0)
    quantidade = models.DecimalField('Quantidade', max_digits=12, decimal_places=3)
    usuariologado = models.CharField('Usuário', max_length=50, blank=True)
    observacao = models.CharField('Observação / Motivo', max_length=200, blank=True)

    class Meta:
        db_table = 'movitem'
        ordering = ['-data', '-idmovimento']
        verbose_name = 'Movimento de Estoque'
        verbose_name_plural = 'Movimentos de Estoque'

    def __str__(self):
        return f'{self.get_ent_sai_display()} | {self.item} | {self.data} | Qtd: {self.quantidade}'


class Requisicao(models.Model):
    STATUS_CHOICES = [
        ('A', 'Aberta'),
        ('P', 'Parcial'),
        ('F', 'Finalizada'),
        ('C', 'Cancelada'),
    ]

    idrequisicao = models.AutoField(primary_key=True)
    empresa = models.ForeignKey(
        Empresa, on_delete=models.PROTECT, verbose_name='Empresa'
    )
    cliforemp = models.ForeignKey(
        ClienteFornecedor, on_delete=models.PROTECT,
        null=True, blank=True, verbose_name='Cliente/Forn.'
    )
    data = models.DateField('Data')
    dataatendi = models.DateField('Data Atendimento', null=True, blank=True)
    status = models.CharField('Status', max_length=1, choices=STATUS_CHOICES, default='A')
    origem = models.CharField('Origem', max_length=20, blank=True)
    idorigem = models.IntegerField('ID Origem', default=0)
    observacao = models.TextField('Observação', blank=True)

    class Meta:
        db_table = 'requis'
        ordering = ['-data', '-idrequisicao']
        verbose_name = 'Requisição'
        verbose_name_plural = 'Requisições'

    def __str__(self):
        return f'Req. {self.idrequisicao} | {self.data} | {self.get_status_display()}'


class ItemRequisicao(models.Model):
    requisicao = models.ForeignKey(
        Requisicao, on_delete=models.CASCADE,
        related_name='itens', verbose_name='Requisição'
    )
    identificacao = models.CharField('Identificação', max_length=50, blank=True)
    quantidade = models.DecimalField('Quantidade', max_digits=12, decimal_places=3, default=0)
    atendido = models.DecimalField('Atendido', max_digits=12, decimal_places=3, default=0)
    saldo = models.DecimalField('Saldo', max_digits=12, decimal_places=3, default=0)
    idorigem = models.IntegerField('ID Origem', default=0)

    class Meta:
        db_table = 'reqitem'
        verbose_name = 'Item da Requisição'
        verbose_name_plural = 'Itens da Requisição'

    def __str__(self):
        return f'{self.requisicao} / {self.identificacao}'


# ── Inventário ────────────────────────────────────────────────────────────────

class Inventario(models.Model):
    STATUS_CHOICES = [
        ('A', 'Aberto'),
        ('F', 'Finalizado'),
        ('X', 'Cancelado'),
    ]

    idinventario = models.AutoField(primary_key=True)
    empresa = models.ForeignKey(
        Empresa, on_delete=models.PROTECT, verbose_name='Empresa'
    )
    data = models.DateField('Data')
    descricao = models.CharField('Descrição / Referência', max_length=200, blank=True)
    status = models.CharField('Status', max_length=1, choices=STATUS_CHOICES, default='A')
    usuario = models.CharField('Usuário', max_length=50, blank=True)
    datafinalizacao = models.DateField('Data Finalização', null=True, blank=True)
    observacao = models.TextField('Observação', blank=True)

    class Meta:
        db_table = 'inventario'
        ordering = ['-data', '-idinventario']
        verbose_name = 'Inventário'
        verbose_name_plural = 'Inventários'

    def __str__(self):
        return f'Inv. {self.idinventario} | {self.data} | {self.get_status_display()}'


class ItemInventario(models.Model):
    inventario = models.ForeignKey(
        Inventario, on_delete=models.CASCADE,
        related_name='itens', verbose_name='Inventário'
    )
    item = models.ForeignKey(
        Item, on_delete=models.SET_NULL,
        null=True, blank=True, verbose_name='Item'
    )
    identificacao = models.CharField('Identificação', max_length=50, blank=True)
    descricao_item = models.CharField('Descrição', max_length=200, blank=True)
    saldo_sistema = models.DecimalField(
        'Saldo Sistema', max_digits=12, decimal_places=3, default=0
    )
    saldo_fisico = models.DecimalField(
        'Saldo Físico', max_digits=12, decimal_places=3, null=True, blank=True
    )
    diferenca = models.DecimalField(
        'Diferença', max_digits=12, decimal_places=3, default=0
    )
    ajustado = models.BooleanField('Ajustado', default=False)

    class Meta:
        db_table = 'invitem'
        ordering = ['identificacao']
        verbose_name = 'Item do Inventário'
        verbose_name_plural = 'Itens do Inventário'

    def __str__(self):
        return f'{self.inventario} / {self.identificacao}'

from django.db import models
from core.models import Empresa
from cadastros.models import (
    ClienteFornecedor, TabelaPreco,
    CondicaoPagamento, Metodo, Item,
)
from financeiro.models import ContaReceber


# ─── CRM — Contatos / Log de Atendimento ─────────────────────────────────────

class ContatoCliente(models.Model):
    cliforemp = models.ForeignKey(
        ClienteFornecedor, on_delete=models.CASCADE,
        related_name='contatos', verbose_name='Cliente'
    )
    empresa = models.ForeignKey(
        Empresa, on_delete=models.PROTECT,
        null=True, blank=True, verbose_name='Empresa'
    )
    datacontato = models.DateField('Data Contato')
    descricao = models.CharField('Descrição', max_length=200)
    status = models.CharField('Status', max_length=50, blank=True)
    proximocontato = models.DateField('Próximo Contato', null=True, blank=True)
    observacao = models.TextField('Observação', blank=True)
    usuario = models.CharField('Usuário', max_length=50, blank=True)

    class Meta:
        db_table = 'clicalls'
        ordering = ['-datacontato', '-id']
        verbose_name = 'Contato do Cliente'
        verbose_name_plural = 'Contatos dos Clientes'

    def __str__(self):
        return f'{self.cliforemp} | {self.datacontato} | {self.descricao[:40]}'


# ─── TeleVenda / Ordem de Serviço ─────────────────────────────────────────────

class TeleVenda(models.Model):
    STATUS_CHOICES = [
        ('A', 'Agendada'),
        ('R', 'Realizada'),
        ('C', 'Cancelada'),
        ('P', 'Pendente'),
        ('F', 'Faturada'),
    ]
    PERIODO_CHOICES = [
        ('M', 'Matutino'),
        ('V', 'Vespertino'),
        ('I', 'Integral'),
    ]

    idtelvenda = models.AutoField(primary_key=True)
    empresa = models.ForeignKey(
        Empresa, on_delete=models.PROTECT, verbose_name='Empresa'
    )
    numero = models.CharField('Número', max_length=20, blank=True)
    dataemissao = models.DateField('Data Emissão', null=True, blank=True)
    dataprevisao = models.DateField('Data Previsão', null=True, blank=True)
    datainstal = models.DateField('Data Realização', null=True, blank=True)
    datahora = models.CharField('Data/Hora', max_length=20, blank=True)
    cliente = models.ForeignKey(
        ClienteFornecedor, on_delete=models.PROTECT,
        related_name='televendas', verbose_name='Cliente'
    )
    idvendrepre = models.IntegerField('ID Vendedor/Rep.', default=0)
    idtecnico = models.IntegerField('ID Técnico', default=0)
    tabela = models.ForeignKey(
        TabelaPreco, on_delete=models.PROTECT,
        null=True, blank=True, verbose_name='Tabela de Preço'
    )
    condicao = models.ForeignKey(
        CondicaoPagamento, on_delete=models.PROTECT,
        null=True, blank=True, verbose_name='Condição Pgto'
    )
    metodo = models.ForeignKey(
        Metodo, on_delete=models.PROTECT,
        null=True, blank=True, verbose_name='Método Pgto'
    )
    status = models.CharField('Status', max_length=1, choices=STATUS_CHOICES, default='A')
    motivocancel = models.CharField('Motivo Cancelamento', max_length=200, blank=True)
    quantidadetotal = models.DecimalField('Qtd. Total', max_digits=12, decimal_places=3, default=0)
    valortotal = models.DecimalField('Valor Total', max_digits=12, decimal_places=2, default=0)
    atend_periodo = models.CharField('Período Atend.', max_length=1, choices=PERIODO_CHOICES, blank=True)
    atend_hora = models.CharField('Hora Atend.', max_length=8, blank=True)
    atend_obs = models.TextField('Obs. Atendimento', blank=True)
    impresso = models.BooleanField('Impresso', default=False)
    idusuario = models.IntegerField('ID Usuário', default=0)
    usuariolanc = models.CharField('Usuário Lançamento', max_length=50, blank=True)
    marca = models.CharField('Marca', max_length=20, blank=True)
    idusumarca = models.IntegerField('ID Usu. Marca', default=0)
    idassroteiro = models.IntegerField('ID Roteiro', default=0)
    idpedido          = models.IntegerField('ID Pedido', default=0)
    idpedido_material = models.IntegerField('ID Pedido Material', default=0)
    equipe = models.IntegerField('Equipe', default=0)

    class Meta:
        db_table = 'telvenda'
        ordering = ['-dataprevisao', '-idtelvenda']
        verbose_name = 'TeleVenda / OS'
        verbose_name_plural = 'TeleVendas / OS'

    def __str__(self):
        return f'OS {self.numero} | {self.cliente} | {self.dataprevisao}'


class ItemTeleVenda(models.Model):
    telvenda = models.ForeignKey(
        TeleVenda, on_delete=models.CASCADE,
        related_name='itens', verbose_name='TeleVenda'
    )
    item = models.ForeignKey(
        Item, on_delete=models.PROTECT,
        null=True, blank=True, verbose_name='Item'
    )
    identificacao = models.CharField('Identificação', max_length=50, blank=True)
    quantidade = models.DecimalField('Quantidade', max_digits=12, decimal_places=3, default=0)
    valorunitario = models.DecimalField('Valor Unit.', max_digits=12, decimal_places=2, default=0)
    instalacao = models.DecimalField('Instalação', max_digits=12, decimal_places=2, default=0)
    valortotal = models.DecimalField('Valor Total', max_digits=12, decimal_places=2, default=0)
    pagamentoav  = models.CharField('Pgto Antecipado', max_length=1, blank=True)
    tipo_item    = models.CharField('Tipo Item', max_length=1, blank=True)
    servico_pai  = models.IntegerField('ID Serviço Pai', default=0)

    class Meta:
        db_table = 'itemtel'
        verbose_name = 'Item da TeleVenda'
        verbose_name_plural = 'Itens da TeleVenda'

    def __str__(self):
        return f'{self.telvenda} / {self.identificacao}'


class ParcelaTeleVenda(models.Model):
    telvenda = models.ForeignKey(
        TeleVenda, on_delete=models.CASCADE,
        related_name='parcelas', verbose_name='TeleVenda'
    )
    parcela = models.IntegerField('Parcela')
    vencimento = models.DateField('Vencimento', null=True, blank=True)
    valor = models.DecimalField('Valor', max_digits=12, decimal_places=2, default=0)

    class Meta:
        db_table = 'parctel'
        ordering = ['telvenda', 'parcela']
        verbose_name = 'Parcela da TeleVenda'
        verbose_name_plural = 'Parcelas da TeleVenda'

    def __str__(self):
        return f'{self.telvenda} | Parcela {self.parcela} | R$ {self.valor}'


# ─── Roteiro de Assistência Técnica ──────────────────────────────────────────

class Roteiro(models.Model):
    STATUS_CHOICES = [
        ('A', 'Aberto'),
        ('E', 'Em Execução'),
        ('F', 'Finalizado'),
        ('C', 'Cancelado'),
    ]

    idassroteiro = models.AutoField(primary_key=True)
    empresa = models.ForeignKey(
        Empresa, on_delete=models.PROTECT, verbose_name='Empresa'
    )
    dateemissao = models.DateField('Data Emissão', null=True, blank=True)
    status = models.CharField('Status', max_length=1, choices=STATUS_CHOICES, default='A')
    qtdassistencias = models.IntegerField('Qtd. Assistências', default=0)
    qtde_matutino = models.IntegerField('Qtd. Matutino', default=0)
    qtde_vespertino = models.IntegerField('Qtd. Vespertino', default=0)
    requisicaook = models.BooleanField('Requisição OK', default=False)
    cliforemp = models.ForeignKey(
        ClienteFornecedor, on_delete=models.PROTECT,
        null=True, blank=True, verbose_name='Responsável'
    )
    destino = models.CharField('Destino', max_length=100, blank=True)
    idrequisicao = models.IntegerField('ID Requisição', default=0)

    class Meta:
        db_table = 'assrot'
        ordering = ['-dateemissao', '-idassroteiro']
        verbose_name = 'Roteiro de Assistência'
        verbose_name_plural = 'Roteiros de Assistência'

    def __str__(self):
        return f'Roteiro {self.idassroteiro} | {self.dateemissao} | {self.get_status_display()}'


class OSRoteiro(models.Model):
    """Ordens de Serviço vinculadas a um roteiro (assrotos)."""
    roteiro = models.ForeignKey(
        Roteiro, on_delete=models.CASCADE,
        related_name='ordens_servico', verbose_name='Roteiro'
    )
    cliente = models.ForeignKey(
        ClienteFornecedor, on_delete=models.PROTECT, verbose_name='Cliente'
    )
    telvenda = models.ForeignKey(
        TeleVenda, on_delete=models.PROTECT,
        null=True, blank=True, verbose_name='OS / TeleVenda'
    )
    execucao = models.CharField('Execução', max_length=1, blank=True)
    recebimento = models.CharField('Recebimento', max_length=1, blank=True)

    class Meta:
        db_table = 'assrotos'
        verbose_name = 'OS do Roteiro'
        verbose_name_plural = 'OSs do Roteiro'

    def __str__(self):
        return f'{self.roteiro} | {self.cliente}'


class TecnicoRoteiro(models.Model):
    """Técnicos escalados para um roteiro com capacidade (assrott)."""
    roteiro = models.ForeignKey(
        Roteiro, on_delete=models.CASCADE,
        related_name='tecnicos', verbose_name='Roteiro'
    )
    tecnico = models.ForeignKey(
        ClienteFornecedor, on_delete=models.PROTECT, verbose_name='Técnico'
    )
    mat_capacidade = models.IntegerField('Cap. Matutino', default=0)
    ves_capacidade = models.IntegerField('Cap. Vespertino', default=0)
    destino = models.CharField('Destino', max_length=100, blank=True)

    class Meta:
        db_table = 'assrott'
        verbose_name = 'Técnico do Roteiro'
        verbose_name_plural = 'Técnicos do Roteiro'

    def __str__(self):
        return f'{self.roteiro} | {self.tecnico}'


class BoletoRoteiro(models.Model):
    """Boletos (contas a receber) vinculados a um roteiro (assrotbl)."""
    roteiro = models.ForeignKey(
        Roteiro, on_delete=models.CASCADE,
        related_name='boletos', verbose_name='Roteiro'
    )
    cliente = models.ForeignKey(
        ClienteFornecedor, on_delete=models.PROTECT, verbose_name='Cliente'
    )
    contarec = models.ForeignKey(
        ContaReceber, on_delete=models.PROTECT, verbose_name='Conta a Receber'
    )
    status = models.CharField('Status', max_length=1, blank=True)

    class Meta:
        db_table = 'assrotbl'
        verbose_name = 'Boleto do Roteiro'
        verbose_name_plural = 'Boletos do Roteiro'

    def __str__(self):
        return f'{self.roteiro} | {self.cliente} | CR {self.contarec_id}'


class CobrancaRoteiro(models.Model):
    """Cobranças com detalhes financeiros em um roteiro (assrotcb)."""
    roteiro = models.ForeignKey(
        Roteiro, on_delete=models.CASCADE,
        related_name='cobranças', verbose_name='Roteiro'
    )
    cliente = models.ForeignKey(
        ClienteFornecedor, on_delete=models.PROTECT, verbose_name='Cliente'
    )
    contarec = models.ForeignKey(
        ContaReceber, on_delete=models.PROTECT, verbose_name='Conta a Receber'
    )
    status = models.CharField('Status', max_length=1, blank=True)
    valor = models.DecimalField('Valor Original', max_digits=12, decimal_places=2, default=0)
    multa = models.DecimalField('Multa %', max_digits=5, decimal_places=2, default=0)
    juros = models.DecimalField('Juros %', max_digits=5, decimal_places=2, default=0)
    mesesatraso = models.IntegerField('Meses Atraso', default=0)
    valormulta = models.DecimalField('Valor Multa', max_digits=12, decimal_places=2, default=0)
    valorjuros = models.DecimalField('Valor Juros', max_digits=12, decimal_places=2, default=0)
    valoratualizado = models.DecimalField('Valor Atualizado', max_digits=12, decimal_places=2, default=0)
    metodo = models.CharField('Método Pgto', max_length=20, blank=True)

    class Meta:
        db_table = 'assrotcb'
        verbose_name = 'Cobrança do Roteiro'
        verbose_name_plural = 'Cobranças do Roteiro'

    def __str__(self):
        return f'{self.roteiro} | {self.cliente} | R$ {self.valoratualizado}'

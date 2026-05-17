from django.db import models
from core.models import Empresa
from cadastros.models import (
    ClienteFornecedor, CondicaoPagamento,
    TabelaPreco, Metodo, Item,
)


# ─── Pedido ──────────────────────────────────────────────────────────────────

class Pedido(models.Model):
    STATUS_CHOICES = [
        ('A', 'Aberto'),
        ('F', 'Faturado'),
        ('I', 'Instalado'),
        ('C', 'Cancelado'),
    ]

    idpedido = models.AutoField(primary_key=True)
    empresa = models.ForeignKey(
        Empresa, on_delete=models.PROTECT, verbose_name='Empresa'
    )
    numero = models.IntegerField('Número', default=0)
    numgrafico = models.CharField('Nº Gráfico', max_length=20, blank=True)
    datagrav = models.DateField('Data Gravação', null=True, blank=True)
    datavenda = models.DateField('Data Venda', null=True, blank=True)
    previnstal = models.DateField('Prev. Instalação', null=True, blank=True)
    datafat = models.DateField('Data Faturamento', null=True, blank=True)
    datainstal = models.DateField('Data Instalação', null=True, blank=True)
    datacancela = models.DateField('Data Cancelamento', null=True, blank=True)
    cliente = models.ForeignKey(
        ClienteFornecedor, on_delete=models.PROTECT,
        related_name='pedidos', verbose_name='Cliente'
    )
    idvendrepre = models.IntegerField('ID Vendedor/Rep.', default=0)
    idtecnico = models.IntegerField('ID Técnico', default=0)
    condicao = models.ForeignKey(
        CondicaoPagamento, on_delete=models.PROTECT,
        null=True, blank=True, verbose_name='Condição Pgto'
    )
    tabela = models.ForeignKey(
        TabelaPreco, on_delete=models.PROTECT,
        null=True, blank=True, verbose_name='Tabela de Preço'
    )
    metodo = models.ForeignKey(
        Metodo, on_delete=models.PROTECT,
        null=True, blank=True, verbose_name='Método Pgto'
    )
    valortotal = models.DecimalField('Valor Total', max_digits=12, decimal_places=2, default=0)
    status = models.CharField('Status', max_length=1, choices=STATUS_CHOICES, default='A')
    tipo_faturamento = models.CharField(
        'Tipo Faturamento', max_length=1,
        choices=[('U', 'Único'), ('S', 'Serviço'), ('M', 'Material')],
        default='U', blank=True,
    )
    motivocancela = models.CharField('Motivo Cancelamento', max_length=200, blank=True)
    observacao = models.TextField('Observação', blank=True)
    control_conf = models.CharField('Controle Conf.', max_length=1, blank=True)
    marca = models.CharField('Marca', max_length=20, blank=True)
    idusumarca = models.IntegerField('ID Usu. Marca', default=0)
    idorigem = models.IntegerField('ID Origem', default=0)
    idcliente_conv = models.IntegerField('ID Cliente Conv.', default=0)
    comissaook = models.CharField('Comissão OK', max_length=1, blank=True)
    # Venda rápida (campo auxiliar VDF)
    v_descricao = models.CharField('V. Descrição', max_length=200, blank=True)
    v_quantidade = models.DecimalField('V. Quantidade', max_digits=12, decimal_places=3, default=0)
    v_preco = models.DecimalField('V. Preço', max_digits=12, decimal_places=2, default=0)

    class Meta:
        db_table = 'pedido'
        ordering = ['-datavenda', '-idpedido']
        verbose_name = 'Pedido'
        verbose_name_plural = 'Pedidos'

    def __str__(self):
        return f'Pedido {self.numero} | {self.cliente} | R$ {self.valortotal}'


class ItemPedido(models.Model):
    pedido = models.ForeignKey(
        Pedido, on_delete=models.CASCADE,
        related_name='itens', verbose_name='Pedido'
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
    numeroped_conv = models.IntegerField('Nº Ped. Conv.', default=0)
    pagamentoav = models.CharField('Pgto Antecipado', max_length=1, blank=True)
    estoqueok   = models.CharField('Estoque OK', max_length=1, blank=True)
    tipo_item   = models.CharField('Tipo Item', max_length=1, blank=True)

    class Meta:
        db_table = 'itemped'
        verbose_name = 'Item do Pedido'
        verbose_name_plural = 'Itens do Pedido'

    def __str__(self):
        return f'{self.pedido} / {self.identificacao}'


class ParcelaPedido(models.Model):
    pedido = models.ForeignKey(
        Pedido, on_delete=models.CASCADE,
        related_name='parcelas', verbose_name='Pedido'
    )
    parcela = models.IntegerField('Parcela')
    vencimento = models.DateField('Vencimento', null=True, blank=True)
    valor = models.DecimalField('Valor', max_digits=12, decimal_places=2, default=0)

    class Meta:
        db_table = 'parcped'
        ordering = ['pedido', 'parcela']
        verbose_name = 'Parcela do Pedido'
        verbose_name_plural = 'Parcelas do Pedido'

    def __str__(self):
        return f'{self.pedido} | Parcela {self.parcela} | R$ {self.valor}'


# ─── Comissão ─────────────────────────────────────────────────────────────────

class ConfiguracaoComissao(models.Model):
    """
    Tabela singleton — parâmetros globais de cálculo de comissão (comissao.fd).
    Televendas (tel), Meios de pagamento (mei) e Revendas por faixa (rev).
    """
    # Televendas
    telprazo = models.DecimalField('Tel. Prazo %', max_digits=5, decimal_places=2, default=0)
    telav = models.DecimalField('Tel. À Vista %', max_digits=5, decimal_places=2, default=0)
    telpremio = models.DecimalField('Tel. Prêmio %', max_digits=5, decimal_places=2, default=0)
    # Meios
    meiprazo = models.DecimalField('Mei. Prazo %', max_digits=5, decimal_places=2, default=0)
    meiav = models.DecimalField('Mei. À Vista %', max_digits=5, decimal_places=2, default=0)
    meipremio = models.DecimalField('Mei. Prêmio %', max_digits=5, decimal_places=2, default=0)
    # Revendas — faixas de volume
    revfaixa1 = models.DecimalField('Rev. Faixa 1', max_digits=12, decimal_places=2, default=0)
    revfaixa2 = models.DecimalField('Rev. Faixa 2', max_digits=12, decimal_places=2, default=0)
    revfaixa3 = models.DecimalField('Rev. Faixa 3', max_digits=12, decimal_places=2, default=0)
    revfaixa4 = models.DecimalField('Rev. Faixa 4', max_digits=12, decimal_places=2, default=0)
    # Percentuais por faixa — naturais
    revpercnat1 = models.DecimalField('Rev. % Nat. F1', max_digits=5, decimal_places=2, default=0)
    revpercnat2 = models.DecimalField('Rev. % Nat. F2', max_digits=5, decimal_places=2, default=0)
    revpercnat3 = models.DecimalField('Rev. % Nat. F3', max_digits=5, decimal_places=2, default=0)
    revpercnat4 = models.DecimalField('Rev. % Nat. F4', max_digits=5, decimal_places=2, default=0)
    # Percentuais por faixa — elétricos
    revpercele1 = models.DecimalField('Rev. % Ele. F1', max_digits=5, decimal_places=2, default=0)
    revpercele2 = models.DecimalField('Rev. % Ele. F2', max_digits=5, decimal_places=2, default=0)
    revpercele3 = models.DecimalField('Rev. % Ele. F3', max_digits=5, decimal_places=2, default=0)
    revpercele4 = models.DecimalField('Rev. % Ele. F4', max_digits=5, decimal_places=2, default=0)

    class Meta:
        db_table = 'comissao'
        verbose_name = 'Configuração de Comissão'
        verbose_name_plural = 'Configuração de Comissão'

    def __str__(self):
        return 'Configuração de Comissão'


class AcertoComissao(models.Model):
    STATUS_CHOICES = [
        ('A', 'Aberto'),
        ('F', 'Finalizado'),
        ('C', 'Cancelado'),
    ]

    idacertocomiss = models.AutoField(primary_key=True)
    empresa = models.ForeignKey(
        Empresa, on_delete=models.PROTECT, verbose_name='Empresa'
    )
    idvendrepre = models.IntegerField('ID Vendedor/Rep.')
    emissao = models.DateField('Emissão', null=True, blank=True)
    perildoini = models.DateField('Período Inicial', null=True, blank=True)
    periodofim = models.DateField('Período Final', null=True, blank=True)
    totalvendido = models.DecimalField('Total Vendido', max_digits=12, decimal_places=2, default=0)
    totalbase = models.DecimalField('Total Base', max_digits=12, decimal_places=2, default=0)
    totalcomissao = models.DecimalField('Total Comissão', max_digits=12, decimal_places=2, default=0)
    percpremio = models.DecimalField('% Prêmio', max_digits=5, decimal_places=2, default=0)
    status = models.CharField('Status', max_length=1, choices=STATUS_CHOICES, default='A')
    observacao = models.TextField('Observação', blank=True)

    class Meta:
        db_table = 'cabcomis'
        ordering = ['-emissao', '-idacertocomiss']
        verbose_name = 'Acerto de Comissão'
        verbose_name_plural = 'Acertos de Comissão'

    def __str__(self):
        return f'Acerto {self.idacertocomiss} | Vend. {self.idvendrepre} | R$ {self.totalcomissao}'


class MovimentoComissao(models.Model):
    acerto = models.ForeignKey(
        AcertoComissao, on_delete=models.CASCADE,
        related_name='movimentos', verbose_name='Acerto'
    )
    empresa = models.ForeignKey(
        Empresa, on_delete=models.PROTECT, verbose_name='Empresa'
    )
    cliente = models.ForeignKey(
        ClienteFornecedor, on_delete=models.PROTECT,
        verbose_name='Cliente'
    )
    pedido = models.ForeignKey(
        Pedido, on_delete=models.PROTECT,
        verbose_name='Pedido'
    )
    identificacao = models.CharField('Identificação', max_length=50, blank=True)
    quantidade = models.DecimalField('Quantidade', max_digits=12, decimal_places=3, default=0)
    valorunitario = models.DecimalField('Valor Unit.', max_digits=12, decimal_places=2, default=0)
    valortotal = models.DecimalField('Valor Total', max_digits=12, decimal_places=2, default=0)
    basecomissao = models.DecimalField('Base Comissão', max_digits=12, decimal_places=2, default=0)
    perccomiss = models.DecimalField('% Comissão', max_digits=5, decimal_places=2, default=0)
    valorcomiss = models.DecimalField('Valor Comissão', max_digits=12, decimal_places=2, default=0)
    valortabela = models.DecimalField('Valor Tabela', max_digits=12, decimal_places=2, default=0)

    class Meta:
        db_table = 'movcomis'
        verbose_name = 'Movimento de Comissão'
        verbose_name_plural = 'Movimentos de Comissão'

    def __str__(self):
        return f'{self.acerto} | {self.identificacao} | R$ {self.valorcomiss}'


# ─── Resumo / Log ─────────────────────────────────────────────────────────────

class Resumo(models.Model):
    """Totalizadores e resumos para dashboards."""
    empresa = models.ForeignKey(
        Empresa, on_delete=models.PROTECT, verbose_name='Empresa'
    )
    descricao = models.CharField('Descrição', max_length=100)
    valor = models.DecimalField('Valor', max_digits=12, decimal_places=2, default=0)
    seq = models.IntegerField('Sequência', default=0)

    class Meta:
        db_table = 'resumo'
        ordering = ['empresa', 'seq']
        verbose_name = 'Resumo'
        verbose_name_plural = 'Resumos'

    def __str__(self):
        return f'{self.descricao} | R$ {self.valor}'


class LogSistema(models.Model):
    """Registro de eventos do sistema (statlog.fd)."""
    date = models.DateField('Data', null=True, blank=True)
    time = models.CharField('Hora', max_length=8, blank=True)
    description = models.TextField('Descrição', blank=True)

    class Meta:
        db_table = 'statlog'
        ordering = ['-date', '-id']
        verbose_name = 'Log do Sistema'
        verbose_name_plural = 'Logs do Sistema'

    def __str__(self):
        return f'{self.date} {self.time} | {self.description[:60]}'

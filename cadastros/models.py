from django.db import models
from core.models import Cidade, Empresa


class Grupo(models.Model):
    idgrupo = models.AutoField(primary_key=True)
    empresa = models.ForeignKey(
        Empresa, on_delete=models.PROTECT,
        null=True, blank=True, verbose_name='Empresa'
    )
    descricao = models.CharField('Descrição', max_length=100)
    idgrupopai = models.ForeignKey(
        'self', on_delete=models.SET_NULL,
        null=True, blank=True, verbose_name='Grupo Pai'
    )
    classificacao = models.CharField('Classificação', max_length=20, blank=True)
    corlista = models.IntegerField('Cor Lista', default=0)
    inativo = models.BooleanField('Inativo', default=False)

    class Meta:
        db_table = 'grupos'
        ordering = ['descricao']
        verbose_name = 'Grupo'
        verbose_name_plural = 'Grupos'

    def __str__(self):
        return self.descricao


class Item(models.Model):
    iditem = models.AutoField(primary_key=True)
    empresa = models.ForeignKey(
        Empresa, on_delete=models.PROTECT,
        null=True, blank=True, verbose_name='Empresa'
    )
    codigo_conv = models.IntegerField('Cód. Convênio', default=0)
    tipoitem = models.IntegerField('Tipo Item', default=0)
    tipo_item = models.CharField(
        'Tipo', max_length=1,
        choices=[('S', 'Serviço'), ('P', 'Produto / Mercadoria'), ('M', 'Matéria-Prima')],
        default='P',
    )
    identificacao = models.CharField('Identificação', max_length=50, blank=True)
    descricao = models.CharField('Descrição', max_length=200)
    modelo = models.CharField('Modelo', max_length=100, blank=True)
    unidade = models.CharField('Unidade', max_length=10, default='UN')
    grupo = models.ForeignKey(
        Grupo, on_delete=models.PROTECT,
        null=True, blank=True, verbose_name='Grupo'
    )
    precobase = models.DecimalField('Preço Base', max_digits=12, decimal_places=2, default=0)
    basecomissao = models.DecimalField('Base Comissão', max_digits=12, decimal_places=2, default=0)
    saldoestoque = models.DecimalField('Saldo Estoque', max_digits=12, decimal_places=3, default=0)
    tempotroca = models.IntegerField('Tempo Troca (dias)', default=0)
    codforn = models.CharField('Cód. Fornecedor', max_length=30, blank=True)
    corlista = models.IntegerField('Cor Lista', default=0)
    mpestoque = models.CharField('MP Estoque', max_length=1, blank=True)
    controla_estoque = models.BooleanField(
        'Controla Estoque',
        default=False,
        help_text='Gera movimentos de estoque (entradas/saídas), participa de requisições e inventários.',
    )
    inativo = models.BooleanField('Inativo', default=False)

    class Meta:
        db_table = 'itens'
        ordering = ['descricao']
        verbose_name = 'Item'
        verbose_name_plural = 'Itens'

    def __str__(self):
        return f'{self.identificacao} - {self.descricao}' if self.identificacao else self.descricao


class Portador(models.Model):
    idportador = models.AutoField(primary_key=True)
    empresa = models.ForeignKey(
        Empresa, on_delete=models.PROTECT,
        null=True, blank=True, verbose_name='Empresa'
    )
    descricao = models.CharField('Descrição', max_length=100)
    inativo = models.BooleanField('Inativo', default=False)

    class Meta:
        db_table = 'portador'
        ordering = ['descricao']
        verbose_name = 'Portador'
        verbose_name_plural = 'Portadores'

    def __str__(self):
        return self.descricao


class Metodo(models.Model):
    idmetodo = models.AutoField(primary_key=True)
    empresa = models.ForeignKey(
        Empresa, on_delete=models.PROTECT,
        null=True, blank=True, verbose_name='Empresa'
    )
    descricao = models.CharField('Descrição', max_length=100)
    sigla = models.CharField('Sigla', max_length=10, blank=True)
    movcaixa = models.BooleanField('Movimenta Caixa', default=True)
    mensagem = models.CharField('Mensagem', max_length=200, blank=True)
    inativo = models.BooleanField('Inativo', default=False)

    class Meta:
        db_table = 'metodos'
        ordering = ['descricao']
        verbose_name = 'Método de Pagamento'
        verbose_name_plural = 'Métodos de Pagamento'

    def __str__(self):
        return f'{self.sigla} - {self.descricao}' if self.sigla else self.descricao


class CondicaoPagamento(models.Model):
    idcondpag = models.AutoField(primary_key=True)
    empresa = models.ForeignKey(
        Empresa, on_delete=models.PROTECT,
        null=True, blank=True, verbose_name='Empresa'
    )
    descricao = models.CharField('Descrição', max_length=100)
    tipo = models.IntegerField('Tipo', default=0)
    condicao = models.CharField('Condição', max_length=100, blank=True)
    dias = models.IntegerField('Dias', default=0)
    parcelas = models.IntegerField('Parcelas', default=1)
    inativo = models.BooleanField('Inativo', default=False)

    class Meta:
        db_table = 'condpgto'
        ordering = ['descricao']
        verbose_name = 'Condição de Pagamento'
        verbose_name_plural = 'Condições de Pagamento'

    def __str__(self):
        return self.descricao


class TabelaPreco(models.Model):
    idtabela = models.AutoField(primary_key=True)
    descricao = models.CharField('Descrição', max_length=100)
    observacao = models.TextField('Observação', blank=True)
    datavalidade = models.DateField('Validade', null=True, blank=True)
    tipo = models.IntegerField('Tipo', default=0)
    empresa = models.ForeignKey(
        Empresa, on_delete=models.PROTECT,
        null=True, blank=True, verbose_name='Empresa'
    )
    inativo = models.BooleanField('Inativo', default=False)

    class Meta:
        db_table = 'tabela'
        ordering = ['descricao']
        verbose_name = 'Tabela de Preço'
        verbose_name_plural = 'Tabelas de Preço'

    def __str__(self):
        return self.descricao


class ItemTabelaPreco(models.Model):
    tabela = models.ForeignKey(
        TabelaPreco, on_delete=models.CASCADE,
        related_name='itens', verbose_name='Tabela'
    )
    item = models.ForeignKey(
        Item, on_delete=models.CASCADE,
        verbose_name='Item'
    )
    identificacao = models.CharField('Identificação', max_length=50, blank=True)
    preco = models.DecimalField('Preço', max_digits=12, decimal_places=2, default=0)
    basecomissao = models.DecimalField('Base Comissão', max_digits=12, decimal_places=2, default=0)
    # Preços por parcela (I a XII)
    i_pagto = models.DecimalField('1x', max_digits=12, decimal_places=2, default=0)
    ii_pagto = models.DecimalField('2x', max_digits=12, decimal_places=2, default=0)
    iii_pagto = models.DecimalField('3x', max_digits=12, decimal_places=2, default=0)
    iv_pagto = models.DecimalField('4x', max_digits=12, decimal_places=2, default=0)
    v_pagto = models.DecimalField('5x', max_digits=12, decimal_places=2, default=0)
    vi_pagto = models.DecimalField('6x', max_digits=12, decimal_places=2, default=0)
    vii_pagto = models.DecimalField('7x', max_digits=12, decimal_places=2, default=0)
    viii_pagto = models.DecimalField('8x', max_digits=12, decimal_places=2, default=0)
    ix_pagto = models.DecimalField('9x', max_digits=12, decimal_places=2, default=0)
    x_pagto = models.DecimalField('10x', max_digits=12, decimal_places=2, default=0)
    xi_pagto = models.DecimalField('11x', max_digits=12, decimal_places=2, default=0)
    xii_pagto = models.DecimalField('12x', max_digits=12, decimal_places=2, default=0)

    class Meta:
        db_table = 'itetabe'
        unique_together = ('tabela', 'item')
        verbose_name = 'Item da Tabela de Preço'
        verbose_name_plural = 'Itens da Tabela de Preço'

    def __str__(self):
        return f'{self.tabela} / {self.item}'


class ClienteFornecedor(models.Model):
    TIPO_CHOICES = [
        ('C', 'Cliente'),
        ('F', 'Fornecedor'),
        ('V', 'Vendedor'),
        ('E', 'Empregado/Técnico'),
    ]
    PESSOA_CHOICES = [('F', 'Física'), ('J', 'Jurídica')]
    ESTADO_CIVIL_CHOICES = [
        ('S', 'Solteiro(a)'),
        ('C', 'Casado(a)'),
        ('D', 'Divorciado(a)'),
        ('V', 'Viúvo(a)'),
    ]

    idcliforemp = models.AutoField(primary_key=True)
    codigo_conv = models.IntegerField('Cód. Convênio', default=0)
    tipocliforemp = models.CharField('Tipo', max_length=1, choices=TIPO_CHOICES, default='C')
    empresa = models.ForeignKey(
        Empresa, on_delete=models.PROTECT,
        null=True, blank=True, verbose_name='Empresa'
    )
    tipopessoa = models.CharField('Tipo Pessoa', max_length=1, choices=PESSOA_CHOICES, default='F')
    estadocivil = models.CharField('Estado Civil', max_length=1, choices=ESTADO_CIVIL_CHOICES, blank=True)
    classificacao = models.CharField('Classificação', max_length=10, blank=True)
    cnpjcpf = models.CharField('CPF/CNPJ', max_length=18, blank=True)
    razao = models.CharField('Razão Social', max_length=150, blank=True)
    fantasia = models.CharField('Fantasia', max_length=150, blank=True)
    nome = models.CharField('Nome', max_length=150, blank=True)
    identinscr = models.CharField('RG / Insc. Estadual', max_length=30, blank=True)
    endereco = models.CharField('Endereço', max_length=200, blank=True)
    bairro = models.CharField('Bairro', max_length=100, blank=True)
    cidade = models.ForeignKey(
        Cidade, on_delete=models.PROTECT,
        null=True, blank=True, verbose_name='Cidade'
    )
    numero = models.CharField('Número', max_length=10, blank=True)
    cep = models.CharField('CEP', max_length=10, blank=True)
    edificio = models.CharField('Edifício', max_length=100, blank=True)
    apto = models.CharField('Apto', max_length=20, blank=True)
    referencia = models.CharField('Referência', max_length=200, blank=True)
    email = models.EmailField('E-mail', blank=True)
    fone = models.CharField('Telefone', max_length=20, blank=True)
    celular = models.CharField('Celular', max_length=20, blank=True)
    convfone = models.CharField('Fone Convênio', max_length=20, blank=True)
    convcelular = models.CharField('Celular Convênio', max_length=20, blank=True)
    convcelular1 = models.CharField('Celular Conv. 1', max_length=20, blank=True)
    convcelular2 = models.CharField('Celular Conv. 2', max_length=20, blank=True)
    observacao = models.TextField('Observação', blank=True)
    obscobranca = models.TextField('Obs. Cobrança', blank=True)
    datacadastro = models.DateField('Data Cadastro', null=True, blank=True)
    # Dados pessoais (pessoa física)
    fdatanasc = models.DateField('Data Nascimento', null=True, blank=True)
    fdataexpid = models.DateField('Data Exp. RG', null=True, blank=True)
    fufexpid = models.CharField('UF Exp. RG', max_length=2, blank=True)
    fnomepai = models.CharField('Nome do Pai', max_length=150, blank=True)
    fnomemae = models.CharField('Nome da Mãe', max_length=150, blank=True)
    fempregador = models.CharField('Empregador', max_length=150, blank=True)
    fcargo = models.CharField('Cargo', max_length=100, blank=True)
    ffoneempre = models.CharField('Fone Empregador', max_length=20, blank=True)
    favalista = models.CharField('Avalista', max_length=150, blank=True)
    responsavel = models.CharField('Responsável', max_length=150, blank=True)
    # Comercial
    idvendrepre = models.IntegerField('ID Vendedor/Rep.', default=0)
    nomevendedor = models.CharField('Vendedor', max_length=100, blank=True)
    nomecidade = models.CharField('Nome Cidade', max_length=100, blank=True)
    limitecredito = models.DecimalField('Limite Crédito', max_digits=12, decimal_places=2, default=0)
    marca = models.CharField('Marca', max_length=20, blank=True)
    idusumarca = models.IntegerField('ID Usu. Marca', default=0)
    perccomiss = models.DecimalField('% Comissão', max_digits=5, decimal_places=2, default=0)
    perccomissp     = models.DecimalField('% Comissão Prom.', max_digits=5, decimal_places=2, default=0)
    valorreferencia = models.DecimalField('Valor Referência', max_digits=12, decimal_places=2, default=0)
    tipovendedor    = models.CharField('Tipo Vendedor', max_length=20, blank=True)
    equipe = models.IntegerField('Equipe', default=0)
    dataultvenda = models.DateField('Últ. Venda', null=True, blank=True)
    dtproximaTroca = models.DateField('Próx. Troca', null=True, blank=True)
    inativo = models.BooleanField('Inativo', default=False)

    class Meta:
        db_table = 'cliforem'
        ordering = ['razao', 'nome']
        verbose_name = 'Cliente / Fornecedor'
        verbose_name_plural = 'Clientes / Fornecedores'

    def __str__(self):
        return self.razao or self.nome or f'Reg. {self.idcliforemp}'

    @property
    def nome_exibicao(self):
        return self.razao or self.fantasia or self.nome


class TelefoneAdicional(models.Model):
    cliforemp = models.ForeignKey(
        ClienteFornecedor, on_delete=models.CASCADE,
        related_name='telefones', verbose_name='Cliente/Forn.'
    )
    numero = models.CharField('Número', max_length=20)
    identificacao = models.CharField('Identificação', max_length=50, blank=True)
    relacao = models.CharField('Relação', max_length=50, blank=True)
    descricao = models.CharField('Descrição', max_length=100, blank=True)

    class Meta:
        db_table = 'clifones'
        verbose_name = 'Telefone Adicional'
        verbose_name_plural = 'Telefones Adicionais'

    def __str__(self):
        return f'{self.numero} ({self.identificacao})'


class HistoricoCliente(models.Model):
    cliforemp = models.ForeignKey(
        ClienteFornecedor, on_delete=models.CASCADE,
        related_name='historico', verbose_name='Cliente'
    )
    empresa = models.ForeignKey(
        Empresa, on_delete=models.PROTECT,
        null=True, blank=True, verbose_name='Empresa'
    )
    numeroped = models.CharField('Nº Pedido', max_length=20, blank=True)
    datavenda = models.DateField('Data Venda', null=True, blank=True)
    datainstal = models.DateField('Data Instalação', null=True, blank=True)
    identificacao = models.CharField('Identificação', max_length=50, blank=True)
    descricao = models.CharField('Descrição', max_length=200, blank=True)
    quantidade = models.DecimalField('Quantidade', max_digits=12, decimal_places=3, default=0)
    valorunit = models.DecimalField('Valor Unit.', max_digits=12, decimal_places=2, default=0)
    valortotal = models.DecimalField('Valor Total', max_digits=12, decimal_places=2, default=0)
    vendedor = models.CharField('Vendedor', max_length=100, blank=True)
    tecnico = models.CharField('Técnico', max_length=100, blank=True)
    ultimavenda = models.DateField('Última Venda', null=True, blank=True)
    proxtroca = models.DateField('Próx. Troca', null=True, blank=True)

    class Meta:
        db_table = 'clihist'
        ordering = ['-datavenda']
        verbose_name = 'Histórico do Cliente'
        verbose_name_plural = 'Histórico dos Clientes'

    def __str__(self):
        return f'{self.cliforemp} | {self.datavenda} | {self.descricao}'

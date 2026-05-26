from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Servico(models.Model):
    ORIGEM_CHOICES = [
        ('OS',     'Ordem de Serviço'),
        ('OP',     'Ordem de Produção'),
        ('API',    'Integração API'),
        ('AVULSO', 'Avulso'),
    ]
    STATUS_CHOICES = [
        ('AGENDADO',    'Agendado'),
        ('A_CAMINHO',   'A Caminho'),
        ('EM_EXECUCAO', 'Em Execução'),
        ('PAUSADO',     'Pausado'),
        ('CONCLUIDO',   'Concluído'),
        ('PENDENTE',    'Pendente'),
        ('CANCELADO',   'Cancelado'),
    ]

    os_codigo      = models.CharField('Código OS', max_length=50, null=True, blank=True)
    roteiro_id     = models.IntegerField('ID Roteiro', null=True, blank=True)
    origem         = models.CharField(max_length=10, choices=ORIGEM_CHOICES, default='OS')
    status         = models.CharField(max_length=20, choices=STATUS_CHOICES, default='AGENDADO')
    tipo_atividade = models.CharField('Tipo de Atividade', max_length=100)
    cliente_id     = models.IntegerField(null=True, blank=True)
    cliente_nome   = models.CharField(max_length=200, blank=True)
    local          = models.CharField(max_length=200, blank=True)
    ativo          = models.CharField('Ativo/Equipamento', max_length=200, blank=True)
    descricao      = models.TextField(blank=True)
    data_prevista  = models.DateField(null=True, blank=True)
    prioridade     = models.IntegerField(default=0)
    criado_em      = models.DateTimeField(auto_now_add=True)
    atualizado_em  = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Serviço'
        verbose_name_plural = 'Serviços'
        ordering = ['prioridade', 'data_prevista']

    def __str__(self):
        return f'{self.tipo_atividade} — {self.cliente_nome} [{self.status}]'


class ServTecnico(models.Model):
    """
    Técnico vinculado a um Serviço de campo.

    Suporta duas origens:
    - NATIVO: usuário Django criado diretamente no sistema.
    - CRM: usuário vinculado a um registro ClienteFornecedor (tipo='E') do módulo cadastros.

    Em ambos os casos o login é feito pelo mesmo User Django.
    O campo `crm_id` guarda o pk do ClienteFornecedor quando origem='CRM'.
    O campo `nome` é snapshot — preserva o histórico mesmo se o registro for removido.
    """
    PAPEL_CHOICES = [
        ('RESPONSAVEL', 'Responsável'),
        ('APOIO',       'Apoio'),
    ]
    ORIGEM_CHOICES = [
        ('NATIVO', 'Usuário Nativo'),
        ('CRM',    'Técnico CRM'),
    ]

    servico  = models.ForeignKey(Servico, on_delete=models.CASCADE, related_name='tecnicos')
    user     = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL,
                                 verbose_name='Usuário Django')
    crm_id   = models.IntegerField('ID CRM', null=True, blank=True)
    nome     = models.CharField('Nome', max_length=200)
    origem   = models.CharField(max_length=10, choices=ORIGEM_CHOICES, default='NATIVO')
    papel    = models.CharField(max_length=15, choices=PAPEL_CHOICES, default='RESPONSAVEL')

    class Meta:
        verbose_name = 'Técnico do Serviço'
        verbose_name_plural = 'Técnicos do Serviço'

    def __str__(self):
        return f'{self.nome} ({self.papel}) — {self.servico}'


class ServMaterial(models.Model):
    ORIGEM_CHOICES = [
        ('REQUISICAO', 'Requisição'),
        ('AVULSO',     'Avulso'),
    ]

    servico              = models.ForeignKey(Servico, on_delete=models.CASCADE, related_name='materiais')
    item_id              = models.IntegerField(null=True, blank=True)
    item_codigo          = models.CharField(max_length=50, blank=True)
    item_descricao       = models.CharField(max_length=200)
    quantidade_prevista  = models.DecimalField(max_digits=10, decimal_places=3)
    quantidade_realizada = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    origem               = models.CharField(max_length=15, choices=ORIGEM_CHOICES, default='REQUISICAO')

    class Meta:
        verbose_name = 'Material do Serviço'
        verbose_name_plural = 'Materiais do Serviço'

    def __str__(self):
        return f'{self.item_descricao} x{self.quantidade_prevista}'


class ServApontamento(models.Model):
    TIPO_CHOICES = [
        ('OBSERVACAO', 'Observação'),
        ('EVIDENCIA',  'Evidência'),
        ('CHECKLIST',  'Checklist'),
        ('MEDICAO',    'Medição'),
    ]

    servico       = models.ForeignKey(Servico, on_delete=models.CASCADE, related_name='apontamentos')
    tipo          = models.CharField(max_length=15, choices=TIPO_CHOICES)
    descricao     = models.TextField(blank=True)
    arquivo       = models.FileField(upload_to='campo/evidencias/', null=True, blank=True)
    user          = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL,
                                      verbose_name='Usuário')
    registrado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Apontamento'
        verbose_name_plural = 'Apontamentos'
        ordering = ['registrado_em']

    def __str__(self):
        return f'{self.tipo} — {self.servico}'


class ServTempo(models.Model):
    """
    Linha do tempo de eventos do serviço.
    Cada mudança de status gera um registro aqui.
    Permite calcular tempo total, pausas, deslocamento etc.
    """
    EVENTO_CHOICES = [
        ('AGENDADO',  'Agendado'),
        ('A_CAMINHO', 'A Caminho'),
        ('INICIO',    'Início'),
        ('PAUSA',     'Pausa'),
        ('RETOMADA',  'Retomada'),
        ('INTERVALO', 'Intervalo'),
        ('FIM',       'Fim'),
        ('CANCELADO', 'Cancelado'),
    ]

    servico    = models.ForeignKey(Servico, on_delete=models.CASCADE, related_name='tempos')
    evento     = models.CharField(max_length=15, choices=EVENTO_CHOICES)
    timestamp  = models.DateTimeField(default=timezone.now)
    data_ref   = models.DateField(null=True, blank=True)
    user       = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL,
                                   verbose_name='Usuário')
    observacao = models.CharField(max_length=300, blank=True)

    def save(self, *args, **kwargs):
        if not self.data_ref and self.timestamp:
            self.data_ref = self.timestamp.date() if hasattr(self.timestamp, 'date') else self.timestamp
        super().save(*args, **kwargs)

    class Meta:
        verbose_name        = 'Tempo de Serviço'
        verbose_name_plural = 'Tempos de Serviço'
        ordering            = ['timestamp']

    def __str__(self):
        return f'{self.evento} — {self.timestamp:%d/%m/%Y %H:%M}'


class ScriptMensagem(models.Model):
    """
    Templates de mensagem para envio via WhatsApp.
    Suportam variáveis reservadas: {cliente}, {os}, {servico}, {local},
    {ativo}, {data}, {tecnico}, {laudo}, {materiais}.
    """
    titulo = models.CharField('Título', max_length=100)
    corpo  = models.TextField('Corpo da Mensagem')
    ativo  = models.BooleanField('Ativo', default=True)
    ordem  = models.IntegerField('Ordem', default=0)

    class Meta:
        verbose_name        = 'Script de Mensagem'
        verbose_name_plural = 'Scripts de Mensagem'
        ordering            = ['ordem', 'titulo']

    def __str__(self):
        return self.titulo

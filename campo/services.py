from django.db import transaction
from django.utils import timezone

from campo.models import Servico, ServTecnico, ServMaterial, ServTempo


def criar_servicos_roteiro(payload: dict) -> list[int]:
    """
    Cria atomicamente Servico + ServTecnico + ServMaterial + ServTempo
    a partir do payload já validado pelo serializer.

    Retorna lista de IDs dos Servico criados.
    """
    roteiro_id  = payload.get('roteiro_id')
    os_codigo   = payload.get('os_codigo')
    tecnicos    = payload.get('tecnicos', [])
    servicos    = payload.get('servicos', [])

    ids_criados = []
    agora       = timezone.now()

    with transaction.atomic():
        for srv_data in servicos:

            # ── 1. Cria o Servico ──────────────────────────────
            servico = Servico.objects.create(
                os_codigo      = os_codigo,
                roteiro_id     = roteiro_id,
                origem         = 'OS',
                status         = 'AGENDADO',
                tipo_atividade = srv_data['tipo_atividade'],
                cliente_id     = srv_data.get('cliente_id'),
                cliente_nome   = srv_data.get('cliente_nome', ''),
                local          = srv_data.get('local', ''),
                ativo          = srv_data.get('ativo', ''),
                descricao      = srv_data.get('descricao', ''),
                data_prevista  = srv_data.get('data_prevista') or None,
            )

            # ── 2. Vincula técnicos ────────────────────────────
            for tec in tecnicos:
                ServTecnico.objects.create(
                    servico  = servico,
                    crm_id   = tec['id'],
                    nome     = tec.get('nome', ''),
                    papel    = tec.get('papel', 'APOIO'),
                    origem   = 'CRM',
                )

            # ── 3. Vincula materiais ───────────────────────────
            for mat in srv_data.get('materiais', []):
                ServMaterial.objects.create(
                    servico             = servico,
                    item_id             = mat.get('item_id'),
                    item_codigo         = mat.get('item_codigo', ''),
                    item_descricao      = mat['item_descricao'],
                    quantidade_prevista = mat['quantidade'],
                    origem              = 'REQUISICAO',
                )

            # ── 4. Evento inicial na linha do tempo ────────────
            ServTempo.objects.create(
                servico    = servico,
                evento     = 'AGENDADO',
                timestamp  = agora,
                data_ref   = agora.date(),
                user       = None,
                observacao = 'Criado via integração roteiro',
            )

            ids_criados.append(servico.id)

    return ids_criados

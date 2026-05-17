"""
Importa condições de pagamento do arquivo binário VDF (DataFlex) condpgto.dat.

Estrutura do registro (128 bytes, 116 utilizados):
  Bytes  0-3   idcondpag  NUM 8.0  (4 bytes, packed BCD com bias)
  Bytes  4-103  descricao  ASC 100
  Bytes 104-107  tipo       NUM 8.0  (4 bytes)
  Bytes 108-110  condicao   ASC   3
  Bytes 111-113  dias       NUM 6.0  (3 bytes)
  Byte  114      inativo    ASC   1  ('T'=inativo, ' '=ativo)
  Byte  115      parcelas   NUM 2.0  (1 byte)

Codificação DataFlex para campos NUM:
  - Campos > 1 byte: descarta 1º byte (bias 0x10), restante = BCD empacotado
  - 1 byte: valor = ((byte >> 4) - 1) * 10 + (byte & 0x0F)
"""

import os
import struct
from django.core.management.base import BaseCommand, CommandError
from cadastros.models import CondicaoPagamento

VDF_DATA = r'C:\Jrmartins\D\EuropaNew\Data\condpgto.dat'
HDR_BYTES = 3200   # tamanho do cabeçalho DataFlex neste arquivo
REC_LEN   = 128    # comprimento fixo do registro


def _bcd_num(raw: bytes) -> int:
    """Converte campo NUM DataFlex para inteiro."""
    if len(raw) == 1:
        b = raw[0]
        return max(0, ((b >> 4) - 1) * 10 + (b & 0x0F))
    # Descartar byte de bias (sempre 0x10), restante = BCD empacotado
    val = 0
    for byte in raw[1:]:
        val = val * 100 + ((byte >> 4) * 10) + (byte & 0x0F)
    return val


def _read_records(path: str):
    """Lê todos os registros do arquivo .dat e retorna lista de dicts."""
    with open(path, 'rb') as f:
        data = f.read()

    records = []
    total = (len(data) - HDR_BYTES) // REC_LEN
    for i in range(total):
        rec = data[HDR_BYTES + i * REC_LEN : HDR_BYTES + (i + 1) * REC_LEN]

        idcondpag = _bcd_num(rec[0:4])
        descricao = rec[4:104].decode('latin-1').strip()
        tipo      = _bcd_num(rec[104:108])
        condicao  = rec[108:111].decode('latin-1').strip()
        dias      = _bcd_num(rec[111:114])
        inativo   = rec[114:115].decode('latin-1').strip().upper() == 'T'

        # Parcelas: prefere condicao se numérico, senão decodifica campo
        try:
            parcelas = int(condicao) if condicao and condicao != '000' else 1
        except ValueError:
            parcelas = max(1, _bcd_num(rec[115:116]))

        # Ignora registros sem descrição (slots vazios)
        if not descricao:
            continue

        records.append({
            'idcondpag': idcondpag,
            'descricao': descricao,
            'tipo':      tipo,
            'condicao':  condicao,
            'dias':      dias,
            'inativo':   inativo,
            'parcelas':  max(1, parcelas),
        })

    return records


class Command(BaseCommand):
    help = 'Importa condições de pagamento do arquivo DataFlex VDF (condpgto.dat)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limpar',
            action='store_true',
            help='Remove todos os registros existentes antes de importar',
        )
        parser.add_argument(
            '--arquivo',
            default=VDF_DATA,
            help=f'Caminho do condpgto.dat (padrão: {VDF_DATA})',
        )

    def handle(self, *args, **options):
        arquivo = options['arquivo']
        if not os.path.exists(arquivo):
            raise CommandError(f'Arquivo não encontrado: {arquivo}')

        if options['limpar']:
            total_del = CondicaoPagamento.objects.count()
            CondicaoPagamento.objects.all().delete()
            self.stdout.write(self.style.WARNING(
                f'  {total_del} registros existentes removidos.'
            ))

        records = _read_records(arquivo)
        self.stdout.write(f'  {len(records)} registros lidos do arquivo DataFlex.')

        criados = atualizados = ignorados = 0

        for r in records:
            obj, created = CondicaoPagamento.objects.update_or_create(
                idcondpag=r['idcondpag'],
                defaults={
                    'descricao': r['descricao'],
                    'tipo':      r['tipo'],
                    'condicao':  r['condicao'],
                    'dias':      r['dias'],
                    'inativo':   r['inativo'],
                    'parcelas':  r['parcelas'],
                },
            )
            if created:
                criados += 1
            else:
                atualizados += 1

        self.stdout.write(self.style.SUCCESS(
            f'\nImportação concluída:'
            f'\n  Criados:    {criados}'
            f'\n  Atualizados: {atualizados}'
        ))

        if options['verbosity'] >= 2:
            self.stdout.write('\nRegistros importados:')
            for r in records:
                flag = '[INATIVO]' if r['inativo'] else ''
                self.stdout.write(
                    f"  {r['idcondpag']:3d}  {r['descricao']:<50}  "
                    f"tipo={r['tipo']}  dias={r['dias']:3d}  "
                    f"parc={r['parcelas']:2d}  {flag}"
                )

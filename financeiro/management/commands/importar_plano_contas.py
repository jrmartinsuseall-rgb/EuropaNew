"""
Importa o Plano de Contas (tabconta + subconta) do DataFlex VDF.

tabconta  —  record 256 bytes (206 usados):
  Bytes   0-3    idconta     NUM 8.0
  Bytes   4-103  descricao   ASC 100
  Byte  104      deb_cred    ASC   1  ('D'=Débito, 'C'=Crédito)
  Bytes 105-204  descrigrupo ASC 100
  Byte  205      inativo     ASC   1

subconta  —  record 128 bytes (109 usados):
  Bytes   0-3    idsubconta  NUM 8.0
  Bytes   4-103  descricao   ASC 100
  Bytes 104-107  idconta     NUM 8.0  (FK → tabconta)
  Byte  108      inativo     ASC   1
"""

import os
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from financeiro.models import PlanoConta, SubConta

VDF_DATA = r'C:\Jrmartins\D\EuropaNew\Data'

# ── Parâmetros por arquivo ───────────────────────────────────
FILES = {
    'tabconta': {
        'path':   os.path.join(VDF_DATA, 'tabconta.dat'),
        'reclen': 256,
        'hdr':    3328,
    },
    'subconta': {
        'path':   os.path.join(VDF_DATA, 'subconta.dat'),
        'reclen': 128,
        'hdr':    3200,
    },
}


def _bcd(raw: bytes) -> int:
    """Converte campo NUM DataFlex → inteiro (BCD empacotado com bias 0x10)."""
    if len(raw) == 1:
        b = raw[0]
        return max(0, ((b >> 4) - 1) * 10 + (b & 0x0F))
    val = 0
    for byte in raw[1:]:
        val = val * 100 + (byte >> 4) * 10 + (byte & 0x0F)
    return val


def _asc(raw: bytes) -> str:
    """Decodifica campo ASC DataFlex → str UTF-8, removendo espaços."""
    return raw.decode('latin-1').strip()


def _read_tabconta(cfg: dict) -> list[dict]:
    with open(cfg['path'], 'rb') as f:
        data = f.read()

    records = []
    total = (len(data) - cfg['hdr']) // cfg['reclen']
    for i in range(total):
        rec = data[cfg['hdr'] + i * cfg['reclen']:
                   cfg['hdr'] + (i + 1) * cfg['reclen']]

        idconta     = _bcd(rec[0:4])
        descricao   = _asc(rec[4:104])
        deb_cred    = _asc(rec[104:105])
        descrigrupo = _asc(rec[105:205])
        inativo     = _asc(rec[205:206]).upper() == 'T'

        if not descricao:
            continue

        records.append({
            'idconta':     idconta,
            'descricao':   descricao,
            'deb_cred':    deb_cred if deb_cred in ('D', 'C') else '',
            'descrigrupo': descrigrupo,
            'inativo':     inativo,
        })
    return records


def _read_subconta(cfg: dict) -> list[dict]:
    with open(cfg['path'], 'rb') as f:
        data = f.read()

    records = []
    total = (len(data) - cfg['hdr']) // cfg['reclen']
    for i in range(total):
        rec = data[cfg['hdr'] + i * cfg['reclen']:
                   cfg['hdr'] + (i + 1) * cfg['reclen']]

        idsubconta = _bcd(rec[0:4])
        descricao  = _asc(rec[4:104])
        idconta    = _bcd(rec[104:108])
        inativo    = _asc(rec[108:109]).upper() == 'T'

        if not descricao:
            continue

        records.append({
            'idsubconta': idsubconta,
            'descricao':  descricao,
            'idconta':    idconta,
            'inativo':    inativo,
        })
    return records


class Command(BaseCommand):
    help = 'Importa tabconta (Plano de Contas) e subconta do DataFlex VDF'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limpar',
            action='store_true',
            help='Remove todos os registros existentes antes de importar',
        )
        parser.add_argument(
            '--dir',
            default=VDF_DATA,
            dest='vdf_dir',
            help=f'Diretório dos arquivos .dat (padrão: {VDF_DATA})',
        )

    def handle(self, *args, **options):
        vdf_dir = options['vdf_dir']
        FILES['tabconta']['path'] = os.path.join(vdf_dir, 'tabconta.dat')
        FILES['subconta']['path'] = os.path.join(vdf_dir, 'subconta.dat')

        for nome, cfg in FILES.items():
            if not os.path.exists(cfg['path']):
                raise CommandError(f'Arquivo não encontrado: {cfg["path"]}')

        with transaction.atomic():
            if options['limpar']:
                sc = SubConta.objects.count()
                tc = PlanoConta.objects.count()
                SubConta.objects.all().delete()
                PlanoConta.objects.all().delete()
                self.stdout.write(self.style.WARNING(
                    f'  Removidos: {tc} contas, {sc} subcontas.'
                ))

            # ── tabconta ────────────────────────────────────────
            contas = _read_tabconta(FILES['tabconta'])
            self.stdout.write(f'  tabconta: {len(contas)} registros lidos.')

            tc_criados = tc_atualizados = 0
            for r in contas:
                _, created = PlanoConta.objects.update_or_create(
                    idconta=r['idconta'],
                    defaults={
                        'descricao':   r['descricao'],
                        'deb_cred':    r['deb_cred'],
                        'descrigrupo': r['descrigrupo'],
                        'inativo':     r['inativo'],
                    },
                )
                if created:
                    tc_criados += 1
                else:
                    tc_atualizados += 1

            # ── subconta ────────────────────────────────────────
            subcontas = _read_subconta(FILES['subconta'])
            self.stdout.write(f'  subconta: {len(subcontas)} registros lidos.')

            sc_criados = sc_atualizados = sc_erros = 0
            for r in subcontas:
                try:
                    conta = PlanoConta.objects.get(pk=r['idconta'])
                except PlanoConta.DoesNotExist:
                    self.stdout.write(self.style.ERROR(
                        f'  subconta {r["idsubconta"]} '
                        f'"{r["descricao"]}": conta {r["idconta"]} não encontrada — ignorada.'
                    ))
                    sc_erros += 1
                    continue

                _, created = SubConta.objects.update_or_create(
                    idsubconta=r['idsubconta'],
                    defaults={
                        'descricao': r['descricao'],
                        'conta':     conta,
                        'inativo':   r['inativo'],
                    },
                )
                if created:
                    sc_criados += 1
                else:
                    sc_atualizados += 1

        self.stdout.write(self.style.SUCCESS(
            f'\nImportação concluída:'
            f'\n  tabconta  =>  criadas: {tc_criados}  atualizadas: {tc_atualizados}'
            f'\n  subconta  =>  criadas: {sc_criados}  atualizadas: {sc_atualizados}'
            + (f'  erros: {sc_erros}' if sc_erros else '')
        ))

        if options['verbosity'] >= 2:
            self.stdout.write('\ntabconta:')
            for r in contas:
                self.stdout.write(
                    f"  {r['idconta']:3d}  [{r['deb_cred']}]  "
                    f"{r['descricao'][:50]:<50}  {r['descrigrupo'][:35]}"
                )
            self.stdout.write('\nsubconta:')
            for r in subcontas:
                self.stdout.write(
                    f"  {r['idsubconta']:3d}  conta={r['idconta']}  {r['descricao']}"
                )

#!/usr/bin/env python3
"""
Gerador de chaves de licença — Europa

Uso:
    python gerar_licenca.py --cnpj "12.345.678/0001-99" --validade "2027-12-31" --usuarios 10
    python gerar_licenca.py --cnpj "12345678000199" --validade "2026-12-31" --usuarios 5 --secret "minha-chave-secreta"

O secret deve ser igual ao valor de LICENSE_SECRET_KEY no .env / settings.py.
Se não informado, tenta ler a variável de ambiente LICENSE_SECRET_KEY.
"""
import argparse
import base64
import hashlib
import hmac
import os
import secrets
import sys


def gerar_chave(cnpj: str, valid_until: str, max_usuarios: int, secret: str) -> str:
    cnpj_digits = ''.join(c for c in cnpj if c.isdigit())
    if len(cnpj_digits) != 14:
        raise ValueError(f'CNPJ inválido: {cnpj!r}. Esperados 14 dígitos.')
    nonce = secrets.token_hex(8)
    payload_str = f"{cnpj_digits}|{valid_until}|{max_usuarios}|{nonce}"
    payload_b64 = base64.urlsafe_b64encode(payload_str.encode()).decode().rstrip('=')
    sig = hmac.new(secret.encode(), payload_b64.encode(), hashlib.sha256).hexdigest()
    return f"{payload_b64}.{sig}"


def main():
    parser = argparse.ArgumentParser(description='Gera chave de licença Europa (HMAC-SHA256)')
    parser.add_argument('--cnpj',      required=True,  help='CNPJ da empresa (com ou sem formatação)')
    parser.add_argument('--validade',  required=True,  help='Data de validade no formato YYYY-MM-DD')
    parser.add_argument('--usuarios',  required=True,  type=int, help='Número máximo de usuários')
    parser.add_argument('--secret',    default=None,   help='Chave secreta HMAC (padrão: var. ambiente LICENSE_SECRET_KEY)')
    args = parser.parse_args()

    secret = args.secret or os.environ.get('LICENSE_SECRET_KEY')
    if not secret:
        print('ERRO: Informe --secret ou defina a variável de ambiente LICENSE_SECRET_KEY.', file=sys.stderr)
        sys.exit(1)

    try:
        chave = gerar_chave(args.cnpj, args.validade, args.usuarios, secret)
    except ValueError as e:
        print(f'ERRO: {e}', file=sys.stderr)
        sys.exit(1)

    print()
    print('=' * 72)
    print('  CHAVE DE LICENÇA GERADA')
    print('=' * 72)
    print(f'  Empresa (CNPJ):  {args.cnpj}')
    print(f'  Válida até:      {args.validade}')
    print(f'  Máx. usuários:   {args.usuarios}')
    print('-' * 72)
    print(f'  {chave}')
    print('=' * 72)
    print()


if __name__ == '__main__':
    main()

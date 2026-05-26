import json

from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from campo.serializers import SerializerError, validar_payload
from campo.services import criar_servicos_roteiro


def _token_valido(request) -> bool:
    auth = request.headers.get('Authorization', '')
    esperado = f'Token {settings.CAMPO_API_TOKEN}'
    return auth == esperado


@csrf_exempt
@require_POST
def confirmar_roteiro(request):
    if not _token_valido(request):
        return JsonResponse({'status': 'erro', 'detalhe': 'Token inválido ou ausente.'}, status=401)

    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'status': 'erro', 'detalhe': 'JSON inválido.'}, status=400)

    try:
        validar_payload(payload)
    except SerializerError as e:
        return JsonResponse({'status': 'erro', 'detalhe': str(e)}, status=400)

    try:
        ids = criar_servicos_roteiro(payload)
    except Exception as e:
        return JsonResponse({'status': 'erro', 'detalhe': f'Erro interno: {e}'}, status=500)

    return JsonResponse({
        'status': 'ok',
        'servicos_criados': len(ids),
        'ids': ids,
    })

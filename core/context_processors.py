from .models import Empresa


def empresa_atual(request):
    """
    Injeta a empresa selecionada no login em todos os templates.
    Disponível como {{ empresa_atual }} em qualquer template que use base.html.
    """
    empresa = None
    if request.user.is_authenticated:
        empresa_id = request.session.get('empresa_id')
        if empresa_id:
            try:
                empresa = Empresa.objects.get(pk=empresa_id)
            except Empresa.DoesNotExist:
                pass
    return {'empresa_atual': empresa}

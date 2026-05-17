from functools import wraps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def admin_required(view_func):
    """
    Exige login + (superusuário OU nivel_adm >= 9).
    Usado para telas de configuração do sistema (Cidades, Bancos, CFOP, Empresa).
    """
    @login_required
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        try:
            if request.user.perfil.nivel_adm >= 9:
                return view_func(request, *args, **kwargs)
        except Exception:
            pass
        raise PermissionDenied
    return _wrapped


def modulo_required(campo_permissao):
    """
    Garante que o usuário está logado E tem acesso ao módulo.
    Uso: @modulo_required('acesso_cadastro')

    Superusuários Django sempre têm acesso.
    Se o PerfilUsuario não existir, acesso negado.
    """
    def decorator(view_func):
        @login_required
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            try:
                perfil = request.user.perfil
            except Exception:
                raise PermissionDenied
            if perfil.inativo:
                raise PermissionDenied
            if not getattr(perfil, campo_permissao, False):
                raise PermissionDenied
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator

from datetime import date
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth import logout

_EXEMPT_PREFIXES = (
    '/login/', '/logout/', '/admin/', '/static/', '/favicon.ico',
    '/selecionar-empresa/',
    '/licenca-bloqueada/',
    '/senha/',
)


class EmpresaObrigatoriaMiddleware:
    """
    Por request:
      1. Garante empresa na sessão
      2. Valida licença ativa da empresa (não-superusuários)
      3. Avisa 30 dias antes da expiração (banner no request)
      4. Bloqueia acesso se licença expirada
      5. Força troca de senha quando expirada
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            path = request.path
            isento = any(path.startswith(p) for p in _EXEMPT_PREFIXES)

            if not isento:
                # ── 1. Empresa obrigatória ───────────────────────
                if not request.session.get('empresa_id'):
                    if request.user.is_superuser:
                        return redirect(f'/selecionar-empresa/?next={path}')
                    logout(request)
                    messages.warning(
                        request,
                        'Acesso negado: nenhuma empresa definida para este usuário. '
                        'Contate o administrador.'
                    )
                    return redirect('core:login')

                # Superusuário isento das demais verificações
                if not request.user.is_superuser:
                    empresa_id = request.session.get('empresa_id')

                    # ── 2 / 3 / 4. Licença ───────────────────────
                    try:
                        from .models import Licenca
                        licenca = Licenca.objects.select_related('empresa').get(
                            empresa_id=empresa_id
                        )
                        if not licenca.ativa or not licenca.is_valid:
                            return redirect('core:licenca_bloqueada')

                        dias = licenca.dias_para_expirar
                        if 0 < dias <= 30:
                            request.licenca_aviso_dias = dias
                    except Licenca.DoesNotExist:
                        return redirect('core:licenca_bloqueada')

                    # ── 5. Expiração de senha ─────────────────────
                    try:
                        perfil = request.user.perfil
                        empresa = perfil.empresa
                        expiry = empresa.senha_expiry_days if empresa else 0
                        if expiry and expiry > 0:
                            changed = perfil.password_changed_at
                            if changed is None:
                                return redirect('core:trocar_senha')
                            delta = (date.today() - changed).days
                            if delta >= expiry:
                                return redirect('core:trocar_senha')
                    except Exception:
                        pass

        response = self.get_response(request)
        return response

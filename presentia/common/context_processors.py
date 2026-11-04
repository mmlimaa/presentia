from typing import Any, Dict
from django.http import HttpRequest
from presentia.courses.models import Nucleo

def admin_nucleos(request: HttpRequest) -> Dict[str, Any]:
    if not request.path.startswith('/admin/'):
        return {}
    
    if not request.user.is_authenticated:
        return {}

    if request.user.is_superuser:
        nucleos = Nucleo.objects.all()
    else:
        nucleos = Nucleo.objects.filter(pk=request.user.nucleo_padrao_id) if request.user.nucleo_padrao_id else Nucleo.objects.none()

    # Tenta pegar o nucleo selecionado no dropdown (via GET) ou o padrao do usuario
    nucleo_selecionado = request.GET.get('nucleo_ativo')
    if nucleo_selecionado:
        request.session['nucleo_ativo'] = nucleo_selecionado
    else:
        nucleo_selecionado = request.session.get('nucleo_ativo')
        
    if not nucleo_selecionado and request.user.nucleo_padrao_id:
        nucleo_selecionado = str(request.user.nucleo_padrao_id)

    return {
        'admin_nucleos_list': nucleos,
        'admin_nucleo_ativo': nucleo_selecionado,
    }



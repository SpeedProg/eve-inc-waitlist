from typing import Dict

from waitlist.base import swag


@swag.definition('ErrorNotFound', tags=['v1_model'])
def error_404(error_msg: str) -> Dict[str, str]:
    """
    file: error_404.yml
    """
    return {'error': error_msg}


@swag.definition('ErrorBadRequest', tags=['v1_model'])
def error_400(error_msg: str) -> Dict[str, str]:
    """
    file: error_400.yml
    """
    return {'error': error_msg}


@swag.definition('ErrorForbidden', tags=['v1_model'])
def error_403(error_msg: str) -> Dict[str, str]:
    """
    file: error_403.yml
    """
    return {'error': error_msg}
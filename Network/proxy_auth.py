"""Create a fresh, single-use authorization token for the proxy."""
import base64
import hashlib
import hmac
import secrets
import time

from ConfDir import Configs


class ProxyAuthError(RuntimeError):
    """The local proxy authorization configuration is incomplete."""


def generate_auth_header() -> dict:
    secret = Configs.PROXY_HMAC_SECRET
    if not secret:
        raise ProxyAuthError('Не задан PROXY_HMAC_SECRET в .env лаунчера')
    timestamp = str(int(time.time()))
    nonce = secrets.token_hex(16)
    signed = f'{timestamp}.{nonce}'
    signature = hmac.new(secret.encode('utf-8'), signed.encode('ascii'), hashlib.sha256).hexdigest()
    token = base64.b64encode(f'{signed}.{signature}'.encode('ascii')).decode('ascii')
    return {'Authorization': f'HMAC {token}'}

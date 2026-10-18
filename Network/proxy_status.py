"""One quiet, asynchronous health check and shared download routing per server."""
import logging
import threading
import time
from dataclasses import dataclass, field

import requests
from ConfDir.Configs import API_KEY, CONFIG, CURSEFORGE_CONFIG

logger = logging.getLogger(__name__)


@dataclass
class ProxyStatus:
    available: bool | None = None
    latency_ms: float | None = None
    started: bool = False
    thread: threading.Thread | None = None
    ready: threading.Event = field(default_factory=threading.Event)
    lock: threading.Lock = field(default_factory=threading.Lock)


_servers = {}
_servers_lock = threading.Lock()


def proxy_url(url=None):
    return (url or CURSEFORGE_CONFIG['proxy_url']).rstrip('/')


def get_proxy_status(url=None):
    key = proxy_url(url)
    with _servers_lock:
        return _servers.setdefault(key, ProxyStatus())


def proxy_available(url=None):
    if not CONFIG.get('use_proxy_for_downloads', True) or not CURSEFORGE_CONFIG.get('enabled', True):
        return False
    status = get_proxy_status(url)
    with status.lock:
        # Downloads can start directly while the health check is still running.
        return status.available is True


def probe_proxy(url=None):
    """HTTP health probes check the actual service; ICMP is not required."""
    url = proxy_url(url)
    status = get_proxy_status(url)
    available = False
    elapsed = None
    if CONFIG.get('use_proxy_for_downloads', True) and CURSEFORGE_CONFIG.get('enabled', True):
        start = time.perf_counter()
        try:
            with requests.get(url + '/api/v1/health', headers={'X-API-Key': API_KEY},
                              timeout=(1, 2)) as response:
                available = response.status_code == 200
                if available:
                    try:
                        data = response.json()
                        if isinstance(data, dict):
                            available = data.get('success') is not False and data.get('status') not in ('error', 'down', 'unhealthy')
                    except ValueError:
                        pass
                if available:
                    elapsed = (time.perf_counter() - start) * 1000
        except requests.RequestException:
            pass
    with status.lock:
        status.available = available
        status.latency_ms = elapsed
        status.started = True
        status.ready.set()
    logger.debug('Proxy %s: available=%s, latency_ms=%s', url, available, elapsed)
    return available


def start_proxy_probe(url=None):
    """Start once per launcher session, without waiting on the GUI thread."""
    url = proxy_url(url)
    status = get_proxy_status(url)
    with status.lock:
        if not status.started:
            status.started = True
            status.thread = threading.Thread(target=probe_proxy, args=(url,), name='proxy-health', daemon=True)
            status.thread.start()
        return status.thread


def mark_proxy_unavailable(url=None):
    status = get_proxy_status(url)
    with status.lock:
        status.available = False
        status.latency_ms = None
    logger.debug('Proxy %s stopped responding; remaining downloads use direct sources', proxy_url(url))

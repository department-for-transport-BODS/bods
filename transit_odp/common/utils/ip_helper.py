import logging
import socket

logger = logging.getLogger(__name__)


def get_hostname():
    return socket.gethostname()


def get_ip_address():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 1))
    except OSError:
        logger.error("Unable to get IP address.")
        return None
    else:
        local_ip_address = s.getsockname()[0]
        return local_ip_address

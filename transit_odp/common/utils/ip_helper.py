import socket


def GetHostname():
    return socket.gethostname()


def GetIpAddress():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 1))
    except OSError:
        print("GetIpAddress() failed")
        return None
    else:
        local_ip_address = s.getsockname()[0]
        return local_ip_address

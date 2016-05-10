from docker import Client

# client cache
clients = {}


def get_client(base_url=None):
    """
    Simple wrapper for mocking later, returns a docker Client object bound
    to the local docker socker under /var/run/docker.sock.
    :return: The docker Client instance
    """
    global client
    if not base_url:
        base_url = 'unix:///var/run/docker.sock'
    if base_url not in clients:
        clients[base_url] = Client(base_url=base_url)
    return clients[base_url]

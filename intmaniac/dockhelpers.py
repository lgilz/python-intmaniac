from intmaniac import tools

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


def create_container(image, command=None, environment={}):
    """
    Creates a new test container instance with the command given. Must be
    called for each command, because we can't change the command once
    it's set.
    :param image: The docker image to use
    :param command: The command to execute with the container, can be <None>
    :param environment: The environment to use in the container
    :return: The container id string
    """
    logger = tools.get_logger(__name__+".create_container")
    dc = get_client()
    tmp = dc.create_container(image,
                              command=command,
                              environment=environment)
    container_id = tmp['Id']
    logger.debug("Container id {} created (image: {}, command: {}, env: {})"
                 .format(
                         container_id[:8], image,
                         command if isinstance(command, str) else str(command),
                         str(environment)
                        )
    )
    return container_id

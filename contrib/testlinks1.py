#!/usr/bin/env python

from docker import Client

if __name__ == "__main__":
    cli = Client(base_url='unix://var/run/docker.sock', version='auto')
    container = cli.create_container(image='busybox', command='ping pingme')
    response = cli.start(
        container=container.get('Id'),
        name="pinging",
        links=(('pingme', 'pingme'),)
    )
    print("Now try 'docker logs -f pinging'!")

FROM python:3-onbuild

MAINTAINER Axel Bock <mr.axel.bock@gmail.com>

RUN pip install docker-compose ; pip install -e .

ENTRYPOINT [ "intmaniac", "-c", "/intmaniac/intmaniac.yaml"]

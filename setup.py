#!/usr/bin/env python

from setuptools import setup, find_packages
from pip.req import parse_requirements
from pip.download import PipSession

import io
from re import match


VERSION = "0.15.2"


def use_line(line_thing):
    return not bool(match('^ *(#.*)?$', str(line_thing)))


install_reqs = parse_requirements("./requirements.txt", session=PipSession())
reqs = [str(ir.req) for ir in install_reqs if use_line(ir)]

long_description = (
    io.open('README.rst', encoding='utf-8').read() +
    '\n' +
    io.open('CHANGES.rst', encoding='utf-8').read()
)

setup(
    name             = 'intmaniac',
    packages         = find_packages(),
    version          = VERSION,
    description      = 'A generic integration test tool utilizing docker-compose (for now)',
    long_description = long_description,
    author           = 'Axel Bock',
    author_email     = 'mr.axel.bock@gmail.com',
    url              = 'https://github.com/flypenguin/python-intmaniac',
    download_url     = 'https://github.com/flypenguin/python-intmaniac/tarball/{}'.format(VERSION),
    keywords         = 'integrationtest sysadmin devops ci cd',
    install_requires = reqs,
    entry_points     = {
        'console_scripts': [
            'intmaniac=intmaniac:console_entrypoint',
        ],
    },
    classifiers      = [
        "License :: OSI Approved :: MIT License",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Programming Language :: Python :: 3",
        "Operating System :: POSIX",
        "Operating System :: MacOS",
        "Topic :: System :: Systems Administration",
        "Topic :: Software Development :: Testing",
    ],
)

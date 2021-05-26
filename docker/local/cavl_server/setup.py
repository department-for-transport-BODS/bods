# coding: utf-8

import sys

from setuptools import find_packages, setup

NAME = "cavl_server"
VERSION = "0.1.0"
# To install the library, run the following
#
# python setup.py install
#
# prerequisite: setuptools
# http://pypi.python.org/pypi/setuptools

REQUIRES = ["connexion"]

setup(
    name=NAME,
    version=VERSION,
    description="CAVL Config API",
    author_email="greg.brown@itoworld.com",
    url="",
    keywords=["Swagger", "CAVL Config API"],
    install_requires=REQUIRES,
    packages=find_packages(),
    package_data={"": ["swagger/swagger.yaml"]},
    include_package_data=True,
    entry_points={"console_scripts": ["cavl_server=cavl_server.__main__:main"]},
    long_description="""\
    Used to configure feed consumers in the CAVL Service
    """,
)

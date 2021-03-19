import os
import sys

from setuptools import find_packages, setup

IS_RTD = os.environ.get("READTHEDOCS", None)

version = "0.4.0b7"

long_description = open(os.path.join(os.path.dirname(__file__), "README.rst")).read()

install_requires = [
    "morepath==0.19",
    "alembic",
    "rulez>=0.1.4,<0.2.0",
    "inverter>=0.1.0<0.2.0",
    "more.cors",
    "celery",
    "redis",
    "jsl",
    "pyyaml>=4.2b1",
    "more.jsonschema",
    "sqlalchemy",
    "sqlalchemy_utils",
    "more.signals",
    "DateTime",
    "transitions",
    "jsonpath_ng",
    "python-dateutil",
    "more.jwtauth",
    "more.itsdangerous",
    "sqlsoup",
    "celery",
    "gunicorn",
    "itsdangerous",
    "pyyaml",
    "passlib",
    "jsonschema",
    "more.transaction",
    "zope.sqlalchemy",
    "python-dateutil",
    "more.cors",
    "sqlalchemy_jsonfield",
    "sqlsoup",
    "celery",
    "gunicorn",
    "itsdangerous",
    "pyyaml",
    "passlib",
    "jsonschema",
    "more.transaction",
    "zope.sqlalchemy",
    "more.basicauth",
    "cryptography",
    "elasticsearch>7.0.0,<8.0.0",
    "pamela",
    "click",
    "cookiecutter",
    "eventlet",
    "wsgigzip",
    "psycopg2",
    "colander",
    "deform",
    "more.chameleon",
    "more.static",
    "RestrictedPython",
    "beaker",
    "zstandard",
    "oauthlib[signedtoken]",
    "requests-oauthlib",
]

if IS_RTD is None:
    install_requires.append("python-ldap")

setup(
    name="morpfw",
    version=version,
    description="Web framework based on morepath",
    long_description=long_description,
    classifiers=[],  # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    keywords="",
    author="Izhar Firdaus",
    author_email="izhar@kagesenshi.org",
    url="http://github.com/morpframework/morpfw",
    license="Apache-2.0",
    packages=find_packages(exclude=["ez_setup", "examples", "tests"]),
    include_package_data=True,
    zip_safe=False,
    install_requires=install_requires,
    extras_require={
        "test": [
            "nose",
            "webtest",
            "pytest",
            "pytest-html",
            "pytest_postgresql",
            "pytest_rabbitmq",
            "pytest-annotate",
            "pytest-cov",
            "pika",
            "mirakuru",
        ],
        "docs": ["sphinxcontrib-httpdomain", "sphinx-click"],
    },
    entry_points={
        "morepath": ["scan=morpfw"],
        "console_scripts": [
            "morpfw=morpfw.cli.main:main",
            "mfw-runmodule=morpfw.cli:run_module",
            "mfw-profilemodule=morpfw.cli:run_module_profile",
        ],
    },
)

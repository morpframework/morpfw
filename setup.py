from setuptools import setup, find_packages
import sys
import os

version = '0.1.0'

setup(name='morpfw',
      version=version,
      description="Web framework based on morepath",
      long_description="""\
""",
      classifiers=[],  # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='',
      author='Izhar Firdaus',
      author_email='izhar@abyres.net',
      url='http://github.com/morpframework/morpfw',
      license='MIT',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          # -*- Extra requirements: -*-
          'rulez',
          'more.cors',
          'celery',
          'redis',
          'jsl',
          'pyyaml',
          'more.jsonschema',
          'jsonobject==0.9.4',
          'sqlalchemy',
          'more.signals',
          'DateTime',
          'transitions',
          'jsonpath_ng',
          'python-dateutil',
          'more.jwtauth',
          'sqlsoup',
          'celery',
          'gunicorn',
          'itsdangerous',
          'pyyaml',
          'passlib',
          'jsonschema',
          'more.transaction',
          'zope.sqlalchemy',
          'python-dateutil',
          'more.cors',
          'sqlalchemy_jsonfield',
          'sqlsoup',
          'celery',
          'gunicorn',
          'itsdangerous',
          'pyyaml',
          'passlib',
          'jsonschema',
          'more.transaction',
          'zope.sqlalchemy',
          'more.basicauth'
      ],
      extras_require={
          'test': [
              'nose',
              'webtest',
              'pytest',
              'pytest-html',
              'pytest_postgresql',
              'pytest_rabbitmq',
              'pika',
              'elasticsearch>=5.0.0,<6.0.0'
          ]
      },
      entry_points={'morepath': ['scan=morpfw']}
      )

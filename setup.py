from setuptools import setup, find_packages
import sys
import os

version = '0.0'

setup(name='morp',
      version=version,
      description="Web framework with weird powers",
      long_description="""\
""",
      classifiers=[],  # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='',
      author='Izhar Firdaus',
      author_email='izhar@abyres.net',
      url='http://github.com/abyres/ccis',
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
          'jsonobject',
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
              'pytest_postgresql',
              'pytest_rabbitmq',
              'pika',
              'elasticsearch>=5.0.0,<6.0.0'
          ]
      },
      entry_points={'morepath': ['scan=morp']}
      )

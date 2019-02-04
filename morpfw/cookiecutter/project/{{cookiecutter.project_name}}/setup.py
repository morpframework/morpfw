from setuptools import setup, find_packages
import sys
import os

version = '{{ cookiecutter.version }}'

setup(name='{{ cookiecutter.project_name }}',
      version=version,
      description="{{ cookiecutter.short_description }}",
      long_description="""\
      """,
      classifiers=[],  # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='',
      author='{{ cookiecutter.author_name }}',
      author_email='{{ cookiecutter.author_email }}',
      url='{{ cookiecutter.project_url }}',
      license='{{ cookiecutter.license }}',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      python_requires=">=3.7",
      install_requires=[
          # -*- Extra requirements: -*-
          'morpfw>=0.2.1rc3',
      ],
      extras_require={
          'test': [
              'morpfw[test]',
          ]
      },
      entry_points="""
      # -*- Entry points: -*-
      """,
      )

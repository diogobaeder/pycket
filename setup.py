from setuptools import setup, find_packages
import sys, os

version = '0.1'

setup(name='pycket',
      version=version,
      description="Redis sessions for Tornado",
      long_description="""\
Redis user sessions to use with Tornado server""",
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='pycket redis tornado session python',
      author='Diogo Baeder',
      author_email='desenvolvedor@diogobaeder.com.br',
      url='',
      license='BSD 2-Clause',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=True,
      install_requires=[
          'redis',
          'tornado',
      ],
      entry_points="""
      # -*- Entry points: -*-
      """,
      )

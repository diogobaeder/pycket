from setuptools import setup, find_packages
import sys, os

version = '0.1.2'

setup(name='pycket',
      version=version,
      description="Redis sessions for Tornado",
      long_description="Redis sessions for Tornado (see GitHub page for more info)",
      classifiers=[
          'Topic :: Internet :: WWW/HTTP :: Session',
          'Topic :: Database',
          ], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='pycket redis tornado session python',
      author='Diogo Baeder',
      author_email='desenvolvedor@diogobaeder.com.br',
      url='https://github.com/diogobaeder/pycket',
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
      test_suite="nose.collector",
      tests_require="nose",
)

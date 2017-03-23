#!/usr/bin/env python
"""PyANCP
"""
from setuptools import setup, find_packages

version = '0.1'

setup(name='PyANCP',
      version=version,
      author='Christian Giese',
      author_email='cgiese@juniper.net',
      url='https://gitlab.bng.dtlabs.de/Testing-Software/PyANCPl',
      license='Apache 2',
      description='Python ANCP Client and Library',
      long_description=open('README.md').read(),
      classifiers=[
       'Programming Language :: Python :: 2.7',
       'Programming Language :: Python :: 3.2',
      ],
      packages=find_packages(),
      zip_safe=True,
      include_package_data=True,
      )

#!/usr/bin/env python
"""PyANCP - Python ANCP (RFC 6320) Client and Library
"""
from setuptools import setup, find_packages

version = '0.1.7'

setup(name='PyANCP',
      version=version,
      author='Christian Giese (GIC-de)',
      url='https://github.com/GIC-de/PyANCP',
      license='MIT',
      description='Python ANCP (RFC 6320) Client and Library',
      long_description=open('README.rst').read(),
      classifiers=[
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3.8',
          'Programming Language :: Python :: 3.9',
          'Programming Language :: Python :: 3.10'
      ],
      packages=find_packages(),
      zip_safe=True,
      include_package_data=True,
      install_requires=['future'],
      )

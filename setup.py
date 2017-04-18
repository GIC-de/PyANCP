#!/usr/bin/env python
"""PyANCP - Python ANCP (RFC 6320) Client and Library
"""
from setuptools import setup, find_packages

version = '0.1.6'

setup(name='PyANCP',
      version=version,
      author='Christian Giese',
      author_email='cgiese@juniper.net',
      url='https://github.com/GIC-de/PyANCP',
      license='MIT',
      description='Python ANCP (RFC 6320) Client and Library',
      long_description=open('README.rst').read(),
      classifiers=[
       'Programming Language :: Python :: 2.7',
       'Programming Language :: Python :: 3.2',
       'Programming Language :: Python :: 3.5',
      ],
      packages=find_packages(),
      zip_safe=True,
      include_package_data=True,
      install_requires=['future'],
      )

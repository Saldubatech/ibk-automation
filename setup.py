# -*- coding: utf-8 -*-

# Learn more on setup.py: https://github.com/kennethreitz/setup.py

from setuptools import setup, find_packages


with open('README.md') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='salduba.pyuml',
    version='0.1.0',
    description='Experiments using Python as a source for UML class Diagrams',
    long_description=readme,
    author='Miguel Pinilla',
    author_email='miguel.pinilla@saldubatech.com',
    url='https://github.com/salduba/pyuml',
    license=license,
    packages=find_packages(exclude=('tests', 'docs'))
)


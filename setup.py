# -*- coding: utf-8 -*-

# Learn more on setup.py: https://github.com/kennethreitz/setup.py

from setuptools import setup, find_packages


with open('README.md') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='salduba.ib_tws_proxy',
    version='0.1.0',
    description='IBK API Access to place orders from CSV',
    long_description=readme,
    author='Miguel Pinilla',
    author_email='miguel.pinilla@saldubatech.com',
    url='https://github.com/salduba/ibk-automation',
    license=license,
    packages=find_packages(exclude=('tests', 'docs'))
)


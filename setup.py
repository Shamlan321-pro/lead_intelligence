# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

with open('requirements.txt') as f:
	requirements = f.read().strip().split('\n')

# get version from __version__ variable in lead_intelligence/__init__.py
from lead_intelligence import __version__ as version

setup(
	name='lead_intelligence',
	version=version,
	description='Advanced lead generation and intelligence platform for ERPNext',
	author='Your Organization',
	author_email='support@yourorganization.com',
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=requirements
)
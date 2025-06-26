# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

with open('requirements.txt') as f:
	requirements = f.read().strip().split('\n')

setup(
	name='lead_intelligence',
	version='1.0.0',
	description='Advanced lead generation and intelligence platform for ERPNext',
	author='Your Organization',
	author_email='support@yourorganization.com',
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=requirements
)
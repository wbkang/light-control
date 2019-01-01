#!/usr/bin/env python3

from setuptools import setup, find_packages, Extension
import unittest

setup(
    name="lightcontrol",
    version='0.1.0',
    description='Light control',
    license='MIT',
    author='Woongbin Kang',
    author_email='wbk@outlook.com',
    packages=find_packages(exclude=['tests*']),
    setup_requires=['pytest-runner'],
    install_requires=["RPi.GPIO",
                      "boto3",
                      'pytz',
                      'flask',
                      'tzlocal'],
    tests_require=['pytest'],
    include_package_data=True,
    entry_points={},
    classifiers=['Private :: Do not upload']
)

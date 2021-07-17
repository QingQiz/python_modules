#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import setuptools


setuptools.setup(
    name="QingQiz",
    version="0.0.2",
    author="QingQiz",
    author_email="sofeeys@outlook.com",
    description="..",
    long_description_content_type="text/markdown",
    url="https://github.com/QingQiz/python_scripts",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
    ],
    python_requires=">=3.6",
    install_requires=[
        'python-pam',
        'requests',
        'pycryptodome',
        'rich'
    ]
)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import setuptools


setuptools.setup(
    name="QingQiz",
    version="0.0.5",
    author="QingQiz",
    author_email="sofeeys@outlook.com",
    description="..",
    long_description_content_type="text/markdown",
    url="https://github.com/QingQiz/python_scripts",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
    ],
    python_requires=">=3.7",
    install_requires=[
        'beautifulsoup4',
        'python-pam',
        'requests',
        'pycryptodome',
        'rich'
    ]
)

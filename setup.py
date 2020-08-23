#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import setuptools


with open("README.md") as f:
    ld = f.read()

setuptools.setup(
    name="QingQiz",
    version="0.0.1",
    author="QingQiz",
    author_email="sofeeys@outlook.com",
    description="..",
    long_description=ld,
    long_description_content_type="text/markdown",
    url="https://github.com/QingQiz/python_scripts",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
    ],
    python_requires=">=3.6",
)

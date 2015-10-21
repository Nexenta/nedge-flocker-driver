# Copyright 2015 Nexenta Inc.
# See LICENSE file for details.

from setuptools import setup, find_packages
import codecs
from os import path

# Get the long description from the relevant file
with codecs.open('DESCRIPTION.rst', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='nedge_flocker_plugin',
    version='1.0',
    description='NexentaEdge Backend Plugin for ClusterHQ/Flocker',
    long_description=long_description,
    author='Nabin Acharya',
    author_email='nabin.archarya@nexenta.com',
    license='Apache 2.0',

    classifiers=[

    'Development Status :: Beta',

    'Intended Audience :: System Administrators',
    'Intended Audience :: Developers',
    'Topic :: Software Development :: Libraries :: Python Modules',

    'License :: OSI Approved :: Apache Software License',

    # Python versions supported 
    'Programming Language :: Python :: 2.7',
    ],

    keywords='backend, plugin, flocker, docker, python',
    packages=find_packages(),
    #packages=find_packages(exclude=['test*']),
)

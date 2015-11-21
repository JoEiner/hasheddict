#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2015 Johannes Schreiner
#
# This file is part of hasheddict.
#
# hasheddict is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# hasheddict is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with hasheddict. If not, see <http://www.gnu.org/licenses/>.

from setuptools import setup

from codecs import open
from os import path
from imp import load_module, PY_SOURCE

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

modulefile = path.join(here, 'hasheddict', '__init__.py')
hasheddict = load_module('hasheddict',
                         open(modulefile),
                         modulefile,
                         ('__init__.py', 'r', PY_SOURCE))

author, email =  hasheddict.__author__.split(', ')
setup(name='hasheddict',
      version=str(hasheddict.__version__),
      description='A dictionary that provides cryptographic hashes of its contents.',
      url=hasheddict.__url__,
      author=author,
      author_email=email,
      license=hasheddict.__license__,
      packages=['hasheddict'],
      zip_safe=True,
      classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Operating System :: OS Independent',
        'Topic :: Security',
        'Topic :: Security :: Cryptography'
      ],
      keywords = 'hash sha authentication checksum dictionary dict')

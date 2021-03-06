#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2010-2016 GRNET S.A.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Packaging module for snf-astakos-app"""

import os

from imp import load_source
from setuptools import setup, find_packages

HERE = os.path.abspath(os.path.normpath(os.path.dirname(__file__)))
VERSION_PY = os.path.join(HERE, 'astakos', 'version.py')

# Package info
VERSION = getattr(load_source('version', VERSION_PY), '__version__')
SHORT_DESCRIPTION = 'Synnefo Identity Management component'

PACKAGES_ROOT = '.'
PACKAGES = find_packages(PACKAGES_ROOT)

# Package meta
CLASSIFIERS = [
    'Development Status :: 3 - Alpha',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Topic :: Utilities',
    'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
]

# Package requirements
INSTALL_REQUIRES = [
    'Django>=1.7, <1.8',
    'httplib2>=0.6.0',
    'python-dateutil>=1.4.1',
    'snf-common',
    'django-tables2',
    'recaptcha-client>=1.0.5',
    'django-ratelimit',
    'requests',
    'requests-oauthlib',
    'snf-django-lib',
    'snf-branding',
    'snf-webproject',
]

EXTRAS_REQUIRES = {
}

TESTS_REQUIRES = [
]

setup(
    name='snf-astakos-app',
    version=VERSION,
    license='GNU GPLv3',
    url='http://www.synnefo.org/',
    description=SHORT_DESCRIPTION,
    classifiers=CLASSIFIERS,

    author='Synnefo development team',
    author_email='synnefo-devel@googlegroups.com',
    maintainer='Synnefo development team',
    maintainer_email='synnefo-devel@googlegroups.com',

    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,

    install_requires=INSTALL_REQUIRES,

    dependency_links=['http://www.synnefo.org/packages/pypi'],

    scripts=['astakos/scripts/snf-component-register'],
    entry_points={
        'synnefo': [
            'default_settings = astakos.synnefo_settings',
            'web_apps = astakos.synnefo_settings:installed_apps',
            'web_middleware = astakos.synnefo_settings:middlware_classes',
            'web_context_processors = astakos.synnefo_settings:context_processors',
            'urls = astakos.urls:urlpatterns',
            'web_static = astakos.synnefo_settings:static_files'
        ],
        'console_scripts': [
            'snf-service-export = astakos.scripts.snf_service_export:main',
        ],
    }
)

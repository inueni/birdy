#!/usr/bin/env python
from setuptools import setup, find_packages
from birdy import __author__, __version__
import os
import sys

try:
    from pypandoc import convert
    def read_md(f):
        return convert(f, 'rst')
except ImportError:
    print("warning: pypandoc module not found, could not convert Markdown to RST")
    def read_md(f):
        return open(f, 'r', encoding='utf-8').read()


if sys.argv[-1] == 'publish':
    try:
        import pypandoc
    except ImportError:
        print("pypandoc not installed.\nUse `pip install pypandoc`.")
        
    print("You probably want to also tag the version now:")
    print("  git tag -a %s -m 'version %s'" % (__version__, __version__))
    print("  git push --tags")
    sys.exit()

setup(
    name = 'birdy',
    version = __version__,
    install_requires = (
        'requests>=1.2.3',
        'requests_oauthlib>=0.3.2',
    ),
    author = 'Mitja Pagon',
    author_email = 'mitja@inueni.com',
    license = 'MIT',
    url = 'https://github.com/inueni/birdy/',
    keywords = 'twitter api tweet birdy search',
    description = 'birdy is a super awesome Twitter API client for Python.',
    long_description = read_md('README.md'),
    include_package_data = True,
    packages = find_packages(),
    zip_safe=False,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'License :: OSI Approved :: MIT License',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Communications :: Chat',
        'Topic :: Internet',
        'Programming Language :: Python',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ]
)
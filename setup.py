#!/usr/bin/env python3
from setuptools import setup, find_packages
import re
import os

version = re.search("__version__ = '([^']+)'", open(
    os.path.join(os.path.dirname(__file__), 'pyhiera/__init__.py')
).read().strip()).group(1)

setup(
    name='pyhiera',
    version=version,
    # description="make random passphrase",
    author="Tatsuo Nakajyo",
    author_email="tnak@nekonaq.com",
    license='BSD',
    packages=find_packages(),
    python_requires='~=3.6.9',
    install_requires=['pyyaml'],
    entry_points={
        'console_scripts': [
            'pyhiera = pyhiera.cli:Command.main',
        ]
    },
)

# Local Variables:
# compile-command: "python3 ./setup.py sdist"
# End:

"""Inline images and file transfers for iTerm2."""

from pathlib import Path

from setuptools import setup

BASEDIR = Path(__file__).resolve().parent

setup(
    name='iterm2-images',
    version='0.1.0',
    description='Enter description here.',
    long_description=(BASEDIR / 'README.rst').read_text(),
    url='https://github.com/crowsonkb/iterm2-images',
    author='Katherine Crowson',
    author_email='crowsonkb@gmail.com',
    license='MIT',
    packages=['iterm2_images'],
    install_requires=(BASEDIR / 'requirements.txt').read_text().strip().split('\n'),
    python_requires='>=3.6',
    include_package_data=True,
    entry_points={
        'console_scripts': ['iidisplay=iterm2_images.display:main'],
    },
)

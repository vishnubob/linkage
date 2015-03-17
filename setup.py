#!/usr/bin/env python

from distutils.core import setup

sctk = {
    "name": "linkage",
    "description": "Linkage Evolver",
    "author":"Giles Hall",
    "packages": ["linkage"],
    "package_dir": {"linkage": "src"},
    "version": "0.1",
}

if __name__ == "__main__":
    setup(**sctk)

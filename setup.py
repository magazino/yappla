#!/usr/bin/env python3
from setuptools import setup # type: ignore

long_description = """
============================================================
    YAPPLA
 ============================================================

    this package contains the YAPPLA planner
    as well as the required data structures to convert between
    the unified_planning framework and YAPPLA.
"""

setup(
      name='up_yappla',
      version='0.0.1',
      description='YAPPLA = Yet Another Probabilistic PLAnner (with unified_planning interface)',
      author='Daniele Calisi',
      author_email='calisi@magazino.eu',
      url='https://www.aiplan4eu-project.eu',
      packages=['up_yappla', 'yappla'],
      license='APACHE',
)

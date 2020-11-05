from setuptools import setup, find_packages, Extension
from os import path
import os

here = path.abspath(path.dirname(__file__))

req = [
    'numpy',
    'spatialmath-python>=0.8.3',
    'scipy',
    'matplotlib',
    'ansitable'
]

swift_req = [
    'pybullet'
]

vp_req = [
    'vpython',
    'numpy-stl'
]

dev_req = [
    'pytest',
    'pytest-cov',
    'flake8',
    'pyyaml',
    'sympy'
]

docs_req = [
    'sphinx',
    'sphinx_rtd_theme',
    'sphinx-autorun',
]

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

# Get the release/version string
with open(path.join(here, 'RELEASE'), encoding='utf-8') as f:
    release = f.read()

def package_files(directory):
    paths = []
    for (pathhere, _, filenames) in os.walk(directory):
        for filename in filenames:
            paths.append(os.path.join('..', pathhere, filename))
    return paths


extra_files = package_files('roboticstoolbox/models/xacro')

frne = Extension(
        'frne',
        sources=[
            './roboticstoolbox/core/vmath.c',
            './roboticstoolbox/core/ne.c',
            './roboticstoolbox/core/frne.c'])

setup(
    name='roboticstoolbox',

    version=release,

    description='A Python library for robotic education and research',

    long_description=long_description,

    long_description_content_type='text/markdown',

    url='https://github.com/petercorke/robotics-toolbox-python',

    author='Jesse Haviland and Peter Corke',

    license='MIT',

    classifiers=[
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 3 - Alpha',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',
        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: MIT License',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        ],

    python_requires='>=3.6',
    
    project_urls={
        'Documentation': 'https://petercorke.github.io/roboticstoolbox-python',
        'Source': 'https://github.com/petercorke/roboticstoolbox-python',
        'Tracker': 'https://github.com/petercorke/roboticstoolbox-python/issues',
        'Coverage': 'https://codecov.io/gh/petercorke/roboticstoolbox-python'
    },

    url='https://github.com/petercorke/roboticstoolbox-python',

    ext_modules=[frne],

    keywords='python robotics robotics-toolbox kinematics dynamics' \
        ' motion-planning trajectory-generation jacobian hessian control' \
        ' simulation robot-manipulator mobile-robot'

    packages=find_packages(exclude=["tests", "examples", "notebooks"]),

    package_data={'roboticstoolbox': extra_files},

    include_package_data=True,

    install_requires=req,

    extras_require={
        'swift': swift_req,
        'dev': dev_req,
        'docs': docs_req,
        'vpython': vp_req
    }
)

import os

from codecs import open
from setuptools import setup, find_packages


ROOT_DIR = os.path.abspath(os.path.dirname(__file__))


with open(os.path.join(ROOT_DIR, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()


def read_requirements(filename):
    def is_pkg(line):
        return line and not line.startswith(('--', 'git', '#'))

    with open(os.path.join(ROOT_DIR, filename), encoding='utf-8') as f:
        return [line for line in f.read().splitlines() if is_pkg(line)]


setup(
    name='Flask SQLAlchemy Bundle',
    version='0.1.0',
    description='Adds SQLAlchemy and Alembic to Flask Unchained',
    long_description=long_description,
    url='https://github.com/briancappello/flask-sqlalchemy-bundle',
    author='Brian Cappello',
    license='MIT',

    # https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
    ],
    packages=find_packages(),
    install_requires=read_requirements('requirements.txt'),
    python_requires='>=3.6',
    include_package_data=True,
    zip_safe=False,
)

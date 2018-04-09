from setuptools import setup, find_packages


with open('README.md', encoding='utf-8') as f:
    long_description = f.read()


setup(
    name='Flask SQLAlchemy Bundle',
    version='0.2.1',
    description='Adds SQLAlchemy and Alembic to Flask Unchained',
    long_description=long_description,
    url='https://github.com/briancappello/flask-sqlalchemy-bundle',
    author='Brian Cappello',
    license='MIT',

    # https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Framework :: Flask',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
    ],
    packages=find_packages(exclude=['docs', 'tests']),
    include_package_data=True,
    zip_safe=False,
    python_requires='>=3.6',
    install_requires=[
        'flask-migrate>=2.1.1',
        'flask-unchained>=0.2.0',
        'flask-sqlalchemy>=2.3',
        'py-yaml-fixtures>=0.1.1',
    ],
    extras_require={
        'dev': [
            'coverage',
            'factory_boy',
            'pytest',
            'pytest-flask',
            'psycopg2',
            'tox',
        ],
    },
    entry_points={
        'pytest11': [
            'flask_sqlalchemy_bundle = flask_sqlalchemy_bundle.pytest',
        ],
    },
)

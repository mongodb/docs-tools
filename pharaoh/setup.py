import pharaoh

from setuptools import setup, find_packages

REQUIRES = ['argh', 'polib', 'flask', 'gunicorn', 'pymongo',
            'pyYAML']

setup(
    name='pharaoh',
    maintainer='judahschvimer',
    maintainer_email='judah.schvimer@mongodb.com',
    description='PO File Translation Verifier',
    version=pharaoh.__version__,
    license='Apache 2.0',
    url='http://github.com/mongodb/docs-tools.git',
    packages=find_packages(),
    test_suite=None,
    install_requires=REQUIRES,
    package_data={'pharaoh': ['quickstart/*']},
    classifiers=[
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Topic :: Documentation',
        'Topic :: Software Development :: Testing',
        'Topic :: Translation',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'License :: OSI Approved :: Apache Software License',
    ],
    entry_points={
        'console_scripts': [
            'pharaoh = pharaoh.cmdline:main',
        ],
        },
    )

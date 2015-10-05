import giza

from setuptools import setup, find_packages

REQUIRES = [
    'argh',
    'docutils',
    'hieroglyph',
    'jinja2',
    'libgiza>=0.2.1',
    'onetimepass',
    'polib',
    'pyyaml',
    'rstcloth>=0.2.5',
    'sphinx-intl',
    'sphinx==1.2.3',
    'sphinxcontrib-httpdomain',
    'wand',
    'boto'
]

setup(
    name='giza',
    maintainer='tychoish',
    maintainer_email='sam@tychoish.com',
    description='Sphinx Documentation Build Automation',
    version=giza.__version__,
    license='Apache 2.0',
    url='http://github.com/mongodb/docs-tools.git',
    packages=find_packages(),
    test_suite=None,
    install_requires=REQUIRES,
    package_data={'giza': ['quickstart/makefile', "quickstart/source/*", "quickstart/source/.gitignore", 'quickstart/config/*.yaml']},
    extras_require={
        'jira': ['jira', 'pyOpenSSL', 'ndg-httpsclient', 'pyasn1', 'requests>=2.1.0'],
        'github': ['github3.py']
    },
    classifiers=[
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Topic :: Documentation',
        'Topic :: Software Development :: Testing',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'License :: OSI Approved :: Apache Software License',
    ],
    entry_points={
        'console_scripts': [
            'giza = giza.cmdline:main',
            'scrumpy = giza.scrumpy:main [jira]',
            'mdbpr = giza.github:main [github]'
           ],
        },
    )

from setuptools import setup
setup(
    name='scholarly-cli',
    version='0.0.1',
    entry_points={
        'console_scripts': [
            'scholarly-cli=scholarly_cli:main'
        ]
    }
)
from setuptools import setup

setup(
    name='matrix-is-tester',
    version='0.1',
    packages=['matrix-is-tester'],
    description="Black-box integration testing for Matrix Identity Servers",
    long_description=open('README.md').read(),
    install_requires=[
        "Twisted>=19.2.1",
    ],
    extras_require={
        'test': [
            "flake8>=3.7.8",
            "isort==4.3.21",
        ],
    },
)

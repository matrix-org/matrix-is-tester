from distutils.core import setup

setup(
    name='syditest',
    version='0.1',
    packages=['syditest'],
    description="Black-box integration testing for Matrix Identity Servers",
    long_description=open('README.md').read(),
    install_requires=[
        "Twisted>=19.2.1",
        "requests==2.22.0"
    ],
)

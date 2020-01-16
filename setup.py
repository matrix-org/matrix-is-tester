from setuptools import setup

setup(
    name="matrix_is_tester",
    version="0.1",
    packages=["matrix_is_tester"],
    description="Black-box integration testing for Matrix Identity Servers",
    long_description=open("README.md").read(),
    install_requires=["Twisted>=19.2.1", "requests>=2.22.0", "six>=1.13.0"],
    extras_require={"lint": ["flake8>=3.7.8", "isort>=4.3.21", "black>=19.3b0"]},
    include_package_data=True,
)

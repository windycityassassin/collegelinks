from setuptools import setup, find_packages

setup(
    name="collegelinks",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'flask',
        'pandas',
        'geopy',
        'pydantic'
    ],
)

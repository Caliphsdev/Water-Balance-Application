"""Minimal setup.py for development testing.

Allows installing package in editable mode: pip install -e .
"""

from setuptools import setup, find_packages

setup(
    name="water-balance-app",
    version="1.0.0",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=[
        # Core dependencies from requirements.txt
        "pandas",
        "openpyxl",
        "matplotlib",
        "Pillow",
        "PyYAML",
        "cryptography",
        "google-auth",
        "google-auth-oauthlib",
        "google-auth-httplib2",
        "google-api-python-client",
        "pytest",
        "pytest-mock",
    ],
)

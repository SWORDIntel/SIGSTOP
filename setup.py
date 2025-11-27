"""Setup configuration for sig-prune-contact."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="sig-prune-contact",
    version="0.1.0",
    author="SWORD Intelligence",
    description="Interactive Signal contact pruning and export tool",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "click==8.1.7",
        "rich==13.7.0",
        "fuzzywuzzy==0.18.0",
        "python-Levenshtein==0.21.1",
        "pydantic==2.5.0",
        "python-dateutil==2.8.2",
    ],
    entry_points={
        "console_scripts": [
            "sig-prune-contact=sig_prune_contact.main:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)

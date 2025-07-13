from setuptools import setup, find_packages

setup(
    name="verify-research-system",
    version="0.2.0",
    description="VERIFY-powered Academic Research System with PRISMA Assistant for systematic literature reviews",
    author="Melvin Breton",
    author_email="126022745+huluobohua@users.noreply.github.com",
    packages=find_packages(include=[
        "knowledge_storm*",
        "prisma_assistant*",
    ]),
    install_requires=[
        "click>=8.0.0",
        "tqdm>=4.60.0",
        "asyncio",
        "dataclasses-json>=0.6.0",
        "pydantic>=2.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "pytest-asyncio>=0.21.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "prisma-assistant=prisma_assistant.cli.main:cli",
        ],
    },
    python_requires=">=3.10",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    keywords="research verification fact-checking academic prisma systematic-review",
)

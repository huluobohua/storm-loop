from setuptools import setup, find_packages

setup(
    name="storm-loop",
    version="0.1.0",
    description="VERIFY-powered Academic Research System with PRISMA Assistant",
    author="Melvin Breton",
    author_email="126022745+huluobohua@users.noreply.github.com",
    packages=find_packages(include=[
        "knowledge_storm*",
        "prisma_assistant*",
    ]),
    install_requires=[
        "click>=8.0.0",
        "tqdm>=4.60.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "prisma-assistant=prisma_assistant.cli.main:cli",
        ],
    },
    python_requires=">=3.10",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)

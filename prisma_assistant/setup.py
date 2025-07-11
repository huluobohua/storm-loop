from setuptools import setup, find_packages

setup(
    name="prisma-assistant",
    version="0.1.0",
    packages=find_packages(),
    install_requires=["click", "tqdm"],
    entry_points={
        "console_scripts": ["prisma-assistant=prisma_assistant.cli:cli"],
    },
)

from setuptools import setup, find_packages

setup(
    name="sobs",
    version="0.0.1",
    packages=find_packages(),
    include_package_data=True,
    install_requires=["peewee", "click"],
    entry_points="""
        [console_scripts]
        sobs=sobs.cli:cli
    """,
)

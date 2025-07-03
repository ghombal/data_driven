from setuptools import setup, find_packages

setup(
    name="data_driven",
    version="0.1.0",
    description="Data ingestion system for market, fundamental, and alternative data",
    author="Gopi Hombal",
    author_email="gopi.hombal@email.com",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "ib-insync",
        "asyncpg",
        "sqlalchemy>=2.0",
        "pydantic>=2.0",
        "aiohttp",
    ],
    python_requires=">=3.10",
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
)

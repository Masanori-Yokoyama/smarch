from setuptools import setup, find_packages

setup(
    name="smarch",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "boto3>=1.34.0",
        "pysmb>=1.2.9",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.3",
            "pytest-cov>=4.1.0",
            "black>=23.12.0",
            "isort>=5.13.2",
            "flake8>=6.1.0",
        ],
    },
    python_requires=">=3.12",
    author="Masanori-Yokoyama",
    author_email="your.email@example.com",
    description="AWS Lambda based SMB file archiver to S3",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/Masanori-Yokoyama/smarch",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.12",
    ],
)
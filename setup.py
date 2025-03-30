from setuptools import setup, find_packages

setup(
    name="concall-parser",
    version="0.1.0",
    description="",
    author="Jay Shah",
    author_email="jayshah0726@gmail.com",
    packages=find_packages(include=["parser", "parser.*"]),
    install_requires=[
        "groq==0.15.0",
        "pdfplumber==0.11.5",
    ],
    extras_require={
        "dev": [
            "ruff==0.4.1",
            "pre-commit==3.7.0",
        ]
    },
    python_requires=">=3.10",
)

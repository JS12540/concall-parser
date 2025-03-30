from setuptools import setup, find_packages

setup(
    name="concall-parser",
    version="0.0.1",
    description="",
    author="Jay Shah, Pranshu Raj",
    author_email="jayshah0726@gmail.com, pranshuraj65536@gmail.com",
    description="A short description of your package",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/JS12540/concall-parser",
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
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
)
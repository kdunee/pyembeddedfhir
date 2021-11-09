"""The setup script."""

from setuptools import setup, find_packages

with open("README.rst") as readme_file:
    readme = readme_file.read()

with open("HISTORY.rst") as history_file:
    history = history_file.read()

requirements = [
    'dataclasses>=0.6;python_version<"3.7"',
    "docker>=5.0.3",
    "psutil>=5.8.0",
]

test_requirements = [
    "pytest>=3",
]

setup(
    author="Kosma Dunikowski",
    author_email="kosmadunikowski@gmail.com",
    python_requires=">=3.6",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    description="A simple way to use a 🔥 FHIR server in 🐍 Python integration tests.",
    install_requires=requirements,
    license="MIT license",
    long_description=readme + "\n\n" + history,
    include_package_data=True,
    keywords="pyembeddedfhir",
    name="pyembeddedfhir",
    packages=find_packages(
        include=["pyembeddedfhir", "pyembeddedfhir.*"]
    ),
    test_suite="tests",
    tests_require=test_requirements,
    url="https://github.com/kdunee/pyembeddedfhir",
    version="1.1.3",
    zip_safe=False,
)

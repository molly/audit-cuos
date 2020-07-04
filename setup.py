import setuptools

with open("README.md", "r") as f:
    long_description = f.read()

setuptools.setup(
    name="audit-cuos",
    version="0.2.post2",
    packages=setuptools.find_packages(),
    url="https://github.com/molly/audit-cuos",
    license="MIT",
    author="Molly White",
    author_email="molly.white5@gmail.com",
    description="Generate activity reports for functionaries on the English Wikipedia.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=["requests>=2.2.1", "python-dateutil>=2.4.2"],
    python_requires=">=3.6",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
)

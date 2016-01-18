from setuptools import setup, find_packages

setup(
    name='audit-cuos',
    version='0.1',
    packages=find_packages(),
    url='https://github.com/molly/audit-cuos',
    license='MIT',
    author='molly',
    author_email='molly.white5@gmail.com',
    description='Generate activity reports for functionaries on the English Wikipedia.',
    install_requires=["requests>=2.2.1"]
)

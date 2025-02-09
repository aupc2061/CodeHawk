from setuptools import setup, find_packages

setup(
    name="code-agent",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "networkx>=2.5",
        "tree-sitter>=0.20.0",
        "pygments>=2.10.0",
        "tqdm>=4.62.0",
        "typing-extensions>=4.0.0",
    ],
    author="CodeHawk",
    description="A tool for analyzing and mapping code repositories",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    python_requires=">=3.8",
)
import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name = "NKTBasik",
    version = '0.1',
    author = 'o.grasdijk',
    author_email = 'o.grasdijk@gmail.com',
    description = 'Python interface for the NKT Photonics Basik fiber seed laser',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url = '',
    data_files = [('NKTBasik/dll', ['NKTBasik/dll/NKTPDLL.dll'])],
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: Windows",
    ],
    python_requires='>=3.6',
)
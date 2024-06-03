import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="imap_box",
    version="0.1.9",
    author="daohu527",
    author_email="daohu527@gmail.com",
    description="High-resolution map visualization and conversion tool",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/daohu527/imap",
    project_urls={
        "Bug Tracker": "https://github.com/daohu527/imap/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "."},
    packages=setuptools.find_packages(where="."),
    install_requires=[
        'protobuf<=3.19.4',
        'matplotlib',
        'pyproj',
        'record_msg<=0.1.1',
    ],
    entry_points={
        'console_scripts': [
            'imap = imap.main:main',
        ],
    },
    python_requires=">=3.6",
)

from setuptools import setup

setup(
    name="cryoCAT",
    version="0.2.0",
    description="Contextual Analysis Tools for CryoET",
    url="https://github.com/turonova/cryoCAT",
    author="Beata Turonova",
    author_email="beata.turonova@gmail.com",
    license="GPLv3+",
    packages=["cryocat"],
    install_requires=[
        "scipy",
        "numpy",
        "pandas",
        "scikit-image",
        "emfile",
        "mrcfile",
        "matplotlib",
        "seaborn",
        "scikit-learn",
        "lmfit",
        "h5py",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: OS Independent",
    ],
    entry_points={"console_scripts": ["wedge_list = cryocat.cli:wedge_list", "tm_ana = cryocat.cli:tm_ana"]},
)

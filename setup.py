from setuptools import find_packages, setup

setup(
    name="virtkvm",
    version="0.0.0",
    description="The poor man's KVM switch for libvirt and VFIO users",
    author="Alexander Bakker",
    author_email="ab@alexbakker.me",
    url="https://github.com/alexbakker/virtkvm",
    packages=find_packages(),
    install_requires=[
        "flask",
        "libvirt-python"
        "pyyaml"
        "xmltodict"
    ],
    entry_points={
        "console_scripts": [
            "virtkvm=virtkvm:main",
        ],
    },
    license="GPLv3"
)

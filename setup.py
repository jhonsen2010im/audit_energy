from setuptools import setup, find_packages

setup(
    name="audit-leads",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "click>=8.1",
        "requests>=2.31",
        "beautifulsoup4>=4.12",
        "lxml>=5.1",
    ],
    entry_points={
        "console_scripts": [
            "audit-leads=audit_leads.cli:cli",
        ],
    },
)

"""
maim_db 安装配置
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="maim_db",
    version="1.0.0",
    author="MaiM Team",
    author_email="team@maim.ai",
    description="maim_db - MaiM 多租户数据平面与数据库模型库",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/maim-project/maim_db",
    package_dir={"": "src"},
    packages=["maim_db", "maim_db.core", "maim_db.maimconfig_models"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Framework :: Django :: 4.0",
        "Framework :: Flask",
        "Topic :: Database",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=[
        "peewee>=3.16.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "ruff>=0.1.0",
            "mypy>=1.0.0",
        ],
        "postgres": [
            "psycopg2-binary>=2.9.0",
        ],
        "mysql": [
            "PyMySQL>=1.0.0",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)

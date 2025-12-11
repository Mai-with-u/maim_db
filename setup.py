"""
AI Project Core 安装配置
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="ai-project-core",
    version="1.0.0",
    author="AI Project Team",
    author_email="team@ai-project.com",
    description="统一数据库核心库 - 支持多租户SaaS架构的数据模型和数据库管理",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ai-project/ai-project-core",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
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

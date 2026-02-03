from setuptools import setup, find_packages

setup(
    name="dis-kubernetes",
    version="0.1.0",
    description="Digital Immune System for Kubernetes",
    author="DIS Team",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "kubernetes>=28.0.0",
        "prometheus-client>=0.19.0",
        "numpy>=1.24.0,<2.0.0",
        "scikit-learn>=1.3.0",
        "tensorflow>=2.15.0,<2.16.0",
        "pandas>=2.0.0",
        "psutil>=5.9.0",
        "pyyaml>=6.0",
    ],
    python_requires=">=3.8",
    entry_points={
        'console_scripts': [
            'dis-agent=dis_k8s.main:main',
        ],
    },
)

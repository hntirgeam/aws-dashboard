from setuptools import setup, find_packages


VERSION = "1.0.0"
DESCRIPTION = "Small EC2 and RDS monitor and control tool"


setup(
    name="aws-dashboard",
    version=VERSION,
    author="hntirgeam",
    author_email="",
    description=DESCRIPTION,
    packages=find_packages(),
    install_requires=["boto3", "click", "colorama", "python-dateutil", "tabulate"],
    keywords=["aws", "monitor", "data", "control panel", "control", "panel"],
    classifiers=[
        "Development Status :: WIP",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Operating System :: Unix",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
    ],
    entry_points = {
        'console_scripts': ['aws-dashboard=aws_dashboard.aws:main'],
    }
)

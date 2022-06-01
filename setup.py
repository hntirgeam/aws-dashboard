from setuptools import setup, find_packages


VERSION = "0.0.5"
DESCRIPTION = "Small EC2 and RDS monitor and control tool "


setup(
    name="aws-monitor",
    version=VERSION,
    author="hntirgeam",
    author_email="",
    description=DESCRIPTION,
    packages=find_packages(),
    install_requires=["boto3", "click", "colorama", "python-dateutil", "tabulate"],
    keywords=["aws", "monitor", "data"],
    classifiers=[
        "Development Status :: 1 - Planning",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Operating System :: Unix",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
    ],
    entry_points = {
        'console_scripts': ['aws-monitor=aws_monitor.aws:main'],
    }
)

from setuptools import setup, find_packages

setup(
    name='network-monitor',
    version='0.1.0',
    author='Your Name',
    author_email='your.email@example.com',
    description='A network monitoring system using SNMP',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    install_requires=[
        'pysnmp',
        'influxdb',
        'pyyaml',
        'requests',
    ],
    entry_points={
        'console_scripts': [
            'network-monitor=main:main',
        ],
    },
)
from setuptools import setup, find_packages

with open('requirements.txt') as f:
    install_requires = f.read().splitlines()

setup(
    name='deadshot',
    version='1.0.0',
    author='Carlos Flores',
    author_email='carlos.flores@potros.itson.edu.mx',
    description='NA',
    packages=find_packages(),
    python_requires='>=3.6',
    install_requires=install_requires,
    entry_points={
        'console_scripts': [
            'deadshot = app.bin.app:main'
        ],
    },
)

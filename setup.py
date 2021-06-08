import setuptools

setuptools.setup(
    name='deadshot',
    version='1.0.0',
    author='Carlos Flores',
    author_email='',
    description='',
    packages=setuptools.find_packages(),
    python_requires='>=3.6',
    install_requires=[],
    entry_points={
            'console_scripts': [
                'deadshot = app.bin.app:main'
            ],
        },
)

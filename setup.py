import setuptools

setuptools.setup(
    name='deadshot',
    version='0.0.1',
    author='',
    author_email='',
    description='',
    packages=setuptools.find_packages(),
    python_requires='>=3.6',
    install_requires=[],
    entry_points={
            'console_scripts': [
                'app = app.bin.app:main'
            ],
        },
)
from setuptools import setup

setup(
    name='uclcoin',
    version='0.0.9',
    description='UCLCoin: A naive blockchain/cryptocurrency implementation',
    long_description=open('README.rst', 'r').read(),
    author='Renato Orgito',
    author_email='orgito@gmail.com',
    maintainer='Renato Orgito',
    maintainer_email='orgito@gmail.com',
    url='https://github.com/orgito/uclcoin',
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Education',
        'Intended Audience :: Science/Research',
        'Topic :: Education',
        'Topic :: Security :: Cryptography',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.6',
    ],
    keywords='uclcoin blockchain cryptocurrency',
    packages=['uclcoin'],
    install_requires=['coincurve'],
    python_requires='>=3.6',
    project_urls={
        'Bug Reports': 'https://github.com/orgito/uclcoin/issues',
        'Source': 'https://github.com/orgito/uclcoin',
    },
)

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name='bci-ble-encryption',
    version='1.0.0',
    author='Dr. Saheed Yusuf',
    author_email='saheed@32bjbenefits.org',
    description='BCI-BLE Encryption Security Research - Doctoral Praxis',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/dryusufsaheed/BCI-BLE-Encryption',
    packages=find_packages(),
    python_requires='>=3.7',
    install_requires=[
        'numpy>=1.21.0',
        'pandas>=1.3.0',
        'scipy>=1.7.0',
        'matplotlib>=3.4.0',
        'seaborn>=0.11.0',
        'mne>=0.23.0',
        'h5py>=3.0.0',
        'pyedflib>=0.1.0',
        'pycryptodome>=3.13.0',
        'scikit-posthocs>=0.10.0',
        'statsmodels>=0.12.0',
        'pingouin>=0.5.1',
        'tabulate>=0.8.9',
        'openpyxl>=3.6.0',
    ],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering :: Medical Science Apps.',
        'Topic :: Security :: Cryptography',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Operating System :: OS Independent',
    ],
    keywords='bci brain-computer-interface encryption security ble bluetooth-low-energy eeg',
    project_urls={
        'Bug Reports': 'https://github.com/dryusufsaheed/BCI-BLE-Encryption/issues',
        'Source': 'https://github.com/dryusufsaheed/BCI-BLE-Encryption',
        'Documentation': 'https://github.com/dryusufsaheed/BCI-BLE-Encryption/tree/main/documentation',
    },
)

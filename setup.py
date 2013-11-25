from distutils.core import setup

setup(
    name='pyaddress',
    version='0.1.2',
    url='https://github.com/pcsforeducation/pyaddress',
    author='Josh Gachnang, Rob Jauquet',
    author_email='Josh@ServerCobra.com',
    description='pyaddress is an address parsing library, taking the guesswork out of using addresses in your '
                'applications.',
    long_description=open('README.rst', 'rt').read(),
    #data_files=[('', ['README.rst','pyaddress/cities.csv', 'pyaddress/suffixes.csv', 'pyaddress/streets.csv', 'pyaddress/tests.py', 'pyaddress/test_list.py'])],
    packages=['address'],
    package_dir={'address': 'address'},
    package_data={'address': ['cities.csv', 'streets.csv', 'suffixes.csv']},
    classifiers=[
        "License :: OSI Approved :: BSD License",
        "Natural Language :: English",
        "Programming Language :: Python :: 2 :: Only",
        "Topic :: Software Development :: Libraries",
        "Topic :: Text Processing",
    ],
    keywords = "example documentation tutorial",
    maintainer="Josh Gachnang, Rob Jauquet",
    maintainer_email="Josh@ServerCobra.com",
)

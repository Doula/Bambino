import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.txt')).read()

requires = [
    'APScheduler',
    'pyramid',
    'pyramid_debugtoolbar',
    'waitress',
    'path.py',
    'gitpython>=0.3.2.RC1',
    'requests',
    'fabric'
    ]

setup(name='Bambino',
      version='0.0',
      description='Bambino',
      long_description=README,
      classifiers=[
        "Programming Language :: Python",
        "Framework :: Pylons",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        ],
      author='',
      author_email='',
      url='',
      keywords='web pyramid pylons',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires=requires,
      tests_require=requires,
      setup_requires=[
        'egggitinfo'
      ],
      test_suite="bambino",
      entry_points = """\
      [paste.app_factory]
      main = bambino:main
      """,
      )


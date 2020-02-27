from setuptools import setup, find_packages

INSTALL_REQUIRES = [
  'wheel',
  'six',
]

TESTS_REQUIRES = [
  'absl-py',
  "mock; python_version<'3.0'"
]

setup(name='pytruth',
      version='1.0.2',
      description='Provides unittest assertions in a fluent style.',
      long_description=open('README.md').read(),
      long_description_content_type='text/markdown',
      url='https://github.com/google/pytruth',
      project_urls={
        'Bug Reports': 'https://groups.google.com/d/forum/pytruth-users',
        'Source': 'https://github.com/google/pytruth',
      },
      author='Gregory Kwok',
      author_email='gkwok@google.com',
      packages=find_packages(),
      license='Apache 2.0',
      install_requires=INSTALL_REQUIRES,
      tests_require=TESTS_REQUIRES,
      classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Software Development :: Quality Assurance',
        'Topic :: Software Development :: Testing',
        'Topic :: Software Development :: Testing :: Mocking',
        'Topic :: Software Development :: Testing :: Unit',
      ])

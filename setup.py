from setuptools import setup, find_packages
import os

def read(*rnames):
    return open(os.path.join(os.path.dirname(__file__), *rnames)).read()


setup(name='collective.sentry',
      version='2.2.4.dev0',
      description="Replace default Plone error_log to send data to GetSentry service",
      long_description=read('README.txt') + '\n',
      classifiers=[
        'Framework :: Plone',
        'Framework :: Plone :: 5.2',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: Implementation :: CPython',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Development Status :: 5 - Production/Stable',
      ],
      keywords='enfold getsentry error_log plone',
      author='Enfold Systems, Inc.',
      author_email='info@enfoldsystems.com',
      url='http://www.enfoldsystems.com',
      license='GPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['collective', ],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          # -*- Extra requirements: -*-
          'sentry-sdk==1.33.1',
          'six',
          'plone.api',
      ],
      extras_require={
          "test": [
              'cssselect',
              'lxml',
              'mock',
              'plone.api >=1.8.5',
              'plone.app.robotframework',
              'plone.app.testing [robot]',
              ],
      },
      entry_points="""
      # -*- Entry points: -*-
      [z3c.autoinclude.plugin]
      target = plone

      [celery_tasks]
      sentryhook = collective.sentry.tasks
      """,
      )

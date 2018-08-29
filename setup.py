from setuptools import setup, find_packages
import os

def read(*rnames):
    return open(os.path.join(os.path.dirname(__file__), *rnames)).read()


setup(name='collective.sentry',
      version='2.0.0',
      description="Replace default Plone error_log to send data to GetSentry service",
      long_description=read('README.txt') + '\n',
      classifiers=[
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python",
        "Framework :: Plone",
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
          'raven>=6.8.0',
      ],
      extras_require={
          "test": [
              "Plone",
              "plone.app.testing",
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

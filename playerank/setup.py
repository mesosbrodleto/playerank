from distutils.core import setup

setup(
    name='playerank',
    version='1.0',
    packages=['playerank',],
    install_requires=[
          'pandas==0.23.4',
          'scipy==0.17.1',
          'numpy==1.11.0',
          'scikit_learn==0.21.3',
      ],
    license='Creative Commons Attribution-Noncommercial-Share Alike license',
    long_description=open('README.md').read(),
)

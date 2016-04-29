from setuptools import setup
import image2ipfs.defaults

setup(name='image2ipfs',
      version=image2ipfs.defaults.VERSION,
      description='Publish your docker image archives to IPFS',
      url='https://github.com/jvassev/image2ipfs',
      author='Julian Vassev',
      author_email='jvassev@gmail.com',
      packages=['image2ipfs'],
      license="ASL 2",
      install_requires=[
            'base58'
      ],
      entry_points={
          'console_scripts': ['image2ipfs=image2ipfs.main:main'],
      },
      include_package_data=True,
      zip_safe=False)

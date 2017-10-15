
from setuptools import setup

setup(
    name='GUM_Dispenser',
    version='0.1',
    description='Testing path functions',
    author='Jordan Fike',
    author_email='jofike@socialsolutions.com', 
    packages=['GUM_Dispenser'],
    entry_points={
        'console_scripts': [
            'GUM_Dispenser = GUM_Dispenser.GUM_Dispenser_Main:main'
        ]
    }
)
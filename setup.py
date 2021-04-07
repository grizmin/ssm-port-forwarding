from setuptools import setup, find_packages

setup(
    name='ssm-port-forwarding',
    version='0.0.1',
    packages=find_packages(),
    url='https://gitlab.bit9.local/kkonstantin/ssm-port-forwarding',
    license='MIT',
    author='Konstantin Krastev',
    author_email='kkonstantin@vmware.com',
    description='session manager remote port forwarding utility',
    include_package_data=True,
    install_requires=[
        'Click',
        'pexpect',
        'boto3',
        'packaging',
        'awscli'
    ],
    tests_require=[
        'pytest',
        'coverage',
        'tox'
    ],
    entry_points='''
        [console_scripts]
        ssmpfwd=ssmpfwd.cli.cli:cli
    ''',

)

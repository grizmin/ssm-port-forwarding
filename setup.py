from setuptools import setup, find_packages

setup(
    name="ssm-port-forwarding",
    version="0.0.4",
    packages=find_packages(),
    url="https://github.com/grizmin/ssm-port-forwarding",
    license="MIT",
    author="Konstantin Krastev",
    author_email="grizmin@grizmin.org",
    description="session manager remote port forwarding utility",
    include_package_data=True,
    install_requires=["Click", "pexpect", "boto3", "packaging", "awscli"],
    tests_require=["pytest", "coverage", "tox"],
    entry_points="""
        [console_scripts]
        ssmpfwd=ssmpfwd.cli.cli:cli
    """,
)

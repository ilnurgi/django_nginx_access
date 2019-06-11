"""
инсталятор
"""

import setuptools

with open('README.md', 'r') as fh:
    long_description = fh.read()

setuptools.setup(
    name='django_nginx_access',
    version='0.0.21',
    author='Ильнур Гайфутдинов',
    author_email='ilnurgi87@gmail.com',
    description='Парсер nginx логов',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/ilnurgi/django_nginx_access/',
    packages=setuptools.find_packages(),
)

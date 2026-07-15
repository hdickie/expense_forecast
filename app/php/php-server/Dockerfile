# Use an official PHP Apache runtime
FROM php:8.2-apache

SHELL ["/bin/bash", "-c"]

# Enable Apache modules
RUN a2enmod rewrite


RUN apt-get update
RUN apt-get install -y libpq-dev python3 virtualenv pip \
    && docker-php-ext-configure pgsql -with-pgsql=/usr/local/pgsql \
    && docker-php-ext-install pgsql pdo pdo_pgsql

# Set the working directory to /var/www/html
WORKDIR /var/www/html

EXPOSE 80

# CMD ["source","./venv/bin/activate"]
# ENV PATH="/var/www/html/venv/bin:$PATH"

RUN virtualenv /ve
ENV PATH="/ve/bin:$PATH"
COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

# The PHP app and Python package are mounted by compose.yaml for local development.


# Start Apache when the container runs
CMD ["apache2-foreground"]

FROM httpd:2.4

# Overwrite the httpd.conf with your custom one
COPY apache-config/httpd.conf /usr/local/apache2/conf/httpd.conf

# Copy your virtual host
COPY apache-config/my-site.conf /usr/local/apache2/conf.d/my-site.conf

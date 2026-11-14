FROM httpd:2.4.65-alpine

LABEL maintainer="s.martinez6@sapalomera.cat"
LABEL description="Practiques Docker"
LABEL version="1.0"

WORKDIR /usr/local/apache2/htdocs

COPY ./static-site/ /usr/local/apache2/htdocs/

EXPOSE 80
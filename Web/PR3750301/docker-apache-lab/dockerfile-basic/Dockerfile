# Utilitzem Apache 2.4.65 com a imatge base (Alpine és una versió lightweight)
FROM httpd:2.4.65-alpine

# Informació sobre qui manté aquesta imatge
LABEL maintainer="s.martinez6@sapalomera.cat"
LABEL description="Apache HTTP Server personalitzat per a pràctiques ASIX"
LABEL version="1.0"

# Copia el contingut web personalitzat
COPY ./web-content/ /usr/local/apache2/htdocs/

# Exposa el port 80 (documentació, no fa res funcionalment)
EXPOSE 80

# La imatge base ja té definit el CMD per iniciar Apache
# CMD ["httpd-foreground"]
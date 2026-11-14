# Docker i Apache HTTP Server

**Shaila Martínez - 2n ASIX**

**Nº 63 - Serveis**

## Estructura

```text
docker-apache-lab/
├── html/                    # Part 1: bind mount
├── dockerfile-basic/        # Part 2: primer Dockerfile
├── dockerfile-multistage/   # Part 2: multi-stage build
├── dockerfile-repte2/       # Repte 2: static-site/
├── apache-config/           # Part 3 i Repte 3
├── apache-vhosts/           # Part 4: Virtual Hosts
├── apache-ssl/              # Part 4: HTTPS, rewrite, logging i Repte 4
└── docker-compose-stack/    # Part 5 i Repte 5 (docker-compose.yml, .env, apache/, logs/)
```

## Contenidors i ports

| Part | Contenidor | Imatge | Port(s) |
| --- | --- | --- | --- |
| 1 | `apache-custom-shailamartinez` | `httpd:2.4.65` | 8080 |
| 2 | `apache-dockerfile` | `apache-custom:v1.0` | 8081 |
| 2 | `apache-multistage` | `apache-multistage:v1.0` | 8082 |
| Repte 2 | `apache-exercise-shailamartinez` | `apache-exercise-shailamartinez:v1.0` | 8083 |
| 3 i Repte 3 | `apache-configured` | `apache-configured:v1.2` | 8084 |
| 4 | `apache-vhosts` | `apache-vhosts:v1.0` | 8085 |
| 4 i Repte 4 | `apache-ssl` | `apache-ssl:v1.3` | 8086 (HTTP), 8443 (HTTPS) |
| 5 | `lamp-apache` | `docker-compose-stack-apache` | 8090 |
| 5 | `lamp-phpmyadmin` | `phpmyadmin:5.2-apache` | 8091 |
| 5 | `lamp-mysql` | `mysql:8.0.35` | 3306 |
| Repte 5 | `lamp-redis` | `redis:7-alpine` | 6379 |

## Part 0: Verificació de l'entorn

```powershell
docker --version
docker ps
docker compose version
```
Docker 29.8.1 i Compose v5.5.1; `docker ps` retorna una taula buida.

## Part 1: Fonaments de Docker

```powershell
docker pull httpd:2.4.65
docker images
docker run -d -p 8080:80 --name primer-apache-shailamartinez httpd:2.4.65
```
A `http://localhost:8080` surt "It works!".

```powershell
docker ps
docker ps -a
docker stop primer-apache-shailamartinez
docker start primer-apache-shailamartinez
docker restart primer-apache-shailamartinez
docker logs primer-apache-shailamartinez
docker logs -f primer-apache-shailamartinez
docker exec primer-apache-shailamartinez ls /usr/local/apache2/htdocs
docker exec -it primer-apache-shailamartinez /bin/bash
```


```powershell
docker stop primer-apache-shailamartinez
docker rm primer-apache-shailamartinez
mkdir docker-apache-lab\html
docker run -d -p 8080:80 --name apache-custom-shailamartinez -v "${PWD}\html:/usr/local/apache2/htdocs" httpd:2.4.65
```
Bind mount: els canvis a `html` es veuen a l'instant

```powershell
docker inspect apache-custom-shailamartinez
docker stats apache-custom-shailamartinez
docker top apache-custom-shailamartinez
```
**Repte 1.** `html\about.html` accessible a `http://localhost:8080/about.html` sense reiniciar.

## Part 2: Dockerfile

```powershell
cd dockerfile-basic
docker build -t apache-custom:v1.0 .
docker images
docker run -d -p 8081:80 --name apache-dockerfile apache-custom:v1.0
```
Imatge basada en `httpd:2.4.65-alpine` (93,2 MB millor que els 177 MB de `httpd:2.4.65`).

```powershell
cd ..\dockerfile-multistage
docker build -t apache-multistage:v1.0 .
docker run -d -p 8082:80 --name apache-multistage apache-multistage:v1.0
docker images | Select-String "apache"
```
Les dues imatges ocupen igual (93,2 MB): Node.js només s'usa a l'etapa de construcció.

**Best practices.** Imatge oficial amb versió fixa, `.dockerignore`, `LABEL`, poques capes i `COPY` al final. No afegeixo `USER`: Apache ja executa els processos amb `daemon`.

```powershell
cd ..\dockerfile-repte2
docker build -t apache-exercise-shailamartinez:v1.0 .
docker run -d -p 8083:80 --name apache-exercise-shailamartinez apache-exercise-shailamartinez:v1.0
```
**Repte 2.** `static-site` amb `index.html`, `services.html` i `contact.html`, a `http://localhost:8083`.

## Part 3: Apache, configuració bàsica

```powershell
docker exec apache-custom-shailamartinez httpd -M
```
`rewrite_module` i `ssl_module` no estan carregats per defecte: s'afegeixen amb `LoadModule`.

```powershell
cd ..\apache-config
docker build -t apache-configured:v1.0 .
docker run -d -p 8084:80 --name apache-configured -v "${PWD}/logs:/usr/local/apache2/logs" apache-configured:v1.0
cat logs/access.log
cat logs/error.log
```
`httpd-custom.conf` carrega els mòduls (`mpm_event` és obligatori), defineix `Options`, `AllowOverride All`, un `LogFormat` amb temps de resposta i capçaleres de seguretat. El volum `-v` deixa llegir els logs des de l'amfitrió.

```powershell
docker stop apache-configured
docker rm apache-configured
docker build -t apache-configured:v1.1 .
docker run -d -p 8084:80 --name apache-configured -v "${PWD}/logs:/usr/local/apache2/logs" apache-configured:v1.1
```
**Repte 3.** Versió `v1.2` amb `RewriteRule ^old-page$ /new-page.html [L]` i `Header always set X-Lab-Version "1.0"`.

```powershell
curl.exe -I http://localhost:8084/old-page
```
`/old-page` serveix `new-page.html` (reescriptura interna) i la resposta porta `X-Lab-Version: 1.0`.

## Part 4: Configuració avançada d'Apache

### Virtual Hosts

```powershell
cd ..\apache-vhosts
docker build -t apache-vhosts:v1.0 .
docker run -d -p 8085:80 --name apache-vhosts -v "${PWD}/logs:/usr/local/apache2/logs" apache-vhosts:v1.0
```
Fitxer `hosts`:
```text
127.0.0.1 site1.local
127.0.0.1 site2.local
```
`http://site1.local:8085` i `http://site2.local:8085` serveixen llocs diferents, amb logs separats.

### HTTPS amb SSL/TLS

```powershell
cd ..\apache-ssl
docker build -t apache-ssl:v1.0 .
docker run -d -p 8086:80 -p 8443:443 --name apache-ssl -v "${PWD}/logs:/usr/local/apache2/logs" apache-ssl:v1.0
curl.exe -I http://localhost:8086/
docker exec apache-ssl openssl x509 -in /usr/local/apache2/certs/server.crt -text -noout
```
Certificat autosignat generat al Dockerfile. El 8086 (HTTP) redirigeix amb un 301 al 8443 (HTTPS), amb HSTS i capçaleres de seguretat.

### mod_rewrite avançat

`.htaccess` amb set regles (`www` → sense `www`, URLs amigables, sense `.php`, redirecció d'URLs antigues, HTTPS a `/admin` i `/login`, bloqueig de bots i redirecció per IP). Un `User-Agent` "Googlebot" a `/api/test` retorna 403.

### Logging personalitzat

```powershell
docker exec apache-ssl httpd -t
curl.exe -k -I https://localhost:8443/prova.jpg
Get-Content .\logs\images.log -Tail 5
docker logs apache-ssl --tail 10
```
Els logs es veuen amb `docker logs`.

### Repte 4: Virtual Host `secure-site-shailamartinez.local`

```powershell
docker stop apache-ssl
docker rm apache-ssl
Remove-Item .\logs\secure-site-*.log
docker build -t apache-ssl:v1.3 .
docker run -d -p 8086:80 -p 8443:443 --name apache-ssl -v "${PWD}/logs:/usr/local/apache2/logs" apache-ssl:v1.3
docker exec apache-ssl httpd -t
curl.exe -k -I --resolve secure-site-shailamartinez.local:8443:127.0.0.1 https://secure-site-shailamartinez.local:8443/
curl.exe -k -I --resolve secure-site-shailamartinez.local:8443:127.0.0.1 https://secure-site-shailamartinez.local:8443/about
curl.exe -k -I --resolve secure-site-shailamartinez.local:8443:127.0.0.1 https://secure-site-shailamartinez.local:8443/private/secret.txt
curl.exe -I -H "Host: secure-site-shailamartinez.local" http://localhost:8086/
```
Fitxer `hosts`:
```text
127.0.0.1 secure-site-shailamartinez.local
```
- El port 80 redirigeix a HTTPS (`Redirect permanent`) i el 443 serveix `htdocs/secure-site`.
- El `.htaccess` bloqueja `/private` (403), elimina `.html` de les URLs i afegeix `X-Secure-Site: true`.
- Logs separats: `secure-site-access.log` i `secure-site-error.log`.
- Vaig treure el `.htaccess` de `htdocs`, que donava `RewriteEngine not allowed here`.

## Part 5: Docker Compose

```powershell
cd ..\docker-compose-stack
docker compose up -d
docker compose logs
docker compose logs -f apache
docker compose ps
docker compose ps --format json
docker compose exec apache bash
docker compose up -d --scale apache=3
```
Tres serveis (`apache`, `mysql`, `phpmyadmin`) a la xarxa `lamp-network`, amb `healthcheck` a MySQL i `depends_on`.

```powershell
docker compose exec apache getent hosts mysql
docker compose exec apache php -r '$c = new mysqli("mysql", "root", "rootpassword", "testdb"); echo $c->server_info, "\n";'
docker compose exec mysql mysql -uroot -prootpassword -e "SHOW DATABASES;"
```
El nom del servei es resol pel DNS intern de Docker. `http://localhost:8090` mostra la connexió a MySQL i les últimes visites, i `http://localhost:8091` phpMyAdmin.

```powershell
docker volume ls
docker volume inspect docker-compose-stack_mysql-data
docker volume prune
docker run --rm -v docker-compose-stack_mysql-data:/data -v "${PWD}:/backup" alpine tar czf /backup/mysql-backup.tar.gz -C /data .
docker compose config
```
Volum amb nom per a MySQL, còpia de seguretat a `mysql-backup.tar.gz` i `.env` (credencials, ports i `TZ`) afegit al `.gitignore`.

### Repte 5: servei Redis

```powershell
docker compose config --services
docker compose up -d --build
docker compose exec apache php -m
docker volume ls
```
Servei `redis` (`redis:7-alpine`, port 6379, volum `redis-data`, `--appendonly yes`). A l'Apache s'instal·la l'extensió amb `pecl install redis` i `index.php` mostra "Shaila Martínez - Nombre de visites" amb `$redis->incr('visites:shaila')` (12 a 13).

## Procediment d'operació

**Desplegar i aturar l'stack**

```powershell
cd docker-apache-lab\docker-compose-stack
docker compose up -d --build
docker compose ps
docker compose stop
docker compose down
docker compose down -v
```
`down -v` també elimina les dades de MySQL i Redis. Cal tenir el `.env` a la carpeta.

**URLs d'accés**

| Servei | URL |
| --- | --- |
| Apache bàsic / bind mount | http://localhost:8080 |
| Imatge pròpia (Dockerfile) | http://localhost:8081 |
| Multi-stage | http://localhost:8082 |
| Repte 2 | http://localhost:8083 |
| Configuració pròpia | http://localhost:8084 |
| Virtual Hosts | http://site1.local:8085, http://site2.local:8085 |
| HTTPS | https://localhost:8443 (http://localhost:8086 hi redirigeix) |
| Repte 4 | https://secure-site-shailamartinez.local:8443 |
| Stack LAMP + Redis | http://localhost:8090 |
| phpMyAdmin | http://localhost:8091 |

**Comprovar els logs**

```powershell
docker logs apache-ssl --tail 10
Get-Content .\logs\secure-site-access.log
Get-Content .\logs\secure-site-error.log
docker compose logs -f apache
```
`secure-site-error.log` només té avisos del certificat autosignat.

**Netejar l'entorn**

```powershell
docker stop $(docker ps -q)
docker rm $(docker ps -aq)
docker volume prune
```
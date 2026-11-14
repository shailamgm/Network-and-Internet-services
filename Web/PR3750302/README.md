# SSO amb JWT a shailamartinez.asix.cat

**Shaila Martínez - 2n ASIX**

**Nº 63 - Serveis**

Les captures de totes les parts estàn al PDF `PR03750302_ShailaMartinez.pdf`

## Estructura

```text
jwt-shailamartinez/
├── README.md
├── PR03750302_ShailaMartinez.pdf   # captures de totes les parts
├── db.shailamartinez.asix.cat      # Part 1: fitxer de zona
├── .env
├── docker-compose.yml
├── certs/        # Part 2: ca.crt, wildcard.crt, wildcard.csr, wildcard.ext
├── keys/         # Part 3: jwt_public.pem
├── auth/         # Part 3: Dockerfile, app.py, users.json
├── api/          # Part 3: Dockerfile, app.py
├── app/          # Part 3: index.html
└── nginx/        # Part 4: templates/jwt.conf.template, snippets/
```

Les claus privades (`certs/ca.key`, `certs/wildcard.key`, `keys/jwt_private.pem`) no s'inclouen a l'entrega: es generen als passos 3 i 4.

## Contenidors i ports

| Contenidor | Imatge | Ports |
| --- | --- | --- |
| `nginx-jwt` | `nginx:1.27-alpine` | 80, 443 |
| `auth-jwt` | `jwt-shailamartinez-auth` | 5000 (intern) |
| `api-jwt` | `jwt-shailamartinez-api` | 5000 (intern) |

| Nom | Funció |
| --- | --- |
| `auth.shailamartinez.asix.cat` | Login, emet el JWT (RS256) i el guarda a la cookie |
| `api.shailamartinez.asix.cat` | API que valida el JWT amb la clau pública |
| `app.shailamartinez.asix.cat` | Pàgina privada, Nginx valida amb `auth_request` |

Servidor: `172.24.63.20`, Master: `172.24.63.10`, usuaris: `shailamartinez` (user) i `admin-shailamartinez` (admin)

## Instruccions per desplegar el projecte des de zero

Requisits: Ubuntu Server amb Docker Engine i el plugin Compose, `openssl`, BIND9 (o `/etc/hosts` al client) i un client amb navegador.

### Pas 1: Zona DNS

Al `dns-master` declarar la zona a `/etc/bind/named.conf.local` i copiar el fitxer `db.shailamartinez.asix.cat` a `/etc/bind/zones/`:

```text
zone "shailamartinez.asix.cat" {
    type master;
    file "/etc/bind/zones/db.shailamartinez.asix.cat";
    allow-transfer { 172.24.63.11; };
};
```

```bash
sudo named-checkconf
sudo named-checkzone shailamartinez.asix.cat /etc/bind/zones/db.shailamartinez.asix.cat
sudo systemctl reload named
dig +short auth.shailamartinez.asix.cat @172.24.63.10
```

`auth`, `api` i `app` són CNAME de `www` (`172.24.63.20`).

### Pas 2: Descomprimir

A la VM del servidor (`172.24.63.20`):

```bash
unzip jwt-shailamartinez.zip
cd jwt-shailamartinez
```

### Pas 3: CA i certificat wildcard

```bash
cd certs
openssl req -x509 -newkey rsa:4096 -sha256 -days 365 -nodes \
  -keyout ca.key -out ca.crt \
  -subj "/CN=CA Laboratori shailamartinez/O=Institut Sa Palomera" \
  -addext "basicConstraints=critical,CA:TRUE" \
  -addext "keyUsage=critical,keyCertSign,cRLSign"

openssl req -newkey rsa:2048 -nodes -keyout wildcard.key -out wildcard.csr \
  -subj "/CN=*.shailamartinez.asix.cat"

cat > wildcard.ext <<EOF
basicConstraints=CA:FALSE
keyUsage=critical,digitalSignature,keyEncipherment
extendedKeyUsage=serverAuth
subjectAltName=DNS:*.shailamartinez.asix.cat,DNS:shailamartinez.asix.cat
EOF

openssl x509 -req -in wildcard.csr -CA ca.crt -CAkey ca.key -CAcreateserial \
  -out wildcard.crt -days 365 -sha256 -extfile wildcard.ext
openssl verify -CAfile ca.crt wildcard.crt
cd ..
```

Ha de sortir `wildcard.crt: OK`. Sobreescriu els `ca.crt` i `wildcard.crt` del lliurament.

### Pas 4: Claus JWT RS256

```bash
cd keys
openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:2048 -out jwt_private.pem
openssl pkey -in jwt_private.pem -pubout -out jwt_public.pem
sudo chown 10001:10001 jwt_private.pem
sudo chmod 400 jwt_private.pem
ls -ln
cd ..
```

La clau privada només la llegeix l'UID 10001 i només es munta a `auth`, l'API només rep `jwt_public.pem`.

### Pas 5: Variables i usuaris

`.env`:

```text
DOMINI=shailamartinez.asix.cat
TOKEN_TTL=900
```

`auth/users.json` ja porta els dos usuaris amb hash scrypt. Per canviar les contrasenyes, generar nous hash i substituir-los:

```bash
docker compose build
docker compose run --rm --no-deps auth python -c \
  "from werkzeug.security import generate_password_hash as g; print(g('LaVostraContrasenya'))"
```

### Pas 6: Construir i arrencar (Part 4)

```bash
docker compose build
docker compose up -d
docker compose ps
docker compose logs nginx | grep -iE "emerg|error"
```

Els tres serveis han d'estar `Up` i els logs no han de mostrar errors. Si es recrea `auth` o `api`, cal `docker compose restart nginx`

### Pas 7: Confiar en la CA al client

```bash
sudo cp ca.crt /usr/local/share/ca-certificates/ca-shailamartinez.crt
sudo update-ca-certificates
```

I importar `ca.crt` a Firefox (Paràmetres --> Privadesa i seguretat --> Certificats --> Autoritats --> Importa).

### Pas 8: Proves (Parts 5 i 6)

```bash
D=shailamartinez.asix.cat
curl https://api.$D/api/public
curl -i https://api.$D/api/perfil
curl -sI https://app.$D/ | grep -iE "^HTTP|location"
curl -i -d username=shailamartinez -d password=dolenta https://auth.$D/login
TOKEN=$(curl -s -H 'Accept: application/json' -d username=shailamartinez -d 'password=LaVostraContrasenya' https://auth.$D/login | python3 -c 'import sys,json; print(json.load(sys.stdin)["access_token"])')
curl -H "Authorization: Bearer $TOKEN" https://api.$D/api/perfil
curl -i -H "Authorization: Bearer $TOKEN" https://api.$D/api/admin
curl -sI -b "access_token=$TOKEN" https://app.$D/ | grep -iE "^HTTP|x-usuari|x-rol"
curl -k https://172.24.63.20/
```

Resultats esperats: 200, 401, 302 cap al login, 401, token, perfil de l'usuari, 403 (no és admin), 200 amb `x-usuari` i `x-rol`, i connexió tancada per Nginx (444). Al navegador, `https://app.shailamartinez.asix.cat` porta al login i després d'autenticar-se, torna a la zona privada sense tornar a demanar credencials (SSO).

## Procediment

```bash
docker compose ps
docker compose logs -f auth
docker compose restart nginx
docker compose down
```

| Servei | URL |
| --- | --- |
| Login | https://auth.shailamartinez.asix.cat/login |
| API | https://api.shailamartinez.asix.cat/api/public |
| Zona privada | https://app.shailamartinez.asix.cat |

## Qüestions

1. **Per què el servei api només rep jwt_public.pem? Què podria fer un atacant que comprometés el contenidor api si també tingués la clau privada?**

Perquè la api només necessita la clau pública per comprovar que els JWT estan ben signats, la clau privada només ha d’estar al servei auth que és el que genera i signa els tokens. Si un atacant aconsegueix la privada des de la api, podria crear els seus propis tokens i posar-se com administrador i accedir als serveis, es faria passar per qualsevol usuari.

2. **Expliqueu la diferència entre els dos models de validació de la pràctica (l'aplicació a api. i Nginx amb auth_request a app.). Quin avantatge té cada un?**

api. és la mateixa aplicació qui comprova el JWT que rep Authorization abans de permetre l’accés a cada endpoint, això permet controlar els permisos segons el rol de l’usuari.

En app. és Nginx qui comprova el token mitjançant auth_request abans de mostrar la pàgina privada. L’avantatge és que no fa falta programar aquesta comprovació dins de la pàgina web perquè nginx controla l’accés directament.

3. **La cookie porta Domain=shailamartinez.asix.cat per poder fer SSO. A Autenticació web i JWT es recomana el prefix __Host-. Per què no el podem fer servir aquí? Quin risc acceptem i com el mitigaríeu?**

Perquè obliga a no posar l’atribut Domain i es necessita compartir la cookie entre els subdominis auth, app i api per poder tenir el SSO.

El risc és que la cookie també s’envia als altres subdominis i si algun d’ells està compromès, podria posar en perill la sessió. Utilitzaria Secure Httponly i SameSite = Lax per mantenir els subdominis protegits amb https i el token tingui una durada limitada.

4. **Un JWT emès té validesa fins a l'exp. Si es roba un token, com el podríeu invalidar abans? Feu servir la claim jti a la resposta.**

Es podria crear una llista de tokens revocats al servidor, cada JWT té un claim jti que és un id únic. Si es roba un token, podem guardar el seu jti en aquesta llista i comprovar-lo cada vegada que es valida un JWT. Si apareix a la llista, es denega encara que no hagi arribat a la data de caducitat.

5. **Per què el login retorna 401 tant si l'usuari no existeix com si la contrasenya és incorrecta, i no dos missatges diferents?**

Per evitar que un atacant pugui saber quins usuaris existeixen, si es mostren missatges diferents es podria provar noms d’usuari i descobrir quins són vàlids.

6. **Què passaria amb el SSO si auth. fos a shailamartinez.asix.cat i app. a un altre domini (per exemple botiga.cat)? Quin protocol es fa servir a la vida real per resoldre-ho?**

Com pertany a un domini diferent ja no es podria compartir i l’usuari no mantindria la sessió automàticament entre els dos dominis.

Es pot resoldre OpenId connect, l'usuari inicia sessió en un servei central i després les altres aplicacions poden reconèixer que ja s'ha identificat, sense haver de compartir la mateixa cookie entre elles.
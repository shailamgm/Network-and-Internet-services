# Nginx endurit i monitorat amb Grafana

**Shaila Martínez - 2n ASIX**

**Nº 63 - Serveis**

## Estructura

```text
nginx-shailamartinez/
├── alloy/
├── certs/
├── fail2ban/
│   ├── filter.d/
│   └── jail.d/
├── grafana/
│   └── provisioning/
├── nginx/
│   ├── snippets/
│   └── templates/
├── prometheus/
└── docker-compose.yml
```

## Configuració de Nginx i seguretat

He configurat Nginx com a proxy invers amb HTTPS i un certificat que inclou els dominis web i de Grafana als SAN.

Les principals mesures aplicades són:

- Ocultar la versió de Nginx.
- Registrar les peticions en format JSON.
- Limitar la mida de les peticions a 2 MB.
- Configurar timeouts i límits de peticions i connexions.
- Bloquejar User-Agents sospitosos.
- Redirigir HTTP a HTTPS.
- Permetre TLS 1.2 i TLS 1.3.
- Afegir capçaleres de seguretat.
- Bloquejar rutes i fitxers sensibles.
- Restringir l'accés a Grafana i `stub_status`.

## Monitoratge amb Docker

He desplegat els serveis amb Docker Compose:

- **Prometheus:** recull les mètriques.
- **Grafana:** mostra les mètriques i els registres.
- **Loki:** emmagatzema els logs.
- **Alloy:** recull i envia els logs.
- **Nginx Exporter:** exposa les mètriques de Nginx.

He comprovat l'estat dels contenidors, els ports en escolta i els targets de Prometheus.

## Dashboard i alertes

He creat un dashboard de Grafana amb vuit panells inicials per consultar connexions, peticions, codis HTTP, IP, rutes i temps de resposta.

També he configurat dues alertes:

- `NginxCaigut`: detecta quan Nginx deixa d'estar disponible.
- `RafegaBloquejada`: detecta un augment de respostes 429.

A la part final he afegit dos panells de Fail2ban:

- **Panell 9:** bloquejos per jail.
- **Panell 10:** últims bloquejos i desbloquejos.

El dashboard final de deu panells està exportat a `grafana/dashboard-shailamartinez.json`.

## Proves de seguretat

He realitzat les proves des del client per comprovar les mesures configurades:

| Prova | Resultat esperat |
|---|---|
| Comprovació de capçaleres | Versió oculta i capçaleres de seguretat presents. |
| Accés HTTP | Redirecció a HTTPS. |
| Accés directe per IP | Connexió tancada amb 444. |
| User-Agent d'escàner | Bloqueig 403. |
| Petició sense User-Agent | Bloqueig 403. |
| Accés a rutes sensibles | Resposta 404. |
| Ràfega de peticions | Respostes 429 en superar el límit. |
| Prova contra `/login` | Limitació de peticions. |
| Petició de 5 MB | Resposta 413. |
| Accés no autoritzat a Grafana | Resposta 403. |
| Escaneig amb Nmap | Identificació dels ports oberts. |
| Aturada de Nginx | Activació de l'alerta corresponent. |

Les captures i els resultats de les proves estan documentats al PDF.

## Configuració de Fail2ban

He instal·lat Fail2ban a la màquina virtual i he creat quatre filtres personalitzats:

- `nginx-json-badbots`
- `nginx-json-botsearch`
- `nginx-json-login`
- `nginx-json-ratelimit`

He configurat sis jails: les quatre anteriors, `sshd` i `recidive`.

Les jails de Nginx utilitzen la cadena `DOCKER-USER` d'iptables per bloquejar el trànsit cap als contenidors. La jail SSH utilitza `INPUT`.

He comprovat el funcionament amb `fail2ban-regex`, `fail2ban-client status` i les regles d'iptables.

També he integrat els logs de Fail2ban amb Alloy i Loki per poder visualitzar els bloquejos des de Grafana.

## Proves de Fail2ban

| Prova | Comportament detectat |
|---|---|
| F1 | User-Agent sospitós (`sqlmap`). |
| F2 | Accés a rutes sensibles. |
| F3 | Intents repetits contra `/login`. |
| F4 | Excés de peticions. |
| F5 | Intents d'autenticació SSH fallits. |
| F6 | Reincidència en diferents bloquejos. |

## Qüestions

1. **Quina diferència hi ha entre la informació que dona stub_status
(Prometheus) i la que obteniu dels logs (Loki)? Per què necessitem les dues
fonts?**

Prometheus dona informació de l’estat de Nginx en temps real, com connexions
actives i peticions. Loki recull els logs i permet veure què ha passat amb cada
petició, com les IP, accessos... Necessitem les dues perquè una ens mostra com
funciona el servidor i l’altra permet detectar i observar possibles problemes o
atacs.

2. **Per què stub_status escolta al port 8080, només és accessible des de la
xarxa 10.10.XX.0/24 i no està publicat?**

Perquè stub_status mostra informació interna del servidor, només hi ha de poder
accedir els serveis de monitoratge des de la seva xarxa. El port no està publicat no
es pot accedir directament des de l’exterior.

3. **Quin avantatge té tenir dues xarxes Docker (frontal i monitoratge) en lloc
d'una? Quin contenidor és a totes dues i per què?**

Tenir dues permet separar el tràfic dels usuaris del trànsit de monitoratge. Millora
la seguretat perquè els serveis interns no queden exposats a la xarxa frontal. El
contenidor Alloy està connectat a les dues xarxes perquè ha de poder recollit els
logs de nginx i enviar-los als serveis de monitoratge.

4. **Amb limit_req zone=general burst=20 nodelay i rate=10r/s, quantes
peticions seguides d'una mateixa IP s'accepten abans de rebre 429? Com
ho heu vist a la prova 7?**

El límit és de 10 peticions per segon i permet una ràfega de fins a 20 peticions.
Amb nodelay les peticions s'accepten sense esperar, quan es supera el límit, nginx
retorna error 429. A la prova 7 s’ha vist perquè en enviar moltes peticions
seguides, algunes van retornar 200 i les que superaven el límit amb 429.

5. **Bloquejar per User-Agent atura sqlmap, però un atacant pot canviar el seu
User-Agent en un segon. Té sentit mantenir aquesta mesura? Quines altres
capes la complementen?**

Si té sentit perquè permet bloquejar eines conegudes com sqlmap ràpidament. Es
complementa amb altres mesures com el límit de peticions de Nginx, Fail2ban, la
monitorització amb Grafana i Loi i el bloqueig de rutes sospitoses.

6. **Si el servidor estigués darrere d'un altre proxy o d'un CDN, totes les
peticions arribarien des de la mateixa IP. Què passaria amb el rate limiting,
amb el panell «Top 10 IP» i amb Fail2ban? Com es resol? (Pista:
real_ip_header.)**

El límit de peticions afectaria tots els usuaris alhora, el panell Top 10 Ip només
mostraria la IP del Proxy i Fail2ban podria bloquejar el Proxy en lloc de l’atacant.
Caldria configurar real_ip_header i indicar quins proxis són de confiança amb
set_real_ip_from, perquè Nginx pugui identificar la IP cada client.

7. **Per què les jails de Nginx han de bloquejar a la cadena DOCKER-USER i la
de sshd a INPUT? Què hauria passat a la prova F1 si haguéssiu deixat
l'acció per defecte de Fail2ban?**

Perquè les connexions que van cap als contenidors passen per les regles de trànsit
de Docker, SSH funciona directament amb la màquina virtual i per això es bloqueja
a Input.

Si s’hagués deixat per defecte, el bloqueig podria no haver afectat les connexions
cap al contenidor nginx i el client hauria continuat accedint a la web.

8. **Quina diferència hi ha entre el limit_req de Nginx i la jail nginx-ratelimit? Per
què cal la jail recidive, i quin risc té posar un bantime permanent o oblidarse la xarxa d'administració a ignoreip?**

Límit_req controla la quantitat de peticions que pot fer la mateixa IP i dona 429
quan es supera el límit. La jail nginx_ratelimit detecta els errors als logs i pot
bloquejar la IP durant un temps.

La recidive serveix per bloquejar durant més temps les I que acumulen molts
bans. Si es posa un bantime permanent, podem deixar una IP bloquejada per
sempre i si s’oblida d’afegir la xarxa d’administració a ignoreip, es pot acabar
bloquejant-nos a nosaltres mateixos i no poder accedir al servidor.

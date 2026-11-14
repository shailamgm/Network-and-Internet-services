"""API protegida: només té la clau PÚBLICA, pot validar tokens però no emetre'n."""
import os

import jwt
from flask import Flask, g, jsonify, request

DOMINI = os.environ["DOMINI"]
ISSUER = f"https://auth.{DOMINI}"
AUDIENCE = f"api.{DOMINI}"

with open("/keys/jwt_public.pem") as f:
    PUBLIC_KEY = f.read()

app = Flask(__name__)
app.json.ensure_ascii = False  # accents llegibles a les respostes JSON


def error(codi, missatge):
    resposta = jsonify(error=missatge)
    resposta.status_code = codi
    if codi == 401:
        resposta.headers["WWW-Authenticate"] = 'Bearer realm="api"'
    return resposta


@app.before_request
def autentica():
    if request.path == "/api/public":
        return None
    capcalera = request.headers.get("Authorization", "")
    token = capcalera.removeprefix("Bearer ") if capcalera.startswith("Bearer ") else request.cookies.get("access_token")
    if not token:
        return error(401, "falta el token")
    try:
        g.claims = jwt.decode(
            token, PUBLIC_KEY, algorithms=["RS256"], audience=AUDIENCE, issuer=ISSUER,
            options={"require": ["exp", "iat", "iss", "aud", "sub"]},
        )
    except jwt.ExpiredSignatureError:
        return error(401, "token caducat")
    except jwt.InvalidTokenError as e:
        return error(401, f"token invàlid: {e}")
    return None


@app.get("/api/public")
def public():
    return jsonify(missatge=f"API de {DOMINI}: endpoint públic")


@app.get("/api/perfil")
def perfil():
    return jsonify(usuari=g.claims["sub"], rol=g.claims["role"], caduca=g.claims["exp"])


@app.get("/api/admin")
def admin():
    if g.claims.get("role") != "admin":
        return error(403, "cal el rol admin")
    return jsonify(missatge=f"Benvingut/da a l'administració, {g.claims['sub']}")

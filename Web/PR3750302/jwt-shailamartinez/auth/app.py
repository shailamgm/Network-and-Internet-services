"""Servei d'autenticació: emet i valida JWT signats amb RS256."""
import json
import os
import time
import uuid

import jwt
from flask import Flask, jsonify, make_response, redirect, request
from werkzeug.security import check_password_hash

DOMINI = os.environ["DOMINI"]                 # p. ex. shailamartinez.asix.cat
ISSUER = f"https://auth.{DOMINI}"
AUDIENCE = f"api.{DOMINI}"
TTL = int(os.environ.get("TOKEN_TTL", "900"))  # segons (15 min)

with open("/keys/jwt_private.pem") as f:
    PRIVATE_KEY = f.read()
with open("/keys/jwt_public.pem") as f:
    PUBLIC_KEY = f.read()
with open("/app/users.json") as f:
    USERS = json.load(f)

app = Flask(__name__)
app.json.ensure_ascii = False  # accents llegibles a les respostes JSON

FORMULARI = f"""<!doctype html>
<html lang="ca"><head><meta charset="utf-8"><title>Login · {DOMINI}</title></head>
<body>
  <h1>Inici de sessió — {DOMINI}</h1>
  <form method="post" action="/login">
    <label>Usuari <input name="username" autocomplete="username"></label><br>
    <label>Contrasenya <input name="password" type="password" autocomplete="current-password"></label><br>
    <button type="submit">Entra</button>
  </form>
</body></html>"""


def emet_token(usuari, rol):
    ara = int(time.time())
    claims = {
        "iss": ISSUER,
        "aud": AUDIENCE,
        "sub": usuari,
        "role": rol,
        "iat": ara,
        "exp": ara + TTL,
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(claims, PRIVATE_KEY, algorithm="RS256", headers={"kid": "clau-1"})


def valida_token(token):
    # Llista blanca d'algorismes: mai es confia en el camp "alg" del token
    return jwt.decode(
        token,
        PUBLIC_KEY,
        algorithms=["RS256"],
        audience=AUDIENCE,
        issuer=ISSUER,
        options={"require": ["exp", "iat", "iss", "aud", "sub"]},
    )


def token_de_la_peticio():
    capcalera = request.headers.get("Authorization", "")
    if capcalera.startswith("Bearer "):
        return capcalera.removeprefix("Bearer ")
    return request.cookies.get("access_token")


@app.get("/login")
def formulari():
    return FORMULARI


@app.post("/login")
def login():
    usuari = request.form.get("username", "")
    contrasenya = request.form.get("password", "")
    registre = USERS.get(usuari)
    if registre is None or not check_password_hash(registre["hash"], contrasenya):
        app.logger.warning("Login fallit per a l'usuari %r", usuari)
        return "Credencials incorrectes\n", 401

    token = emet_token(usuari, registre["role"])
    if request.accept_mimetypes.best == "application/json":
        resposta = make_response(jsonify(access_token=token, token_type="Bearer", expires_in=TTL))
    else:
        resposta = make_response(redirect(f"https://app.{DOMINI}/"))
    # Domain=.DOMINI: la cookie viatja a auth., api. i app. (SSO entre subdominis)
    resposta.set_cookie(
        "access_token", token, max_age=TTL, domain=f".{DOMINI}", path="/",
        secure=True, httponly=True, samesite="Lax",
    )
    return resposta


@app.get("/verify")
def verify():
    """Endpoint per a l'auth_request de Nginx: 204 si el token és vàlid, 401 si no."""
    token = token_de_la_peticio()
    if not token:
        return "", 401
    try:
        claims = valida_token(token)
    except jwt.InvalidTokenError as error:
        app.logger.warning("Token rebutjat: %s", error)
        return "", 401
    resposta = make_response("", 204)
    resposta.headers["X-User"] = claims["sub"]
    resposta.headers["X-Role"] = claims["role"]
    return resposta


@app.post("/logout")
def logout():
    resposta = make_response(redirect(f"https://auth.{DOMINI}/login"))
    resposta.delete_cookie("access_token", domain=f".{DOMINI}", path="/", secure=True, httponly=True, samesite="Lax")
    return resposta

import requests
import hashlib
import hmac
import secrets
import json
import re

IP_ROTEADOR = "192.168.3.1"
USERNAME = "admin"
PASSWORD = "187237"

session = requests.Session()
base_url = f"http://{IP_ROTEADOR}"


def gerar_nonce():
    return secrets.token_hex(32)


def obter_csrf():
    print("→ Obtendo CSRF...")
    response = session.get(f"{base_url}/html/index.html")

    csrf_param = re.search(r'<meta name="csrf_param" content="([^"]+)"', response.text)
    csrf_token = re.search(r'<meta name="csrf_token" content="([^"]+)"', response.text)

    if csrf_param and csrf_token:
        print("✓ CSRF obtido")
        return {"csrf_param": csrf_param.group(1), "csrf_token": csrf_token.group(1)}
    return None


def get_client_proof(password, salt, iterations, first_nonce, server_nonce):
    """ORDEM CORRETA DOS PARÂMETROS DO HMAC!"""

    auth_msg = f"{first_nonce},{server_nonce},{server_nonce}".encode()

    salted_password = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), bytes.fromhex(salt), iterations
    )

    # ORDEM CORRETA: (msg, key, hash) ← INVERTIDO!
    client_key = hmac.new(
        b"Client Key",  # ← msg primeiro!
        salted_password,  # ← key depois!
        hashlib.sha256,
    ).digest()

    stored_key = hashlib.sha256(client_key).digest()

    # ORDEM CORRETA: (msg, key, hash) ← INVERTIDO!
    client_signature = hmac.new(
        auth_msg, stored_key, hashlib.sha256  # ← msg primeiro!  # ← key depois!
    ).digest()

    client_proof = bytes(a ^ b for a, b in zip(client_key, client_signature))

    return client_proof.hex()


def login():
    csrf = obter_csrf()
    if not csrf:
        print("✗ Falha ao obter CSRF")
        return False

    first_nonce = gerar_nonce()
    print(f"✓ First nonce: {first_nonce[:20]}...")

    # PASSO 1: Enviar username e nonce
    print("\n[1/2] Enviando username...")
    url1 = f"{base_url}/api/system/user_login_nonce"
    data1 = {"data": {"username": USERNAME, "firstnonce": first_nonce}, "csrf": csrf}

    resp1 = session.post(
        url1,
        json=data1,
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "X-Requested-With": "XMLHttpRequest",
            "_ResponseFormat": "JSON",
        },
    )

    if resp1.status_code != 200:
        print(f"✗ Erro HTTP: {resp1.status_code}")
        return False

    result1 = resp1.json()

    if result1.get("err") != 0:
        print(f"✗ Erro na resposta: {result1.get('err')}")
        return False

    salt = result1["salt"]
    iterations = result1["iterations"]
    server_nonce = result1["servernonce"]

    print(f"✓ Server nonce: {server_nonce[:30]}...")

    # PASSO 2: Calcular e enviar proof
    print("\n[2/2] Calculando client proof...")
    client_proof = get_client_proof(
        PASSWORD, salt, iterations, first_nonce, server_nonce
    )

    print(f"✓ Client proof: {client_proof[:20]}...")

    url2 = f"{base_url}/api/system/user_login_proof"
    data2 = {
        "data": {"clientproof": client_proof, "finalnonce": server_nonce},
        "csrf": {
            "csrf_param": result1["csrf_param"],
            "csrf_token": result1["csrf_token"],
        },
    }

    resp2 = session.post(
        url2,
        json=data2,
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "X-Requested-With": "XMLHttpRequest",
            "_ResponseFormat": "JSON",
        },
    )

    if resp2.status_code != 200:
        print(f"✗ Erro HTTP: {resp2.status_code}")
        return False

    result2 = resp2.json()

    if result2.get("err") == 0:
        print(f"\n{'='*60}")
        print(f"✓✓✓ LOGIN BEM-SUCEDIDO! ✓✓✓")
        print(f"{'='*60}")
        print(f"Level: {result2.get('level')}")
        return True
    else:
        print(f"\n✗ Login falhou!")
        print(f"Erro: {result2.get('err')}")
        print(f"Categoria: {result2.get('errorCategory')}")
        print(json.dumps(result2, indent=2))
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("LOGIN HUAWEI WiFi AX2 - ORDEM CORRETA DO HMAC")
    print("=" * 60)

    if login():
        print("\n→ Testando acesso à API...")
        resp = session.get(f"{base_url}/api/system/deviceinfo")
        info = resp.json()
        print(f"✓ Modelo: {info.get('custinfo', {}).get('CustDeviceName')}")
        print(f"✓ Versão: {info.get('SoftwareVersion')}")

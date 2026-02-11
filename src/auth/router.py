import os
import hashlib
import hmac
import secrets
import re
from typing import Optional

import requests
from dotenv import load_dotenv

from src.utils.logger import get_logger

load_dotenv()

logger = get_logger(__name__)


def _generate_nonce() -> str:
    return secrets.token_hex(32)


def _get_csrf_token(session: requests.Session, base_url: str) -> Optional[dict]:
    logger.debug("Obtaining CSRF token")
    response = session.get(f"{base_url}/html/index.html")

    csrf_param_match = re.search(
        r'<meta name="csrf_param" content="([^"]+)"', response.text
    )
    csrf_token_match = re.search(
        r'<meta name="csrf_token" content="([^"]+)"', response.text
    )

    if csrf_param_match and csrf_token_match:
        logger.debug("CSRF token obtained successfully")
        return {
            "csrf_param": csrf_param_match.group(1),
            "csrf_token": csrf_token_match.group(1),
        }

    logger.error("Failed to obtain CSRF token")
    return None


def _calculate_client_proof(
    password: str, salt: str, iterations: int, first_nonce: str, server_nonce: str
) -> str:
    auth_message = f"{first_nonce},{server_nonce},{server_nonce}".encode()

    salted_password = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), bytes.fromhex(salt), iterations
    )

    client_key = hmac.new(
        b"Client Key",
        salted_password,
        hashlib.sha256,
    ).digest()

    stored_key = hashlib.sha256(client_key).digest()

    client_signature = hmac.new(auth_message, stored_key, hashlib.sha256).digest()

    client_proof = bytes(
        client_key_byte ^ signature_byte
        for client_key_byte, signature_byte in zip(client_key, client_signature)
    )

    return client_proof.hex()


def get_authenticated_session(
    router_ip: str, username: str, password: str
) -> Optional[requests.Session]:
    logger.info(f"Starting router authentication process for {router_ip}")

    session = requests.Session()
    base_url = f"http://{router_ip}"

    csrf_tokens = _get_csrf_token(session, base_url)
    if not csrf_tokens:
        return None

    first_nonce = _generate_nonce()
    logger.debug(f"First nonce generated: {first_nonce[:20]}...")

    logger.debug("Sending username to obtain server nonce")
    nonce_url = f"{base_url}/api/system/user_login_nonce"
    nonce_payload = {
        "data": {"username": username, "firstnonce": first_nonce},
        "csrf": csrf_tokens,
    }

    request_headers = {
        "Content-Type": "application/json; charset=utf-8",
        "X-Requested-With": "XMLHttpRequest",
        "_ResponseFormat": "JSON",
    }

    nonce_response = session.post(
        nonce_url, json=nonce_payload, headers=request_headers
    )

    if nonce_response.status_code != 200:
        logger.error(f"HTTP error obtaining nonce: {nonce_response.status_code}")
        return None

    nonce_data = nonce_response.json()

    if nonce_data.get("err") != 0:
        logger.error(f"Error in nonce response: {nonce_data.get('err')}")
        return None

    salt = nonce_data["salt"]
    iterations = nonce_data["iterations"]
    server_nonce = nonce_data["servernonce"]

    logger.debug(f"Server nonce received: {server_nonce[:30]}...")

    logger.debug("Calculating client proof")
    client_proof = _calculate_client_proof(
        password, salt, iterations, first_nonce, server_nonce
    )

    logger.debug(f"Client proof calculated: {client_proof[:20]}...")

    logger.debug("Sending client proof for authentication")
    proof_url = f"{base_url}/api/system/user_login_proof"
    proof_payload = {
        "data": {"clientproof": client_proof, "finalnonce": server_nonce},
        "csrf": {
            "csrf_param": nonce_data["csrf_param"],
            "csrf_token": nonce_data["csrf_token"],
        },
    }

    proof_response = session.post(
        proof_url, json=proof_payload, headers=request_headers
    )

    if proof_response.status_code != 200:
        logger.error(f"HTTP error sending proof: {proof_response.status_code}")
        return None

    proof_data = proof_response.json()

    if proof_data.get("err") == 0:
        logger.info(f"Login successful. Level: {proof_data.get('level')}")
        return session

    logger.error(
        f"Login failed. Error: {proof_data.get('err')}, "
        f"Category: {proof_data.get('errorCategory')}"
    )
    return None

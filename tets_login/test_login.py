import hashlib
import hmac

# Valores capturados do navegador
FIRST_NONCE = "b43297073d98dc90d8b407d3fbe917079898dc8a5e2f0d03f0c71b82b3b43228"
FINAL_NONCE = "b43297073d98dc90d8b407d3fbe917079898dc8a5e2f0d03f0c71b82b3b432289iA0gSjJSDwO6e2zD2zdGa7AxTGLdE8d"
CLIENT_PROOF_ESPERADO = (
    "139d4af8d60eb3fa0c0fea60e87def5c19716e2cce4f07c9465df49e132dc87b"
)

# Informações do servidor (assumindo valores padrão)
SALT = "a5c94253c216f67bca2baff8dacad895813d1c07092f22abef2e8b95ce10a053"
ITERATIONS = 1000

# TESTE COM VÁRIAS SENHAS POSSÍVEIS
senhas_teste = [
    "admin",
    "Admin",
    "ADMIN",
    "admin123",
    "Admin123",
    # Adicione outras possibilidades
]

print("=" * 70)
print("TESTE REVERSO - TENTANDO DESCOBRIR A SENHA CORRETA")
print("=" * 70)


def calcular_client_proof(password, salt, iterations, first_nonce, final_nonce):
    """Calcula o client proof usando SCRAM-SHA256"""

    # AuthMessage = firstNonce,finalNonce,finalNonce
    auth_msg = f"{first_nonce},{final_nonce},{final_nonce}"

    # SaltedPassword = PBKDF2(password, salt, iterations)
    salt_bytes = bytes.fromhex(salt)
    salted_password = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt_bytes, iterations
    )

    # ClientKey = HMAC(SaltedPassword, "Client Key")
    client_key = hmac.new(salted_password, b"Client Key", hashlib.sha256).digest()

    # StoredKey = SHA256(ClientKey)
    stored_key = hashlib.sha256(client_key).digest()

    # ClientSignature = HMAC(StoredKey, AuthMessage)
    client_signature = hmac.new(
        stored_key, auth_msg.encode("utf-8"), hashlib.sha256
    ).digest()

    # ClientProof = ClientKey XOR ClientSignature
    client_proof_bytes = bytes(a ^ b for a, b in zip(client_key, client_signature))
    client_proof = client_proof_bytes.hex()

    return client_proof


print(f"\nClient Proof ESPERADO (do navegador):")
print(f"  {CLIENT_PROOF_ESPERADO}")
print(f"\nTestando senhas...\n")

for senha in senhas_teste:
    client_proof = calcular_client_proof(
        senha, SALT, ITERATIONS, FIRST_NONCE, FINAL_NONCE
    )

    match = "✓ MATCH!" if client_proof == CLIENT_PROOF_ESPERADO else "✗"

    print(f"{match} Senha: '{senha}'")
    print(f"     Proof: {client_proof}")

    if client_proof == CLIENT_PROOF_ESPERADO:
        print(f"\n{'='*70}")
        print(f"🎉 SENHA ENCONTRADA: '{senha}' 🎉")
        print(f"{'='*70}")
        break
else:
    print(f"\n{'='*70}")
    print("⚠ NENHUMA SENHA CORRESPONDEU!")
    print("=" * 70)
    print("\nPossíveis problemas:")
    print("1. A senha não está na lista de teste")
    print("2. O SALT pode estar diferente (vamos verificar)")
    print("\nVamos pegar o SALT correto da resposta do servidor...")
    print("\nDigite sua senha REAL (a que você usa no navegador):")
    senha_real = input().strip()

    client_proof_real = calcular_client_proof(
        senha_real, SALT, ITERATIONS, FIRST_NONCE, FINAL_NONCE
    )

    print(f"\nCom a senha '{senha_real}':")
    print(f"  Proof calculado: {client_proof_real}")
    print(f"  Proof esperado:  {CLIENT_PROOF_ESPERADO}")

    if client_proof_real == CLIENT_PROOF_ESPERADO:
        print("\n✓ SENHAS CORRESPONDEM!")
    else:
        print("\n✗ Ainda não corresponde. O problema pode estar no SALT.")
        print("\nPrecisamos capturar a RESPOSTA da requisição user_login_nonce")
        print("(aquela que retorna salt, iterations, servernonce)")

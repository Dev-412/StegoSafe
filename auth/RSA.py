import random
import math


# ---------------- PRIME CHECK ----------------

def is_prime(n):
    if n < 2:
        return False
    for i in range(2, int(math.sqrt(n)) + 1):
        if n % i == 0:
            return False
    return True


def generate_prime(start=1000, end=5000):
    while True:
        p = random.randint(start, end)
        if is_prime(p):
            return p


# ---------------- GCD ----------------

def gcd(a, b):
    while b:
        a, b = b, a % b
    return a


# ---------------- EXTENDED GCD ----------------

def extended_gcd(a, b):
    if b == 0:
        return a, 1, 0
    g, x1, y1 = extended_gcd(b, a % b)
    return g, y1, x1 - (a // b) * y1


# ---------------- MOD INVERSE ----------------

def mod_inverse(e, phi):
    g, x, _ = extended_gcd(e, phi)
    if g != 1:
        raise Exception("Inverse does not exist")
    return x % phi


# ---------------- FAST EXP ----------------

def mod_exp(base, exp, mod):
    res = 1
    base %= mod
    while exp:
        if exp & 1:
            res = (res * base) % mod
        exp >>= 1
        base = (base * base) % mod
    return res


# ---------------- KEY GEN ----------------

def generate_keys():

    p = generate_prime()
    q = generate_prime()
    while p == q:
        q = generate_prime()

    n = p * q
    phi = (p - 1) * (q - 1)

    e = 65537
    if gcd(e, phi) != 1:
        e = 3
        while gcd(e, phi) != 1:
            e += 2

    d = mod_inverse(e, phi)

    return (e, n), (d, n)


# ---------------- BLOCK ENCRYPT ----------------

def encrypt(message, public_key):

    e, n = public_key

    data = message.encode()
    cipher = []

    for b in data:
        c = mod_exp(b, e, n)
        cipher.append(c)

    return cipher

def decrypt(cipher, private_key):

    d, n = private_key

    result = ""

    for c in cipher:
        m = mod_exp(c, d, n)

        # ensure valid ascii
        if m < 0 or m > 255:
            raise Exception(f"Invalid decrypted byte: {m}")

        result += chr(m)

    return result



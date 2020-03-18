# https://tools.ietf.org/html/rfc7516
# https://cryptojwt.readthedocs.io/en/latest/


Create the RSA certificates
````
# Create RSA certificates
CERT_PATH='saml2_sp/saml2_config/certificates'
openssl req -nodes -new -x509 -days 3650 -keyout $CERT_PATH/key.pem -out $CERT_PATH/cert.pem
````

Encrypt
````
from cryptojwt.jwk.rsa import import_private_rsa_key_from_file
from cryptojwt.jwe.jwe_rsa import JWE_RSA

RSA_KEY_PATH = 'saml2_sp/saml2_config/certificates/key.pem'

priv_key = import_private_rsa_key_from_file(RSA_KEY_PATH)
pub_key = priv_key.public_key()
plain = b'Now is the time for all good men to come to the aid of ...'
_rsa = JWE_RSA(plain, alg="RSA1_5", enc="A128CBC-HS256")
jwe = _rsa.encrypt(pub_key)
````

Decrypt
````
from cryptojwt.jwe.jwe import factory
from cryptojwt.jwk.rsa import RSAKey

_decryptor = factory(jwe, alg="RSA1_5", enc="A128CBC-HS256")
_dkey = RSAKey(priv_key=priv_key)
msg = _decryptor.decrypt(jwe, [_dkey])
````

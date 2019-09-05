openssl genrsa -out sp-key.pem 2048
openssl req -new -key sp-key.pem -out sp.csr
openssl x509 -req -days 3650 -in sp.csr -signkey sp-key.pem -out sp.crt

# convert them to pem
openssl x509 -inform PEM -in sp.crt > sp-cert.pem

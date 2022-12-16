echo "Creating cal........................"
openssl genrsa -out root.key

echo "Script executed from: ${PWD}"
openssl req -new -x509 -key root.key -out root.crt -days 3650 -subj "/CN=againstall/OU=SD/O=UA/L=Elche/S=CV/C=ES"

echo "Creating server certs........................"
openssl genrsa -out server.key
openssl req -new -key server.key -out server.csr -subj "/CN=againstall/OU=SD/O=UA/L=Elche/S=CV/C=ES"
openssl x509 -req -in server.csr -days 3650 -sha256 -CAcreateserial -CA root.crt -CAkey root.key -out server.crt

echo "Creating client certs........................"
openssl genrsa -out client.key
openssl req -new -key client.key -out client.csr -subj "/CN=againstall/OU=SD/O=UA/L=Elche/S=CV/C=ES"
openssl x509 -req -in client.csr -days 3650 -sha256 -CAcreateserial -CA root.crt -CAkey root.key -out client.crt

echo "Creating server keystore........................"

keytool -keystore kafka.truststore.jks -alias CARoot -import -file root.crt -keypass againstall -storepass againstall
keytool -genkey -alias localhost -keystore kafka.keystore.jks -validity 3650 -dname "CN=againstall, OU=SD, O=UA, L=Elche, S=CV, C=ES" -keypass againstall -storepass againstall
#keytool -keystore kafka.keystore.jks -alias localhost -validity 3650 -dname "CN=againstall, OU=SD, O=UA, L=Elche, S=CV, C=ES"
keytool -keystore kafka.keystore.jks -alias localhost -certreq -file kafka.unsigned.crt -keypass againstall -storepass againstall
openssl x509 -req -CA root.crt -CAkey root.key -in kafka.unsigned.crt -out kafka.signed.crt -days 3650 -CAcreateserial
keytool -keystore kafka.keystore.jks -alias CARoot -import -file root.crt -keypass againstall -storepass againstall
keytool -keystore kafka.keystore.jks -alias localhost -import -file kafka.signed.crt -keypass againstall -storepass againstall
echo "againstall" > ssl.creds

echo "Creating client keystore........................"
#keytool -keystore client.keystore.jks -alias localhost -validity 3650 -dname "CN=againstall, OU=SD, O=UA, L=Elche, S=CV, C=ES"
keytool -genkey -keystore client.keystore.jks -alias localhost -validity 3650 -dname "CN=againstall, OU=SD, O=UA, L=Elche, S=CV, C=ES" -keypass againstall -storepass againstall
keytool -keystore client.keystore.jks -alias localhost -certreq -file client.unsigned.cert -keypass againstall -storepass againstall
openssl x509 -req -CA root.crt -CAkey root.key -in client.unsigned.cert -out client.signed.cert -days 3650 -CAcreateserial
keytool -keystore client.keystore.jks -alias CARoot -import -file root.crt -keypass againstall -storepass againstall
keytool -keystore client.keystore.jks -alias localhost -import -file client.signed.cert -keypass againstall -storepass againstall


#cp root.crt root.key server.key server.crt client.crt client.key ssl.creds kafka.truststore.jks kafka
openssl x509 -in root.crt -out root.pem -outform PEM
#cp root.pem /etc/pki/ca-trust/source/anchors/
#update-ca-trust
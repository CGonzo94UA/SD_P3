#!/bin/bash
set -euf -o pipefail

cd "$(dirname "$0")/../secrets/" || exit

echo "🔖  Generating kafka certificates and other secrets."
echo "⚠️  Remember to type in \"yes\" for all prompts."
sleep 2

TLD="local"
PASSWORD="againstall"

# Generate CA key
openssl req -new -x509 -keyout kafka.key \
	-out kafka.crt -days 365 \
	-subj "/CN=againstall/OU=SD/O=UA/L=Elche/S=CV/C=ES" \
	-passin pass:$PASSWORD -passout pass:$PASSWORD

	# Create keystores
	keytool -genkey -noprompt \
		-alias kafka \
		-dname "CN=againstall, OU=SD, O=UA, L=Elche, S=CV, C=ES" \
		-keystore kafka.server.keystore.jks \
		-keyalg RSA \
		-storepass $PASSWORD \
		-keypass $PASSWORD


	# Create CSR, sign the key and import back into keystore
	keytool -keystore kafka.server.keystore.jks -alias kafka -certreq -file kafka.csr -storepass $PASSWORD -keypass $PASSWORD

	openssl x509 -req -CA kafka.crt -CAkey kafka.key -in kafka.csr -out kafka-signed.crt -days 365 -CAcreateserial -passin pass:$PASSWORD

	keytool -keystore kafka.server.keystore.jks -alias CARoot -import -file kafka.crt -storepass $PASSWORD -keypass $PASSWORD

	keytool -keystore kafka.server.keystore.jks -alias kafka -import -file kafka-signed.crt -storepass $PASSWORD -keypass $PASSWORD

	# Create truststore and import the CA cert. SERVER
	keytool -keystore kafka.server.truststore.jks -alias CARoot -import -file kafka.crt -storepass $PASSWORD -keypass $PASSWORD

	# Create truststore and import the CA cert. CLIENT
	keytool -keystore kafka.client.truststore.jks -alias CARoot -import -file kafka.crt -storepass $PASSWORD -keypass $PASSWORD

	echo $PASSWORD >kafka_sslkey_creds
	echo $PASSWORD >kafka_keystore_creds
	echo $PASSWORD >kafka_truststore_creds

echo "✅  All done."
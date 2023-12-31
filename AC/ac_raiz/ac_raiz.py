from cryptography.hazmat.primitives import serialization
import os
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import hashes
from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
import datetime
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.x509.oid import NameOID

ahora = datetime.datetime.utcnow()

class AC_raiz():
    def __init__(self):
        self.__private_key = self.CargarClave()
        self._public_key = None
        self.name = None
        self.certificado = self.CargarCertificado()

    def CargarClave(self):
        path = os.path.dirname(__file__) + "/key.pem"
        with open(path, "rb") as key_file:
            private_key = serialization.load_pem_private_key(
                key_file.read(),
                password=None,
            )
        self._public_key = private_key.public_key()

        return private_key

    def CargarCertificado(self):
        with open(os.path.dirname(__file__) + "/certificado.pem", "rb") as archivo:
            certificado_pem = archivo.read()
        certificado = x509.load_pem_x509_certificate(certificado_pem, default_backend())
        
        if certificado.not_valid_after < ahora:
            certificado = self.GenerarACRaiz()

        self.name = certificado.subject
        return certificado

    def verificar_firma_csr(self, csr, public_key_solicitante):
        try:
            # Verifica la firma de la CSR
            public_key_solicitante.verify(
                csr.signature,
                csr.tbs_certrequest_bytes,
                padding.PKCS1v15(),
                hashes.SHA256(),
            )
            return self.OtorgarCertificado(csr, public_key_solicitante)
        except Exception as e:
            print(f"Error al verificar la firma de la CSR: {e}")
            print("Detalles de la CSR:")
            print(csr)
            print("Detalles de la clave pública del solicitante:")
            print(public_key_solicitante)
            return None

    def OtorgarCertificado(self, csr, public_key_solicitante):
        certificate = x509.CertificateBuilder().subject_name(
            csr.subject
        ).issuer_name(
            self.name
        ).public_key(
            public_key_solicitante
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.datetime.utcnow()
        ).not_valid_after(
            datetime.datetime.utcnow() + datetime.timedelta(days=730)
        ).add_extension(
            x509.SubjectAlternativeName([x509.DNSName(u"localhost")]),
            critical=False,
        # Firmamos el certificado con la clave privada de la Autoridad de Certificación
        ).sign(self.__private_key, hashes.SHA256(), default_backend())
        
        return certificate
    
    def GenerarACRaiz(self):
        key = self.__private_key
        subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "ES"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Madrid"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, "Colmenarejo"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Hailo"),
        x509.NameAttribute(NameOID.COMMON_NAME, "hailo.com"),
        ])
        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
             key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.datetime.now(datetime.timezone.utc)
        ).not_valid_after(
            datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=730)
        ).add_extension(
            x509.SubjectAlternativeName([x509.DNSName("localhost")]),
            critical=False,
        ).sign(key, hashes.SHA256())

        with open(os.path.dirname(__file__) + "/certificado.pem", "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
        return cert
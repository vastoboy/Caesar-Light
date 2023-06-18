#Created by Xand

#Disclaimer: This reverse shell should only be used in the lawful, remote administration of authorized systems. Accessing a computer network without authorization or permission is illegal.


from caesar import Caesar
import os


art = """
          /$$$$$$
         /$$__  $$
        | $$  \__/  /$$$$$$   /$$$$$$   /$$$$$$$  /$$$$$$   /$$$$$$
        | $$       |____  $$ /$$__  $$ /$$_____/ |____  $$ /$$__  $$
        | $$        /$$$$$$$| $$$$$$$$|  $$$$$$   /$$$$$$$| $$  \__/
        | $$    $$ /$$__  $$| $$_____/ \____  $$ /$$__  $$| $$
        |  $$$$$$/|  $$$$$$$|  $$$$$$$ /$$$$$$$/|  $$$$$$$| $$
         \______/  \_______/ \_______/|_______/  \_______/|__/
"""



print(art)



cr = Caesar("IP-Address", 5000, "ES-INDEX", "http://localhost:9200")

if not os.path.exists("ClientFolder"):
    os.mkdir("ClientFolder")

cr.show_commands()
cr.start()


#Created by Vasto Boy

#Disclaimer: This reverse shell should only be used in the lawful, remote administration of authorized systems. Accessing a computer network without authorization or permission is illegal.

import os
from caesar import Caesar


art = """
     ██████╗ █████╗ ███████╗███████╗ █████╗ ██████╗     ██╗     ██╗ ██████╗ ██╗  ██╗████████╗
    ██╔════╝██╔══██╗██╔════╝██╔════╝██╔══██╗██╔══██╗    ██║     ██║██╔════╝ ██║  ██║╚══██╔══╝
    ██║     ███████║█████╗  ███████╗███████║██████╔╝    ██║     ██║██║  ███╗███████║   ██║   
    ██║     ██╔══██║██╔══╝  ╚════██║██╔══██║██╔══██╗    ██║     ██║██║   ██║██╔══██║   ██║   
    ╚██████╗██║  ██║███████╗███████║██║  ██║██║  ██║    ███████╗██║╚██████╔╝██║  ██║   ██║   
     ╚═════╝╚═╝  ╚═╝╚══════╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝    ╚══════╝╚═╝ ╚═════╝ ╚═╝  ╚═╝   ╚═╝   
"""


print(art)

client_folder_name = "ClientFolder"
cr = Caesar("IP-ADDRESS", 5000, "caesar-index", "http://localhost:9200", client_folder_name)

if not os.path.exists(client_folder_name):
    os.mkdir(client_folder_name)

cr.show_commands()
cr.start()


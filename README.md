# Caesar Light Reverse Shell

<img src="https://img.shields.io/badge/Python-FFD43B?style=for-the-badge&logo=python&logoColor=blue" alt="Python"> <img src="https://img.shields.io/badge/Elastic_Search-005571?style=for-the-badge&logo=elasticsearch&logoColor=white" alt="Elasticsearch"> <img src="https://img.shields.io/badge/Linux-FCC624?style=for-the-badge&logo=linux&logoColor=black" alt="Linux"><img src="https://img.shields.io/badge/Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white" alt="Windows"><img src="https://img.shields.io/badge/VirtualBox-21416b?style=for-the-badge&logo=VirtualBox&logoColor=white" alt="Virtualbox">


This project presents Caesar-Light, a simple Python TCP reverse shell designed to manage multiple client connections simultaneously. Caesar-Light is integrated with Elasticsearch to store target information, allowing for easy retrieval and analysis of data collected from connected targets. Additionally, images and audio files collected from connected clients will be stored in individual client folders named using their client ID.

Caesar-Light consists of a client-server program. The server component should be run on a Linux system, while the client component should be run on a Windows system. To set up the server component, Elasticsearch should be installed and configured on the Linux system. An index should be created in Elasticsearch specifically for the server program, allowing it to store target information retrieved from connected clients. Once Elasticsearch is set up and the index is created, the server program can be executed, allowing it to listen for incoming connections from client devices.

Caesar-Light serves as a prototype and is strictly intended for educational purposes only. The application facilitates a basic but effective demonstration of how reverse shell connections can be established and controlled remotely. While Python may not be the ideal choice for advanced malware development due to its limitations, this project provides a foundational understanding of how such malicious software operates.


## Setup Elasticsearch
* Before using Packet-Sniffer, ensure that you have Elasticsearch installed and configured. Elasticsearch is used for storing and indexing captured packet data. Follow these steps to set up Elasticsearch:

* Install Elasticsearch: Download and install Elasticsearch from the official Elasticsearch website.

* Start Elasticsearch: Start the Elasticsearch service using the appropriate method for your operating system. Refer to the Elasticsearch documentation for detailed instructions on how to start the service.

* Configure Elasticsearch: Optionally, configure Elasticsearch settings such as cluster name, node settings, network host, etc., as per your requirements. Refer to the Elasticsearch documentation for guidance on configuration options.

* Verify Elasticsearch Setup: Confirm that Elasticsearch is running and accessible by visiting http://localhost:9200 in your web browser. You should see a JSON response indicating the Elasticsearch cluster status.

* Create Elasticsearch Index: Create an index in Elasticsearch to store the captured packet data. You can use the Elasticsearch API or tools like Kibana to create the index with the desired settings and mappings.

* Once Elasticsearch is set up and configured, you can start using Packet-Sniffer to capture and analyze network packets, with the captured data being stored in Elasticsearch for further analysis and visualization.


## Example

### Reverse Shell Diagram
![Picture3](https://github.com/8itwise/Caesar-Reverse-Shell/assets/18365258/01fbe7d9-9871-4f1c-8c1c-71bd657fd40a)



### Clients
Display previously connected clients and clients with an active connection to the server\
![Picture5](https://github.com/8itwise/Caesar-Reverse-Shell/assets/18365258/78420df0-11b1-4671-8dcb-87f66ae29ed4)



### Reverse Shell
Get a reverse shell and interact with the tartget's machine
![Picture6](https://github.com/8itwise/Caesar-Reverse-Shell/assets/18365258/1f4e3bd2-05fd-4fd0-a6d8-7f1d9160c147)




## Features

```

            Caesar Commands
                 'guide': ['Display Caesar's user commands']
                 'clients':['lists clients within ES index']
                 'connected':['lists all active connection within ES index']
                 'shell (target ES Client_ID)':['selects a target and creates a session between the server and the client machine']
                 'delete (target ES Client_ID)': ['remove specified document from index']
                 'delete all': ['remove all document from index']
                 'get (target ES Client_ID)': ['retrieves indexed data of specified target']
                 'show fields (target ES Client_ID)': ['displays existing field for specified target']
                 'field (target ES Client_ID) (FIELD NAME):  ['displays specified field']

            Client Commands                                                
                'quit':['quits the session and takes user back to Caesar ES interface']           
                'get (filename or path)':['Receieve specified file from target client']
                'send (filename or absolute path)':['send specified file to the target client']      
                'screenshot':['takes a screen shot of the client machine']
                'camshot':['captures an image from the client's webcam']  
                'camfeed': ['live feed from target's webcam']
                'screenfeed': ['live feed from target's screen']
                'audiofeed': ['live audio feed from target's microphone']
                'encrypt (PASSWORD) (FILENAME)': ['encrypts specified file']            
                'decrypt (PASSWORD)(FILENAME)': ['decrypts specified file']   
                'reboot' : ['reboot client system']
                'shutdown' : ['shutdown client system']


```

## Installation

Caesar Reverse Shell requires Python 3 and certain dependencies. Use pip to install the required packages:

```
pip install -r requirements.txt

```

## Disclaimer

This code is intended for educational and informational purposes only. Use it responsibly and ensure compliance with applicable laws and regulations. Respect the privacy and security of others.  
The author of this code assume no liability and is not responsible for misuses or damages caused by any code contained in this repository in any event that, accidentally or otherwise, it comes to be utilized by a threat agent or unauthorized entity as a means to compromise the security, privacy, confidentiality, integrity, and/or availability of systems and their associated resources. In this context the term "compromise" is henceforth understood as the leverage of exploitation of known or unknown vulnerabilities present in said systems, including, but not limited to, the implementation of security controls, human or electronically-enabled.
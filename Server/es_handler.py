import json
from prettytable import PrettyTable
from elasticsearch import Elasticsearch



class EsHandler:


        def __init__(self, db_name, es_url):
            self.pt = PrettyTable()
            self.db_name = db_name
            self.es = Elasticsearch(es_url)



        # saves first portion of client file in index
        def store_client_information(self, ip, conn, client_info):
                client_info = json.loads(client_info)
                ip = {"ip": "".join(ip)}
                client_info_dict = ip.copy() # prepend ip to the start of the dictionary
                client_info_dict.update(client_info)

                try:
                    # store client info in elastic search
                    resp = self.es.index(index=self.db_name, document=client_info_dict)
                    return {resp['_id']: conn} # update dictionary with document id and socket object
                except Exception as e:
                    print("[+]Unable to store data!!!")
                    print(e)



        # update specified es document
        def append_information(self, dictKey, client_info, client_id):
                doc = { dictKey: client_info }

                try: 
                    resp= self.es.update(index=self.db_name, id=client_id, doc=doc)
                except Exception as e:
                    print("[+]Unable to store data!!!")
                    print(e)



        # display all clients with active connections
        def get_connected_client(self, socket_object_dict):
            self.pt.field_names = ["Client ID", "IP Address", "Mac Address", "OS", "Node Name", "Release", "Version", "Machine", "Date-Joined", "Time-Joined", "User"]
            for client_id, socket_obj in socket_object_dict.items():
                 try:
                    # check for active socket connection
                    socket_obj.send("conn check".encode())
                    resp = self.es.get(index=self.db_name, id=client_id)
                    self.pt.add_row([
                                 resp["_id"],
                                 resp["_source"].get("ip"),
                                 resp["_source"].get("mac-address"),
                                 resp["_source"].get("os"),
                                 resp["_source"].get("node-name"),
                                 resp["_source"].get("release"),
                                 resp["_source"].get("version"),
                                 resp["_source"].get("machine"),
                                 resp["_source"].get("date-joined"),
                                 resp["_source"].get("time-joined"),
                                 resp["_source"].get("user")
                                 ])
                    print(self.pt)

                 except Exception as e:
                    print("[-]No active connections!!!")

            self.pt.clear()



        # deletes all documents in specified index
        def delete_all_docs(self):
            try:
                self.es.delete_by_query(index=self.db_name, body={"query": {"match_all": {}}})
                print("[+]Documents deleted sucessfully!!!")
            except Exception as e:
                print(e)
                print("[+]Unable delete documents")



        # retrieve client information documents from elastic search
        def retrieve_client_information(self):
            resp = self.es.search(index=self.db_name, size=100, query={"match_all": {}})
            self.tabulate_data(resp)



        # tabulate es date using prettytable
        def tabulate_data(self, resp):
            for hit in resp['hits']['hits']:
                self.pt.field_names = ["Client ID", "IP Address", "Mac Address", "OS", "Node Name", "Release", "Version", "Machine", "Date-Joined", "Time-Joined", "User"]
                self.pt.add_row([
                             hit["_id"],
                             hit["_source"].get("ip"),
                             hit["_source"].get("mac-address"),
                             hit["_source"].get("os"),
                             hit["_source"].get("node-name"),
                             hit["_source"].get("release"),
                             hit["_source"].get("version"),
                             hit["_source"].get("machine"),
                             hit["_source"].get("date-joined"),
                             hit["_source"].get("time-joined"),
                             hit["_source"].get("user")
                             ])

            print(self.pt)
            self.pt.clear()



        # retrieves document from index
        def retrieve_client_document(self, client_id):
            try:
                resp = self.es.get(index=self.db_name, id=client_id)
                print(json.dumps(resp['_source'], indent=4))
            except Exception as e:
                print(e)
                print("[-]Document does not exist!!!")



        # checks if connected client is present in index
        def is_conn_present(self, mac_address):
            try:
                resp = self.es.search(index=self.db_name,  query={"match": {"mac-address": mac_address}})
                if (resp['hits']['total']['value'] > 0):
                    return True
                else:
                    return False
            except Exception as e:
                print(e)
                print("[-]Document does not exist!!!")



        # updates existing client document using client mac address as identifier
        def update_document(self, mac_address, client_ip, client_info):
            client_id = str()

            client_info = json.loads(client_info)
            ip = {"ip": "".join(client_ip)}
            client_info_dict = ip.copy() # prepend ip to the start of the dictionary
            client_info_dict.update(client_info)

            try:
                resp = self.es.search(index=self.db_name,  query={"match": {"mac-address": mac_address}})

                for hit in resp['hits']['hits']: # get client ID
                    client_id = (hit["_id"])

                resp = self.es.update(index=self.db_name, id=client_id, doc=client_info_dict)
                return client_id

            except Exception as e:
                print(e)
                print("[-]Document does not exist!!! \n")



        # deletes client document from index
        def delete_client_document(self, client_id):
            try:
                self.es.delete(index=self.db_name, id=client_id)
                print("[+]Document deleted sucessfully!!! \n")
            except:
                print("[-]Document does not exist!!! \n")




        # retrieves the specified feilds in a document
        def show_fields(self, client_id):
            try:
                resp = self.es.get(index=self.db_name, id=client_id)
                
                self.pt.field_names = ["Client Fields"]

                for field in resp["_source"].keys():
                    self.pt.add_row([field])
               
                print(self.pt)
                self.pt.clear()

            except Exception as e:
                print("[-]Document does not exist!!! /n")




        # retrieves the specified feilds in a document
        def get_field(self, client_id, feild_parameter):
            try:
                resp = self.es.get(index=self.db_name, id=client_id)
                resp = resp['_source'].get(feild_parameter)

                if resp == "null":
                    print("[-]Field does not exist")
                else:
                    print(json.dumps(resp, indent=4))
            except:
                print("[-]Field does not exist")



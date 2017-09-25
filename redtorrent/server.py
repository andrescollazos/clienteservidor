import os
import sys
import zmq
import json
import base64

MY_DIR = "tcp://*:" + sys.argv[1]

def loadFiles(path):
    files = {}
    dataDir = os.fsencode(path)
    for file in os.listdir(dataDir):
        filename = os.fsdecode(file)
        print("Loading {}".format(filename))
        files[filename] = file
    return files


def main():
    try:
        folder = sys.argv[2]
        print("Serving files from {}".format(folder))
        files = loadFiles(folder)
        print("Load info on {} files.".format(len(files)))
    except:
        print("[Server]: ¡Error! No se encontro directorio, cree uno (serverN/)")
        return -1
    # Create the socket and the context
    context = zmq.Context()
    c = context.socket(zmq.REQ)
    c.connect("tcp://localhost:5555") # Direccion del tracker
    tracker_msg = {"tipe": "server", "dir": "tcp://localhost:" + sys.argv[1]}
    c.send_json(tracker_msg)
    resp = c.recv_json()

    if resp["rsp"] == "ACK":
        s = context.socket(zmq.REP)
        s.bind(MY_DIR)

        while True:
            msg = s.recv_json()

            if msg['tipe'] == "up":
                filename = folder + "/" + msg["filename"] + ".part"

                with open(filename, "wb") as output:
                    print("[Server]: Recibiendo parte ", msg["filename"])
                    fstring = msg['file']
                    fbytes = base64.b64decode(fstring)

                    output.write(fbytes)

                s.send_json("ACK")
            elif msg['tipe'] == "download":
                filename = folder + "/" + msg["filename"] + ".part"
                with open(filename, 'rb') as f:
                    byte_content = f.read()
                    print("[Server]: Enviando parte, size: ", len(byte_content))
                    base64_bytes = base64.b64encode(byte_content)
                    base64_string = base64_bytes.decode('utf-8')

                    raw_data = {'file': base64_string, 'filename': msg["filename"]}
                    s.send_json(raw_data)

    else:
        print("NO FUE POSIBLE CONECTAR CON TRACKER")

if __name__ == '__main__':
    main()

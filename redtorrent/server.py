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
    folder = sys.argv[2]
    print("Serving files from {}".format(folder))
    files = loadFiles(folder)
    print("Load info on {} files.".format(len(files)))

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
    else:
        print("NO FUE POSIBLE CONECTAR CON TRACKER")

if __name__ == '__main__':
    main()

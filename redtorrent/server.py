import os
import sys
import zmq
import json
import base64
import hashlib

MY_DIR = "tcp://*:" + sys.argv[1]
IP = "tcp://localhost:"+ sys.argv[1]

def loadFiles(path):
    files = {}
    dataDir = os.fsencode(path)
    for file in os.listdir(dataDir):
        filename = os.fsdecode(file)
        print("Loading {}".format(filename))
        files[filename] = file
    return files

class Node():
    def __init__(self, ip):
        self.ip = ip
        # Calcular sha256 de la ip:
        sha_ip = hashlib.sha256()
        sha_ip.update((ip.encode()))
        self.id = sha_ip.hexdigest()
        self.ht = {}
        self.sig = -1
        self.sig_id = -1
        self.ant = -1
        self.ant_id = -1


def main():
    try:
        folder = sys.argv[2]
        print("Serving files from {}".format(folder))
        files = loadFiles(folder)
        print("Load info on {} files.".format(len(files)))
    except:
        pass
        #print("[Server]: ¡Error! No se encontro directorio, cree uno (serverN/)")
        #return -1

    # Create the socket and the context
    node = Node(IP)
    print("ID: ", node.id)
    context = zmq.Context()
    #c = context.socket(zmq.REQ)
    #c.connect("tcp://localhost:5555") # Direccion del tracker
    #tracker_msg = {"tipe": "server", "dir": "tcp://localhost:" + sys.argv[1]}
    #c.send_json(tracker_msg)
    #resp = c.recv_json()

    #if resp["rsp"] == "ACK":
    s = context.socket(zmq.REP)
    s.bind(MY_DIR)

    # Conectarse a un servidor, cuando no se ingresa este campo, quiere decir que
    # es el primer nodo
    try:
        node_dir = "tcp://localhost:" + sys.argv[3]
        c = context.socket(zmq.REQ)
        c.connect(node_dir)

        c_msg = {"tipe": "join", "id": node.id, "dir": node.ip}
        #print("Enviare mensaje tipo JOIN")
        c.send_json(c_msg)

        resp = c.recv_json()

        node.sig = resp["sig"]
        node.sig_id = resp["sig_id"]
        node.ant = resp["ant"]
        node.ant_id = resp["ant_id"]

    except:
        print("[¡PRIMER SERVIDOR EN CONECTARSE!]")


    while True:
        print("ESPERANDO MENSAJES")
        print("Sig = ", node.sig, "Ant = ", node.ant)
        msg = s.recv_json()

        # Mensaje tipo join, indica que un nodo se quiere conectar
        if msg['tipe'] == "join":
            # En caso de que no se tenga ninguna conexion:
            if (node.sig == -1 and node.ant == -1):
                node.sig = msg["dir"]
                node.sig_id = msg["id"]
                node.ant = msg["dir"]
                node.ant_id = msg["id"]
                raw_send = {'sig': node.ip, 'ant': node.ip, 'sig_id': node.id, 'ant_id': node.id}

                s.send_json(raw_send)
            elif msg["id"] > node.id and msg["id"] < node.sig_id:
                # Avisar al siguiente que su nuevo predecesor es nodo que intenta entrar
                n = context.socket(zmq.REQ)
                n.connect(node.sig)

                n_msg = {'tipe': "c_ant", "id": msg["id"], "dir": msg["dir"]}
                n.send_json(n_msg)
                resp = n.recv_json()

                raw_send = {"sig": node.sig, "ant": node.ip, "sig_id": node.sig_id, "ant_id": node.id}
                node.sig = msg["dir"]
                node.sig_id = msg["id"]
                s.send_json(raw_send)
            # Quiere decir que es el primero del anillo
            elif node.ant_id > node.id:
                # Verificar si el nodo que desea ingresar el mayor al ultimo
                if msg["id"] > node.ant_id:
                    # Avisar al predecesor que su nuevo sucesor es el nodo que intenta entrar
                    n = context.socket(zmq.REQ)
                    n.connect(node.ant)

                    n_msg = {"tipe": "c_sig", "id": msg["id"], "dir": msg["dir"]}
                    n.send_json(n_msg)
                    resp = n.recv_json()
                    #c.close()

                    # Enviar al nodo que desear conectarse la informacion necesaria
                    raw_send = {"sig": node.ip, 'ant':node.ant, 'sig_id': node.id, 'ant_id': node.ant_id}
                    node.ant = msg["dir"]
                    node.ant_id = msg["id"]
                    s.send_json(raw_send)

            #elif msg["id"] > node.id and msg["id"] < node.sig_id:
            #else:
            #    pass

        elif msg['tipe'] == "c_sig":
            node.sig = msg["dir"]
            node.sig_id = msg["id"]
            s.send_json("OK")

        elif msg['tipe'] == 'c_ant':
            node.ant = msg["dir"]
            node.ant_id = msg["id"]
            s.send_json("OK")

        elif msg['tipe'] == "up":
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

    #else:
    #    print("NO FUE POSIBLE CONECTAR CON TRACKER")

if __name__ == '__main__':
    main()

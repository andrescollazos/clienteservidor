import os
import sys
import zmq
import json
import base64
import hashlib
import time

MY_DIR = "tcp://*:" + sys.argv[1]
IP = "tcp://localhost:"+ sys.argv[1]

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
        self.sharing = False

    def star_connection(self, context, ip):
        node_dir = ip #"tcp://localhost:" + sys.argv[3]
        print("Estableciendo conexion a: ", ip)
        c = context.socket(zmq.REQ)
        c.connect(node_dir)
        c_msg = {"tipe": "join", "id": self.id, "dir": self.ip}
        c.send_json(c_msg)

        resp = c.recv_json()

        if ('sig' in resp) and ('ant' in resp):
            self.sig = resp["sig"]
            self.sig_id = resp["sig_id"]
            self.ant = resp["ant"]
            self.ant_id = resp["ant_id"]
        elif resp == "occupied":
            print("NO SE PUEDE ESTABLECER CONEXION, REITENTANDO EN 1 seg...")
            time.sleep(1)
            self.star_connection(context, ip)

    # Metodo para saber si corresponde o no al nodo atender al cliente
    def corresponds(self, msg):
        # Verificar si es el primer nodo: ( Ni < Nanti) Ni -> Nodo Actual, Nanti -> Nodo predecesor del actual
        if (self.id < self.ant_id) and (msg['filename'] > self.ant_id or msg['filename'] < self.id):
            return True
        elif msg['filename'] > self.ant_id and msg['filename'] < self.id:
            return True
        else:
            return False

    def loadFiles(self, path):
        files = {}
        dataDir = os.fsencode(path)
        for file in os.listdir(dataDir):
            filename = os.fsdecode(file)
            print("Loading {}".format(filename))
            self.ht.update({filename.split(".")[0]: path + "/" + filename})
        #print("HT: ", self.ht, "\n\n")

    # Metodo para enviar un mensaje a todos los nodos avisando de algun evento especial
    # Para que los demás nodo no reciban conexiones tipo join
    def broadcast(self, context, init, msg):
        n = context.socket(zmq.REQ)
        n.connect(self.sig)

        n_msg = {'tipe': "broadcast", "init": init, "msg": msg}
        n.send_json(n_msg)
        r = n.recv_json()

def main():
    # Create the socket and the context
    node = Node(IP)
    print("ID: ", node.id[:4], "...")

    folder = sys.argv[2]
    node.loadFiles(folder)

    context = zmq.Context()
    s = context.socket(zmq.REP)
    s.bind(MY_DIR)

    # Conectarse a un servidor, cuando no se ingresa este campo, quiere decir que
    # es el primer nodo
    try:
        node_dir = "tcp://localhost:" + sys.argv[3]
        node.star_connection(context, node_dir)

    except:
        print("[¡PRIMER SERVIDOR EN CONECTARSE!]")


    while True:
        print("ESPERANDO MENSAJES")
        try:
            print("Sig = ", node.sig_id[:4], "...", "Ant = ", node.ant_id[:4], "...")
        except:
            print("No hay mas nodo conectados!")
        msg = s.recv_json()

        print("---------------------------")
        print("ID: ", node.id[:4], "...")
        print("MENSAJE RECIBIDO: \n\t", "Tipo: ", msg['tipe'])
        print("HT: ")
        for i, key in enumerate(node.ht):
            print(i, ":", node.ht[key].split("/")[1][:5], "...")
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
            elif not node.sharing:
                if msg["id"] > node.id and msg["id"] < node.sig_id:
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
                elif node.ant_id > node.id and msg["id"] > node.ant_id: # Verificar si el nodo que desea ingresar el mayor al ultimo
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
                else:
                    # Preguntar al sucesor si le corresponde atender al nodo entrante:
                    n = context.socket(zmq.REQ)
                    n.connect(node.sig)
                    n_msg = {"tipe": "join", "id": msg["id"], "dir": msg["dir"]}
                    n.send_json(n_msg)
                    resp = n.recv_json()

                    raw_send = {"sig": resp["sig"], "ant": resp["ant"], "sig_id": resp["sig_id"], "ant_id": resp["ant_id"]}
                    s.send_json(raw_send)
            else:
                print("No puedo recibir conexiones, estoy recibiendo archivos")
                s.send_json("occupied")

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

        elif msg['tipe'] == 'up':
            # Verificar si me corresponde atender al cliente
            if 'n_part' in msg:
                if msg['n_part'] == 'init':
                    #print("EMPIEZA A COMPARTIR PARTES")
                    node.sharing = True
                    node.broadcast(context, node.id, "share-init")

            correspond = node.corresponds(msg)

            if correspond:
                #print("Me corresponde a mi: ")
                if msg['tipe_file'] == "index":
                    data = {"file": msg['filename'], "parts": msg['parts'], "name": msg["name"]}
                    json_data = json.dumps(data, indent=2)
                    file_name = folder + '/' + msg['filename']+".json"

                    with open(file_name, 'w') as output:
                        output.write(json_data)
                        node.ht.update({msg["filename"]: file_name})

                    raw_send = {'resp': "ack", 'tipe_a': 'index', 'dir': IP}
                    s.send_json(raw_send)
                else:
                    raw_send = {'resp': 'ok', 'tipe_a': 'part', 'dir': IP}
                    s.send_json(raw_send)
            else:
                #print("No me corresponde a mi: ")

                su = context.socket(zmq.REQ)
                su.connect(node.sig)
                if msg["tipe_file"] == "index":
                    send = {'tipe': 'up', 'tipe_file': "index", 'filename': msg['filename'], 'parts': msg['parts'], 'name': msg['name']}
                elif msg["tipe_file"] == 'part':
                    send = {'tipe': 'up', 'tipe_file': 'part', 'filename': msg['filename']}
                su.send_json(send)
                resp = su.recv_json()

                raw_send = {'resp': resp["resp"], 'tipe_a': resp["tipe_a"], 'dir': resp["dir"]}
                s.send_json(raw_send)

        elif msg['tipe'] == 'up-a':
            filename = folder + "/" + msg['filename'] + ".part"

            with open(filename, "wb") as output:
                print("[Server]: Recibiendo parte") #, msg["filename"])
                fstring = msg['file']
                fbytes = base64.b64decode(fstring)
                output.write(fbytes)

                # Almacenar dato el HT:
                node.ht.update({msg["filename"]: filename})
            s.send_json("ACK")
            if 'n_part' in msg:
                if msg['n_part'] == 'finish':
                    print("YA RECIBI TODAS LAS PARTES")
                    node.sharing = False
                    node.broadcast(context, node.id, 'share-finish')

        elif msg['tipe'] == "download":

            if 'n_part' in msg:
                if msg['n_part'] == 'init':
                    #print("EMPIEZA A COMPARTIR PARTES")
                    node.sharing = True
                    node.broadcast(context, node.id, "share-init")
            # Verificar si me corresponde atender al cliente
            correspond = False

            print(node.ht)
            print("Lo tengo?", msg['filename'] in node.ht)
            if msg['filename'] in node.ht:
                if msg['tipe_file'] == 'index':
                    with open(node.ht[msg['filename']], "r") as input_j:
                        json_data = json.load(input_j)
                        s.send_json(json_data)
                else:
                    raw_send = {'resp-d': 'ok', 'dir': IP}
                    s.send_json(raw_send)
            else:
                # Si no corresponde al nodo antenderlo pregunta al sucesor
                su = context.socket(zmq.REQ)
                su.connect(node.sig)
                if msg["tipe_file"] == "index":
                    send = {'tipe': 'download', 'tipe_file': 'index', 'filename': msg['filename']}
                elif msg["tipe_file"] == 'part':
                    send = {'tipe': 'download', 'tipe_file': 'part', 'filename': msg['filename']}
                su.send_json(send)
                resp = su.recv_json()

                #raw_send = {'resp-d': resp["resp"], 'dir': resp["dir"]}
                s.send_json(resp)

        elif msg['tipe'] == 'down-a':
            with open(node.ht[msg['filename']], 'rb') as f:
                byte_content = f.read()
                print("[Server]: Enviando parte, size: ", len(byte_content))
                base64_bytes = base64.b64encode(byte_content)
                base64_string = base64_bytes.decode('utf-8')

                raw_data = {'file': base64_string, 'filename': msg["filename"]}
                s.send_json(raw_data)
                if 'n_part' in msg:
                    if msg['n_part'] == 'finish':
                        #print("YA RECIBI TODAS LAS PARTES")
                        node.sharing = False
                        node.broadcast(context, node.id, 'share-finish')

        elif msg['tipe'] == 'broadcast':
            if not(msg['init'] == node.id):
                if msg['msg'] == 'share-init':
                    node.sharing = True
                    s.send_json("Ok")
                    node.broadcast(context, msg['init'], msg['msg'])
                elif msg['msg'] == 'share-finish':
                    node.sharing = False
                    s.send_json("Ok")
                    node.broadcast(context, msg['init'], msg['msg'])
            else:
                s.send_json("Ok")
    #else:
    #    print("NO FUE POSIBLE CONECTAR CON TRACKER")

if __name__ == '__main__':
    main()

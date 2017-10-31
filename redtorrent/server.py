import os
import sys
import zmq
import json
import base64
import hashlib
import time         # Funcion sleep
import threading    # Trabajo con hilos

MY_DIR = "tcp://*:" + sys.argv[1]
IP = "tcp://localhost:"+ sys.argv[1]

# Clase para el manejo de la información de un nodo
class Node():
    # Metodo de inicializacion
    def __init__(self, ip):
        self.ip = ip
        # Calcular sha256 de la ip: Calcular el token correspondiente
        sha_ip = hashlib.sha256()
        sha_ip.update((ip.encode()))
        self.id = sha_ip.hexdigest()
        self.ht = {}            # Porción de la DHT
        self.sig = -1           # Direccion IP del nodo sucesor o siguiente
        self.sig_id = -1        # Token del nodo sucesor o siguiente
        self.ant = -1           # Direccion IP del nodo predecesor o anterior
        self.ant_id = -1        # Token del nodo predecesor o anterior
        self.folder = 0         # Directorio para almacenar los archivos
        self.sharing = False    # Para conocer si esta compartiendo archivos (Sirve para controlar ingreso)
        self.transfer = False   # Para indicar que puede empezar a transferir archivos de un nodo a este
        self.hresp = False      # Conocer si el nodo ya le dio respuesta (Si ya transfirio los archivos)
        self.first = False      # Para saber si el nodo es el primero o no

    # Con este metodo se inicia la conexion de un nodo entrante a un nodo que este en la red
    def star_connection(self, context, ip):
        node_dir = ip #"tcp://localhost:" + sys.argv[3]
        print("Estableciendo conexion a: ", ip)
        c = context.socket(zmq.REQ)
        c.connect(node_dir)
        c_msg = {"tipe": "join", "id": self.id, "dir": self.ip}
        c.send_json(c_msg)

        # El nodo que antiende al entrante responde la solicitud con un mensaje
        # indicandole cual será su nodo predecesor y su nodo sucesor
        resp = c.recv_json()

        if ('sig' in resp) and ('ant' in resp):
            print(">> Asignados nodos siguiente y anterior: ")
            print(">>\tSig: ", resp["sig"])
            print(">>\tAnt: ", resp["ant"])

            # Cambiar nodo sucesor y nodo predecesor
            self.sig = resp["sig"]
            self.sig_id = resp["sig_id"]
            self.ant = resp["ant"]
            self.ant_id = resp["ant_id"]

            # Solicitar archivos que hace parte de la HT del nodo.
            print(">> Solicitar transferencia de archivos")
            # Cuando la variable transfer se pone en verdadero, el hilo principal
            # empezará a enviar solicitudes para que le transfieran los archivos que
            # le corresponden. Es necesario que se intente en repetidas ocasiones
            # ya que al iniciar un nodo, por la recursividad se envian multiples mensajes
            # y puede que un nodo en un momento dado este a penas respondiendo y cuando
            # se le pida transferir los archivos estará ocupado y no podrá antender
            self.transfer = True


        elif resp == "occupied":
            print("NO SE PUEDE ESTABLECER CONEXION, REITENTANDO EN 1 seg...")
            time.sleep(1)
            self.star_connection(context, ip)

    # Metodo para saber si corresponde o no al nodo atender al cliente
    def corresponds(self, msg):
        # El primer nodo hace referencia al nodo con un token lexicograficamente menor al resto
        # Este caso es especial ya que es el unico nodo de la red que su predecesor es mayor
        # Verificar si es el primer nodo: ( Ni < Nanti) Ni -> Nodo Actual, Nanti -> Nodo predecesor del actual
        if (self.id < self.ant_id) and (msg['filename'] > self.ant_id or msg['filename'] < self.id):
            return True
        elif msg['filename'] > self.ant_id and msg['filename'] < self.id:
            return True
        else:
            return False

    # Metodo para cargar en la porcion de HT los archivos que esten en carpeta
    # Este metodo se usa al iniciar, ya que puede que se retire de la red el no, pero solo
    # momentaneamente mientras se recupera de algun fallo
    def loadFiles(self):
        files = {}
        dataDir = os.fsencode(self.folder)
        for file in os.listdir(dataDir):
            filename = os.fsdecode(file)
            print("Loading {}".format(filename))
            self.ht.update({filename.split(".")[0]: self.folder + "/" + filename})

    # Metodo para enviar un mensaje a todos los nodos avisando de algun evento especial
    # Para que los demás nodo no reciban conexiones tipo join
    def broadcast(self, context, init, msg):
        n = context.socket(zmq.REQ)
        # El nodo avisar unicamente a su sucesor
        n.connect(self.sig)

        # Su sucesor replicara el mensaje
        n_msg = {'tipe': "broadcast", "init": init, "msg": msg}
        n.send_json(n_msg)
        r = n.recv_json() # La respuesta es un simple OK
        # Pero debe haber respuesta ya que es un sistema peticion-respuesta

# Esta funcion le permite a un nodo en un contexto, pedirle a su sucesor o antecesor
# que le transferiera los archivos que le lexicograficamente le corresponden al nodo.
def Ntransfer(node, context):
    # Para una red con solo dos nodos, es decir una que apenas comienza, no necesita
    # transferir archivos. Ya que un nodo solo no puede atender a un cliente
    if not(node.ant_id == node.sig_id):
        # El caso de que se trate del primer nodo (El lexicograficamente menor a todos los demás)
        if node.ant_id > node.id:
            # Se informa al resto de nodos que no admitan mensajes tipo join, mientras se da el
            # el proceso de transferencia para evitar inconsistencias
            node.broadcast(context, node.id, 'share-init')

            # Ya que se trate del nodo menor, quiere decir que le corresponden
            # tanto los archivos mayores al ultimo nodo, como los
            # los archivos menores al token de él.
            c = context.socket(zmq.REQ)
            c.connect(node.sig)

            # Solicitar al nodo sucesor que le entrege los archivos menores al token del nodo.
            c_msg = {'tipe': 'transfer', 'id': node.id, 'which': 'minors'}
            print(">> Solicitando archivos a: ", node.sig)
            c.send_json(c_msg)
            print(">> Esperando respuesta")
            # La respuesta es un diccionario con los tokens de las partes y con el nombre con que
            # son almacenados, este nombre es el mismo token pero con la extensión del achivo (.part o .json)
            resp = c.recv_json()
            print(">>\tRespuesta recibida: ", resp)

            tam = len(resp)
            for i, value in enumerate(resp):
                with open(node.folder + "/" + resp[value], 'wb') as f:
                    # Enviar mensaje tipo 'down-a', es decir de descarga aprobada,
                    # Al mensaje se agrega la llave 'eliminate' ya que se quiere que al
                    # transferir el archivo, se borre de donde este.
                    send = {'tipe': 'down-a', 'filename': value, 'eliminate': 1}
                    c.send_json(send)
                    # r es la respuesta con los bytes que conformar la parte del archivo
                    r = c.recv_json()
                    # Se agrega a la HT
                    node.ht.update({value: node.folder + "/" + resp[value]})
                    fstring = r['file']
                    fbytes = base64.b64decode(fstring)
                    f.write(fbytes)

            # Solicitar al nodo predecesor que envie las partes mayores que el
            c = context.socket(zmq.REQ)
            c.connect(node.ant)
            c_msg = {'tipe': 'transfer', 'id': node.id, 'which': 'greater'}
            print(">> Solicitando archivos a: ", node.ant)
            c.send_json(c_msg)
            print(">> Esperando respuesta")
            resp = c.recv_json()
            print(">>\tRespuesta recibida: ", resp)
            # Pedir las partes:
            for i, value in enumerate(resp):
                with open(node.folder + "/" + resp[value], 'wb') as f:
                    send = {'tipe': 'down-a', 'filename': value, 'eliminate': 1}
                    c.send_json(send)
                    r = c.recv_json()
                    node.ht.update({value: node.folder + "/" + resp[value]})
                    fstring = r['file']
                    fbytes = base64.b64decode(fstring)
                    f.write(fbytes)

            # Cuando se termina el proceso, es decir cuando obtiene una respuesta
            # El hilo principal que es el que controla la transferencia, puede parar el control
            node.hresp = True

            # Informar al resto de nodos que el proceso de transferencia acabo y por tanto
            # pueden recibir nuevas solicitudes tipo join
            node.broadcast(context, node.id, 'share-finish')
            #node.transfer = False
        else:
            # Esta es la opcion en el resto de casos, donde siempre se deberá cumplir que
            # Nh < Ni < Nj, donde Ni es el nodo que ingreso a la red.
            node.broadcast(context, node.id, 'share-init')

            # Solicitar al nodo sucesor que envie las partes menores que el nodo
            c = context.socket(zmq.REQ)
            c.connect(node.sig)
            c_msg = {'tipe': 'transfer', 'id': node.id, 'which': 'minors'}
            print(">> Solicitando archivos a: ", node.sig)
            c.send_json(c_msg)
            print(">> Esperando respuesta")
            resp = c.recv_json()
            print(">>\tRespuesta recibida: ", resp)

            tam = len(resp)
            for i, value in enumerate(resp):
                with open(node.folder + "/" + resp[value], 'wb') as f:
                    send = {'tipe': 'down-a', 'filename': value, 'eliminate': 1}
                    c.send_json(send)
                    r = c.recv_json()
                    node.ht.update({value: node.folder + "/" + resp[value]})
                    fstring = r['file']
                    fbytes = base64.b64decode(fstring)
                    f.write(fbytes)

            node.hresp = True
            node.broadcast(context, node.id, 'share-finish')

# FUNCION PRINCIPAL
def main(node, context):
    s = context.socket(zmq.REP)
    s.bind(MY_DIR)

    # Conectarse a un servidor, cuando no se ingresa este campo, quiere decir que
    # es el primer nodo
    try:
        node_dir = "tcp://localhost:" + sys.argv[3]
        node.star_connection(context, node_dir)
    except:
        print("[¡PRIMER SERVIDOR EN CONECTARSE!]")
        node.first = True

    while True:
        print(">> Esperando mensajes...")
        try:
            print("Sig = ", node.sig_id[:4], "...", "Ant = ", node.ant_id[:4], "...")
        except:
            print("No hay mas nodo conectados!")

        msg = s.recv_json()

        print("---------------------------")
        print("ID: ", node.id[:4], "...")
        print("MENSAJE RECIBIDO: \n\t", "Tipo: ", msg['tipe'])

        # Mostrar en pantalla la HT
        for i, key in enumerate(node.ht):
            print(i, ":", node.ht[key].split("/")[1][:5], "...")
            # node.ht[key].split("/")[1][:5] quiere decir:
            # La cadena node.ht[key] viene con la carpeta y la extensión
            # Pero solo interesa el archivo, por eso el split para separar
            # la carpeta del nombre del archivo, y como se quiere el nombre, se
            # pone el [1], y el [:5] es que solo interesa los primeros cinco caracteres
            # del nombre, ya que es una cadena muy extensa.


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
            elif not node.sharing: # Cuando se esta compartiendo un archivo no se reciben conexiones
                # Es el caso donde se cumple que el nodo entrante sea mayor que el nodo que lo atiende
                # y que además el nodo entrante es menor al sucesor del nodo que lo atiende.
                if msg["id"] > node.id and msg["id"] < node.sig_id:
                    # Responder al nodo que envia la solicitud join, con la informacion requerida para
                    # ingresar a al red
                    raw_send = {"sig": node.sig, "ant": node.ip, "sig_id": node.sig_id, "ant_id": node.id}
                    s.send_json(raw_send)

                    # Avisar al nodo siguiente que su nuevo predecesor es el nodo que intenta entrar
                    print(">> Nodo sucesor debe cambiar predecesor: ")
                    n = context.socket(zmq.REQ)
                    n.connect(node.sig)
                    #print(">> Conexion establecida a: ", node.sig_id[:4])
                    n_msg = {'tipe': "c_ant", "id": msg["id"], "dir": msg["dir"]}
                    n.send_json(n_msg)
                    #print(">> Recibiendo respuesta")
                    resp = n.recv_json()
                    #print(">>\t", resp)

                    # Cambiar el siguiente
                    node.sig = msg["dir"]
                    node.sig_id = msg["id"]

                elif node.ant_id > node.id and (msg["id"] > node.ant_id or msg["id"] < node.id):
                    # Este es el caso especial, es cuando el nodo que intenta entrar es mayor que
                    # el nodo mayor que esta en la red. O Cuando el nodo que intenta ingresar el menor al
                    # nodo menor que esta en la red.

                    # Enviar al nodo que desear conectarse la informacion necesaria
                    raw_send = {"sig": node.ip, 'ant':node.ant, 'sig_id': node.id, 'ant_id': node.ant_id}
                    s.send_json(raw_send)

                    # Avisar al predecesor que su nuevo sucesor es el nodo que intenta entrar
                    n = context.socket(zmq.REQ)
                    n.connect(node.ant)

                    print(">> Nodo predecesor debe cambiar sucesor: ")
                    n_msg = {"tipe": "c_sig", "id": msg["id"], "dir": msg["dir"]}
                    n.send_json(n_msg)
                    #print(">> Recibiendo respuesta")
                    resp = n.recv_json()
                    #print(">>\t", resp )

                    # Cambiar predecesor o anterior
                    node.ant = msg["dir"]
                    node.ant_id = msg["id"]
                    #c.close()
                else:
                    # Esta es la opcion cuando no le corresponde al nodo atender al que ingresa

                    # Preguntar al sucesor si le corresponde atender al nodo entrante:
                    n = context.socket(zmq.REQ)
                    n.connect(node.sig)
                    # Enviar mensaje identico que recibio al nodo sucesor
                    n_msg = {"tipe": "join", "id": msg["id"], "dir": msg["dir"]}
                    #print("[No me corresponde antederlo.]")
                    #print("Transferir [Tipo: join, id: {0}, dir: {1}]".format(msg["id"][:4], msg["dir"]))
                    n.send_json(n_msg)
                    resp = n.recv_json()

                    print(">> Enviar respuesta a ", msg["id"][:4])
                    raw_send = {"sig": resp["sig"], "ant": resp["ant"], "sig_id": resp["sig_id"], "ant_id": resp["ant_id"]}
                    s.send_json(raw_send)
            else:
                # Se informa al nodo entrante que no se le puede atender
                # Este lo intentara cada segundo hasta que sea posible su atencion
                print("No puedo recibir conexiones, estoy recibiendo archivos")
                s.send_json("occupied")

        elif msg['tipe'] == "c_sig": # Cuando se la avisa a un nodo que debe cambiar su sucesor
            node.sig = msg["dir"]
            node.sig_id = msg["id"]
            s.send_json("OK")

        elif msg['tipe'] == 'c_ant': # Cuando se le avisa a un nodo que debe cambiar su predecesor
            node.ant = msg["dir"]
            node.ant_id = msg["id"]
            s.send_json("OK")

        elif msg['tipe'] == 'up': # Cuando un cliente manifiesta su intencion de subir un archivo

            # Verificar si me corresponde atender al cliente
            if 'n_part' in msg: # Si la parte se encuentra en la porcion de HT del nodo
                if msg['n_part'] == 'init':
                    node.sharing = True
                    # Informar al resto de nodos que no permitan solicitudes join para evitar inconsistencias
                    node.broadcast(context, node.id, "share-init")

            # Llamar metodo que verifica si corresponde al nodo antender la solicitud
            correspond = node.corresponds(msg)

            if correspond:
                # Si el archivo que se desea subir es un uno de indices, se guarda de inmediato.
                if msg['tipe_file'] == "index":
                    data = {"file": msg['filename'], "parts": msg['parts'], "name": msg["name"]}
                    json_data = json.dumps(data, indent=2)
                    file_name = node.folder + '/' + msg['filename']+".json"

                    with open(file_name, 'w') as output:
                        output.write(json_data)
                        node.ht.update({msg["filename"]: file_name})

                    raw_send = {'resp': "ack", 'tipe_a': 'index', 'dir': IP}
                    s.send_json(raw_send)
                else:
                    # Si es un archivo tipo parte, se le indica al cliente que efectivamente
                    # el nodo cuenta con el archivo y que se lo puede solicitar, por eso
                    # hay una llave con la dirección.
                    raw_send = {'resp': 'ok', 'tipe_a': 'part', 'dir': IP}
                    s.send_json(raw_send)
            else:
                # En caso de que no le corresponda al nodo atenderlo

                su = context.socket(zmq.REQ)
                # Se le informa al sucesor que atienda la solicitud
                su.connect(node.sig)
                if msg["tipe_file"] == "index":
                    send = {'tipe': 'up', 'tipe_file': "index", 'filename': msg['filename'], 'parts': msg['parts'], 'name': msg['name']}
                elif msg["tipe_file"] == 'part':
                    send = {'tipe': 'up', 'tipe_file': 'part', 'filename': msg['filename']}
                su.send_json(send)
                resp = su.recv_json()

                # El nodo recibe la respuesta de su sucesor y la retransmite a donde le llego la solicitud a él
                raw_send = {'resp': resp["resp"], 'tipe_a': resp["tipe_a"], 'dir': resp["dir"]}
                s.send_json(raw_send)

        elif msg['tipe'] == 'up-a': # Cuando un cliente conoce a donde enviar sus archivos
            filename = node.folder + "/" + msg['filename'] + ".part"

            with open(filename, "wb") as output:
                print("[Server]: Recibiendo parte") #, msg["filename"])
                fstring = msg['file']
                fbytes = base64.b64decode(fstring)
                output.write(fbytes)

                # Almacenar dato el HT:
                node.ht.update({msg["filename"]: filename})
            s.send_json("ACK")

            # Cuando un cliente envia la ultima parte, le indica al servidor con una llave 'n_part'
            # Con el fin de que el nodo haga un broadcast informando que ya se pueden recibir
            # solicitudes tipo join
            if 'n_part' in msg:
                if msg['n_part'] == 'finish':
                    node.sharing = False
                    node.broadcast(context, node.id, 'share-finish')

        elif msg['tipe'] == "download": # El caso de que un cliente o nodo manifiesta la intencion de obtener un archiv

            # El cliente tambien le indica al nodo que empieza a descargar las partes
            # para que el nodo le comunique al resto que no permitan mensaje tipos join
            if 'n_part' in msg:
                if msg['n_part'] == 'init':
                    #print("EMPIEZA A COMPARTIR PARTES")
                    node.sharing = True
                    node.broadcast(context, node.id, "share-init")
            # Verificar si me corresponde atender al cliente
            correspond = False

            print(">> Verificando existencia en nodo de ...", msg['filename'] in node.ht)
            if msg['filename'] in node.ht:
                if msg['tipe_file'] == 'index':
                    with open(node.ht[msg['filename']], "r") as input_j:
                        json_data = json.load(input_j)
                        s.send_json(json_data)
                else:
                    # Si lo encuentra le indica al nodo a que puede solicitar el archivo
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

                # El nodo retransmite la respuesta que recibe de su sucesor
                s.send_json(resp)

        elif msg['tipe'] == 'down-a': # En el caso de que un cliente o nodo conozca que el nodo posee el archivo
            with open(node.ht[msg['filename']], 'rb') as f:
                byte_content = f.read()
                print("[Server]: Enviando parte, size: ", len(byte_content))
                base64_bytes = base64.b64encode(byte_content)
                base64_string = base64_bytes.decode('utf-8')

                raw_data = {'file': base64_string, 'filename': msg["filename"]}
                s.send_json(raw_data) # Envio de bytes

                # Cuando es un nodo el que solicita un archivo, es porque desea transferirlo
                # y por tanto el nodo que lo posee actualmente ya no lo necesita y por tanto
                # lo borra de su HT y de sus archivos en el directorio.
                if 'eliminate' in msg:
                    os.remove(node.ht[msg['filename']])
                    del node.ht[msg['filename']]

                # Cuando el cliente esta recibiendo la ultima parte, lo informa al nodo
                # par que una vez terminado el recibimiento el nodo informe a los demas
                # que ya pueden recibir mensajes tipo join sin causar inconsistencias
                if 'n_part' in msg:
                    if msg['n_part'] == 'finish':
                        node.sharing = False
                        node.broadcast(context, node.id, 'share-finish')

        elif msg['tipe'] == 'broadcast': # Cuando un nodo informa a otro de que no reciba ciertas solicitudes
            # Cuando se da msg['init'] == node.id, quiere decir que el mensaje
            # ya paso por toda la red y llego a quien lo envio
            if not(msg['init'] == node.id):
                # Cuando se empieza a compartir un archivo
                if msg['msg'] == 'share-init':
                    print(">> Modo share: OK")
                    print(">> \tTransferir a: ", node.sig)
                    node.sharing = True
                    s.send_json("Ok")
                    # Informar al sucesor que entre en modo share
                    node.broadcast(context, msg['init'], msg['msg'])
                elif msg['msg'] == 'share-finish': # Cuando se terminar de compartir
                    node.sharing = False
                    s.send_json("Ok")
                    # Informar al sucesor que puede salir del modo share
                    node.broadcast(context, msg['init'], msg['msg'])
            else:
                s.send_json("Ok")
        elif msg['tipe'] == 'transfer': # Cuando un nodo le solicita a otro que le transfiera archivos
            # El nodo que recibe esta solicitud lo que hace es enviar en un diccionario las partes
            # que le correspoden al nodo que hace la solicitud transfer
            send = {}
            print(">> Transfiriendo: ")
            if msg['which'] == 'greater': # Para valores mayores al token del nodo que hace la solicitud
                for i, value in enumerate(node.ht):
                    if value > msg['id']:
                        print(">>\t", value[:4])
                        send.update({value: node.ht[value].split("/")[1]})
            elif msg['which'] == 'minors': # Para valores menores al token del nodo que hace la solicitud
                for i, value in enumerate(node.ht):
                    if value < msg['id']:
                        print(">>\t", value[:4])
                        send.update({value: node.ht[value].split("/")[1]})

            s.send_json(send)

    #else:
    #    print("NO FUE POSIBLE CONECTAR CON TRACKER")

if __name__ == '__main__':
    node = Node(IP) # Crear NODO
    context = zmq.Context()
    print("ID: ", node.id[:4], "...")

    node.folder = sys.argv[2] # Asignar directorio
    node.loadFiles()

    # Crear un hilo para la funcion main
    hiloMain = threading.Thread(target = main, args = (node, context, ))
    hiloMain.start() # Iniciar el proceso

    # Dar tiempo mientras los nodos se conectan
    time.sleep(2)

    # Este ciclo en el hilo principal esta controlando que a un nodo que se conecta
    # si se le transfieran los archivos correspondiente
    while True:
        if node.first: # Si es el primer nodo rompe, porque no es necesario verificar esto.
            break
        elif node.transfer:
            # Se crea un hilo para la funcion Ntransfer que se encarga de la transferencia
            # entre nodos.
            hiloTransfer = threading.Thread(target = Ntransfer, args = (node, context))
            hiloTransfer.start()
            time.sleep(0.5)
            if node.hresp:  # Cuando el nodo obtiene una respuesta es decir cuando se le
                break       # transfieren los archivos, termina este proceso de control.

import os
import sys
import zmq
import threading
import json

def loadFiles(path):
    files = {}
    dataDir = os.fsencode(path)
    for file in os.listdir(dataDir):
        filename = os.fsdecode(file)
        #print("Loading {}".format(filename))
        files[filename] = file
    return files

def main():
    try:
        folder = sys.argv[1]
    except:
        print("[Tracker]: ¡Error! Debe especificar un directorio (tracker_archives/)")
        return -1

    print("Serving files from {}".format(folder))
    files = loadFiles(folder)
    print("Load info on {} files.".format(len(files)))

    context = zmq.Context()
    s_port = "tcp://*:5555"
    # Actuar como servidor
    s = context.socket(zmq.REP)
    s.bind(s_port)

    servers = []

    while True:
        msg = s.recv_json()

        if msg['tipe'] == "upload":
            print("[TRACKER]: Petición de subida recibida")
            if not len(servers) == 0:
                archive_name = msg["file"]
                archive_parts = msg["parts"]
                PARTS = {}

                print("[TRACKER]: Creando archivo redtorrent ...")
                for i, part in enumerate(archive_parts):
                    PARTS.update({part : servers[i%len(servers)]})

                data = {"file":archive_name, "parts": PARTS, "servers": servers, "file_name": msg["file_name"]}
                json_data = json.dumps(data, indent=2)
                file_name = folder + archive_name+".json"

                with open(file_name, 'w') as output:
                    output.write(json_data)

                s.send_json(data)

                print("[TRACKER]: Archivo creado correctamente")
            else:
                print("[TRACKER]: No hay servidores disponibles")
        elif msg['tipe'] == "server":
            print("[TRACKER]: Conexion de servidor")
            servers.append(msg["dir"])
            s.send_json({"rsp": "ACK"})
            print("[TRACKER]: Servidores disponibles: ", len(servers))
        elif msg['tipe'] == "download":
            fkey = msg["file"]
            if fkey in files:
                with open(folder+fkey, "r") as input_j:
                    json_data = json.load(input_j)
                    s.send_json(json_data)

        files = loadFiles(folder)

    #print("bloqueante")


'''def t_server(s_port):
    context = zmq.Context()
    r = context.socket(zmq.REP)
    r.bind(s_port)

def t_client(c_port):
    context = zmq.Context()
    s = context.socket(zmq.REQ)
    s.connect(c_port)
'''

if __name__ == '__main__':
    main()
    '''servidor = threading.Thread(target=t_server, args=(sys.argv[2],))
    cliente = threading.Thread(target=t_client, args=(sys.argv[3],))

    servidor.start()
    cliente.start()
    '''

import zmq
import sys
import hashlib
import os
import math
import json
import base64

def sha256_parts(filename, part_size):
    tam = os.path.getsize(filename)
    parts = math.ceil(tam/part_size)
    PARTS = []
    with open(filename, 'rb') as f:
        for i in range(parts):
            part = f.read(part_size)
            sha256 = hashlib.sha256()
            sha256.update(part)
            PARTS.append(sha256.hexdigest())
    return PARTS

def main():
    context = zmq.Context()

    PART_SIZE = 1000000
    salir = False
    filename = sys.argv[1].split(".")[0]
    while not salir:
        print("Menu: ")
        print("\t1. Subir archivo")
        print("\t2. Descargar archivo")
        print("\t3. Salir")

        opcion = int(input("\tDigite una opcion: "))

        if opcion == 1:
            s = context.socket(zmq.REQ)
            #dir_tracker = sys.argv[2]
            s.connect("tcp://localhost:5555")
            sha256 = hashlib.sha256()

            with open(sys.argv[1], 'rb') as f:
                block = f.read()
                sha256.update(block)
                name = (sha256.hexdigest())

            parts = sha256_parts(sys.argv[1], PART_SIZE)
            raw_data = {'tipe': "upload", 'file': name, 'parts':parts}
            s.send_json(raw_data)

            response = s.recv_json()

            servers = response["servers"]
            SERVERS = {}
            for i, server in enumerate(servers):
                se = context.socket(zmq.REQ)
                se.connect(server)
                SERVERS.update({server: se})

            # ENVIAR ARCHIVOS A LOS SERVIDORES:
            parts = response["parts"]
            print("[CLIENTE]: Compartiendo archivo")
            with open(sys.argv[1], 'rb') as f:
                for i, part in enumerate(parts):

                    s = SERVERS[parts[part]]

                    byte_content = f.read(PART_SIZE)
                    print("[Cliente]: Compartiendo la parte {0}, size: {1}".format(i, len(byte_content)))
                    base64_bytes = base64.b64encode(byte_content)
                    base64_string = base64_bytes.decode('utf-8')

                    raw_data = {'tipe':"up", 'part': i, 'file': base64_string, 'filename':part}
                    s.send_json(raw_data)
                    resp = s.recv_json()

                    if not resp == "ACK":
                        print("[Cliente]: Sucedio un problema enviando la parte ", i)
                        break
            print("[Cliente]: Partes enviadas correctamente")

        elif opcion == 2:
            pass
        elif opcion == 3:
            salir = True
        else:
            print("Opcion incorrecta\n")

if __name__ == '__main__':
    main()


import zmq
import sys
import hashlib
import os
import math
import json
import base64

# Funcionque permite obtener un token unico para cada parte de un archivo
def sha256_parts(filename, part_size):
    # Obtener tamaño de del archivo
    tam = os.path.getsize(filename)
    # Cantidad de partes
    parts = math.ceil(tam/part_size)
    PARTS = [] # Arreglo de sha256sum de cada parte
    with open(filename, 'rb') as f:
        for i in range(parts):
            # Leer parte del archivo
            part = f.read(part_size)
            sha256 = hashlib.sha256()
            sha256.update(part)
            PARTS.append(sha256.hexdigest())
    return PARTS

def main():
    context = zmq.Context()

    # Tamaño fijo de las partes 1MB
    PART_SIZE = 1000000
    salir = False

    # Nombre del archivo (Debe pedirse por teclado)
    #filename = sys.argv[1].split(".")[0]
    s = context.socket(zmq.REQ)
    # Conectarse con el tracker
    s.connect("tcp://localhost:5555")
    while not salir:

        print("Menu: ")
        print("\t1. Subir archivo")
        print("\t2. Descargar archivo")
        print("\t3. Salir")

        opcion = int(input("\tDigite una opcion: "))
        if opcion == 1:
            print("Digite el nombre del archivo (con la extensión): ")
            filename = input()

            sha256 = hashlib.sha256()

            # Crear token unico general para el archivo
            with open(filename, 'rb') as f:
                block = f.read()
                sha256.update(block)
                name = (sha256.hexdigest())

            # Usar funcion para calcular el token para cada parte
            parts = sha256_parts(filename, PART_SIZE)
            raw_data = {'tipe': "upload", 'file': name, 'parts':parts, 'file_name': filename}
            s.send_json(raw_data)

            response = s.recv_json()

            # Servidores disponibles para enviar el archivo
            servers = response["servers"]
            SERVERS = {}
            print("Servidores disponibles: ", servers)
            for i, server in enumerate(servers):
                # Crear un socket
                se = context.socket(zmq.REQ)
                se.connect(server)
                # Diccionario para relacionar la dirección del socket con el socket
                SERVERS.update({server: se})

            # ENVIAR ARCHIVOS A LOS SERVIDORES:
            parts = response["parts"]
            print("[CLIENTE]: Compartiendo archivo")
            with open(filename, 'rb') as f:
                for i, part in enumerate(parts):

                    so = SERVERS[parts[part]]

                    byte_content = f.read(PART_SIZE)
                    print("[Cliente]: Compartiendo la parte {0}, size: {1}".format(i, len(byte_content)))
                    base64_bytes = base64.b64encode(byte_content)
                    base64_string = base64_bytes.decode('utf-8')

                    raw_data = {'tipe':"up", 'part': i, 'file': base64_string, 'filename':part}
                    so.send_json(raw_data)
                    resp = so.recv_json()

                    if not resp == "ACK":
                        print("[Cliente]: Sucedio un problema enviando la parte ", i)
                        break
            print("[Cliente]: Partes enviadas correctamente")
            print("[COMPARTIR ARCHIVO]:")
            print("\tPara compartir el archivo que acabo de subir, guarde esta clave y compartala con quien desee: ")
            print("\tCLAVE: ", response["file"])

            print("¿Desea guardarla en un archivo .txt?")
            save = input("(Y/N)? ")

            if save == "y" or save == "Y":
                file_name_s = "share-" + filename + ".txt"
                with open(file_name_s, "w") as fsave:
                    fsave.write("KEY: " + response["file"])
                    print("Archivo creado correctamente, nombre: ", file_name_s)
            #with open(filename+".json", 'w') as output:
            #    json_data = json.dumps(response, indent=2)
            #    output.write(json_data)
            #print("[Cliente]: Torrent creado correctamente")

        elif opcion == 2:
            print("Digite la clave del archivo que desea descargar: ")
            key = input()

            raw_data = {'tipe': "download", 'file': key + ".json"}
            
            s.send_json(raw_data)

            response = s.recv_json()

            servers = response["servers"]
            SERVERS = {}
            print("Servidores disponibles: ", servers)
            for i, server in enumerate(servers):
                # Crear un socket
                se = context.socket(zmq.REQ)
                se.connect(server)
                # Diccionario para relacionar la dirección del socket con el socket
                SERVERS.update({server: se})

            with open("down-" + response["file_name"], 'wb') as f:
                r_parts = response["parts"]
                for i, part in enumerate(r_parts):
                    sp = SERVERS[r_parts[part]]

                    #byte_content = f.read(PART_SIZE)
                    print("[Cliente]: Descargando la parte ", i)
                    #base64_bytes = base64.b64encode(byte_content)
                    #base64_string = base64_bytes.decode('utf-8')

                    raw_data = {'tipe':"download", 'filename':part}
                    sp.send_json(raw_data)

                    resp = sp.recv_json()

                    print("[Server]: Recibiendo parte ", resp["filename"])
                    fstring = resp['file']
                    fbytes = base64.b64decode(fstring)

                    f.write(fbytes)
            #with open("response.json", 'w') as output:
            #    json_data = json.dumps(response, indent=2)
            #    output.write(json_data)

        elif opcion == 3:
            salir = True
        else:
            print("Opcion incorrecta\n")

if __name__ == '__main__':
    main()

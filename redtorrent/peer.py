import zmq
import sys
import hashlib
import os
import math
import json
import base64
import time

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

# Funcion para enviar un mensaje, si el servidor esta ocupado, espera un segundo
# y reenvia el mensaje hasta recibir la respuesta esperada.
def send_msg(socket, msg):
    socket.send_json(msg)

    resp = socket.recv_json()

    if resp == "occupied":
        time.sleep(1)
        send_msg(socket, msg)
    else:
        return resp

def main():
    context = zmq.Context()

    # Tamaño fijo de las partes 5MB
    PART_SIZE = 1000000
    salir = False

    # Nombre del archivo (Debe pedirse por teclado)
    #filename = sys.argv[1].split(".")[0]
    s = context.socket(zmq.REQ)
    # Conectarse con el tracker
    serv = "tcp://localhost:" + sys.argv[1]
    print("Intentando conectarse a: ", serv)
    s.connect(serv)
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
            raw_data = {'tipe': 'up', 'tipe_file': "index", 'filename': name, 'parts':parts, 'name': filename, 'n_part': 'init'}
            s.send_json(raw_data)

            response = s.recv_json()

            if response["resp"] == "ack":
                with open(filename, 'rb') as f:
                    tam = len(parts)
                    for i, part in enumerate(parts):
                        # Preparar mensaje
                        byte_content = f.read(PART_SIZE)
                        print("[Cliente]: Compartiendo la parte {0}, size: {1}".format(i, len(byte_content)))
                        base64_bytes = base64.b64encode(byte_content)
                        base64_string = base64_bytes.decode('utf-8')
                        send = {'tipe': 'up-a', 'tipe_file': 'part', 'file': base64_string, 'filename': part}
                        if i + 1 == tam:
                            send.update({'n_part': 'finish'})

                        # Enviar mensaje manifestando intencion de envio de parte
                        raw_send = {'tipe': 'up', 'tipe_file': 'part', 'filename': part}
                        s.send_json(raw_send)
                        resp = s.recv_json()

                        # Si la respuesta es afirmativa:
                        if resp["resp"] == "ok":
                            # Si el servidor destino es el mismo que me atiende inicialmente:
                            if resp["dir"] == serv:
                                s.send_json(send)
                                r = s.recv_json()
                            else:
                                # Crear el socket respectivo para el server dispuesto a recibir
                                so = context.socket(zmq.REQ)
                                so.connect(resp["dir"])
                                so.send_json(send)
                                r = so.recv_json()

                            if not r == "ACK":
                                print ("[Cliente]: Sucedio un problema enviando la parte", i)
                                break
                        else:
                            print("[Server]: No se puede recibir la parte")
                            break

                print("[Cliente]: Partes enviadas correctamente")
                print("[COMPARTIR ARCHIVO]:")
                print("\tPara compartir el archivo que acabo de subir, guarde esta clave y compartala con quien desee: ")
                print("\tCLAVE: ", name)

                print("¿Desea guardarla en un archivo .txt?")
                save = input("(Y/N)? ")

                if save == "y" or save == "Y":
                    file_name_s = "share-" + filename + ".txt"
                    with open(file_name_s, "w") as fsave:
                        fsave.write("KEY: " + name)
                        print("Archivo creado correctamente, nombre: ", file_name_s)
            else:
                print("[SERVER]: No se pudo recibir el archivo Index!")
                break

        elif opcion == 2:
            print("Digite la clave del archivo que desea descargar: ")
            key = input()

            raw_data = {'tipe': "download", 'tipe_file': 'index', 'filename': key, 'n_part': 'init'}
            s.send_json(raw_data)

            response = s.recv_json()

            with open("down-" + response["name"], 'wb') as f:
                r_parts = response["parts"]
                tam = len(r_parts)
                for i, part in enumerate(r_parts):
                    print("[Cliente]: Descargando la parte ", i)

                    # Enviar mensaje manifestando intencion de descargar parte:
                    raw_data = {'tipe': 'download', 'tipe_file': 'part', 'filename':part}
                    s.send_json(raw_data)

                    resp = s.recv_json()
                    down_send = {'tipe': 'down-a', 'filename': part}
                    if i + 1 == tam:
                        down_send.update({'n_part': 'finish'})

                    if resp['resp-d'] == 'ok':
                        if resp['dir'] == serv:
                            s.send_json(down_send)
                            r = s.recv_json()
                        else:
                            # Crear el socket respectivo para el server dispuesto a recibir
                            so = context.socket(zmq.REQ)
                            so.connect(resp['dir'])
                            so.send_json(down_send)
                            r = so.recv_json()

                        print("[Server]: Recibiendo parte ", r["filename"])
                        fstring = r['file']
                        fbytes = base64.b64decode(fstring)

                        f.write(fbytes)
                    else:
                        print("OCURRIO UN PROBLEMA, NO SE PUEDE RECIBIR PARTE")
                        break

        elif opcion == 3:
            salir = True
        else:
            print("Opcion incorrecta\n")

if __name__ == '__main__':
    main()

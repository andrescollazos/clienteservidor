import os
import sys
import zmq

def loadFiles(path):
    files = {}
    dataDir = os.fsencode(path)
    for file in os.listdir(dataDir):
        filename = os.fsdecode(file)
        print("Loading {}".format(filename))
        files[filename] = file
    return files

def get_part(fileName, tam, p):
    with open(fileName, "rb") as input:
        input.seek(p * tam)
        data = input.read(tam)

    return data

def main():
    musicFolder = sys.argv[1]
    print("Serving files from {}".format(musicFolder))
    files = loadFiles(musicFolder)
    print("Load info on {} files.".format(len(files)))

    # Create the socket and the context
    context = zmq.Context()
    s = context.socket(zmq.REP)
    s.bind("tcp://*:5555")

    TAM_MIN = 512000

    while True:
        msg = s.recv_json()
        #print(s.get_monitor_socket())
        if msg["operacion"] == "lista":
            print("[RECIBIDO]: Solicitud de listar canciones")
            s.send_json({"canciones": list(files.keys())})

        elif msg["operacion"] == "descarga":
            fileName = musicFolder + msg["cancion"]
            if msg["parte"] == "-1":
                tam = os.path.getsize(fileName)
                tam = int(tam*(msg["porcentaje"]/100))
                cantidad_partes = int(tam/TAM_MIN)
                if not cantidad_partes*TAM_MIN ==  tam:
                    cantidad_partes += 1
                print("CANTIDAD DE PARTES A ENVIAR DE {0} B: {1}".format(TAM_MIN, cantidad_partes))
                s.send_json({"cantidad_partes": cantidad_partes})
            else:
                print("[RECIBIDO]: Solicitud de descarga, parte ", msg["parte"])

                part = get_part(fileName, TAM_MIN, int(msg["parte"]))
                s.send(part)

if __name__ == '__main__':
    main()

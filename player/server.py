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

def dividir_archivo(fileName, tam, p = 100):
    with open(fileName, "rb") as input:
        data = input.read()
        t = len(data) # TAMANO TOTAL DEL ARCHIVO
        # Calcular nuevo tamano a partir del porcentaje
        tamt = int(t*(p/100))
        tamp = int(tamt*1.0/tam)
        tamr = tamt - tam*tamp
        input.seek(0)
        PARTS = []
        for i in range(tamp):
            PARTS.append(input.read(tam))
        PARTS.append(input.read(tamr))
    #print("Archivo divido en {} partes".format(len(PARTS)))
    return PARTS

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
        elif msg["operacion"] == "reproducir":
            print("[RECIBIDO]: Solicitud de reproducir cancion al ", msg["porcentaje"], "%")
            fileName = musicFolder + msg["cancion"]
            with open(fileName,"rb") as input:
                data = input.read()
                tam = len(data) # TAMANO TOTAL DEL ARCHIVO
                # Calcular nuevo tamano a partir del porcentaje
                tam = int(tam*(msg["porcentaje"]/100))
                input.seek(0)
                data = input.read(tam)

                # ENVIO DE PARTES
                s.send(data)

        elif msg["operacion"] == "descarga":
            print("[RECIBIDO]: Solicitud de descarga, parte ", msg["parte"])
            fileName = musicFolder + msg["cancion"]

            PARTS = dividir_archivo(fileName, TAM_MIN, msg["porcentaje"])
            if not(msg["parte"] == len(PARTS)):
                s.send(PARTS[msg["parte"]])
            else:
                s.send(bytes("FINISH", 'utf-8'))

if __name__ == '__main__':
    main()

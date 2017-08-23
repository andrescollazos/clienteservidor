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

def main():
    musicFolder = sys.argv[1]
    print("Serving files from {}".format(musicFolder))
    files = loadFiles(musicFolder)
    print("Load info on {} files.".format(len(files)))

    # Create the socket and the context
    context = zmq.Context()
    s = context.socket(zmq.REP)
    s.bind("tcp://*:5555")

    while True:
        msg = s.recv_json()
        #print(s.get_monitor_socket())
        if msg["operacion"] == "lista":
            s.send_json({"canciones": list(files.keys())})
        elif msg["operacion"] == "descarga":
            fileName = musicFolder + msg["cancion"]
            with open(fileName,"rb") as input:
                data = input.read()
                s.send(data)
        elif msg["operacion"] == "reproducir":
            fileName = musicFolder + msg["cancion"]
            with open(fileName,"rb") as input:
                data = input.read()
                s.send(data)
if __name__ == '__main__':
    main()

import numpy as np
import random
from scipy.spatial import distance
import ast
import sys
import zmq
import json

MY_DIR = "tcp://*:" + sys.argv[1]
PORT = sys.argv[1]

DATASETS = ["datasets/DS_1Clusters_100Points.txt",
            "datasets/DS_3Clusters_999Points.txt",
            "datasets/DS2_3Clusters_999Points.txt",
            "datasets/DS_5Clusters_10000Points.txt",
            "datasets/DS_7Clusters_100000Points.txt"
            ]

def main():
    context = zmq.Context()
    s = context.socket(zmq.REP)
    s.bind(MY_DIR)

    n_mappers = 0
    f_mappers = 0
    matrix_dist = []
    m_exists = False
    i_ant = False
    key_ant = ""
    while True:
        print("Esperando conexiones...")
        msg = s.recv_json()
        #print("Recibí conexion: ", msg)
        #s.send_json("OK")
        if msg["type"] == "dist":
            n_mappers = int(msg["mappers"])

            print("Recibi distancias")
            json_data = json.dumps(msg, indent=2)
            with open(PORT + "-" + msg["save"] + ".json", msg["ap"]) as output:
                output.write(json_data)
                print("Guarde distancias.")
            s.send_json("OK")

            if not m_exists:
                rows = int(msg["pdr"])
                cols = int(msg["clusters"])
                for i in range(rows):
                    r = []
                    for j in range(cols):
                        r.append([])
                    matrix_dist.append(r)
                m_exists = True

            key = msg["key"]
            centroid = int(key.split("-")[0])
            dates = msg["dates"]
            c_dates = 0

            if not(key == key_ant):
                inc = 0
            else:
                inc = i_ant

            #print("Key: ", key, " c: ", centroid)
            for c, i in enumerate(matrix_dist):
                c += inc
                if type(i[centroid]) == type([]): # Debe ser una lista
                    if not len(i[centroid]):
                        print(c, ". lenI: {0} c: {1} | lenD: {2} c_d: {3}".format(len(i), centroid, len(dates), c_dates))
                        i[centroid] = dates[c_dates]
                        c_dates += 1
                    if c_dates == len(dates):
                        i_ant = c_dates
                        key_ant = key
                        break
                    #print(c, ". i: ", i, " ", type(i), " c: ", centroid)

        if msg["type"] == "end-data":
            f_mappers += 1
            s.send_json("OK")
            if f_mappers == n_mappers:
                save_d = {"matriz": matrix_dist}
                json_data = json.dumps(save_d, indent=2)
                with open(PORT + "-distances.json", 'w') as output:
                    output.write(json_data)


if __name__ == '__main__':
    main()

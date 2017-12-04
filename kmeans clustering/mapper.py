import numpy as np
import random
from scipy.spatial import distance
import ast
import sys
import zmq
import math
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
    while True:
        #print("Esperando conexiones...")
        msg = s.recv_json()

        if msg["type"] == "map":
            print("[mapper]: Conexión recibida")
            s.send_json("OK") # Acuse de recibo para f

            # El mensaje que se recibe esta estructurado de la siguiente manera:
            # NUM_CLUSTER:CANTIDAD_DATOS:SECCION_DATASET
            # Es decir, si quisieramos calcular las distancias de 25000 puntos
            # que se encuentran en la cuarta parte , respecto al segundo cluster
            # el mensaje sería de la forma: '1:25000:3'
            data = msg["pr_dataset"].split("|")[1:]
            for i, elem in enumerate(data):
                data[i] = elem.split(":")

            dataset = msg["dataset"]
            num_clusters = msg["clusters"]
            centroids = msg["centroids"]
            pdm = int(msg["pdm"])
            # Procesar cadena de centroides:
            #print("Centroids: ")
            centroids = centroids.split("::")[1:]
            for i, centroid in enumerate(centroids):
                centroids[i] = centroid.split(",")
                p = []
                for j, c in enumerate(centroids[i]):
                    p.append(ast.literal_eval(centroids[i][j]))
                centroids[i] = p #(ast.literal_eval(centroids[i][0]), ast.literal_eval(centroids[i][1]))
                #print(centroids[i])

            distances = {}
            with open(dataset, "rt") as a_dataset:
                #print("Iter: ", iters)
                a = list(a_dataset)
                for i, dat in enumerate(data):
                    centroid = int(dat[0])
                    cont = pdm*int(dat[2]) # El contador se posiciona dependiendo de la seccion
                    lim = cont + int(dat[1])
                    hsh = dat[0] + "-" + dat[2] + "-" + dat[1]
                    dist = []
                    while cont < lim:
                        #print("Cont: {0} lim: {1}".format(cont, lim))
                        point = a[cont].split("::")
                        p = []
                        for i, po in enumerate(point):
                            p.append(ast.literal_eval(point[i]))
                        point = p # (ast.literal_eval(point[0]), ast.literal_eval(point[1]))
                        d = distance.euclidean(point, centroids[centroid])
                        dist.append(d)
                        cont += 1
                    distances.update({hsh: dist})

            # Enviar distancias a los reducers
            pdr = int(msg["pdr"])
            ip_reducers = msg["reducers"]

            # Conectarse a los reducers
            reducers = []
            for i, r in enumerate(ip_reducers):
                rs = context.socket(zmq.REQ)
                rs.connect(r)
                reducers.append(rs)

            hasant = 0
            for d in distances:
                red_msg = {} # Mensaje que se enviara a cada reducer
                raw_d = []

                # Se le debe indicar al reducer de que seccion esta obteniendo una distancia
                # para guardar la coherencia.
                sec = d.split("-")[1]
                hashd = d.split("-")[0]

                # Al trabajr con mas mappers, la informacion se dividira más, asi es que
                # las llaves pueden coincidir es necesario conocer que llave ya se envio
                if not(hasant == hashd):
                    secr = 0
                hasant = hashd

                for i, di in enumerate(distances[d]):
                    # i+int(sec)*pdm esto permite ubicar al contador en la seccion de las distancias correspondientes
                    # Esta condicion permite al mapper enviar la seccion correspondiente
                    # Si no se cumple la condicion aumentara en una la seccion
                    if not (i+int(sec)*pdm) < pdr + pdr*secr:
                        secr += 1
                        raw_d = []
                    raw_d.append(di)
                    # La llave se compone del cluster + seccion + el volumen de datos
                    red_msg.update({hashd+"-"+str(secr)+"-"+str(pdr): raw_d})
                    cont += 1

                for key in (red_msg):
                    ky = key.split("-")
                    i_reducer = int(ky[1]) # Identificar a que reducer enviar
                    centroid = ky[0]
                    size = int(ky[2])

                    # Si no se cumple que el identificador sea mayor que la cantidad de reducers
                    if not(i_reducer >= len(reducers)):
                        #print("SEND Iter: ", iters, " centroids: ", centroids)
                        n_save = key
                        # Se enviara un mensaje de tipo dist, junto con los datos de las distancias
                        # Y la demás información correspondiente al sistema Map reduce
                        msg_red = {"type": "dist", "dates": red_msg[key],
                                "key": key,"save": key, "ap": 'a',
                                "mappers": msg["mappers"],
                                "clusters": msg["clusters"],
                                "reducers": msg["reducers"],
                                "pdr": pdr,
                                "centroids": centroids,
                                "dataset": msg["dataset"]}
                        sck = reducers[i_reducer]
                    else:
                        a_key = centroid + "-" + str(i_reducer - 1) + "-" + str(size)
                        n_save = a_key
                        n_size = size + len(red_msg[key])
                        n_key = centroid + "-" + str(i_reducer - 1) + "-" + str(n_size)
                        dates = red_msg[a_key] + red_msg[key] # Cuando hay dos con la misma llave
                        #ap = 'w'
                        msg_red = {"type": "dist", "dates": dates,
                                "key": n_key, "save": a_key, "ap": 'w',
                                "mappers": msg["mappers"],
                                "clusters": msg["clusters"],
                                "reducers": msg["reducers"],
                                "pdr": pdr,
                                "centroids": centroids,
                                "dataset": msg["dataset"]}
                        sck = reducers[i_reducer - 1]
                        #json_data = json.dumps(save, indent=2)
                    sck.send_json(msg_red)
                    print("Response: ", sck.recv_json())

            # Enviar a los reducers el mensaje diciendo que termino de enviar datos.
            for rs in reducers:
                rs.send_json({"type": "end-data"})
                print("Response: ", rs.recv_json())

        if msg["type"] == "end":
            print("Finalizar conexión")
            return 0


if __name__ == '__main__':
    main()

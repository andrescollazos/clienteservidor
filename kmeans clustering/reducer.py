import numpy as np
import random
import ast
import sys
import zmq
import json

MY_DIR = "tcp://*:" + sys.argv[1]
PORT = sys.argv[1]
S_DIR = "tcp://localhost:7000" # Direccion del S

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

    s_sck = context.socket(zmq.REQ)
    s_sck.connect(S_DIR)

    n_mappers = 0       # Cuantos mappers hay
    f_mappers = 0       # De cuantos se ha recibido informacion
    matrix_dist = []    # Matriz para estructurar la info para la comparacion
    m_exists = False    # Saber si la matriz ya fue creada
    i_ant = False       # Contador para ubicarse en la matriz
    key_ant = ""        # La llave anteriormente recibida
    while True:
        msg = s.recv_json()

        if msg["type"] == "dist":
            print("[Reducer]: Conexión recibida")
            n_mappers = int(msg["mappers"])

            s.send_json("OK")

            # Si la matriz no existe se procede a crearla
            if not m_exists:
                rows = int(msg["pdr"])      # Volumen de datos
                cols = int(msg["clusters"]) # Cantidad de clusters
                for i in range(rows):
                    r = []
                    for j in range(cols):
                        r.append([])
                    matrix_dist.append(r)
                m_exists = True

            # Información del sistema MAP REDUCE
            key = msg["key"]
            reducers = msg["reducers"]
            centroids = msg["centroids"]
            pdr = msg["pdr"]
            dataset = msg["dataset"]

            # Identificador de cada centroide
            centroid = int(key.split("-")[0])
            # Identificador de la seccion de la cual se lee la info
            sec = int(key.split("-")[1])
            # Distancias entregadas por cada mapper
            dates = msg["dates"]
            c_dates = 0

            # Como hay llaves que pueden repetirse, conviene identificar y hacer
            # un incremento en el contador de posiciones de la matriz para no llegar
            # a sobreescribir datos en la matriz.
            if not(key == key_ant):
                inc = 0
            else:
                inc = i_ant

            for c, i in enumerate(matrix_dist):
                c += inc # Se hace el incremento al contador
                if type(i[centroid]) == type([]): # Debe ser una lista
                    if not len(i[centroid]):
                        i[centroid] = dates[c_dates]
                        c_dates += 1
                    if c_dates == len(dates):
                        i_ant = c_dates
                        key_ant = key
                        break

        if msg["type"] == "end-data":
            # El tipo de mensaje end-data quiere decir que un mapper i termino de enviar
            # las distancias
            f_mappers += 1
            s.send_json("OK") # Acuse de recibo

            if f_mappers == n_mappers: # Todos los mappers enviaron la info
                save_d = {"matriz": matrix_dist}
                minors = [] # Arreglo de los menores, las posiciones con el data set se corresponden

                # Calcular centro más cercano
                for i in matrix_dist:
                    # np.argmin permite obtener la posicion del menor elemento en un arreglo
                    minors.append(int(np.argmin(i)))

                # Mensaje para S, en el cual se reenvian los centroides y la seccion correspondiente
                msg_s = {"type": "minors", "centroids": centroids,
                        "sec": sec, "reducers": len(reducers),
                        "pdr": pdr, "minors": minors,
                        "dataset": dataset}

                s_sck.send_json(msg_s)
                print("Response: ", s_sck.recv_json())
                # Reiniciar parametros de ejecución
                f_mappers = 0
                i_ant = False
                key_ant = ""
                matrix_dist = []
                m_exists = False

        if msg["type"] == "end":
            print("Finalizar conexión")
            return 0

if __name__ == '__main__':
    main()

import numpy as np
import random
from scipy.spatial import distance
import ast
import sys
import zmq
import math
import json

MY_DIR = "tcp://*:" + sys.argv[1]
F_DIR = "tcp://localhost:3001"
PORT = sys.argv[1]
DELTA = 1e-5

DATASETS = ["datasets/DS_1Clusters_100Points.txt",
            "datasets/DS_3Clusters_999Points.txt",
            "datasets/DS2_3Clusters_999Points.txt",
            "datasets/DS_5Clusters_10000Points.txt",
            "datasets/DS_7Clusters_100000Points.txt"
            ]

# Esta funcion toma un dataset y lo convierte en puntos de N dimensiones
def dataset_to_list_points(dataset):
    points = []
    with open(dataset, 'r') as reader:
        for point in reader:
            p = point.split("::")
            po = []
            for j, poi in enumerate(p):
                po.append(ast.literal_eval(p[j]))
            #p = (ast.literal_eval(p[0]), ast.literal_eval(p[1]))
            points.append(po)
    return points

def main():
    context = zmq.Context()
    s = context.socket(zmq.REP)
    s.bind(MY_DIR)

    n_reducers = 0      # Cantidad de reducers en el sistema
    f_reducers = 0      # Cuantos reducers han enviado informacion
    near_centroids = [] # Arreglo para organizar un punto de acuerdo al cluster mas cercanp
    n_e = False         # Saber si el arreglo anterior exite
    a_clusters = []     # Arreglo de clusters

    while True:
        msg = s.recv_json()

        if msg["type"] == "minors":
            print("[S]: Conexión recibida")
            s.send_json("OK") # Acuse de recibo

            n_reducers = int(msg["reducers"])
            f_reducers += 1

            # Información del sistema MAP REDUCE
            pdr = int(msg["pdr"])
            sec = int(msg["sec"])
            centroids = msg["centroids"]
            minors = msg["minors"]

            # Aun no se ha creado el vector
            if not n_e:
                # Cargar puntos:
                points = dataset_to_list_points(msg["dataset"])

                # El arreglo tendrá igual tamaño a la cantidad de puntos procesados
                for i in range(pdr*len(centroids)):
                    near_centroids.append([])
                n_e = True

            # Lista de centroides que corresponde a la
            for i, minor in enumerate(minors):
                i = i + sec*pdr # Ubicar el contador en una sección especifica del arreglo
                near_centroids[i] = minor

            # Cuando se recibio toda la información de los reducers
            if f_reducers == n_reducers:

                # Inicializar arreglo para los clusters, si N=3 -> a_clusters tendra tres posiciones
                for i in range(len(centroids)):
                    a_clusters.append([])

                # Recorrer el vector near_centroids que contiene la informacion de que cluster
                # esta más cercano a cada punto.
                for i, cent in enumerate(near_centroids):
                    # Ubicarse en el respectivo cluster
                    a_clusters[cent].append(points[i])

                # Calcular nuevos centroides:
                n_centroids = []
                for i, cluster in enumerate(a_clusters):
                    # Crear variable para la suma:
                    dimension = len(points[0])
                    sum_coordinates = []
                    for j in range(dimension):
                        sum_coordinates.append(0)
                    #sum_coordinates = [0, 0]

                    for point in cluster:
                        for j, x in enumerate(point):
                            sum_coordinates[j] += x

                    for j, sum_c in enumerate(sum_coordinates):
                        sum_coordinates[j] = (sum_coordinates[j]/len(cluster))
                    #sum_coordinates[0] = (sum_coordinates[0]/len(cluster))
                    #sum_coordinates[1] = (sum_coordinates[1]/len(cluster))
                    n_centroids.append(sum_coordinates)


                # Calcular diferencia con respecto al centroide anterior:
                dif = 0
                for i, centroid in enumerate(centroids):
                    #print("Dif: {0} - {1} = {2}".format(centroid, n_centroids[i], distance.euclidean(centroid, n_centroids[i])))
                    dif += distance.euclidean(centroid, n_centroids[i])

                print("DIFERENCIA: ", dif, " DELTA: ", DELTA)
                # Si la sumatoria de las diferencias entre los centroides viejos y nuevos
                # es menor al DELTA (1e-5), quiere decir que converge y que halló una solución
                if dif < DELTA:
                    converge = True
                else:
                    converge = False

                response = {"type": "resp", "converge": str(converge), "n_centroids": n_centroids, "clusters": a_clusters}
                f_sck = context.socket(zmq.REQ)
                f_sck.connect(F_DIR) # Conectarse a F
                f_sck.send_json(response)
                print("Response: ", f_sck.recv_json())
                # Reiniciar parametros para ejucion
                n_reducers = 0
                f_reducers = False
                near_centroids = []
                n_e = False
                a_clusters = []

        elif msg["type"] == "end":
            pass

if __name__ == '__main__':
    main()

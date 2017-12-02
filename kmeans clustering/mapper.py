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

DATASETS = ["DS_1Clusters_100Points.txt",
            "DS_3Clusters_999Points.txt",
            "DS2_3Clusters_999Points.txt",
            "DS_5Clusters_10000Points.txt",
            "DS_7Clusters_100000Points.txt"
            ]

class Point():
    def __init__(self, coordinates):
        self.coordinates = coordinates
        self.dimension = len(coordinates)

    def __str__(self):
        return 'Coordinates: ' + str(self.coordinates) + \
               ' -> Dimension: ' + str(self.dimension)

class Cluster:
    def __init__(self, points):
        if len(points) == 0:
            raise Exception("Cluster cannot have 0 Points")
        else:
            self.points = points
            self.dimension = points[0].dimension

        # Check that all elements of the cluster have the same dimension
        for p in points:
            if p.dimension != self.dimension:
                raise Exception(
                    "Point %s has dimension %d different with %d from the rest "
                    "of points") % (p, len(p), self.dimension)

        # Calculate Centroid
        self.centroid = self.calculate_centroid()
        self.converge = False

    def calculate_centroid(self):
        sum_coordinates = np.zeros(self.dimension)
        for p in self.points:
            for i, x in enumerate(p.coordinates):
                sum_coordinates[i] += x

        return (sum_coordinates / len(self.points)).tolist()

def main():
    context = zmq.Context()
    s = context.socket(zmq.REP)
    s.bind(MY_DIR)

    while True:
        print("Esperando conexiones...")
        msg = s.recv_json()

        if msg["type"] == "map":
            # Recibir conexion inicial: mapear
            print("Recibí conexion: ", msg['pr_dataset'])
            s.send_json("OK")

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
            centroids = centroids.split("::")[1:]
            for i, centroid in enumerate(centroids):
                centroids[i] = centroid.split(",")
                centroids[i] = (ast.literal_eval(centroids[i][0]), ast.literal_eval(centroids[i][1]))

            distances = {}
            with open(dataset, "rt") as a_dataset:
                a = list(a_dataset)
                for i, dat in enumerate(data):
                    print("-----------------------")
                    print("Dat: ", dat)
                    centroid = int(dat[0])
                    cont = pdm*int(dat[2])
                    lim = cont + int(dat[1])
                    hsh = dat[0] + "-" + dat[2] + "-" + dat[1]
                    dist = []
                    while cont < lim:
                        print("Cont: {0} lim: {1}".format(cont, lim))
                        point = a[cont].split("::")
                        point = (ast.literal_eval(point[0]), ast.literal_eval(point[1]))
                        #print("i: {0} C: {1} P: {2}".format(i, centroid, point))
                        d = distance.euclidean(point, centroids[centroid])
                        dist.append(d)
                        print("P: {0} C: {1} D: {2}".format(point, centroid, d))
                        cont += 1
                    distances.update({hsh: dist})

            # Enviar distancias a los reducers
            pdr = int(msg["pdr"])
            reducers = int(msg["reducers"])
            raw_reduce = {}

            json_data = json.dumps(distances, indent=2)
            with open(PORT + "n.json", 'w') as output:
                output.write(json_data)

            # Ordenar distancias
            #for j in range(num_clusters):
            #    for d in distances:
            #        inf = d.split("-")
            #        if int(inf[0]) == j:
            #            raw_reduce.update({d: distances[d]})

            json_data = json.dumps(raw_reduce, indent=2)
            with open(PORT + "a.json", 'w') as output:
                output.write(json_data)



        if msg["type"] == "end":
            print("Finalizar conexión")
            return 0

if __name__ == '__main__':
    main()

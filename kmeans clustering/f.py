# Este modulo será el encargado de asignar el trabajo es decir:
#
import numpy as np
import random
from scipy.spatial import distance
import ast
import sys
import zmq
import math

DATASETS = ["DS_1Clusters_100Points.txt",
            "DS_3Clusters_999Points.txt",
            "DS2_3Clusters_999Points.txt",
            "DS_5Clusters_10000Points.txt",
            "DS_7Clusters_100000Points.txt"
            ]
ITERATIONS = 1000

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

    # Conectarse a los mappers, para eso se hace uso de un archivo de texto.
    mappers = []
    try:
        with open(sys.argv[3], "rt") as maps:
            # Conectarse a mappers
            maps = list(maps)
            for i, map_i in enumerate(maps):
                maps[i] = map_i.replace("\n", "")

            for i, m in enumerate(maps):
                ms = context.socket(zmq.REQ)
                ms.connect(m)
                mappers.append(ms)
    except:
        print("Ocurrio un error conectandose a los mappers")

    # Conectarse a los reducers, para eso se hace uso de un archivo de texto.
    reducers = []
    try:
        with open(sys.argv[4], "rt") as reds:
            # Conectarse a reducers:
            reds = list(reds)
            for i, red in enumerate(reds):
                reds[i] = red.replace("\n", "")

            for i, r in enumerate(reds):
                rs = context.socket(zmq.REQ)
                rs.connect(r)
                reducers.append(rs)
    except:
        print("Ocurrio un error conectandose a los reducers")

    print("BIENVENIDO AL CLASIFICADOR")
    try:
        DATASET = int(sys.argv[1]) - 1
        NUM_CLUSTERS = int(sys.argv[2])
        print("Dataset seleccionado: ", DATASETS[DATASET])
    except:
        print("Error: Debe especificar data set >> python f.py NUM_DATASET{1-4}")
        return 0

    # Seleccionar centroides iniciales
    with open(DATASETS[DATASET], "rt") as dataset:
        #print("Cantidad de datos:", len(list(dataset)))
        dataset = list(dataset)
        NUM_DATOS = len(dataset)
        initial = random.sample(dataset, NUM_CLUSTERS)
        str_centroids = ""
        for i, elem in enumerate(initial):
            elem = elem.split("::")
            initial[i] = (ast.literal_eval(elem[0]), ast.literal_eval(elem[1]))
            str_centroids += "::" + elem[0] + "," + str(ast.literal_eval(elem[1]))
        print ("Centroides iniciales: ", initial)
    # Crear los N clusters iniciales
    clusters = []
    for point in initial:
        clusters.append(Cluster([Point(point)]))

    # Inicialize list of lists to save the new points of cluster
    new_points_cluster = []
    for i in range(NUM_CLUSTERS):
        new_points_cluster.append([])

    converge = False
    it_counter = 0

    # Parametros de trabajo:
    C = NUM_DATOS*NUM_CLUSTERS # Es la cantidad total de datos que deberá procesar
    limM = math.floor(C/len(mappers)) # Es el numero maximo de datos que puede tomar un mapper
    limR = math.floor(C/len(reducers))# Es el numero maximo de datos que puede tomar un reducer
    pdm = math.floor(NUM_DATOS/len(mappers)) # Es la porcion de datos por cluster con los que trabajara el mapper
    pdr = math.floor(NUM_DATOS/len(reducers))# Es la porcion de datos por cluster con los que trabajara el reducer
    print("C: {0} lm: {1} lr: {2} pdm: {3} pdr: {4}".format(C, limM, limR, pdm, pdr))
    # Ciclo principal, el programa se ejecuta hasta que converga el algoritmo
    # o hasta que se cumpla cierta cantidad iteraciones
    while (not converge) and (it_counter < ITERATIONS):
        # Asignar trabajo a cada mapper dependiendo de los clusters:
        cont_cluster = 0
        cap = []    # Este arreglo de igual tamaño a la cantidad de clusters
                    # contiene la informacion de cuanta porcion de datos ha sido entregada para un cluster
        for i in clusters:
            cap.append(NUM_DATOS) # Cada cluster analiza la misma cantidad de datos

        cont = int(NUM_DATOS/pdm)    # Necesitamos conocer que seccion del dataset leera un cluster
                    # evitando que otro cluster lea dicha parte.
        for i in range(len(mappers)):
            msg = ""    # Mensaje que se le enviara la mapper para que este sepa que
                        # datos debe examinar
            capm = 0 # Contador que mide cuanta porcion de datos ha entregado a un mapper
            print(".................")
            while cap[cont_cluster] > 0 and limM > capm:
                msg = "|" + str(cont_cluster) + ":" + str(pdm + cap[cont_cluster]%pdm) + ":" + str(cont-1) + msg

                # cap[cont_cluster]%pdm es un incremento que se hace cuando la porcion restante por enviar
                # no alcanza a ser divisible por pdm eje: resta 34 por enviar y el pdm es de 33, este incrementaria 1
                capm += pdm + cap[cont_cluster]%pdm
                cap[cont_cluster] -= pdm + cap[cont_cluster]%pdm
                cont -= 1
                if cap[cont_cluster] == 0:
                    cont_cluster += 1
                    cont = int(NUM_DATOS/pdm)
                if cont_cluster >= len(clusters):
                    break
            print("Enviar a Mapper ", i+1, " :", msg)
            mappers[i].send_json({"type": "map", "dataset": DATASETS[DATASET],
                                  "pr_dataset": msg, "clusters": len(clusters),
                                  "centroids": str_centroids,
                                  "pdm": pdm,
                                  "pdr": pdr,
                                  "reducers": len(reducers)}
                                )
            r = mappers[i].recv_json()
            if not r == "OK":
                print("Ocurrio un problema")
                return 0
        break

        #break

if __name__ == '__main__':
    main()

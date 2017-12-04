# Este modulo será el encargado de asignar el trabajo es decir:
#
import numpy as np                  # Trabajo con arreglos
import random                       # Generar numeros aleatoreos
from scipy.spatial import distance
import ast
import sys
import zmq
import math
import json
import matplotlib.pyplot as plt

# Datasets de pruebas en dos dimensiones
DATASETS = ["datasets/DS_1Clusters_100Points.txt",
            "datasets/DS_3Clusters_999Points.txt",
            "datasets/DS2_3Clusters_999Points.txt",
            "datasets/DS_5Clusters_10000Points.txt",
            "datasets/DS_7Clusters_100000Points.txt"
            ]

# En el caso de que no se logre convergencia es conveninete tener iteraciones limite
ITERATIONS = 1000

# Colores para mostrar graficamente los puntos
COLORS = ['red', 'blue', 'green', 'yellow', 'gray', 'pink', 'violet', 'brown',
          'cyan', 'magenta']

# Direccion para escuchar las solicitudes de S
MY_DIR = "tcp://*:3001"

def main():
    context = zmq.Context()
    s = context.socket(zmq.REP)
    s.bind(MY_DIR)

    # Conectarse a los mappers, para eso se hace uso de un archivo de texto.
    mappers = []
    try:
        with open(sys.argv[3], "rt") as maps:
            # Conectarse a mappers
            maps = list(maps)
            # Procesar el texto
            for i, map_i in enumerate(maps):
                maps[i] = map_i.replace("\n", "")

            # Llenar el arreglo de socket
            for i, m in enumerate(maps):
                ms = context.socket(zmq.REQ)
                ms.connect(m)
                mappers.append(ms)
    except:
        print("Ocurrio un error conectandose a los mappers")

    # Conectarse a los reducers, para eso se hace uso de un archivo de texto.
    reducers = []   # Arreglo para los sockets
    ip_reducers = []# Arreglo para las direcciones ip respectivas
    try:
        with open(sys.argv[4], "rt") as reds:
            # Procesar el texto
            reds = list(reds)
            for i, red in enumerate(reds):
                reds[i] = red.replace("\n", "")

            # Llenar el arreglo de sockets
            for i, r in enumerate(reds):
                rs = context.socket(zmq.REQ)
                rs.connect(r)
                ip_reducers.append(r)
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

        # random.sample permite extraer un numero N de datos de un arreglo
        initial = random.sample(dataset, NUM_CLUSTERS)
        str_centroids = "" # Cadena para representar a los centroides

        # Los puntos en el dataset viene de la forma x::y
        for i, elem in enumerate(initial):
            elem = elem.split("::")
            p = []
            # Convertir de cadena al punto
            for j, e in enumerate(elem):
                p.append(ast.literal_eval(elem[j])) #ast.literal_eval convierte cadena a float
            initial[i] = p
                #initial[i] = (ast.literal_eval(elem[0]), ast.literal_eval(elem[1]))

            # Construir cadena para representar los centroides
            st = ""
            for j, e in enumerate(elem):
                if j == len(elem) - 1:
                    # Al final de la linea siempre esta el simbolo \n, por eso
                    # convertimos a flotante y luego lo pasamos a cadena
                    st += str(ast.literal_eval(elem[j]))
                else:
                    st += elem[j] + ","
            str_centroids += "::" + st #elem[0] + "," + str(ast.literal_eval(elem[1]))
        print ("Centroides iniciales: ", initial)

    # Crear los N clusters iniciales
    clusters = []
    # Iniciamos los N cluster apartir de los primeros centroides.
    for point in initial:
        clusters.append([point])

    # Varia que determina si el algoritmo converge o no
    converge = False
    # Contador de interaciones
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

        cont = int(NUM_DATOS/pdm)   # Necesitamos conocer que seccion del dataset leera un cluster
                                    # evitando que otro cluster lea dicha parte.
        for i in range(len(mappers)):
            msg = ""    # Mensaje que se le enviara la mapper para que este sepa que
                        # datos debe examinar
            capm = 0 # Contador que mide cuanta porcion de datos ha entregado a un mapper
            #print(".................")
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
            #print("Enviar a Mapper ", i+1, " :", msg, " c: ", str_centroids)
            mappers[i].send_json({"type": "map", "dataset": DATASETS[DATASET],
                                  "pr_dataset": msg, "clusters": len(clusters),
                                  "centroids": str_centroids,
                                  "pdm": pdm,
                                  "pdr": pdr,
                                  "reducers": ip_reducers,
                                  "mappers": len(mappers)}
                                )
            r = mappers[i].recv_json()
            if not r == "OK":
                print("Ocurrio un problema")
                return 0

        # Comprar que converja
        resp = s.recv_json()
        if resp["type"] == "resp":
            s.send_json("OK")

            if resp["converge"] == "True":
                converge = True

                #plt.plot()
                #for i, cluster in enumerate(resp["clusters"]):
                    # plot points
                #    for point in cluster:
                #        x, y = point[0], point[1]
                #        plt.plot(x, y, linestyle='None', color=COLORS[i], marker='.')
                #    plt.plot(resp["n_centroids"][i][0], resp["n_centroids"][i][1], 'o', color=COLORS[i],
                #             markeredgecolor='k', markersize=10)
                #plt.show()
                # Crear archivo para centroides:
                save = {"centroids: ": resp["n_centroids"]}
                json_data = json.dumps(save, indent=2)
                with open("centroids.json", 'w') as output:
                    output.write(json_data)

                # Crear archivo para los clusters:
                for i in range(len(resp["clusters"])):
                    save = {i: resp["clusters"][i]}
                    json_data = json.dumps(save, indent=2)
                    with open(str(i) + "cluster.json", 'w') as output:
                        output.write(json_data)

                print("--------------------------------------------------------")
                print("EJECUCIÓN TERMINADA: ")
            else:
                it_counter += 1
                print("--------------------------------------------------------")
                print("Iter: ", it_counter)
                print("Estado: ")
                print("centroides viejos: ")
                for strc in str_centroids.split("::"):
                    print(strc)

                str_centroids = ""
                for i, centroid in enumerate(resp["n_centroids"]):
                    cad = ""
                    for j, ce in enumerate(centroid):
                        if j == len(centroid) - 1:
                            cad += str(centroid[j])
                        else:
                            cad += str(centroid[j]) + ","
                    str_centroids += "::" + cad
                print("Centroides nuevos: ")
                for strc in str_centroids.split("::"):
                    print(strc)

        #break

if __name__ == '__main__':
    main()

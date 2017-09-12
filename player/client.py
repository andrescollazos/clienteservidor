import zmq
import sys
import pygame

def main():
    pygame.init()

    TRACK_END = pygame.USEREVENT+1
    TRACKS = []#"1.ogg","3.ogg"] #Three sound effects I have
    track = 0
    # Create the socket and the context
    context = zmq.Context()
    s = context.socket(zmq.REQ)
    s.connect("tcp://localhost:5555")

    print("/////////////////////////////////")
    print("Player ISC")
    print("/////////////////////////////////")

    pygame.display.set_mode((500,500))
    pygame.mixer.music.set_endevent(TRACK_END)

    parte = 0
    while True:
        for event in pygame.event.get():
            # En caso de cerrar la ventana, se termina el programa
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            # Cuando se termina una cancion
            elif event.type == TRACK_END:
                # Recorrer el arreglo de canciones de forma ciclica
                track = (track+1)%len(TRACKS)
                # Cargar cancion
                pygame.mixer.music.load(TRACKS[track])
                # Reproducir
                pygame.mixer.music.play()
            # Cuando el usuario presiona una tecla sobre la ventana:
            elif event.type == pygame.KEYDOWN:
                # Las operaciones tienen dos argumentos: operacion y cancion
                operacion = input("\nOperacion? ")
                operacion = operacion.split(" ")
                try:
                    cancion = operacion[1]
                except:
                    pass
                try:
                    # Porcentaje de la cancion que escuchara el usuario
                    porcentaje = int(operacion[2])
                except:
                    # A no ser de que lo especifique, solicitara la cancion al 100%
                    porcentaje = 100
                operacion = operacion[0]
                #print ("Operacion [{}, {}]".format(operacion, cancion))

                if operacion == "lista":
                    s.send_json({"operacion": "lista"})
                    respuesta = s.recv_json()
                    print("Canciones disponibles")
                    for i, c  in enumerate(respuesta["canciones"]):
                        print("\t{0}.{1}".format(i + 1, c))
                elif operacion == "reproducir" or operacion == "adicionar":
                    #cancion_recibida = False
                    if operacion == "reproducir":
                        TRACKS = []
                    s.send_json({"operacion": "descarga",
                                 "cancion": cancion,
                                 "porcentaje": porcentaje,
                                 "parte": "-1",
                                })
                    datos = s.recv_json()
                    cantidad_partes = int(datos["cantidad_partes"])

                    while not parte == cantidad_partes:
                        #print("[PETICION ENVIADA]: [descarga,{0},{1},{2}]".format(cancion, porcentaje, parte))
                        s.send_json({"operacion": "descarga",
                                     "cancion": cancion,
                                     "porcentaje": porcentaje,
                                     "parte": parte
                                    })
                        musicaOgg = s.recv()
                        with open(cancion, "ab") as archivoOgg:
                            archivoOgg.write(musicaOgg)
                            parte += 1
                            print("Partes recibidas: ", parte)
                    parte = 0
                    TRACKS.append(cancion)
                    if operacion == "reproducir":
                        pygame.mixer.music.load(TRACKS[0])
                        pygame.mixer.music.play()
                else:
                    print("No esta implementando")

if __name__ == '__main__':
    main()

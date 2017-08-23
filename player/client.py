import zmq
import sys
import pygame

def main():
    pygame.init()

    TRACK_END = pygame.USEREVENT+1
    TRACKS = []#"1.ogg","3.ogg"] #Three sound effects I have
    track = 0
    init = True
    # Create the socket and the context
    context = zmq.Context()
    s = context.socket(zmq.REQ)
    s.connect("tcp://localhost:5555")

    print("/////////////////////////////////")
    print("Player ISC")
    print("/////////////////////////////////")

    pygame.display.set_mode((500,500))
    pygame.mixer.music.set_endevent(TRACK_END)

    n_cancion = 1
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
                # Verificar que tenga dos argumentos, ya que la operacion lista solo tiene 1
                if len(operacion) > 1:
                    cancion = operacion[1]
                operacion = operacion[0]
                #print ("Operacion [{}, {}]".format(operacion, cancion))

                if operacion == "lista":
                    s.send_json({"operacion": "lista"})
                    respuesta = s.recv_json()
                    print("Canciones disponibles")
                    for i, c  in enumerate(respuesta["canciones"]):
                        print("\t{0}.{1}".format(i + 1, c))
                elif operacion == "reproducir":
                    TRACKS = [] # Reproducir elimina lista de reproducir
                    s.send_json({"operacion": "reproducir", "cancion":cancion})
                    musicaOgg = s.recv()
                    # Crear archivo
                    with open(cancion, "wb") as archivoOgg:
                        archivoOgg.write(musicaOgg)
                        TRACKS.append(cancion) # Agregar a la lista de canciones
                        # Cargar cancion
                        pygame.mixer.music.load(TRACKS[0])
                        # Reproducir
                        pygame.mixer.music.play()

                elif operacion == "adicionar" and len(TRACKS) > 0:
                    s.send_json({"operacion": "reproducir", "cancion":cancion})
                    musicaOgg = s.recv()

                    with open(cancion, "wb") as archivoOgg:
                        archivoOgg.write(musicaOgg)
                        TRACKS.append(cancion)

                else:
                    print("No esta implementando")


if __name__ == '__main__':
    main()

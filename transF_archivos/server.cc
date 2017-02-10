#include <iostream>
#include <string>
#include <zmqpp/zmqpp.hpp>
#include <math.h>
#include <fstream>
#include <cstring>

using namespace std;
using namespace zmqpp;

int main() {

  cout << "This is the server\n";

	context ctx;
	socket s(ctx, socket_type::rep);

	cout << "Binding socket to tcp port 5555\n";
	s.bind("tcp://*:5555");

	while (true) {
		cout << "Waiting for message to arrive!\n";
		message m;
		s.receive(m);

    string order;
    m >> order;

    if (order == "m") {
      cout << "MOSTRAR TODOS LOS ARCHIVOS" << endl;
      s.send("Estos son mis archivos \n\t1. IMAGEN\n\t2.imagen2\n\t3.imgaen3.\n");
    }
  }
   /*
   ofstream fsalida("prueba.dat",
      ios::out | ios::binary);

   strcpy(pepe.nombre, "Jose Luis");
   pepe.edad = 32;
   pepe.altura = 1.78;

   string g = "bin1";
   fsalida.write(reinterpret_cast<char *>(&g), sizeof(g));
   fsalida.close();

   ifstream fentrada("prueba.dat", ios::in | ios::binary);

   string text = "    ";
   fentrada.read(reinterpret_cast<char *>(&text), sizeof(text));
   cout << text << endl << "HOLAAAAAAA" << endl;
   fentrada.close(); */

   return 0;
}

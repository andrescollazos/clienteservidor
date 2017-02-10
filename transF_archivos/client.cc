#include <iostream>
#include <string>
#include <iostream>
#include <zmqpp/zmqpp.hpp>

using namespace std;
using namespace zmqpp;

int main() {
	cout << "DESCARGA TUS ARCHIVOS...\n";

	context ctx;
	socket s(ctx, socket_type::req);

	//cout << "Connecting to tcp port 5555\n";
	s.connect("tcp://localhost:5555");

	message lista;
	lista << "m";
	s.send(lista);

	message answer;
	string listado;
	
	s.receive(answer);
	answer >> listado;

	cout << "LISTA DE ARCHIVOS DISPONIBLES EN EL SERVIDOR: " << endl;
	cout << listado << endl;


	return 0;
}

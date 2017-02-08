/*
	Se construye una calculadora basica, el servidor recibe los siguientes tipos de
	Mensajes y en base en ellos hace el calculo respectivo y retorna el resultado al
	cliente.

	Tipos de Operaciones recibidas:
		"+ a b" Suma
		"- a b" Resta
		"* a b" Multiplicacion
		"/ a b" Division
		"r a b" Raiz b de a (a elevado a la 1/b)
		"p a b" a elevado a la b
*/
#include <iostream>
#include <string>
#include <zmqpp/zmqpp.hpp>

using namespace std;
using namespace zmqpp;

int main() {
	cout << "CALCULADORA\n";

	context ctx;
	socket s(ctx, socket_type::rep);

	cout << "[SERVER DICE]: Binding socket to tcp port 5555\n";
	s.bind("tcp://*:5555");
	while (true) {
		cout << "[SERVER DICE]: Esperando mensajes...\n";
		message m;
		s.receive(m);

		string text;
		m >> text;
		cout << "[SERVER DICE]: Recibi -> " << text << endl;
	  cout << "Finished\n";
		return 0;
	}
}

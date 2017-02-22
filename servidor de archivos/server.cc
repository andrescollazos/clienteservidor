#include <iostream>
#include <string>
#include <fstream>
#include <zmqpp/zmqpp.hpp>

using namespace std;
using namespace zmqpp;

// Funcion que permite leer los bytes de un archivo y retornarlos en un vector
vector<char> readFileToBytes(const string& fileName) {
	// ios::binary - > Abrir el archivo en modo binario
	// ios::ate -> Posicionar el puntero al final del archivo
	ifstream ifs(fileName, ios::binary | ios::ate);
	ifstream::pos_type pos = ifs.tellg(); // Conocer la cantidad de bytes del arch.

	vector<char> result(pos);

	// Retornar el puntero a la primera posicion
	ifs.seekg(0, ios::beg);
	ifs.read(result.data(), pos);

	return result;
}

// Convertir un fichero a un mensaje para enviar
void fileToMesage(const string& fileName, message& msg) {
	// Convertir un archivo en un vector de bytes
	vector<char> bytes = readFileToBytes(fileName);
	msg.add_raw(bytes.data(), bytes.size());
}

// Convertir un mensaje a un fichero
void messageToFile(const message& msg, const string& fileName) {
	// Tener apuntar a un espacio en memoria donde estaran los datos
	const void *data;
	msg.get(&data, 0); // Obtener el primer elemento del mensaje
	size_t size = msg.size(0); // Calcular los bytes

	// Crear un archivo, que se trabajara de manera binaria
	ofstream ofs(fileName, ios::binary);
	// Escribir los bytes en el archivo
	ofs.write((char*)data, size);
}

int main() {
	cout << "SERVIDOR\n";

	context ctx;
	socket s(ctx, socket_type::rep);
	s.bind("tcp://*:5555");

	// Recibir primer mensaje:
	// op - filename
	// op: operacion a realizar up - down - list - remove
	// filename: nombre del archivo.
	message m;
	string fileName, op;
	
	while (true) {
		s.receive(m);
		m >> op >> fileName;

		// Saber que operacion va a realizar el usuario

		// Descargar archivo
		if (op == "down") {
			cout << "[SERVER]: Solicitud de Descarga: " << fileName << endl;
			message response;
			fileToMesage(fileName, response);
			s.send(response);
			cout << "[SERVER]: Descarga Realizada" << endl;
		}
		// Subir archivo
		else if (op == "up") {
			// El servidor envia un mensaje "f",
			// que significa que el usuario puede enviar los bytes
			s.send("f");

			// Se prepara un mensaje para recibir los bytes
			message file;
			s.receive(file);
			cout << "[SERVER]: Solicitud de subida: " << fileName << endl;

			string upName("up-" + fileName);
			messageToFile(file, upName);
			cout << "[SERVER]: Subida Realizada" << endl;
		}
	}
	cout << "Finished\n";
	return 0;
}

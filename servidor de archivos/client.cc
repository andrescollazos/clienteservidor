#include <iostream>
#include <string>
#include <vector>
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

int main(int argc, char** argv) {
	cout << "SERVIDOR DE TRANSFERENCIA DE ARCHIVOS" << endl;
	// argv[1] -> Nombre del archivo
	// argv[2] -> Operacion a realizar: up - down - list - remove

	if (argc != 3) {
		cerr << "Must be called: " << argv[0] << " file operation\n";
		return 1;
	}

	context ctx;
	socket s(ctx, socket_type::req);
	s.connect("tcp://localhost:5555");

	// Nombre del archivo
	string fileName(argv[1]);
	message m;
	m << argv[2] << fileName;
	s.send(m);

	// Casos de uso

	// Descargar archivo:
	if ((string)argv[2] == "down") {
		message file;
		cout << "[SERVER]: Recibiendo Archivo ..." << endl;
		s.receive(file);
		cout << "[SERVER]: Archivo recibido ..." << endl;

		// File contiene los bytes que seran escritos
		string downloadName("down-" + fileName); // Cambiar de nombre
		cout << "[SERVER]: Sincronizando archivo ..." << endl;
		messageToFile(file, downloadName);
		cout << "[SERVER]: Operacion terminada ..." << endl;

	}
	else if ((string)argv[2] == "up") {
		message response;
		s.receive(response);
		string ack;
		response >> ack;

		if (ack == "f") {
			cout << "[SERVER]: Proceso de subir archivo autorizado ..." << endl;
			message file;
			// Convertir archivo a un mensaje
			fileToMesage(fileName, file);
			cout << "[SERVER]: Subiendo archivo ..." << endl;
			s.send(file);
			cout << "[SERVER]: Archivo subido ..." << endl;
		}
	}

	return 0;
}

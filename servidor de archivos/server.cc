#include <iostream>
#include <string>
#include <fstream>
#include <zmqpp/zmqpp.hpp>
#include "user.h"

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
	// Realizar operaciones sobre los archivos directamente es mas lento, que
	// cargarlos a memoria, procesarlos y una vez terminado ese proceso, guardarlos
	cout << "[SERVER]: Esperando conexiones ..." << endl;

	context ctx;
	socket s(ctx, socket_type::rep);
	s.bind("tcp://*:5555");

	// Recibir primer mensaje:
	// op - filename
	// op: operacion a realizar up - down - list - remove
	// filename: nombre del archivo.
	message m;
	string fileName, op;
	string username, password;

	// Proceso de autenticacion:
	s.receive(m);
	user useri; // Contiene la informacion de un usuario i
	bool exists = false;
	m >> username >> password;

	// El servidor recibe la conexion de un usuario con nombre y contrasena
	// En caso de que el servidor no encuentre el archivo del usuario, lo creara
	string archive_name = "." + username + ".dat";
	ifstream if_user(archive_name, ios::in | ios::binary);
	if(if_user.good()) {
		cout << "[SERVER]: Cargando Datos de Usuario: " << endl;
		useri.read(if_user);
		exists = true;
	}
	// En caso de que el usuario no exista, se crea un objeto
	if(!exists) {
		cout << "[SERVER]: Usuario no existia, se crea ..." << endl;
		useri.userName_ = username;
		useri.password_ = password;
	}
	ofstream of_user;
	of_user.open(archive_name, ios::out | ios::app | ios::binary);
	if (!of_user.is_open()) {
		cout << "[SERVER]: Error al abrir el archivo!" << endl;
		return -1;
	}
	s.send("authenticated");
	cout << "[SERVER]: Usuario autenticado-- Puede iniciar peticiones " << endl;
	while(true) {
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

			string upName(useri.userName_ + "-" + fileName);
			messageToFile(file, upName);
			useri.archives_.push_back(upName);
			useri.write(of_user);
			cout << "[SERVER]: Subida Realizada" << endl;
			s.send("correctamente"); // Se subio el archivo correctamente
		}
		else if (op == "rm") {
			cout << "[SERVER]: Solicitud de Borrado" << endl;
			string remov = "up-" + fileName;
			// La funcion remove() recibe const char, no string
			const char * rem = remov.c_str(); // Conversion string -> const char
			if (remove(rem)!= 0) {
				cout << "[SERVER]: Borrado Incorrecto" << endl;
				s.send("Incorrecto");
			}
			else {
				cout << "[SERVER]: Borrado Correctamente" << endl;
				s.send("Correctamente");
			}
		}
		else if (op == "finish") {
			cout << "[SERVER]: Terminar!" << endl;
			useri.write(of_user);
			of_user.close();
			break;
		}
	}

	cout << "Finished\n";
	return 0;
}

#include <iostream>
#include <string>
#include <fstream>
#include <zmqpp/zmqpp.hpp>
#include "json.hpp"

using namespace std;
using namespace zmqpp;
using json = nlohmann::json;

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
	string username; //, password;
	json dates;


	while(true) {
		system("clear");

		s.receive(m);
		m >> username >> op >> fileName;

		// Saber que operacion va a realizar el usuario

		// Descargar archivo
		if (op == "down") {
			cout << "[SERVER]: Solicitud de Descarga: " << fileName << endl;
			// Comprar que existe el archivo y que es del usuario:
			ifstream proof(username + "-" + fileName, ios::binary);
			if (proof.good()) {
				cout << "Archivo si existe!" << endl;
				proof.close();
				message response;
				fileToMesage(username + "-" + fileName, response);
				cout << "[SERVER]: Enviando archivo ..." << endl;
				s.send("ok"); // Informa que empieza la descarga
				s.receive(m);
				s.send(response);
				cout << "[SERVER]: Descarga Realizada" << endl;
				//s.receive(m);
			}
			else {
				cout << "[SERVER]: El archivo solicitado NO se encuentra" << endl;
				s.send("bad"); // Informa que la descarga no sera realizada
				//s.receive(m);
			}
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

			string upName(username + "-" + fileName);
			messageToFile(file, upName);
			dates[username].push_back(upName);
			cout << "[SERVER]: Subida Realizada" << endl;
			s.send("correctamente"); // Se subio el archivo correctamente

			for (json::iterator it = dates.begin(); it != dates.end(); ++it) {
        cout << it.key() << " : " << it.value() << "\n";
      }
		}
		else if (op == "rm") {
			cout << "[SERVER]: Solicitud de Borrado" << endl;
			string remov = username + "-" + fileName;
			// La funcion remove() recibe const char, no string
			const char * rem = remov.c_str(); // Conversion string -> const char
			if (remove(rem)!= 0) {
				cout << "[SERVER]: Borrado Incorrecto" << endl;
				s.send("Incorrecto");
			}
			else {
				//useri.pop(fileName);
				cout << "[SERVER]: Borrado Correctamente" << endl;
				s.send("Correctamente");
			}
		}
		else if (op == "list") {
			cout << "[SERVER]: Solicitud de Listado" << endl;
			//string list_ = "";
			json lst;
			lst["lista"] = dates[username];
			string mtext = lst.dump(); // Serializar
			s.send(mtext);
		}
	}

	cout << "Finished\n";
	return 0;
}

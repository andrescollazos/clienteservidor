#include <iostream>
#include <string>
#include <vector>
#include <fstream>
#include <zmqpp/zmqpp.hpp>
#include <unistd.h>
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

int main(int argc, char** argv) {
	cout << "SERVIDOR DE TRANSFERENCIA DE ARCHIVOS" << endl;
	// argv[1] -> Nombre del archivo
	// argv[2] -> Operacion a realizar: up - down - list - remove

	if (argc != 2) {
		cerr << "Error: " << argv[0] << " debe especificar username\n";
		return 1;
	}

	context ctx;
	socket s(ctx, socket_type::req);
	s.connect("tcp://localhost:5555");
	//string aut;
	string username(argv[1]);


	while(true) {
		system("clear");
		int opcion = 0;
		while(not(opcion >= 1 && opcion <= 5)) {
			cout << "OPCIONES:" << endl;
			cout << "\t1. Subir Archivo" << endl;
			cout << "\t2. Descargar Archivo" << endl;
			cout << "\t3. Eliminar Archivo" << endl;
			cout << "\t4. Listar Archivos" << endl;
			cout << "\t5. Salir" << endl;
			cout << "DIGITE UNA OPCION: ";
			cin >> opcion;
		}

		string fileName;
		message m;

		// Casos de uso

		// Descargar archivo:
		if (opcion == 2) {
			cout << "\n\t DESCARGAR ARCHIVOS" << endl;
			cout << "Digite el nombre del archivo (con su extension): ";
			cin >> fileName;
			m << username << "down" << fileName;
			s.send(m);

			message approved;
			string app;
			s.receive(approved);
			approved >> app;

			if (app == "ok") {
				s.send("ok"); // Listo para recibir archivo..
				message file;
				cout << "[SERVER]: Recibiendo Archivo ..." << endl;
				s.receive(file);
				cout << "[SERVER]: Archivo recibido ..." << endl;

				// File contiene los bytes que seran escritos
				string downloadName("down-" + username + "-" + fileName); // Cambiar de nombre
				cout << "[SERVER]: Sincronizando archivo ..." << endl;
				messageToFile(file, downloadName);
				cout << "[SERVER]: Operacion terminada ..." << endl;
				//s.send("ok");
			}
			else if (app == "bad"){
				//s.send("ok");
				cout << "[SERVER]: No se encuentra el archivo especificado." << endl ;
			}
		}
		else if (opcion == 1) {
			cout << "\n\t SUBIR ARCHIVOS" << endl;
			cout << "Digite el nombre del archivo (con su extension): ";
			cin >> fileName;
			m << username << "up" << fileName;
			s.send(m);

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

				s.receive(response);
				response >> ack;
				cout << "[SERVER]: Archivo subido: " << ack << endl;
			}
		}
		else if (opcion == 3) {
			cout << "\n\t ELIMINAR ARCHIVOS" << endl;
			cout << "Digite el nombre del archivo (con su extension): ";
			cin >> fileName;
			m << username << "rm" << fileName;
			s.send(m);

			cout << "[SERVER]: Procediendo a eliminar archivo ..." << endl;
			message response;
			s.receive(response);
			string result;
			response >> result;

			cout << "Proceso completado: " << result << " ..." << endl;
		}
		else if (opcion == 4) {
			cout << "\n\t LISTAR ARCHIVOS" << endl;
			m << username << "list" << "";
			s.send(m);

			//cout << "[SERVER]: Esperando listado de archivos ..." << endl;

			s.receive(m);
			string result;
			m >> result;
			json lst = json::parse(result);
			cout << "Lista de archivos:" << endl;
			for (json::iterator it = lst.begin(); it != lst.end(); ++it) {
  			cout << it.value() << "\n";
			}

			usleep(5000000);
		}
		else if (opcion == 5) {
			cout << "TERMINANDO SESIÓN ..." << endl;
			break;
		}
	}

	return 0;
}

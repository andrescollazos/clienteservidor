#include <iostream>
#include <string>
#include <fstream>
#include <zmqpp/zmqpp.hpp>

using namespace std;
using namespace zmqpp;

// Clase Usuario
class user {
	public:
		string name;
		string password;
		vector<string> archives;

		void reg(string nom, string pass) {
			name = nom;
			password = pass;
		}
		void add_arch(string arch) {
			archives.push_back(arch);
		}

		void view() {
			std::cout << "Nombre: " << name << endl;
			std::cout << "Archivos: " << endl;
			int sze = (int)archives.size();
			for(int i = 0; i < sze ; i++) {
				std::cout << "\t "<< (i+1) << ". " << archives[i] << endl;
			}
		}
};

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
	vector<user> users; // Vector que contiene la informacion en tiempo de ejecucion
	user useri; // Contiene la informacion de un usuario i
	int n_users = 0; // Numero de usuarios
	ifstream if_users_arch(".users.dat", ios::in | ios::binary);
	// El archivo debe existir, si no se crea
	if (if_users_arch.good()) {
		cout << "[SERVER]: Cargando datos de usuarios ..." << endl;
		if_users_arch.seekg(0, ios::end);
		ifstream::pos_type pos = if_users_arch.tellg();
		if_users_arch.seekg(0, ios::beg);
		n_users = ((int)pos)/((int)sizeof(user));
		cout << "[SERVER]: Cantidad de usuarios " << n_users << endl;
		for(int i = 0; i < n_users; i++) {
			cout << "\tCargando Usuario: ";
			if_users_arch.read(reinterpret_cast<char *>(&useri), sizeof(user));
			cout << useri.name << " ..." << endl;
			users.push_back(useri);
		}
		int a;
		cout << "a: ";
		cin >> a;
		cout << "AL MENOS NO ENTRO" << endl;
		if_users_arch.close();
		cout << "[SERVER]: Datos cargados correctamente ..." << endl;
	}
	ofstream of_users_arch(".users.dat", ios::out | ios::binary);

	//fsalida.write(reinterpret_cast<char *>(&andres), sizeof(user));

	cout << "[SERVER]: Esperando peticiones ..." << endl;

	context ctx;
	socket s(ctx, socket_type::rep);
	s.bind("tcp://*:5555");

	// El servidor recibe la conexion de un usuario con nombre y contrasena
	// En caso de que el servidor no encuentre el usuario en los registros
	// le informara que no existe el usuario, que si desea crearlo.
	while (true) {
		// Recibir primer mensaje:
		// op - filename
		// op: operacion a realizar up - down - list - remove
		// filename: nombre del archivo.
		message m;
		string fileName, op;
		string username, password;
		bool exists = false;
		bool auth;

		// Proceso de autenticacion:
		s.receive(m);
		m >> username >> password;
		// Comprobar que el usuario exista.
		for (int i = 0; i < n_users; i++) {
			if (users[i].name == username) {
				// El usuario existe, debemos comprar la contrasena
				exists = true;
				if (users[i].password == password) {
					cout << "[SERVER]: autenticacion terminada" << endl;
					s.send("authenticated");
					auth = true;
				}
				else {
					cout << "[SERVER]: Contrasenia incorrecta" << endl;
					s.send("password-err");
					auth = false;
				}
			}
		}
		if (not(exists)) {
			// EL usuario no existe, entonces se crea:
			cout << "[SERVER]: Usuario no exite, se procede a crearlo" << endl;
			s.send("bad-authenticated");
			useri.reg(username, password);
			users.push_back(useri);
			of_users_arch.write(reinterpret_cast<char *>(&useri), sizeof(user));
			n_users++;
			auth = false;
		}

		if (auth) {
			cout << "[SERVER]: Usuario autenticado-- Puede iniciar peticiones " << endl;
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
				of_users_arch.close();
				break;
			}
		}
	}
	cout << "Finished\n";
	return 0;
}

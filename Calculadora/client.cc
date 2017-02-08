#include <iostream>
#include <string>
#include <iostream>
#include <zmqpp/zmqpp.hpp>

using namespace std;
using namespace zmqpp;

int main() {
	message m;
	int opcion = -1;
	string a, b;

	cout << "CALCULADORA\n";

	context ctx;
	socket s(ctx, socket_type::push);

	//cout << "Connecting to tcp port 5555\n";
	s.connect("tcp://localhost:5555");

	cout << "Tipo de operaciones: \n";
	cout << "\t1. + a b : Suma a con b\n";
	cout << "\t2. - a b : Resta a con b\n";
	cout << "\t3. * a b : Multiplica a con b\n";
	cout << "\t4. / a b : Divide a entre b\n";
	cout << "\t5. r a b : a elevado a la 1/b\n";
	cout << "\t6. p a b : Eleva a la b\n";

	while (not (opcion > 0 && opcion <= 6)) {
		cout << "\nSeleccione una de las opciones: ";
		cin >> opcion;
	}

	cout << "\n Digite a: ";
	cin >> a;
	cout << a << "\n";
	cout << "\n Digite b: ";
	cin >> b;
	cout << b << "\n";

	if (opcion == 1) {
		cout << "\n Escogite la opcion SUMA";
		string men = "+ " + a + " " + b;
		m << men;
		s.send(m);
	}
	if (opcion == 2) {
		cout << "\n Escogite la opcion RESTA";
		m << "- " + a + b ;
	}
	if (opcion == 3) {
		cout << "\n Escogite la opcion MULTIPLICACION";
		m << "* " + a + b ;
	}
	if (opcion == 4) {
		cout << "\n Escogite la opcion DIVISION";
		m << "/ " + a + b ;
	}
	if (opcion == 5) {
		cout << "\n Escogite la opcion RADICACION";
		m << "r " + a + b ;
	}
	if (opcion == 6) {
		cout << "\n Escogite la opcion POTENCIACION";
		m << "p " + a + b ;
	}

	s.send(m);
	int i;
	cin >> i;
	cout << "\n\n Finished";

	return 0;
}

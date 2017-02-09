#include <iostream>
#include <string>
#include <iostream>
#include <zmqpp/zmqpp.hpp>

using namespace std;
using namespace zmqpp;

int main() {
	cout << "CALCULADORA\n";

	context ctx;
	socket s(ctx, socket_type::req);

	//cout << "Connecting to tcp port 5555\n";
	s.connect("tcp://localhost:5555");

	cout << "Tipo de operaciones: \n";
	cout << "\t1. + a b : Suma a con b\n";
	cout << "\t2. - a b : Resta a con b\n";
	cout << "\t3. * a b : Multiplica a con b\n";
	cout << "\t4. / a b : Divide a entre b\n";
	cout << "\t5. f a : Factorial de a\n";
	cout << "\t6. p a : a es primo? \n";

	int opcion = 0;
	int a, b;

	while (not (opcion >= 1 && opcion <= 6)) {
		cout << "\nSeleccione una de las opciones: ";
		cin >> opcion;
	}

	cout << "\n Digite a: ";
	cin >> a;
	if (not(opcion >= 5)) {
		cout << "\n Digite b: ";
		cin >> b;
	}

	message m;
	if (opcion == 1) {
		m << "+" << a << b;
	}
	else if (opcion == 2) {
		m << "-" << a << b;
	}
	else if (opcion == 3) {
		m << "*" << a << b;
	}
	else if (opcion == 4) {
		m << "/" << a << b;
	}
	else if (opcion == 5) {
		m << "f" << a << 0;
	}
	else if (opcion == 6) {
		m << "p" << a << 0;
	}

	s.send(m);

	message answer;
	s.receive(answer);

	int result;
	answer >> result;
	if(opcion == 6) {
			if (result == 1)
				cout << "Resultado: Si es primo." << endl;
			else
				cout << "Resultado: No es primo." << endl;
	}
	else
		cout << "Resultado: " << result << endl;


	//int i;
	//cin >> i;
    //   	cout << "Finished\n";
	return 0;
}

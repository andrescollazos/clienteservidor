#include <iostream>
#include <string>
#include <zmqpp/zmqpp.hpp>
#include <math.h>

using namespace std;
using namespace zmqpp;

int factorial(int n){
	int result = 1;
	for (int i = n; i > 0; i--) {
			result *= i;
	}
	return result;
}

int es_primo(int n) {
	int divisores = 2;

	for (int i = 2; i < n; i++) {
		if (n % i == 0) {
			divisores++;
		}
	}
	if (divisores == 2) return 1;
	return 0;
}

int main() {
	cout << "SERVIDOR ARITMETICO\n";

	context ctx;
	socket s(ctx, socket_type::rep);

	cout << "[SERVER DICE] : Binding socket to tcp port 5555\n";
	s.bind("tcp://*:5555");

	while (true) {
		message m;
		s.receive(m);

		string operation;
		int arg1, arg2, result;

		m >> operation >> arg1 >> arg2;
		if (operation == "+") {
			result = arg1 + arg2;
		}
		else if (operation == "-") {
			result = arg1 - arg2;
		}
		else if (operation == "*") {
			result = arg1 * arg2;
		}
		else if (operation == "/") {
			result = arg1 / arg2;
		}
		else if (operation == "f") {
			result = factorial(arg1);
		}
		else if (operation == "p") {
			result = es_primo(arg1);
		}

		// Procesando el mensaje
		cout << "[SERVER DICE] : Received " << arg1 << " " << operation << " "<< arg2 << " => " << result << endl;

		message response;
		response << result;

		s.send(response);
	}

	//cout << "Finished\n";
	return 0;
}

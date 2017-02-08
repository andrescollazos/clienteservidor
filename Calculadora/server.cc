#include <iostream>
#include <string>
#include <zmqpp/zmqpp.hpp>

using namespace std;
using namespace zmqpp;

int main() {
	cout << "This is the server\n";

	context ctx;
	socket s(ctx, socket_type::rep);

	cout << "Binding socket to tcp port 5555\n";
	s.bind("tcp://*:5555");

	while (true) {
		message m;
		s.receive(m);

		string operation;
		int arg1, arg2;

		m >> operation >> arg1 >> arg2;
		int result = arg1 + arg2;

		// Procesando el mensaje
		cout << "Received " << arg1 << " " << operation << " "<< arg2 << " = " << result << endl;

		message response;
		response << result;

		s.send(response);


		//cout << "Finished\n";
		return 0;
	}
}

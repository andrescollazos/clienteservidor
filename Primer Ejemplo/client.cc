#include <iostream>
#include <string>
#include <iostream>
#include <zmqpp/zmqpp.hpp>

using namespace std;
using namespace zmqpp;

int main() {
	cout << "This is the client\n";

	context ctx;
	socket s(ctx, socket_type::push);

	cout << "Connecting to tcp port 5555\n";
	s.connect("tcp://192.168.8.66:5555");

	cout << "Sending a hello message!\n";
	message m;

	while (true) {
		for (int i = 0; i < 10; i++) {
			m << "\n\n HELLO WORLD";
			s.send(m);
		}

	}


	int i;
	cin >> i;
       	cout << "Finished\n";
	return 0;
}

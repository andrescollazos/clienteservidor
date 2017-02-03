#include <iostream>
#include <string>
#include <iostream>
#include <zmqpp/zmqpp.hpp>

using namespace std;
using namespace zmqpp;

int main() {
	cout << "This is the client\n";

	context ctx;
	socket s(ctx, socket_type::req);

	cout << "Connecting to tcp port 5555\n";
	s.connect("tcp://localhost:5555");

	cout << "Sending a hello message!\n";
	message m;
	m << "Hello world server!!";

	s.send(m);

	int i;
	cin >> i;	
       	cout << "Finished\n";
	return 0;
}

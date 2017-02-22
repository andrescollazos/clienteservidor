#include <iostream>
#include <string>
#include <fstream>
#include <zmqpp/zmqpp.hpp>

using namespace std;
using namespace zmqpp;


vector<char> readFileToBytes(const string& fileName) {
	ifstream ifs(fileName, ios::binary | ios::ate);
	ifstream::pos_type pos = ifs.tellg();

	vector<char> result(pos);

	ifs.seekg(0, ios::beg);
	ifs.read(result.data(), pos);

	return result;
}

void fileToMesage(const string& fileName, message& msg) {
	vector<char> bytes = readFileToBytes(fileName);
	msg.add_raw(bytes.data(), bytes.size());
}

int main() {
	cout << "This is the server\n";

	context ctx;
	socket s(ctx, socket_type::rep);
	s.bind("tcp://*:5555");

	message m;
	s.receive(m);

	string fileName;
	m >> fileName;

	message response;
	// m contains the filename requested by the client.
	fileToMesage(fileName,response);
	s.send(response);

	cout << "Finished\n";
	return 0;
}

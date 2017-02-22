#include <iostream>
#include <string>
#include <vector>
#include <fstream>
#include <zmqpp/zmqpp.hpp>

using namespace std;
using namespace zmqpp;

/**
 * Writes the raw data contained in msg to a file on disk with name fileName.
 *
 * Assumptions:
 * - The message consists of only one part.
 * - That part is binary written to disk
 */
void messageToFile(const message& msg, const string& fileName) {
	const void *data;
	msg.get(&data, 0);
	size_t size = msg.size(0);

	ofstream ofs(fileName, ios::binary);
	ofs.write((char*)data, size);
}

int main(int argc, char** argv) {
	cout << "Filetransfer example\n";
	if (argc != 2) {
		cerr << "Must be called: " << argv[0] << " file\n";
		return 1;
	}

	context ctx;
	socket s(ctx, socket_type::req);
	s.connect("tcp://localhost:5555");

	// Request the file in argv[1]
	string fileName(argv[1]);
	message m;
	m << fileName;
	s.send(m);

	message response;
	s.receive(response);

	// response contains the file, write it to disk
	string downloadName("down-" + fileName);
	messageToFile(response, downloadName);
    cout << "Finished\n";
	return 0;
}

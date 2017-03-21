#include "json.hpp"
#include <iostream>
#include <zmqpp/zmqpp.hpp>

using namespace std;
using namespace zmqpp;
using json = nlohmann::json;

int main(int argc, char const *argv[]) {
  cout << "Server " << argv[1] << endl;
  context ctx;
  socket s(ctx, socket_type::rep);
  string dir = "tcp://*:" + string(argv[2]);
  s.bind(dir);

  while(true) {
    // RECIBO DE DATOS
    message request;
    s.receive(request);

    string mtext;
    request >> mtext;

    json j = json::parse(mtext);
    cout << argv[1] << ": " << j[argv[1]] << endl;

    message response;
    response << "OK";
    s.send(response);
  }
  int i;
  cin >> i;
  return 0;
}

#include "json.hpp"
#include <iostream>
#include <zmqpp/zmqpp.hpp>

using namespace std;
using namespace zmqpp;
using json = nlohmann::json;

int main() {
  cout << "Server" << endl;
  context ctxr, ctxt, ctxh, ctxp;
  socket r(ctxr, socket_type::rep);
  socket t(ctxt, socket_type::req);
  socket h(ctxh, socket_type::req);
  socket p(ctxp, socket_type::req);
  r.bind("tcp://*:5555");
  t.connect("tcp://localhost:5556"); // temperature server
  h.connect("tcp://localhost:5557"); // humidity server
  p.connect("tcp://localhost:5558"); // precipitation server

  while(true) {
    // SEPERACIÓN DE DATOS
    message request;

    // 1. Recibir datos de Collector
    r.receive(request);

    string mtext;
    request >> mtext;
    json j = json::parse(mtext);
    /*
    cout << "Temperature: " << j["temperature"] << endl;
    cout << "Humidity: " << j["humidity"] << endl;
    cout << "Precipitation: " << j["precipitation"] << endl;
    */
    message response;
    response << "OK";
    r.send(response);

    // 2. Separar datos
    json te, hu, pr;
    te["temperature"] = j["temperature"];
    hu["humidity"] = j["humidity"];
    pr["precipitation"] = j["precipitation"];

    // Enviar mensaje divido a los Servidores
    t.send(te.dump()); // temperature server
    t.receive(response);
    h.send(hu.dump()); // humidity server
    h.receive(response);
    p.send(pr.dump()); // precipitation server
    p.receive(response);
  }

  return 0;
}

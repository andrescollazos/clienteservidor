#include "json.hpp"
#include <iostream>
#include <string>
#include <time.h>
#include <unistd.h>
#include <zmqpp/zmqpp.hpp>


using namespace std;
using namespace zmqpp;
using json = nlohmann::json;

// Medir_Temperatura (°C)
int measure_temp () {
  // Retorna un valor entre -50° y 50°
  srand (time(NULL));
  return rand()%101 - 50;
}

// Medir_Humedad
int measure_hum () {
  // Retorna un valor entre 0% y 100%
  srand (time(NULL));
  return rand()%101;
}

// Medir_Precipitacion
int measure_prec () {
  srand (time(NULL));
  return rand()%200;
}

int main() {
  context ctx;
  socket s(ctx, socket_type::req);
  s.connect("tcp://localhost:5555");

  cout << "Collector" << endl;
  unsigned int microseconds;

  cout << "Cada cuantos segundos se mide? ";
  cin >> microseconds;
  microseconds *= 1000000; // Convertir a segundos
  int temperature;
  unsigned int humidity, precipitation;

  while (true) {
    // MEDICION
    temperature = measure_temp();   // Medir temperatura
    humidity = measure_hum();       // Medir humedad
    precipitation = measure_prec(); // Medir precipitacion

    system("clear");
    cout << "Midiendo Temperatura: " << temperature << "°C" << endl;
    cout << "Midiendo Humedad: " << humidity << "%" << endl;
    cout << "Midiendo Precipitación: " << precipitation << " mm" << endl;

    // ENVIO DE DATOS
    message m;

    // 1. Estructurar informacion en JSON
    json j;
    j["temperature"] = temperature;
    j["humidity"] = humidity;
    j["precipitation"] = precipitation;

    string mtext = j.dump(); // Serializar
    // 2. Envio
    m << mtext;
    s.send(m);
    message resp;
    s.receive(resp);
    usleep(microseconds);
  }
  return 0;
}

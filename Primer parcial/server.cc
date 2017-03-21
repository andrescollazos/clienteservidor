#include "json.hpp"
#include <iostream>
#include <cmath>
#include <fstream>
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

  // Variables para el analisis de los datos:
  json dates;               // Datos registrados
  string date_max = "NULL"; // Fecha mayor registro
  int max = 0;              // Valor maximo registrado
  string date_min;        // Fecha menor registro
  int min = 0;            // Valor minimo registrado
  double mean = 0.0;        // Media
  double deviation = 0.0;  // Desviación estandar

  while(true) {
    system("clear");

    // RECIBO DE DATOS
    message request;
    s.receive(request);

    string mtext;
    request >> mtext;

    json j = json::parse(mtext);
    // 1. Guardar dato en el vector de datos:
    int value = (int)j[argv[1]];
    dates.push_back(value);

    // 2. Calculo de la media:
    int suma = 0;
    int tam = dates.size();
    for (json::iterator it = dates.begin(); it != dates.end(); ++it) {
      suma += (int)*it;
    }
    mean = suma / tam;

    // 3. Calculo de la desviacion estandar
    suma = 0;
    if (mean > 1) {
      for (json::iterator it = dates.begin(); it != dates.end(); ++it) {
        deviation += pow((int)*it - mean, 2);
      }
      deviation *= (1 / (mean - 1));
      deviation = sqrt(deviation);
    }
    cout << "Tamaño del vector: " << tam << endl;
    cout << "Media: " << mean << endl;
    cout << "Desviacion: " << deviation << endl;
    cout << "Dato Mayor: " << dates[max] << " Fecha: " << date_max << endl;
    cout << "Dato Menor: " << dates[min] << " Fecha: " << date_min << endl;
    //cout << "Computer " << j["Computer"] << ": "<< j[argv[1]] << endl;

    message response;
    response << "OK";
    s.send(response);

    // 4. Mayor registro
    if (value >= dates[max]) {
      max = tam - 1;
      date_max = j["hour"];
    }

    // 5. Menor registro
    if (value <= dates[min]) {
      min = tam - 1;
      date_min = j["hour"];
    }

    // 4. Guardar datos en archivo
    string name = ".dates-" + string(argv[1]) + ".json";
    ofstream d(name);
    d << std::setw(4) << dates << std::endl;

    // 5. Guardar analisis de datos:
    json analysis;
    analysis["Media"] = mean;
    analysis["Desviacion"] = deviation;
    analysis["Mayor registro"] = dates[max];
    analysis["Fecha Mayor registro"] = date_max;
    analysis["Menor registro"] = dates[min];
    analysis["Fecha Menor registro"] = date_min;
    name = "Analisis-" + string(argv[1]) + ".json";
    ofstream a(name);
    a << std::setw(4) << analysis << std::endl;
  }

  return 0;
}

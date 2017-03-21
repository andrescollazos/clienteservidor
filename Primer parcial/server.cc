#include "json.hpp"
#include <iostream>
#include <cmath>
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
  vector<int> dates;      // Datos registrados
  //string date_max;        // Fecha mayor registro
  //int max = 0;            // Valor maximo registrado
  //string date_min;        // Fecha menor registro
  //int min = 0;            // Valor minimo registrado
  double mean = 0.0;      // Media
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
    dates.push_back(j[argv[1]]);

    // 2. Calculo de la media:
    int suma = 0;
    int tam = (int)dates.size();
    for(int i = 0; i < tam; i++) {
      suma += dates[i];
    }
    mean = suma / tam;

    // 3. Calculo de la desviacion estandar
    suma = 0;
    for(int i = 0; i < tam; i++) {
      deviation += pow(dates[i] - mean, 2);
    }
    deviation *= (1 / (mean - 1));
    deviation = sqrt(deviation);

    cout << "Tamaño del vector: " << tam << endl;
    cout << "Media: " << mean << endl;
    cout << "Desviacion: " << deviation << endl;
    //cout << "Computer " << j["Computer"] << ": "<< j[argv[1]] << endl;

    message response;
    response << "OK";
    s.send(response);
  }
  int i;
  cin >> i;
  return 0;
}

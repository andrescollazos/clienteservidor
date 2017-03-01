#include <iostream>
#include <fstream>
#include <vector>

// include headers that implement a archive in simple text format
//#include <boost/archive/text_oarchive.hpp>
//#include <boost/archive/text_iarchive.hpp>

using namespace std;

class ISerializable {
  public:
    virtual void read (std::istream& in) = 0;
    virtual void write(std::ostream& out) = 0;
};

class user : public ISerializable {
  public:
    string userName_;
    string password_;
    vector<string> archives_;
    //double a_;
    //int b_;
    //string cad_;

    user() {}
    user(string userName, string password) : userName_(userName), password_(password) {}
    ~user() {}

    // Metodos para serializar (write) y deserializar (read)
    virtual void read (std::istream& in);
    virtual void write(std::ostream& out);

    // Metodos
    virtual void pop(string archive);

};

void user::read(std::istream& in) {
  cout << "Deserializando datos" << endl;

  size_t len;
  size_t leni;
  char* auxCad;

  // userName_
  in.read((char*) &len, sizeof(size_t));
  auxCad = new char[len+1];

  in.read(auxCad, len);
  auxCad[len] = '\0';
  userName_ = auxCad;
  cout << "Username: " << userName_ << " Len: " << len << endl;

  // password_
  in.read((char*) &len, sizeof(size_t));
  auxCad = new char[len+1];

  in.read(auxCad, len);
  auxCad[len] = '\0';
  password_ = auxCad;
  cout << "password_: " << password_ << " Len: " << len << endl;

  // archives_
  in.read((char*) &len, sizeof(size_t));
  cout << "Archives, len: " << len << endl;
  for (int i = 0; i < (int)len; i++) {
    cout << "Iter"<< i;
    in.read((char*) &leni, sizeof(size_t));
    cout << " len: " << leni;
    in.read(auxCad, leni);
    auxCad[leni] = '\0';
    cout << " string: " << auxCad << endl;
    archives_.push_back(auxCad);
  }

  delete [] auxCad;
}

void user::write(std::ostream& out) {
  cout << "Serializando datos: " << endl;
  size_t len, leni;
  // UserName_
  len = userName_.length();
  out.write((char*) &len, sizeof(size_t));
  out.write((char*) userName_.c_str(), len);
  cout << "\tUserName: " << userName_ << endl;

  // Password_
  len = password_.length();
  out.write((char*) &len, sizeof(size_t));
  out.write((char*) password_.c_str(), len);
  cout << "\tPassword: " << password_ << endl;

  // Vector de archivos.
  len = archives_.size(); // Tamaño del arreglo
  out.write((char *) &len, sizeof(size_t));
  for(int i = 0; i < (int)len; i++) {
    // Tamaño de la cadena i:
    leni = archives_[i].length();
    cout << "Iter " << i << " string: " << archives_[i] << " len: " << leni << endl;
    out.write((char *) &leni, sizeof(size_t));
    out.write((char*) archives_[i].c_str(), leni);
  }

  //out.write((char*) &a_, sizeof(double)); // Escribir un double
}

// Metodo que permite eliminar un elemento del vector archives_
void user::pop(string archive) {
  for (int i = 0; i < (int)archives_.size(); i++) {
    cout << "Iter " << i << ": Elemento: " << archives_[i] << " == " << archive << endl;
    if (archive == archives_[i]) {
      cout << "Eliminando... " << endl;
      archives_.erase(archives_.begin()+i, archives_.begin()+(i+1));
    }
  }
}
/*
int main(int argc, char *argv[]) {
  {
    ofstream fout;
    fout.open("data.dat", ios::out | ios::app | ios::binary);
    if (!fout.is_open()) {
      cout << "ERROR!" << endl;
      return -1;
    }

    user o("Andres", "1232131");
    o.archives_.push_back("mi.png");
    o.archives_.push_back("mi2.png");
    o.archives_.push_back("mi3.png");
    o.archives_.push_back("mi4.png");
    o.write(fout);

    user p("Roberto", "sdfsdfds");//, new vector<string>);
    p.archives_.push_back("mp.png");
    p.archives_.push_back("mp1.png");
    p.archives_.push_back("mp2.png");
    p.write(fout);

  }

  ifstream fin("data.dat", ios_base::binary);
  user q;
  q.read(fin);
  user r;
  r.read(fin);

  return 0;

}*/

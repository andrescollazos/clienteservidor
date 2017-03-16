CC	= g++ -std=c++11 -Wall -L/usr/local/lib -I/usr/local/include
LDFLAGS = -lpthread -lzmqpp -lzmq

all: server brocker collector

server: server.cc
	$(CC) -o server server.cc $(LDFLAGS)

brocker: collector.cc
	$(CC) -o collector collector.cc $(LDFLAGS)

collector: brocker.cc
		$(CC) -o brocker brocker.cc $(LDFLAGS)

clean:
	rm -f collector server brocker

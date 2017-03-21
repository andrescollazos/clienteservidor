CC	= g++ -std=c++11 -Wall -L/usr/local/lib -I/usr/local/include
LDFLAGS = -lpthread -lzmqpp -lzmq

all: server brocker collector

server: server.cc
	$(CC) -o server server.cc $(LDFLAGS)

collector: collector.cc
	$(CC) -o collector collector.cc $(LDFLAGS)

brocker: brocker.cc
		$(CC) -o brocker brocker.cc $(LDFLAGS)

clean:
	rm -f collector server brocker

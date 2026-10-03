#include <arpa/inet.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <unistd.h>

#define PORT 4444
#define ITEM_SIZE 16
int exploit;

void handle_client(int client_fd);
void client_stackOverflow(int client_fd);
void client_formatString(int client_fd);
void client_heapOverflow(int client_fd);
void client_integerOverflow(int client_fd);

int main(int argc, char* argv[])
{
	// Grab Exploit value from command line
	if (argv[1] != NULL)
	{
		exploit = atoi(argv[1]);
		exploit = (exploit <= -1  || exploit >= 5) ? 1 : exploit;
	}
	else	
	{
		exploit = 0;
	}

	// Socket file descriptors
	int server_fd;
	int client_fd;

	struct sockaddr_in server_addr;

	// Create TCP socket using IPv4
	server_fd = socket(AF_INET, SOCK_STREAM, 0);

	if (server_fd < 0)
	{
		fprintf(stderr, "socket");
		return 1;
	}

	// Avoids address already in use error on restart
	int option = 1;
	setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, &option, sizeof(option));

	// Init address struct specifying address and port
	memset(&server_addr, 0, sizeof(server_addr));
	server_addr.sin_family = AF_INET;
	server_addr.sin_addr.s_addr = INADDR_ANY;
	server_addr.sin_port = htons(PORT);

	//Make sure the socket is bound to the specified address and port
	if (bind(server_fd,
			(struct sockaddr *)&server_addr,
			sizeof(server_addr)) < 0)
	{
		fprintf(stderr, "bind");
		close(server_fd);
		return 1;
	}

	// Start listening for incoming connections
	if (listen(server_fd, 5) < 0) {
		fprintf(stderr, "listen");
		close(server_fd);
		return 1;
	}

	printf("Listening on TCP port %d...\n", PORT);
	if (exploit != 0)
		printf("Exploit #%d\n", exploit);
	else
		printf("No Exploit\n");

	while (1)
	{
		// Wait until client connects and then handle said client
		client_fd = accept(server_fd, NULL, NULL);

		if (client_fd < 0)
		{
			fprintf(stderr, "accept");
			continue;
		}

		switch (exploit)
		{
			case 0:
				handle_client(client_fd);
				break;
				
			case 1:
				client_stackOverflow(client_fd);
				break;

			case 2:
				client_formatString(client_fd);
				break;

			case 3:
				client_heapOverflow(client_fd);
				break;
			
			case 4:
				client_integerOverflow(client_fd);
				break;
		}
		
	}

	close(server_fd);
	return 0;
}

void handle_client(int client_fd)
{
	// Small buffer to intentionally demonstrate a stack overflow vulnerability.
	char buffer[256];

	printf("Client connected.\n");

	ssize_t bytes_received = recv(client_fd, buffer, sizeof(buffer) - 1, 0);

	if (bytes_received < 0) {
		fprintf(stderr, "recv");
		close(client_fd);
		return;
	}

	printf("Received %zd bytes.\n", bytes_received);

	send(client_fd, "Request processed\n", 18, 0);

	close(client_fd);
}

// Handle client with CWE-121 active
void client_stackOverflow(int client_fd)
{
	// Small buffer to intentionally demonstrate a stack overflow vulnerability.
	char buffer[64];

	printf("Client connected.\n");

	// Receive at most 256 bytes from the client
	ssize_t bytes_received = recv(client_fd, buffer, 256, 0);

	if (bytes_received < 0) {
		fprintf(stderr, "recv");
		close(client_fd);
		return;
	}

	printf("Received %zd bytes.\n", bytes_received);

	send(client_fd, "Request processed\n", 18, 0);

	close(client_fd);
}

// Handle client with CWE-134 active
void client_formatString(int client_fd)
{
	char buffer[256];

	printf("Client connected.\n");

	// Prevent buffer overflow with sizeof()
	ssize_t bytes_received = recv(client_fd, buffer, sizeof(buffer) - 1, 0);

	if (bytes_received < 0) {
		fprintf(stderr, "recv");
		close(client_fd);
		return;
	}

	buffer[bytes_received] = '\0';

	printf("Received %zd bytes.\n", bytes_received);

	// Source of format-String vulnerability, allows client to format their string
	printf(buffer);

	send(client_fd, "Request processed\n", 18, 0);

	close(client_fd);
}

// Handle client with CWE-122 active
void client_heapOverflow(int client_fd)
{
	char input[256];

	printf("Client connected.\n");

	ssize_t bytes_received = recv(client_fd, input, sizeof(input), 0);

	if (bytes_received < 0)
	{
		fprintf(stderr, "recv");
		close(client_fd);
		return;
	}

	printf("Received %zd bytes.\n", bytes_received);

	char *buffer = malloc(64);

	if (buffer == NULL)
	{
		fprintf(stderr, "malloc");
		close(client_fd);
		return;
	}

	// Source of heap buffer overflow vulnerability
	memcpy(buffer, input, bytes_received);

	printf("Data copied to heap buffer.\n");

	send(client_fd, "Request processed\n", 18, 0);

	free(buffer);
	close(client_fd);
}

// Handle with CWE-680 active
void client_integerOverflow(int client_fd)
{
	uint32_t count;

	printf("Client connected.\n");

	//The client supplies the number of items.
	ssize_t received = recv(client_fd, &count, sizeof(count), MSG_WAITALL);

	if (received != sizeof(count))
	{
		fprintf(stderr, "recv count");
		close(client_fd);
		return;
	}

	printf("Client requested %u items.\n", count);

	// Implementing vulnerability through multiplication causing the integer overflow
	uint32_t allocation_size = count * ITEM_SIZE;

	printf("Calculated allocation size: %u bytes.\n", allocation_size);

	char *buffer = malloc(allocation_size);

	if (buffer == NULL && allocation_size != 0)
	{
		fprintf(stderr, "malloc");
		close(client_fd);
		return;
	}

	char input[32];

	received = recv(client_fd, input, sizeof(input), 0);

	if (received < 0)
	{
		fprintf(stderr, "recv data");
		free(buffer);
		close(client_fd);
		return;
	}


	if (received > 0 && buffer != NULL)
	{
		memcpy(buffer, input, received);
	}

	printf("Received %zd bytes of data.\n", received);

	send(client_fd, "Request processed\n", 18, 0);

	free(buffer);
	close(client_fd);
}
server 


import socket
import threading
import sys

# Global variables
clients = []
peer_socket = None
server_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1

# Port configuration
CLIENT_PORT = 8001 if server_id == 1 else 8002
INTER_SERVER_PORT = 9001 if server_id == 1 else 9002
PEER_PORT = 9002 if server_id == 1 else 9001

def broadcast_to_clients(message):
    """Send message to all connected clients"""
    for client in clients[:]:
        try:
            client.send(message.encode())
        except:
            clients.remove(client)

def handle_client(client_socket):
    """Handle individual client messages"""
    while True:
        try:
            message = client_socket.recv(1024).decode()
            if not message:
                break
                
            print(f"[SERVER {server_id}] Received: {message}")
            
            # Broadcast to local clients
            broadcast_to_clients(f"[SERVER {server_id}] {message}")
            
            # Forward to peer server
            if peer_socket:
                try:
                    peer_socket.send(f"[SERVER {server_id}] {message}".encode())
                except:
                    print(f"[SERVER {server_id}] Failed to forward to peer")
                    
        except:
            break
    
    clients.remove(client_socket)
    client_socket.close()

def handle_peer_messages():
    """Handle messages from peer server"""
    global peer_socket
    while True:
        try:
            message = peer_socket.recv(1024).decode()
            if not message:
                break
            print(f"[SERVER {server_id}] From peer: {message}")
            broadcast_to_clients(message)
        except:
            print(f"[SERVER {server_id}] Peer connection lost")
            break

def connect_to_peer():
    """Connect to peer server"""
    global peer_socket
    while True:
        try:
            peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            peer_socket.connect(('localhost', PEER_PORT))
            print(f"[SERVER {server_id}] Connected to peer server")
            
            # Start listening for peer messages
            peer_thread = threading.Thread(target=handle_peer_messages)
            peer_thread.daemon = True
            peer_thread.start()
            break
        except:
            peer_socket = None
            threading.Event().wait(2)  # Wait 2 seconds before retry

def start_inter_server():
    """Start inter-server communication listener"""
    inter_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    inter_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    inter_socket.bind(('localhost', INTER_SERVER_PORT))
    inter_socket.listen(1)
    print(f"[SERVER {server_id}] Inter-server listening on port {INTER_SERVER_PORT}")
    
    while True:
        try:
            peer_conn, addr = inter_socket.accept()
            print(f"[SERVER {server_id}] Peer server connected from {addr}")
            
            # Handle incoming peer messages
            def handle_incoming_peer():
                global peer_socket
                peer_socket = peer_conn
                handle_peer_messages()
            
            peer_thread = threading.Thread(target=handle_incoming_peer)
            peer_thread.daemon = True
            peer_thread.start()
            
        except Exception as e:
            print(f"[SERVER {server_id}] Inter-server error: {e}")

def main():
    print(f"Starting Server {server_id}")
    print(f"Client port: {CLIENT_PORT}")
    print(f"Inter-server port: {INTER_SERVER_PORT}")
    
    # Start inter-server listener
    inter_thread = threading.Thread(target=start_inter_server)
    inter_thread.daemon = True
    inter_thread.start()
    
    # Connect to peer server (with delay for server 2)
    if server_id == 2:
        threading.Event().wait(1)  # Wait for server 1 to start
    
    peer_thread = threading.Thread(target=connect_to_peer)
    peer_thread.daemon = True
    peer_thread.start()
    
    # Start client server
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(('localhost', CLIENT_PORT))
    server_socket.listen(5)
    print(f"[SERVER {server_id}] Listening for clients on port {CLIENT_PORT}")
    
    while True:
        try:
            client_socket, addr = server_socket.accept()
            clients.append(client_socket)
            print(f"[SERVER {server_id}] Client connected from {addr}")
            
            # Start client handler thread
            client_thread = threading.Thread(target=handle_client, args=(client_socket,))
            client_thread.daemon = True
            client_thread.start()
            
        except KeyboardInterrupt:
            print(f"\n[SERVER {server_id}] Shutting down...")
            break
        except Exception as e:
            print(f"[SERVER {server_id}] Error: {e}")

if __name__ == "__main__":
    main()



client 

import socket
import threading
import sys
import time

# Client configuration
client_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1
username = f"User{client_id}"

def select_server():
    """Allow user to choose server or use round-robin"""
    print(f"\n=== Server Selection for {username} ===")
    print("1. Server 1 (port 8001)")
    print("2. Server 2 (port 8002)")
    print("3. Auto-select (round-robin)")
    
    while True:
        choice = input("Choose server (1/2/3): ").strip()
        
        if choice == '1':
            return 8001, "Server 1"
        elif choice == '2':
            return 8002, "Server 2"
        elif choice == '3':
            # Round-robin based on client_id
            if client_id % 2 == 1:
                return 8001, "Server 1 (auto-selected)"
            else:
                return 8002, "Server 2 (auto-selected)"
        else:
            print("Invalid choice! Please enter 1, 2, or 3")

SERVER_PORT, server_name = select_server()

def receive_messages(sock):
    """Receive and display messages from server"""
    while True:
        try:
            message = sock.recv(1024).decode()
            if not message:
                break
            print(f"\n{message}")
            print(f"{username}> ", end="", flush=True)
        except:
            print("\nDisconnected from server")
            break

def main():
    print(f"Client {client_id} ({username}) starting...")
    print(f"Connecting to {server_name} on port {SERVER_PORT}")
    
    # Connect to server
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(('localhost', SERVER_PORT))
        print(f"Connected to {server_name}!")
        
        # Send join message
        join_msg = f"{username} joined the chat"
        client_socket.send(join_msg.encode())
        
        # Start message receiver thread
        receiver_thread = threading.Thread(target=receive_messages, args=(client_socket,))
        receiver_thread.daemon = True
        receiver_thread.start()
        
        # Send messages
        print(f"\nYou can start chatting! (Type 'quit' to exit)")
        while True:
            message = input(f"{username}> ")
            
            if message.lower() == 'quit':
                client_socket.send(f"{username} left the chat".encode())
                break
                
            if message.strip():
                client_socket.send(f"{username}: {message}".encode())
        
        client_socket.close()
        print("Goodbye!")
        
    except Exception as e:
        print(f"Error connecting to server: {e}")

if __name__ == "__main__":
    main()





-------------------------------------------------mininet----------------------------------------------------------------------------------------------


from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import OVSSwitch, Controller
from mininet.cli import CLI
from mininet.log import setLogLevel

class ThreeSwitchTopo(Topo):
    def build(self):
        # Add switches
        s1 = self.addSwitch('s1')
        s2 = self.addSwitch('s2')
        s3 = self.addSwitch('s3')

        # Add hosts
        h1 = self.addHost('h1')
        h2 = self.addHost('h2')
        h3 = self.addHost('h3')
        server = self.addHost('server')

        # Connect hosts to switches
        self.addLink(h1, s1)
        self.addLink(h2, s2)
        self.addLink(h3, s3)
        self.addLink(server, s1)  # Assuming server connected to s1
        # Connect switches
        self.addLink(s1, s2)
        self.addLink(s2, s3)

def run():
    topo = ThreeSwitchTopo()
    net = Mininet(topo=topo, controller=Controller)
    net.start()
    
    net.pingAll()
    # Print MAC addresses and IPs
    for host in ['h1', 'h2', 'h3', 'server']:
        print(f"\n{host} interfaces:")
        print(net.get(host).cmd('ifconfig -a'))
        print(f"{host} IP address:")
        print(net.get(host).cmd('ip addr show'))
    print(net.get('h1').cmd('ping -c 3 server'))
    print(net.get('h1').cmd('arp'))
    net.get('server').cmd('iperf -s &')
    print(net.get('h1').cmd('iperf -c server'))

    CLI(net)
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    run()



----udpc----------------------------------------------------------------------------------------------------------------------

import socket
import threading
import sys
import time
from queue import Queue # Import Queue just in case for future use

MAX_MSG_SIZE = 1024

class ChatClient:
    def __init__(self, server_host, tcp_port, udp_port, protocol):
        self.server_host = server_host
        self.tcp_port = tcp_port
        self.udp_port = udp_port
        self.protocol = protocol.lower()

        self.tcp_sock = None
        self.udp_sock = None
        self.running = True
        self.input_queue = Queue()

        if self.protocol == 'tcp':
            self.tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                self.tcp_sock.connect((server_host, tcp_port))
                print(f"Connected to server {server_host}:{tcp_port} via TCP")
            except Exception as e:
                print(f"Failed to connect to TCP server: {e}")
                sys.exit(1)
        elif self.protocol == 'udp':
            self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # Bind to an ephemeral port to listen for server broadcasts
            self.udp_sock.bind(('', 0)) 
            print(f"Ready to send to server {server_host}:{udp_port} via UDP. Listening on {self.udp_sock.getsockname()}")
        else:
            print("Unsupported protocol! Use TCP or UDP only.")
            sys.exit(1)

    def get_user_input(self):
        # Dedicated thread for input to avoid blocking the main send loop
        while self.running:
            try:
                msg = input()
                self.input_queue.put(msg)
            except EOFError:
                # Handle Ctrl+D (Unix)
                self.running = False
                self.input_queue.put("exit")
                break
            except Exception:
                break


    def send_messages(self):
        print("Enter messages to send. Type 'exit' to quit.")
        
        # Start input thread
        threading.Thread(target=self.get_user_input, daemon=True).start()
        
        while self.running:
            try:
                # Get message from the queue (blocking)
                msg = self.input_queue.get(timeout=0.1) 
            except Exception:
                continue # Timeout, loop and check self.running

            if msg.lower() == "exit":
                self.running = False
                break
            
            encoded_msg = msg.encode()

            if self.protocol == 'tcp':
                try:
                    self.tcp_sock.sendall(encoded_msg)
                except Exception as e:
                    print(f"Error sending TCP message: {e}")
                    self.running = False
            elif self.protocol == 'udp':
                try:
                    self.udp_sock.sendto(encoded_msg, (self.server_host, self.udp_port))
                except Exception as e:
                    print(f"Error sending UDP message: {e}")
                    self.running = False
            
            self.input_queue.task_done()
            time.sleep(0.01) # Small delay

    def receive_messages(self):
        if self.protocol == 'tcp':
            try:
                while self.running:
                    self.tcp_sock.settimeout(0.1)
                    try:
                        data = self.tcp_sock.recv(MAX_MSG_SIZE)
                    except socket.timeout:
                        continue # Loop and check self.running

                    if not data:
                        print("\nDisconnected from server.")
                        break
                    print(f"\nBroadcast: {data.decode()}")
            except Exception as e:
                if self.running:
                    print(f"\nError receiving TCP messages: {e}")
            finally:
                self.running = False
        elif self.protocol == 'udp':
            try:
                while self.running:
                    self.udp_sock.settimeout(0.1)
                    try:
                        data, _ = self.udp_sock.recvfrom(MAX_MSG_SIZE)
                    except socket.timeout:
                        continue # Loop and check self.running
                        
                    if not data:
                        continue
                    print(f"\nBroadcast: {data.decode()}")
            except Exception as e:
                if self.running:
                    print(f"\nError receiving UDP messages: {e}")
            finally:
                self.running = False

    def run(self):
        threading.Thread(target=self.receive_messages, daemon=True).start()
        self.send_messages()
        
        # Cleanup
        if self.tcp_sock:
            try:
                self.tcp_sock.close()
            except Exception:
                pass
        if self.udp_sock:
            try:
                self.udp_sock.close()
            except Exception:
                pass
        
        print("Client exited.")
        # Ensure program exits even with daemon threads
        sys.exit(0)

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: python chat_client.py <ServerHost> <TCPPort> <UDPPort> <Protocol>")
        print("Example: python chat_client.py 127.0.0.1 5000 5001 TCP")
        sys.exit(1)

    server_host = sys.argv[1]
    try:
        tcp_port = int(sys.argv[2])
        udp_port = int(sys.argv[3])
    except ValueError:
        print("Ports must be valid integers.")
        sys.exit(1)
        
    protocol = sys.argv[4].lower()

    client = ChatClient(server_host, tcp_port, udp_port, protocol)
    client.run()



---udps-------------------------------------------------------------------------------------------------------------------


import socket
import threading
import sys
import time
from queue import Queue

MAX_MSG_SIZE = 1024

class ChatServer:
    def __init__(self, server_name, tcp_port, udp_port, peer_tcp_host, peer_tcp_port):
        self.server_name = server_name
        self.tcp_port = tcp_port
        self.udp_port = udp_port
        self.peer_tcp_host = peer_tcp_host
        self.peer_tcp_port = peer_tcp_port

        # Clients connected over TCP: list of socket objects
        self.tcp_clients = []
        # Clients for UDP: keep track of client addresses
        self.udp_clients = set()

        # Lock for accessing clients list
        self.clients_lock = threading.Lock()

        # Start TCP server socket for client connections
        self.tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.tcp_sock.bind(('', tcp_port))
            self.tcp_sock.listen(5)
        except Exception as e:
            print(f"Error binding TCP socket on port {tcp_port}: {e}")
            sys.exit(1)

        # Start UDP socket for client connections
        self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            self.udp_sock.bind(('', udp_port))
        except Exception as e:
            print(f"Error binding UDP socket on port {udp_port}: {e}")
            sys.exit(1)

        # Dedicated TCP socket to connect to peer server for forwarding messages
        self.peer_sock = None
        self.peer_sock_lock = threading.Lock()

        # Message queue to send to peer server (REVISED: Use standard Queue)
        self.forward_queue = Queue()

        # Start threads
        self.running = True
        threading.Thread(target=self.accept_tcp_clients, daemon=True).start()
        threading.Thread(target=self.receive_udp_clients, daemon=True).start()
        threading.Thread(target=self.connect_to_peer_server, daemon=True).start()
        threading.Thread(target=self.forward_messages_to_peer, daemon=True).start()

    def accept_tcp_clients(self):
        print(f"[{self.server_name}] TCP listening on port {self.tcp_port}")
        while self.running:
            try:
                client_sock, addr = self.tcp_sock.accept()
                print(f"[{self.server_name}] TCP client connected from {addr}")
                with self.clients_lock:
                    self.tcp_clients.append(client_sock)
                threading.Thread(target=self.handle_tcp_client, args=(client_sock,addr), daemon=True).start()
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"[{self.server_name}] accept_tcp_clients error: {e}")

    def handle_tcp_client(self, client_sock, addr):
        try:
            while self.running:
                # Set a timeout for recv to allow loop to check self.running
                client_sock.settimeout(0.1)
                try:
                    msg = client_sock.recv(MAX_MSG_SIZE)
                except socket.timeout:
                    continue 
                
                if not msg:
                    break
                
                # Broadcast message with indication of source client and protocol
                message = msg.decode()
                full_msg = f"{self.server_name} TCP {addr}: {message}"
                print(f"[{self.server_name}] Received from TCP client: {full_msg}")
                self.broadcast(full_msg)
                self.forward_to_peer(full_msg) # Enqueue for peer
        except Exception as e:
            if self.running:
                print(f"[{self.server_name}] TCP client {addr} error: {e}")
        finally:
            with self.clients_lock:
                if client_sock in self.tcp_clients:
                    self.tcp_clients.remove(client_sock)
            try:
                client_sock.close()
            except Exception:
                pass
            if self.running:
                print(f"[{self.server_name}] TCP client {addr} disconnected")

    def receive_udp_clients(self):
        print(f"[{self.server_name}] UDP listening on port {self.udp_port}")
        while self.running:
            try:
                # Set a timeout for recvfrom to allow loop to check self.running
                self.udp_sock.settimeout(0.1)
                try:
                    data, addr = self.udp_sock.recvfrom(MAX_MSG_SIZE)
                except socket.timeout:
                    continue

                if addr not in self.udp_clients:
                    self.udp_clients.add(addr)
                    print(f"[{self.server_name}] UDP client detected from {addr}")
                
                message = data.decode()
                full_msg = f"{self.server_name} UDP {addr}: {message}"
                print(f"[{self.server_name}] Received from UDP client: {full_msg}")
                self.broadcast(full_msg)
                self.forward_to_peer(full_msg) # Enqueue for peer
            except Exception as e:
                if self.running:
                    print(f"[{self.server_name}] receive_udp_clients error: {e}")

    def broadcast(self, message):
        with self.clients_lock:
            encoded_message = message.encode()
            
            # --- TCP broadcast ---
            dead_clients = []
            for client in self.tcp_clients:
                try:
                    client.sendall(encoded_message)
                except Exception:
                    dead_clients.append(client)
            for dc in dead_clients:
                self.tcp_clients.remove(dc)
            
            # --- UDP broadcast ---
            dead_addrs = set()
            for addr in self.udp_clients:
                try:
                    self.udp_sock.sendto(encoded_message, addr)
                except Exception:
                    # UDP failures are harder to detect, but a connection refused/network error might occur
                    dead_addrs.add(addr) 
            self.udp_clients -= dead_addrs

    def connect_to_peer_server(self):
        while self.running:
            with self.peer_sock_lock:
                if self.peer_sock is None:
                    try:
                        temp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        temp_sock.connect((self.peer_tcp_host, self.peer_tcp_port))
                        self.peer_sock = temp_sock
                        print(f"[{self.server_name}] Connected to peer server at {(self.peer_tcp_host, self.peer_tcp_port)}")
                        
                        # Start a thread to receive forwarded messages from peer
                        threading.Thread(target=self.handle_peer_messages, daemon=True).start()
                    except Exception as e:
                        print(f"[{self.server_name}] Peer connection failed: {e}, retrying...")
                        self.peer_sock = None # Ensure it's None if connection failed
            
            if self.peer_sock is not None:
                # Connection was successful, break out of retry loop
                break 
                
            time.sleep(3)

    def handle_peer_messages(self):
        sock = None
        # Must acquire lock to safely read peer_sock, but release it before blocking on recv
        with self.peer_sock_lock:
            sock = self.peer_sock
            if sock:
                sock.settimeout(0.5) # Timeout to allow checking self.running
        
        try:
            while self.running and sock:
                try:
                    data = sock.recv(MAX_MSG_SIZE)
                except socket.timeout:
                    continue # Loop and check self.running

                if not data:
                    # Peer closed connection
                    break
                    
                message = data.decode()
                print(f"[{self.server_name}] Received forwarded message from peer: {message}")
                # Rebroadcast to local clients
                self.broadcast(message)
        except Exception as e:
            if self.running:
                print(f"[{self.server_name}] Error receiving peer messages: {e}")
        finally:
            self.disconnect_peer()

    def disconnect_peer(self):
        with self.peer_sock_lock:
            if self.peer_sock:
                try:
                    self.peer_sock.close()
                except Exception:
                    pass
                self.peer_sock = None
                print(f"[{self.server_name}] Lost connection to peer server.")
        
        # Restart the connection process in a separate thread to avoid blocking
        if self.running:
            threading.Thread(target=self.connect_to_peer_server, daemon=True).start()

    def forward_to_peer(self, message):
        # REVISED: Enqueue the message immediately. The sender thread is non-blocking.
        if self.running:
            self.forward_queue.put(message)

    def forward_messages_to_peer(self):
        # REVISED: Dedicated thread to dequeue and send messages when peer_sock is available
        while self.running:
            message = self.forward_queue.get() # Blocking call, waits for a message

            sent = False
            with self.peer_sock_lock:
                if self.peer_sock:
                    try:
                        self.peer_sock.sendall(message.encode())
                        sent = True
                    except Exception as e:
                        print(f"[{self.server_name}] Forward to peer failed: {e}. Requeuing message.")
                        # Message failed to send, put it back in the queue for the next connection
                        self.forward_queue.put(message)
                        self.disconnect_peer() # Force a reconnect attempt

            if sent:
                self.forward_queue.task_done()
            
            time.sleep(0.01) # Small sleep to avoid busy-waiting between successful sends

if __name__ == '__main__':
    if len(sys.argv) != 6:
        print("Usage: python chat_server.py <ServerName> <TCPPort> <UDPPort> <PeerTCPHost> <PeerTCPPort>")
        print("Example: python chat_server.py ServerA 5000 5001 127.0.0.1 6000")
        sys.exit(1)

    server_name = sys.argv[1]
    try:
        tcp_port = int(sys.argv[2])
        udp_port = int(sys.argv[3])
        peer_host = sys.argv[4]
        peer_port = int(sys.argv[5])
    except ValueError:
        print("Ports must be valid integers.")
        sys.exit(1)

    server = ChatServer(server_name, tcp_port, udp_port, peer_host, peer_port)

    # Keep main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nServer shutting down.")
        server.running = False
        server.tcp_sock.close() # Close server sockets to unblock accept/recvfrom
        server.udp_sock.close()
        server.disconnect_peer() # Ensure peer socket is closed
        sys.exit(0)



------namespaces--------------------------------------

Show All Interfaces	ip link show	ip link show
Show Specific Interface	ip link show <iface>	ip link show eth0
Set Interface UP	ip link set <iface> up	ip link set veth-h0 up
Set Interface DOWN	ip link set <iface> down	ip link set veth-h0 down
Change MAC Address	ip link set dev <iface> address <MAC>	ip link set dev eth0 address 00:11:22:33:44:55
Change MTU	ip link set dev <iface> mtu <value>	ip link set dev eth0 mtu 1400

Task	Command	Example
Set an IP Address	ip addr add <ip/cidr> dev <interface>	ip addr add 192.168.1.10/24 dev eth0
Bring Interface UP	ip link set <interface> up	ip link set eth0 up
Bring Interface DOWN	ip link set <interface> down	ip link set eth0 down
View Interface Status	ip link show <interface>	ip link show eth0
View IP Addresses	ip addr show <interface>	ip addr show eth0



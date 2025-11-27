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

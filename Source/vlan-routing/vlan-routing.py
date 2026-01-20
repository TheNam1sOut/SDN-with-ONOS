#Importing necessary libraries
from mininet.net import Mininet # For mininet topo
from mininet.node import RemoteController # For connecting to ONOS
from mininet.topo import Topo
from mininet.link import TCLink #Traffic-Control Link, can be used for bandwidth control and many more
from mininet.cli import CLI
from mininet.log import setLogLevel, info

# Our topology will look like this
"""
        s0a
      /  |   \
     /   |    \
    /    |     \
  sa1   sb1    sc1
 /  \   /  \    |  \
ha1 ha2 hb1 hb2 hc1 hc2
"""
# Our ONOS controller will connect to all of the switches 
# Furthermore, we will define different VLAN for our hosts
# ha1, hb1, hc1 will be from 10.0.10.0/24
# ha2, hb2, hc2 will be from 10.0.20.0/24

ONOS_IP='172.17.0.5'
ONOS_OF_PORT=6653

class VlanRoutingTopo(Topo):
    def __init__(self, **opts):
        super( VlanRoutingTopo, self ).__init__(**opts)
	
        # To ensure all five switches show up in ONOS GUI, assign a unique ID when adding switches
        # Central switches (s0a, s0b)
        s0a = self.addSwitch('s0a', dpid='0000000000000001')
        #s0b = self.addSwitch('s0b', dpid='0000000000000002')

        #Leaf switches (sa1, sb1, sc1)
        sa1 = self.addSwitch('sa1', dpid='0000000000000003')
        sb1 = self.addSwitch('sb1', dpid='0000000000000004')
        sc1 = self.addSwitch('sc1', dpid='0000000000000005')

        #Hosts (ha1, ha2, hb1, hb2, hc1, hc2)
        ha1 = self.addHost('ha1', ip = '10.0.10.11/24', mac='00:00:00:00:01:01', defaultRoute='via 10.0.10.1')
        ha2 = self.addHost('ha2', ip = '10.0.20.11/24', mac='00:00:00:00:02:01', defaultRoute='via 10.0.20.1')
        hb1 = self.addHost('hb1', ip = '10.0.10.12/24', mac='00:00:00:00:01:02', defaultRoute='via 10.0.10.1')	
        hb2 = self.addHost('hb2', ip = '10.0.20.12/24', mac='00:00:00:00:02:02', defaultRoute='via 10.0.20.1')
        hc1 = self.addHost('hc1', ip = '10.0.10.13/24', mac='00:00:00:00:01:03', defaultRoute='via 10.0.10.1')
        hc2 = self.addHost('hc2', ip = '10.0.20.13/24', mac='00:00:00:00:02:03', defaultRoute='via 10.0.20.1')

        #Main links
        # Central switches links
        #self.addLink(s0a, s0b, port1=1, port2=1)#, cls = TCLink, bw = 100)
        # Central switch to branch switches
        self.addLink(s0a, sa1, port1=2, port2=1)#, cls = TCLink, bw = 100)
        self.addLink(s0a, sb1, port1=3, port2=1)#, cls = TCLink, bw = 100)
        self.addLink(s0a, sc1, port1=4, port2=1)#, cls = TCLink, bw = 100)
        #sa1 to hosts
        self.addLink(sa1, ha1, port1=2, port2=1)#, cls = TCLink, bw = 100)	
        self.addLink(sa1, ha2, port1=3, port2=1)#, cls = TCLink, bw = 100)
        #sb1 to hosts
        self.addLink(sb1, hb1, port1=2, port2=1)#, cls = TCLink, bw = 100)	
        self.addLink(sb1, hb2, port1=3, port2=1)#, cls = TCLink, bw = 100)	
        #sc1 to hosts
        self.addLink(sc1, hc1, port1=2, port2=1)#, cls = TCLink, bw = 100)
        self.addLink(sc1, hc2, port1=3, port2=1)#, cls = TCLink, bw = 100)
        #Backup links
        #self.addLink(s0b, sa1, port1=2, port2=4)#, cls = TCLink, bw = 50)
        #self.addLink(s0b, sb1, port1=3, port2=4)#, cls = TCLink, bw = 50)
        #self.addLink(s0b, sc1, port1=4, port2=4)#, cls = TCLink, bw = 50)

# This function will be used to run our defined topo
def run():
    setLogLevel('info')
    topo = VlanRoutingTopo()
    onos_ctrl = RemoteController('c0', ip=ONOS_IP, port=ONOS_OF_PORT)
    net = Mininet(topo=topo, controller=onos_ctrl, link=TCLink, autoSetMacs=False)
    
    net.start()

    info('*** Setting up Static ARP for Gateways\n')
    ha1 = net.get('ha1')
    ha2 = net.get('ha2')
    hb1 = net.get('hb1')
    hb2 = net.get('hb2')
    hc1 = net.get('hc1')
    hc2 = net.get('hc2')

    # STATIC ARP SO THAT PACKETS CAN GO TO THE LEAF SWITCHES FIRST, USING A DUMMY MAC 00:00:00:00:00:99
    ha1.cmd('arp -s 10.0.10.1 00:00:00:00:00:99')
    ha2.cmd('arp -s 10.0.20.1 00:00:00:00:00:99')
    hb1.cmd('arp -s 10.0.10.1 00:00:00:00:00:99')
    hb2.cmd('arp -s 10.0.20.1 00:00:00:00:00:99')
    hc1.cmd('arp -s 10.0.10.1 00:00:00:00:00:99')
    hc2.cmd('arp -s 10.0.20.1 00:00:00:00:00:99')

    info('*** Network is up\n')
    CLI(net)
    net.stop()

if __name__ == '__main__':
    run()
topos = { 'VlanRouting': ( lambda: VlanRoutingTopo() ) }

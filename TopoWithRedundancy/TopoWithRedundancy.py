#Importing necessary libraries
from mininet.net import Mininet # For mininet topo
from mininet.node import RemoteController # For connecting to ONOS
from mininet.topo import Topo
from mininet.link import TCLink #Traffic-Control Link, can be used for bandwidth control and many more
from mininet.cli import CLI
from mininet.log import setLogLevel, info

# Our topology will look like this
"""
        s0a - s0b (s0b will be s0a's replacement, in case s0a is down)
      /  |   \
     /   |    \
    /    |     \
  sa1   sb1    sc1
 /  \   /  \    |  \
ha1 ha2 hb1 hb2 hc1 hc2
"""
# Our ONOS controller will connect to all of the switches 
# Furthermore, we will define different VLAN for our hosts
# ha1, ha2 will be from 10.0.10.0/24
# hb1, hb2 will be from 10.0.20.0/24
# hc1, hc2 will be from 10.0.30.0/24
class RedundantVlanTopo(Topo):
	def __init__(self, **opts):
		super( RedundantVlanTopo, self ).__init__(**opts)
	
		# To ensure all five switches show up in ONOS GUI, assign a unique ID when adding switches
		# Central switches (s0a, s0b)
		s0a = self.addSwitch('s0a', dpid='0000000000000001')
		s0b = self.addSwitch('s0b', dpid='0000000000000002')
		
		#Leaf switches (sa1, sb1, sc1)
		sa1 = self.addSwitch('sa1', dpid='0000000000000003')
		sb1 = self.addSwitch('sb1', dpid='0000000000000004')
		sc1 = self.addSwitch('sc1', dpid='0000000000000005')

		#Hosts (ha1, ha2, hb1, hb2, hc1, hc2)
		ha1 = self.addHost('ha1', ip = '10.0.10.11/24')
		ha2 = self.addHost('ha2', ip = '10.0.10.12/24')
		hb1 = self.addHost('hb1', ip = '10.0.10.21/24')	
		hb2 = self.addHost('hb2', ip = '10.0.10.22/24')
		hc1 = self.addHost('hc1', ip = '10.0.10.31/24')
		hc2 = self.addHost('hc2', ip = '10.0.10.32/24')
		
		#Main links
		# Central switches links
		self.addLink(s0a, s0b)#, cls = TCLink, bw = 100)
		# Central switch to branch switches
		self.addLink(s0a, sa1)#, cls = TCLink, bw = 100)
		self.addLink(s0a, sb1)#, cls = TCLink, bw = 100)
		self.addLink(s0a, sc1)#, cls = TCLink, bw = 100)
		#sa1 to hosts
		self.addLink(sa1, ha1)#, cls = TCLink, bw = 100)	
		self.addLink(sa1, ha2)#, cls = TCLink, bw = 100)
		#sb1 to hosts
		self.addLink(sb1, hb1)#, cls = TCLink, bw = 100)	
		self.addLink(sb1, hb2)#, cls = TCLink, bw = 100)	
		#sc1 to hosts
		self.addLink(sc1, hc1)#, cls = TCLink, bw = 100)
		self.addLink(sc1, hc2)#, cls = TCLink, bw = 100)
		#Backup links
		self.addLink(s0b, sa1)#, cls = TCLink, bw = 50)
		self.addLink(s0b, sb1)#, cls = TCLink, bw = 50)
		self.addLink(s0b, sc1)#, cls = TCLink, bw = 50)

# This function will be used to run our defined topo
def run():
    setLogLevel('info') # Mostly for debugging
    topo = RedundantVlanTopo()
    net = Mininet(topo=topo,controller=None,link=TCLink)
    #c0 = net.addController('c0', controller = RemoteController, ip = '172.17.0.5', port = 6653)
    net.start() # Starts it
    info('*** Network is up\n')
    CLI(net) # Opens the terminal for demo
    net.stop() # Stops the topo, if terminal is closed

if __name__ == '__main__':
    run()
topos = { 'TopoWithRedundancy': ( lambda: RedundantVlanTopo() ) }

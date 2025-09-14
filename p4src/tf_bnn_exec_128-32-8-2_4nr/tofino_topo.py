from p4utils.utils.compiler import BF_P4C
from p4utils.mininetlib.network_API import NetworkAPI

import os
import sys

P4_SRC = sys.argv[1]
SDE = os.environ['SDE']
SDE_INSTALL = os.environ['SDE_INSTALL']
P4_PROGRAM = os.path.join(os.path.dirname(os.path.abspath(__file__)), P4_SRC)
P4C='/home/sgeraci/p4/open-p4studio/install/bin/p4c-tna'

net = NetworkAPI()

# Network general options
net.setLogLevel('debug')
net.enableCli()

# Tofino compiler
net.setCompiler(compilerClass=BF_P4C, sde=SDE, sde_install=SDE_INSTALL, p4c=P4C)

# Network definition
net.addTofino('s1', sde=SDE, sde_install=SDE_INSTALL)
net.setP4SourceAll(P4_PROGRAM)

net.addHost('h1')
# net.addHost('h2')

net.addLink('h1', 's1', port1=1)
# net.addLink('s1', 'h2', port1=2)

# Assignment strategy
net.l2()

# Nodes general options
net.enableLogAll()
net.enablePcapDump('s1')    
# Start the network
net.startNetwork()

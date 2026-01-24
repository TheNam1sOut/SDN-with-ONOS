# SDN with ONOS

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![ONOS Version](https://img.shields.io/badge/ONOS-2.7.0%2B-blue.svg)](https://onosproject.org/)
[![Mininet Version](https://img.shields.io/badge/Mininet-2.3.0%2B-green.svg)](http://mininet.org/)
[![VirtualBox Version](https://img.shields.io/badge/VirtualBox-7.0%2B-blue.svg)](https://www.virtualbox.org/)

<!-- TOC --><a name="table-of-content"></a>
## Table of content
<!-- TOC start (generated with https://github.com/derlin/bitdowntoc) -->

- [SDN with ONOS](#sdn-with-onos)
  - [Table of content](#table-of-content)
  - [Letter of gratitude](#letter-of-gratitude)
  - [Summary](#summary)
  - [Chapter 1: Theory](#chapter-1-theory)
    - [Section 1.1: Overview of SDN](#section-11-overview-of-sdn)
    - [Section 1.2: Why you should use SDN](#section-12-why-you-should-use-sdn)
    - [Section 1.3: SDN's architecture](#section-13-sdns-architecture)
    - [Section 1.4: OpenFlow protocol, OpenFlow switch, and OpenFlow flow table](#section-14-openflow-protocol-openflow-switch-and-openflow-flow-table)
  - [Chapter 2: Implementation](#chapter-2-implementation)
    - [Section 2.1: Overview](#section-21-overview)
    - [Section 2.2: First Scenario - Forwarding packets](#section-22-first-scenario---forwarding-packets)
    - [Section 2.3: Second scenario - Banning host ha1 from pinging ha2](#section-23-second-scenario---banning-host-ha1-from-pinging-ha2)
    - [Section 2.4: Third Scenario - Only allowing host ha1 to ping hb2](#section-24-third-scenario---only-allowing-host-ha1-to-ping-hb2)
    - [Section 2.5: Fourth Scenario - Testing connection using backup switch s0b](#section-25-fourth-scenario---testing-connection-using-backup-switch-s0b)
    - [Section 2.6: Fifth Scenario - Routing packets](#section-26-fifth-scenario---routing-packets)

<!-- TOC end -->
<!-- TOC --><a name="letter-of-gratitude"></a>
## Letter of gratitude
The project would not have been possible without the help of our lecturer, **Msc. Do Hoang Hien**, as well as the work of **Group 5**, consisting of **Duong Phuoc Nhat Nam (me), Nguyen Gia Luan, Luong Hoang Long** and **Le Minh**.
<!-- TOC --><a name="summary"></a>
## Summary
This README serves as a summary to what we have researched and done in the report, you can find out more at the report [here, written in Vietnamese](https://github.com/TheNam1sOut/SDN-with-ONOS/blob/master/%5BNT132.Q12.ANTT%5D-Nhom5_BaoCaoCuoiKy.pdf). You can also read the report's slides [here, written in Vietnamese also](https://github.com/TheNam1sOut/SDN-with-ONOS/blob/master/%5BNT132.Q12.ANTT%5D-Nhom5.pdf).

In chapter 1, we will mostly discuss the general idea on how SDN works. In chapter 2, we will discuss on the technology used for the project, setting up the environment, how to use the source code in the repository and explaining the ideas behind the source code.
<!-- TOC --><a name="chapter-1-theory"></a>
## Chapter 1: Theory
<!-- TOC --><a name="section-11-overview-of-sdn"></a>
### Section 1.1: Overview of SDN
**SDN (Software-Defined Network)** is an alternative approach to traditional network. Let's look at the picture below for traditional network.

![Traditional Network](/Images/TraditionalNetwork.png)

As you can see, each networking device has a routing/forwarding table and an algorithm to determine how to send the packets. This is called the data plane and the control plane. **SDN**, however, separates the control plane from the data plane, by having a remote controller instead, and the networking devices now only have the data plane, as illustrated below.

![SDN](/Images/SDN.png)
<!-- TOC --><a name="section-12-why-you-should-use-sdn"></a>
### Section 1.2: Why you should use SDN
To first know why you should use SDN, we will first want to know about tradional network's flaws, including:

1. Unable to automate configuration, as you will have to manually configure each networking device.
2. Installing additional services e.g. firewall, load balancer requires a dedicated device.
3. Poor scaling options.

As a proposed solution to traditional network, SDN aims to solve those problems.

1. Changes are present throughout the network when configuring the controller alone.
2. Automation is much easier as the controller is a software.
3. Scalability, maintenance and operation is much less of an issue.
4. Installing services into the controller is much easier.


<!-- TOC --><a name="section-13-sdns-architecture"></a>
### Section 1.3: SDN's architecture
SDN has 3 layers: **Application layer, control layer** and **infrastructure layer**. Between the layers are the **northbound APIs**, and **southbound APIs** used to communicate between the layers.

* Application layer: This is where you will install services into the controller.
* Control layer: This is the controller itself.
* Infrastructure layer: This layer will basically contain the networking devices, like your switches. 
* Northbound APIs: This is how the application layer and the control layer communicate e.g. REST APIs as used in our implementation.
* Southbound APIs: This is how the control layer and the infrastructure layer communicate. A famous example of soundbound APIs is the 
OpenFlow protocol, which we will discuss below.

![SDN_Architecture](/Images/SDN_Architecture.png)
<!-- TOC --><a name="section-14-openflow-protocol-openflow-switch-and-openflow-flow-table"></a>
### Section 1.4: OpenFlow protocol, OpenFlow switch, and OpenFlow flow table
As mentioned above, **OpenFlow** protocol is a way for the control layer and the infrastructure to communicate. To be specific, it allows the controller to access and modified the content inside the data plane.

To understand more about OpenFlow, we will go into the OpenFlow **switch** and **flow table**.

Firstly, an OpenFlow switch has dedicated channels to let the controller gain access and modified data. Furthermore, it has several flow tables (similar to our routing/forwarding tables in traditional network) forming a pipeline, which means that we can use each subsequent flow table to handle more specific tasks, like what we will discuss in **Section 2.6**.

![OpenFlow_Switch](/Images/OpenFlow_Switch.png)

Each flow table will have multiple flow entries. Each entry will have some notable fields as the following:
* Match field: Determines the packets that this entry will handle. It can filter using VLAN ID, source and destination MAC address, source and destination IP address, and the input switch port.
* Priority: Used to resolve issues when there are more than one eligible flow entry to handle the packet. The flow rule with the higher priority will be used.
* Counter: Counts the times this entry has been used.
* Instruction: Determines the action needed to handle the packet, including:
    * Forward to an output port.
    * Forward it to the controller in case there is no other eligible flow entry.
    * Drop the packet.
    * Edit the packet's headers.
    * Transfer the packet to the subsequent flow table.
* Timeout: The flow entry's expiration time.
* Cookie: Can be used by the controller to filter flow entries.

![OpenFlow_FlowTable](/Images/OpenFlow_FlowTable.png)

Next, we will go deeper into how OpenFlow will be used in Chapter 2.
<!-- TOC --><a name="chapter-2-implementation"></a>
## Chapter 2: Implementation
<!-- TOC --><a name="section-21-overview"></a>
### Section 2.1: Overview
In order to implement our SDN, we need to define some technology used for this project, including:
1. **ONOS (Open Network Operating System)**: The controller for our SDN, it also comes with a CLI (Command Line Interface), a web GUI (Graphical User Interface) to visualize the network and to configure the network easier, and services to help with most of the scenarios here.
2. **Mininet**: The tool to define our SDNs.
3. **VirtualBox**: Main software used to create a VM (Virtual Machine). We will use a prebuilt VM provided by ONOS ([Installation guide here](https://wiki.onosproject.org/display/ONOS/Basic+ONOS+Tutorial#BasicONOSTutorial-Downloadandinstallrequiredsoftware)) to get started with Mininet and ONOS easier, though we do recommend that you should **build them yourself**, as the **prebuilt version is rather outdated**. 

Before getting to the deployment and implementing scenarios, you should familiarize yourself with ONOS first [here](https://wiki.onosproject.org/display/ONOS/Basic+ONOS+Tutorial).

After that, we should go deploy our SDNs for the scenarios. The first SDN will cover the first four scenarios, while the second one will cover the last scenario.

The commands to run the source codes can be found at *./Source/scripts-to-run.txt*.

1. First SDN
   * Information on the first SDN: 
      - 5 switches: main switch (**s0a** - upper left), backup switch (**s0b** - upper right), 3 leaf switches (from left to right: **sa1, sb1, sc1**).
      - 6 hosts, each leaf switch has 2 hosts, all hosts **share the same subnet (10.0.10.0/24)**. Name and IP of each host from left to right: **ha1** - 10.0.10.11; **ha2** - 10.0.10.12; **hb1** - 10.0.10.21; **hb2** - 10.0.10.22; **hc1** - 10.0.10.31; **hc2** - 10.0.10.32.

   ![First SDN](/Images/FirstSDN_Network.png)
   
   * The source code to deploy the first SDN is at *./Source/TopoWithRedundancy/TopoWithRedundancy.py*, use this file with this command (change the directory to where the file is):

```bash
sudo mn --custom=/home/sdn/Desktop/Project/TopoWithRedundancy.py --topo=TopoWithRedundancy --controller remote,ip=172.17.0.5,port=6653 --switch=ovsk,protocols=OpenFlow13
```

2. Second SDN
   * Information on the second SDN: 
      - 4 switches: main switch (**s0a** - upper left), 3 leaf switches (from left to right: **sa1, sb1, sc1**).
      - 6 hosts, each leaf switch has 2 hosts, hosts on the left side use **subnet 10.0.10.0/24** with **VLAN 10**, while hosts on the right side use **subnet 10.0.20.0/24** with **VLAN 20**. Name and IP of each host from left to right: **ha1** - 10.0.10.11; **ha2** - 10.0.20.11; **hb1** - 10.0.10.12; hb2 - 10.0.20.22; **hc1** - 10.0.10.13; **hc2** - 10.0.20.13.

   ![Second SDN](/Images/SecondSDN_Network.png)
   
   * The source code to deploy the second SDN is at *./Source/vlan-routing/vlan-routing.py*, use this file with this command (you need to install newer python version first, and change your current directory to where the file is):

```bash
PY=~/.pyenv/versions/3.8.18/bin/python3.8
sudo $PY vlan-routing.py
```

The sections below will assume you have already deployed the required SDNs for the scenarios.
<!-- TOC --><a name="section-22-first-scenario-forwarding-packets"></a>
### Section 2.2: First Scenario - Forwarding packets

Simply activate the reactive switching app at the **ONOS CLI** to complete this scenario:

```bash
app activate org.onosproject.fwd
```
<!-- TOC --><a name="section-23-second-scenario-banning-host-ha1-from-pinging-ha2"></a>
### Section 2.3: Second scenario - Banning host ha1 from pinging ha2

We will build this flow rule at *./Source/TopoWithRedundancy/drop-ha1-to-hb1.json*. Note that `deviceId` is from **sa1**, `instructions` is set to none (drop the packet), and the `criteria` is set to only ban ICMP Request packets coming from **ha1** to **hb1**.
```json
{
  "priority": 50000,
  "timeout": 0,
  "isPermanent": true,
  "deviceId": "of:0000000000000003",
  "treatment": {
    "instructions": []
  },
  "selector": {
    "criteria": [
      { "type": "ETH_TYPE", "ethType": "0x800" },   
      { "type": "IPV4_SRC", "ip": "10.0.10.11/32" },
      { "type": "IPV4_DST", "ip": "10.0.10.21/32" },
      { "type": "IP_PROTO", "protocol": "1" },
      { "type": "ICMPV4_TYPE", "icmpType": "8" }     
    ]
  }
}
```
Next, send the JSON file to ONOS with this command:
```curl
curl -u onos:rocks -X POST -H "Content-Type: application/json" -d @drop-ha1-to-hb1.json http://172.17.0.5:8181/onos/v1/flows/of:0000000000000003
```
<!-- TOC --><a name="section-24-third-scenario-only-allowing-host-ha1-to-ping-hb2"></a>
### Section 2.4: Third Scenario - Only allowing host ha1 to ping hb2

We will build 2 flow rules at *./Source/TopoWithRedundancy/drop-to-hb2.json* and *./Source/TopoWithRedundancy/permit-ha1.json*.

* Content of *drop-to-hb2.json* (set this flow rule at **sb1**, ban all ICMP Request packets coming to **hb2**):
```json
{
  "priority": 50000,
  "timeout": 0,
  "isPermanent": true,
  "deviceId": "of:0000000000000004",
  "treatment": {
    "instructions": []
  },
  "selector": {
    "criteria": [
      { "type": "ETH_TYPE", "ethType": "0x800" },   
      { "type": "IPV4_DST", "ip": "10.0.10.22/32" },
      { "type": "IP_PROTO", "protocol": "1" },
      { "type": "ICMPV4_TYPE", "icmpType": "8" }     
    ]
  }
}
```

* Content of *permit-ha1.json* (set this flow rule at **sb1**, amd set this rule's `priority` higher to avoid applying *drop-to-hb2.json* to **ha1**):
```json
{
  "priority": 51000,
  "timeout": 0,
  "isPermanent": true,
  "deviceId": "of:0000000000000004",
  "treatment": {
    "instructions": [{ "type": "OUTPUT", "port": "3" }]
  },
  "selector": {
    "criteria": [
      { "type": "ETH_TYPE", "ethType": "0x800" },   
      { "type": "IPV4_SRC", "ip": "10.0.10.11/32" },
      { "type": "IPV4_DST", "ip": "10.0.10.22/32" },
      { "type": "IP_PROTO", "protocol": "1" },
      { "type": "ICMPV4_TYPE", "icmpType": "8" }     
    ]
  }
}
```
Next, send the JSON files to ONOS with these commands:
```curl
curl -u onos:rocks -X POST -H "Content-Type: application/json" -d @drop-to-hb2.json http://172.17.0.5:8181/onos/v1/flows/of:0000000000000004

curl -u onos:rocks -X POST -H "Content-Type: application/json" -d @permit-ha1.json http://172.17.0.5:8181/onos/v1/flows/of:0000000000000004

```
<!-- TOC --><a name="section-25-fourth-scenario-testing-connection-using-backup-switch-s0b"></a>
### Section 2.5: Fourth Scenario - Testing connection using backup switch s0b

Simply turn off the links from the leaf switches to the main switch and test the connection using `pingall` command from the **Mininet CLI**.

![Fourth_Scenario](/Images/FirstSDN_FourthScenario.png)

```bash
link s0a sa1 down
link s0a sb1 down
link s0a sc1 down
```
<!-- TOC --><a name="section-26-fifth-scenario-routing-packets"></a>
### Section 2.6: Fifth Scenario - Routing packets

**Warning: Make sure you start ONOS cleanly again, as this scenario will use the second SDN, and previous configurations from the first SDN may mess with this scenario.**

Since we cannot use any app from the prebuilt VM, there are two approaches to this scenario: Build a routing app, or manually install every flow rule to make sure packets can reach the hosts. For the sake of simplicity, we will use the second approach. The snippets below will be taken from *./Source/vlan-routing/configure-onos-router.py*, except for the first task, which is from *./Source/vlan-routing/vlan-routing.py*.

We will need to do the following:

1. Configure the default gateway (IP + MAC) for each host.
* IP:

```python
ha1 = self.addHost('ha1', ip = '10.0.10.11/24', mac='00:00:00:00:01:01', defaultRoute='via 10.0.10.1')
ha2 = self.addHost('ha2', ip = '10.0.20.11/24', mac='00:00:00:00:02:01', defaultRoute='via 10.0.20.1')
hb1 = self.addHost('hb1', ip = '10.0.10.12/24', mac='00:00:00:00:01:02', defaultRoute='via 10.0.10.1')	
hb2 = self.addHost('hb2', ip = '10.0.20.12/24', mac='00:00:00:00:02:02', defaultRoute='via 10.0.20.1')
hc1 = self.addHost('hc1', ip = '10.0.10.13/24', mac='00:00:00:00:01:03', defaultRoute='via 10.0.10.1')
hc2 = self.addHost('hc2', ip = '10.0.20.13/24', mac='00:00:00:00:02:03', defaultRoute='via 10.0.20.1')
```
* MAC: 

```python
# STATIC ARP SO THAT PACKETS CAN GO TO THE LEAF SWITCHES FIRST, USING A DUMMY MAC 00:00:00:00:00:99
ha1.cmd('arp -s 10.0.10.1 00:00:00:00:00:99')
ha2.cmd('arp -s 10.0.20.1 00:00:00:00:00:99')
hb1.cmd('arp -s 10.0.10.1 00:00:00:00:00:99')
hb2.cmd('arp -s 10.0.20.1 00:00:00:00:00:99')
hc1.cmd('arp -s 10.0.10.1 00:00:00:00:00:99')
hc2.cmd('arp -s 10.0.20.1 00:00:00:00:00:99')
```

2. Define flow rule when packets enter the switch. The flow rule will add the host's corresponding VLAN, and forward it to **table 1** for further processing. 

```python
def provision_ingress_rule(device_id, host_port, vlan_id):
    print(f"Configuring Ingress for Port {host_port} on VLAN {vlan_id}...")
    rule = {
        "priority": 40000, "isPermanent": True, "deviceId": device_id, "tableId": 0,
        "selector": { 
            "criteria": [ {"type": "IN_PORT", "port": host_port} ] 
        },
        "treatment": { "instructions": [
            {"type": "L2MODIFICATION", "subtype": "VLAN_PUSH"},
            {"type": "L2MODIFICATION", "subtype": "VLAN_ID", "vlanId": vlan_id},
            {"type": "TABLE", "tableId": 1}
        ]}
    }
    send_flow(device_id, rule)
```
3. Routing between hosts sharing the same switches. We will rewrite the MAC's source and destination like routing in traditional networks, and then remove the VLAN tag before forwarding to the destination.

```python
def provision_intra_switch_route(
    name,
    device_id,
    src_vlan,
    dst_ip,        # Target IP (e.g., 10.0.20.11/32)
    dst_mac,       # Target MAC (e.g., 00:00...02:01)
    dst_vlan,      # Target VLAN (e.g., 20)
    out_port       # Target Port (e.g., 3)
):
    print(f"Configuring Local Route: {name}...")
    rule = {
        "priority": 40000, "isPermanent": True, "deviceId": device_id, "tableId": 1,
        "selector": {
            "criteria": [
                {"type": "IPV4_DST", "ip": dst_ip},
                {"type": "ETH_TYPE", "ethType": "0x0800"},
                {"type": "VLAN_VID", "vlanId": src_vlan}
            ]
        },
        "treatment": { "instructions": [
            # 1. Rewrite DST MAC to Host MAC
            {"type": "L2MODIFICATION", "subtype": "ETH_DST", "mac": dst_mac},
            # 2. Rewrite SRC MAC to Router MAC (Gateway)
            {"type": "L2MODIFICATION", "subtype": "ETH_SRC", "mac": ROUTER_MAC},
            # 3. Change VLAN ID to Target VLAN
            {"type": "L2MODIFICATION", "subtype": "VLAN_ID", "vlanId": dst_vlan},
            # 4. Pop VLAN (Host expects untagged)
            {"type": "L2MODIFICATION", "subtype": "VLAN_POP"},
            # 5. Output to Host Port
            {"type": "OUTPUT", "port": out_port}
        ]}
    }
    send_flow(device_id, rule)
```
4. Routing between hosts from different switches (same/different subnets). Both routing from the same or different subnets share the same steps: Forward from the source leaf switch to the main switch **(different implementation)**, forward from the main switch to the destination leaf switch and forward from the destination leaf switch to the destination.

* Forward from the source leaf switch to the main switch:

```python
# Same subnet (we simply forward the packet without further actions):
rule_src = {
   "priority": 40000, "isPermanent": True, "deviceId": src_leaf_id, "tableId": 1,
   "selector": {
      "criteria": [
            {"type": "ETH_DST", "mac": dst_mac},
            {"type": "VLAN_VID", "vlanId": vlan_id}
      ]
   },
   "treatment": { "instructions": [
      {"type": "OUTPUT", "port": src_uplink}
   ]}
}
```

```python
# Different subnet (change source and destination MAC addresses and change to destination VLAN before forwarding to the main switch): 
rule_src = {
   "priority": 41000, # Higher priority than generic matches
   "isPermanent": True, "deviceId": src_leaf_id, "tableId": 1,
   "selector": {
      "criteria": [
            {"type": "ETH_DST", "mac": ROUTER_MAC},
            {"type": "IPV4_DST", "ip": dst_ip},
            {"type": "ETH_TYPE", "ethType": "0x0800"},
            {"type": "VLAN_VID", "vlanId": src_vlan}
      ]
   },
   "treatment": { "instructions": [
      # Rewrite Headers
      {"type": "L2MODIFICATION", "subtype": "ETH_SRC", "mac": ROUTER_MAC},
      {"type": "L2MODIFICATION", "subtype": "ETH_DST", "mac": dst_mac},
      {"type": "L2MODIFICATION", "subtype": "VLAN_ID", "vlanId": dst_vlan},
      # Forward Up
      {"type": "OUTPUT", "port": src_uplink}
   ]}
}
``` 
* Forward from the main switch to the destination leaf switch:

```python
rule_spine = {
   "priority": 40000, "isPermanent": True, "deviceId": spine_id, "tableId": 0,
   "selector": {
      "criteria": [ {"type": "ETH_DST", "mac": dst_mac} ]
   },
   "treatment": { "instructions": [
      {"type": "OUTPUT", "port": spine_downlink}
   ]}
}
```

* Forward from the destination leaf switch to the destination (remove the VLAN tag before forwarding):

```python
rule_dst = {
   "priority": 40000, "isPermanent": True, "deviceId": dst_leaf_id, "tableId": 0,
   "selector": {
      "criteria": [
            {"type": "ETH_DST", "mac": dst_mac},
            {"type": "VLAN_VID", "vlanId": dst_vlan}
      ]
   },
   "treatment": { "instructions": [
      {"type": "L2MODIFICATION", "subtype": "VLAN_POP"},
      {"type": "OUTPUT", "port": dst_host_port}
   ]}
}
```

5. Define the function to send flow rules.

```python
def send_flow(device_id, flow_data):
   url = f'http://{ONOS_IP}:{ONOS_PORT}/onos/v1/flows/{device_id}'
   response = requests.post(url, auth=AUTH, data=json.dumps(flow_data), headers={'Content-Type': 'application/json'})
   if response.status_code not in [200, 201]:
      print(f" [FAIL] {device_id} Error: {response.text}")
```

To use *configure-onos-router.py*, simply use this command:

```bash
$PY configure-onos-router.py
```
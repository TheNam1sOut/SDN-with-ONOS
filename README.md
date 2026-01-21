# SDN with ONOS

<!-- TOC --><a name="table-of-content"></a>
## Table of content
<!-- TOC start (generated with https://github.com/derlin/bitdowntoc) -->

- [Letter of gratitude](#letter-of-gratitude)
- [Table of content](#table-of-content)
- [Summary](#summary)
- [Chapter 1: Theory](#chapter-1-theory)
   * [Section 1.1: Overview of SDN](#section-11-overview-of-sdn)
   * [Section 1.2: Why you should use SDN](#section-12-why-you-should-use-sdn)
   * [Section 1.3: SDN's architecture](#section-13-sdns-architecture)
   * [Section 1.4: OpenFlow protocol, OpenFlow switch, and OpenFlow flow table](#section-14-openflow-protocol-openflow-switch-and-openflow-flow-table)
- [Chapter 2: Implementation](#chapter-2-implementation)
   * [Section 2.1: Overview](#section-21-overview)
   * [Section 2.2: First Scenario - Forwarding packets](#section-22-first-scenario-forwarding-packets)
   * [Section 2.3: Second scenario - Banning host ha1 from pinging ha2](#section-23-second-scenario-banning-host-ha1-from-pinging-ha2)
   * [Section 2.4: Third Scenario - Only allowing host ha1 to ping hb2](#section-24-third-scenario-only-allowing-host-ha1-to-ping-hb2)
   * [Section 2.5: Fourth Scenario - Testing connection using backup switch s0b](#section-25-fourth-scenario-testing-connection-using-backup-switch-s0b)
   * [Section 2.6: Fifth Scenario - Routing packets](#section-26-fifth-scenario-routing-packets)

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
SDN has 3 layers: Application layer, control layer and infrastructure layer. Between the layers are the northbound APIs, and southbound APIs used to communicate between the layers.

* Application layer: This is where you will install services into the controller.
* Control layer: This is the controller itself.
* Infrastructure layer: This layer will basically contain the networking devices, like your switches. 
* Northbound APIs: This is how the application layer and the control layer communicate e.g. REST APIs as used in our implementation.
* Southbound APIs: This is how the control layer and the infrastructure layer communicate. A famous example of soundbound APIs is the 
OpenFlow protocol, which we will discuss below.

![SDN_Architecture](/Images/SDN_Architecture.png)
<!-- TOC --><a name="section-14-openflow-protocol-openflow-switch-and-openflow-flow-table"></a>
### Section 1.4: OpenFlow protocol, OpenFlow switch, and OpenFlow flow table
As mentioned above, OpenFlow protocol is a way for the control layer and the infrastructure to communicate. To be specific, it allows the controller to access and modified the content inside the data plane.

To understand more about OpenFlow, we will go into the OpenFlow switch and flow table.

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

Next, we will go deeper into how OpenFlow will be used in Chapter 2.


![OpenFlow_FlowTable](/Images/OpenFlow_FlowTable.png)
<!-- TOC --><a name="chapter-2-implementation"></a>
## Chapter 2: Implementation
<!-- TOC --><a name="section-21-overview"></a>
### Section 2.1: Overview
<!-- TOC --><a name="section-22-first-scenario-forwarding-packets"></a>
### Section 2.2: First Scenario - Forwarding packets
<!-- TOC --><a name="section-23-second-scenario-banning-host-ha1-from-pinging-ha2"></a>
### Section 2.3: Second scenario - Banning host ha1 from pinging ha2
<!-- TOC --><a name="section-24-third-scenario-only-allowing-host-ha1-to-ping-hb2"></a>
### Section 2.4: Third Scenario - Only allowing host ha1 to ping hb2
<!-- TOC --><a name="section-25-fourth-scenario-testing-connection-using-backup-switch-s0b"></a>
### Section 2.5: Fourth Scenario - Testing connection using backup switch s0b
<!-- TOC --><a name="section-26-fifth-scenario-routing-packets"></a>
### Section 2.6: Fifth Scenario - Routing packets
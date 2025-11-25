import requests
import json

# Configuration
ONOS_IP = '172.17.0.5'
ONOS_PORT = '8181'
AUTH = ('onos', 'rocks') 
# Define Device IDs
DEV_HA1 = '00:00:00:00:01:01'
DEV_HA2 = '00:00:00:00:02:01'
DEV_HB1 = '00:00:00:00:01:02'
DEV_HB2 = '00:00:00:00:02:02'
DEV_HC1 = '00:00:00:00:01:03'
DEV_HC2 = '00:00:00:00:02:03'

DEV_SA1 = 'of:0000000000000003'
DEV_SB1 = 'of:0000000000000004'
DEV_SC1 = 'of:0000000000000005'
DEV_S0A = 'of:0000000000000001' # The Spine
ROUTER_MAC = '00:00:00:00:00:99'

headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}

def send_flow(device_id, flow_data):
    url = f'http://{ONOS_IP}:{ONOS_PORT}/onos/v1/flows/{device_id}'
    response = requests.post(url, auth=AUTH, data=json.dumps(flow_data), headers={'Content-Type': 'application/json'})
    if response.status_code not in [200, 201]:
        print(f" [FAIL] {device_id} Error: {response.text}")

# --- 1. INGRESS RULE (Table 0 -> Table 1) ---
# "If packet comes in Port X, push VLAN Y, and go to Table 1"
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

# --- 2. INTRA-SWITCH ROUTE (Table 1 -> Output) ---
# "If Dest IP is Local, rewrite MACs and deliver"
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

# --- 3. L2 INTER-SWITCH FORWARDING (Same Subnet, Different Switch) ---
def provision_l2_remote_forwarding(
    name,
    src_leaf_id,
    dst_leaf_id,
    spine_id,
    dst_mac,         # The actual Host MAC
    vlan_id,         # The shared VLAN (e.g., 10)
    src_uplink,      # Port on Src Leaf -> Spine
    spine_downlink,  # Port on Spine -> Dst Leaf
    dst_host_port    # Port on Dst Leaf -> Host
):
    print(f"--- Provisioning L2 Path (Bridging): {name} ---")

    # 1. SRC LEAF: Bridge to Spine
    # STRICTNESS: Match specific Host MAC and VLAN. 
    # Do NOT match Router MAC here.
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
    send_flow(src_leaf_id, rule_src)

    # 2. SPINE: Forward to Destination Leaf
    # Spine acts as a transparent L2 bridge based on MAC
    rule_spine = {
        "priority": 40000, "isPermanent": True, "deviceId": spine_id, "tableId": 0,
        "selector": {
            "criteria": [ {"type": "ETH_DST", "mac": dst_mac} ]
        },
        "treatment": { "instructions": [
            {"type": "OUTPUT", "port": spine_downlink}
        ]}
    }
    send_flow(spine_id, rule_spine)

    # 3. DST LEAF: Deliver to Host
    rule_dst = {
        "priority": 40000, "isPermanent": True, "deviceId": dst_leaf_id, "tableId": 0,
        "selector": {
            "criteria": [
                {"type": "ETH_DST", "mac": dst_mac},
                {"type": "VLAN_VID", "vlanId": vlan_id}
            ]
        },
        "treatment": { "instructions": [
            {"type": "L2MODIFICATION", "subtype": "VLAN_POP"},
            {"type": "OUTPUT", "port": dst_host_port}
        ]}
    }
    send_flow(dst_leaf_id, rule_dst)


# --- 4. L3 INTER-SWITCH ROUTING (Different Subnet, Different Switch) ---
def provision_l3_remote_routing(
    name,
    src_leaf_id,
    dst_leaf_id,
    spine_id,
    src_vlan,        # VLAN where packet originates (e.g., 10)
    dst_vlan,        # VLAN where packet is going (e.g., 20)
    dst_ip,          # Specific Dest IP (e.g., 10.0.20.12/32)
    dst_mac,         # Final Host MAC
    src_uplink,      # Port on Src Leaf -> Spine
    spine_downlink,  # Port on Spine -> Dst Leaf
    dst_host_port    # Port on Dst Leaf -> Host
):
    print(f"--- Provisioning L3 Path (Routing): {name} ---")

    # 1. SRC LEAF: Route to Spine
    # STRICTNESS: Must match ETH_DST == ROUTER_MAC (00:00:00:00:00:99)
    # This distinguishes this flow from L2 bridging.
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
    send_flow(src_leaf_id, rule_src)

    # 2. SPINE: Forward to Destination Leaf
    # Note: The packet now has the Final Host MAC (rewritten by Src Leaf)
    rule_spine = {
        "priority": 40000, "isPermanent": True, "deviceId": spine_id, "tableId": 0,
        "selector": {
            "criteria": [ {"type": "ETH_DST", "mac": dst_mac} ]
        },
        "treatment": { "instructions": [
            {"type": "OUTPUT", "port": spine_downlink}
        ]}
    }
    send_flow(spine_id, rule_spine)

    # 3. DST LEAF: Deliver to Host
    # Note: The packet arrives with dst_vlan and dst_mac
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
    send_flow(dst_leaf_id, rule_dst)

# Essential to keep the pipeline flowing if ARP requests happen
def provision_arp_punt(device_id):
    print(f"Configuring ARP Punt on {device_id}...")
    rule = {
        "priority": 41000, "isPermanent": True, "deviceId": device_id, "tableId": 1,
        "selector": {
            "criteria": [ {"type": "ETH_TYPE", "ethType": "0x0806"} ]
        },
        "treatment": { "instructions": [
            {"type": "OUTPUT", "port": "CONTROLLER"}
        ]}
    }
    send_flow(device_id, rule)

# --- MAIN EXECUTION ---
if __name__ == "__main__":
    
    # SETUP SWITCH INFRASTRUCTURE
    provision_arp_punt(DEV_SA1)
    provision_arp_punt(DEV_SB1)
    provision_arp_punt(DEV_SC1)
    provision_arp_punt(DEV_S0A)

    # SETUP HOST INGRESS (mostly so that table 1 can actually handle the routing (changing MAC dst and src, VLAN dst, etc.))
    ## ha1 (Port 2, VLAN 10)
    provision_ingress_rule(DEV_SA1, host_port=2, vlan_id=10)
    ## ha2 (Port 3, VLAN 20)
    provision_ingress_rule(DEV_SA1, host_port=3, vlan_id=20)
    ## hb1 (Port 2, VLAN 10)
    provision_ingress_rule(DEV_SB1, host_port=2, vlan_id=10)
    ## hb2 (Port 3, VLAN 20)
    provision_ingress_rule(DEV_SB1, host_port=3, vlan_id=20)
    ## hc1 (Port 2, VLAN 10)
    provision_ingress_rule(DEV_SC1, host_port=2, vlan_id=10)
    ## hc2 (Port 3, VLAN 20)
    provision_ingress_rule(DEV_SC1, host_port=3, vlan_id=20)

    '''
    SETUP LOCAL ROUTING
    '''

    ## Route: ha1 -> ha2
    provision_intra_switch_route(
        name="ha1 to ha2",
        device_id=DEV_SA1,
        src_vlan=10,
        dst_ip="10.0.20.11/32",
        dst_mac="00:00:00:00:02:01",
        dst_vlan=20,
        out_port=3
    )

    ## Route: ha2 -> ha1 (Reverse)
    provision_intra_switch_route(
        name="ha2 to ha1",
        device_id=DEV_SA1,
        src_vlan=20,
        dst_ip="10.0.10.11/32",
        dst_mac="00:00:00:00:01:01",
        dst_vlan=10,
        out_port=2
    )

    ## Route: hb1 -> hb2
    provision_intra_switch_route(
        name="hb1 to hb2",
        device_id=DEV_SB1,
        src_vlan=10,
        dst_ip="10.0.20.12/32",
        dst_mac="00:00:00:00:02:02",
        dst_vlan=20,
        out_port=3
    )

    ## Route: hb2 -> hb1 (Reverse)
    provision_intra_switch_route(
        name="hb2 to hb1",
        device_id=DEV_SB1,
        src_vlan=20,
        dst_ip="10.0.10.12/32",
        dst_mac="00:00:00:00:01:02",
        dst_vlan=10,
        out_port=2
    )

    ## Route: hc1 -> hc2
    provision_intra_switch_route(
        name="hc1 to hc2",
        device_id=DEV_SC1,
        src_vlan=10,
        dst_ip="10.0.20.13/32",
        dst_mac="00:00:00:00:02:03",
        dst_vlan=20,
        out_port=3
    )

    ## Route: hc2 -> hc1 (Reverse)
    provision_intra_switch_route(
        name="hc2 to hc1",
        device_id=DEV_SC1,
        src_vlan=20,
        dst_ip="10.0.10.13/32",
        dst_mac="00:00:00:00:01:03",
        dst_vlan=10,
        out_port=2
    )

    '''
    SETUP SAME SUBNET FORWARDING
    '''

    ## ha1 - hb1 - hc1
    ### ha1 -> hb1
    provision_l2_remote_forwarding(
        name="L2: ha1->hb1",
        src_leaf_id=DEV_SA1,
        dst_leaf_id=DEV_SB1,
        spine_id=DEV_S0A,
        dst_mac=DEV_HB1,       # hb1 MAC
        vlan_id=10,            # Both are VLAN 10
        src_uplink=1,
        spine_downlink=3,      # s0a connects to sb1 on port 3
        dst_host_port=2        # hb1 is on port 2 of sb1
    )

    ### hb1 -> ha1 (Return Path)
    provision_l2_remote_forwarding(
        name="L2: hb1->ha1",
        src_leaf_id=DEV_SB1,
        dst_leaf_id=DEV_SA1,
        spine_id=DEV_S0A,
        dst_mac=DEV_HA1,
        vlan_id=10,
        src_uplink=1,
        spine_downlink=2,      # s0a connects to sa1 on port 2
        dst_host_port=2
    )

    ### ha1 -> hc1
    provision_l2_remote_forwarding(
        name="L2: ha1->hc1",
        src_leaf_id=DEV_SA1,
        dst_leaf_id=DEV_SC1,
        spine_id=DEV_S0A,
        dst_mac=DEV_HC1,       # hc1 MAC
        vlan_id=10,            # Both are VLAN 10
        src_uplink=1,
        spine_downlink=4,      # s0a connects to sc1 on port 4
        dst_host_port=2        # hc1 is on port 2 of sc1
    )

    ### hc1 -> ha1 (Return Path)
    provision_l2_remote_forwarding(
        name="L2: hc1->ha1",
        src_leaf_id=DEV_SC1,
        dst_leaf_id=DEV_SA1,
        spine_id=DEV_S0A,
        dst_mac=DEV_HA1,
        vlan_id=10,
        src_uplink=1,
        spine_downlink=2,      # s0a connects to sa1 on port 2
        dst_host_port=2
    )

    ### hb1 -> hc1
    provision_l2_remote_forwarding(
        name="L2: hb1->hc1",
        src_leaf_id=DEV_SB1,
        dst_leaf_id=DEV_SC1,
        spine_id=DEV_S0A,
        dst_mac=DEV_HC1,       # hc1 MAC
        vlan_id=10,            # Both are VLAN 10
        src_uplink=1,
        spine_downlink=4,      # s0a connects to sc1 on port 4
        dst_host_port=2        # hc1 is on port 2 of sc1
    )

    ### hc1 -> hb1 (Return Path)
    provision_l2_remote_forwarding(
        name="L2: hc1->hb1",
        src_leaf_id=DEV_SC1,
        dst_leaf_id=DEV_SB1,
        spine_id=DEV_S0A,
        dst_mac=DEV_HB1,
        vlan_id=10,
        src_uplink=1,
        spine_downlink=3,      # s0a connects to sb1 on port 3
        dst_host_port=2
    )

    ## ha2 - hb2 - hc2
    ### ha2 -> hb2
    provision_l2_remote_forwarding(
        name="L2: ha2->hb2",
        src_leaf_id=DEV_SA1,
        dst_leaf_id=DEV_SB1,
        spine_id=DEV_S0A,
        dst_mac=DEV_HB2,       # hb2 MAC
        vlan_id=20,            # Both are VLAN 20
        src_uplink=1,
        spine_downlink=3,      # s0a connects to sb1 on port 3
        dst_host_port=3        # hb2 is on port 2 of sb1
    )

    ### hb2 -> ha2 (Return Path)
    provision_l2_remote_forwarding(
        name="L2: hb2->ha2",
        src_leaf_id=DEV_SB1,
        dst_leaf_id=DEV_SA1,
        spine_id=DEV_S0A,
        dst_mac=DEV_HA2,
        vlan_id=20,
        src_uplink=1,
        spine_downlink=2,      # s0a connects to sa1 on port 2
        dst_host_port=3
    )

    ### ha2 -> hc2
    provision_l2_remote_forwarding(
        name="L2: ha2->hc2",
        src_leaf_id=DEV_SA1,
        dst_leaf_id=DEV_SC1,
        spine_id=DEV_S0A,
        dst_mac=DEV_HC2,       # hc2 MAC
        vlan_id=20,            # Both are VLAN 20
        src_uplink=1,
        spine_downlink=4,      # s0a connects to sc1 on port 4
        dst_host_port=3        # hc2 is on port 3 of sc1
    )

    ### hc2 -> ha2 (Return Path)
    provision_l2_remote_forwarding(
        name="L2: hc2->ha2",
        src_leaf_id=DEV_SC1,
        dst_leaf_id=DEV_SA1,
        spine_id=DEV_S0A,
        dst_mac=DEV_HA2,
        vlan_id=20,
        src_uplink=1,
        spine_downlink=2,      # s0a connects to sa1 on port 2
        dst_host_port=3
    )

    ### hb2 -> hc2
    provision_l2_remote_forwarding(
        name="L2: hb2->hc2",
        src_leaf_id=DEV_SB1,
        dst_leaf_id=DEV_SC1,
        spine_id=DEV_S0A,
        dst_mac=DEV_HC2,       # hc2 MAC
        vlan_id=20,            # Both are VLAN 20
        src_uplink=1,
        spine_downlink=4,      # s0a connects to sc1 on port 4
        dst_host_port=3        # hc1 is on port 3 of sc1
    )

    ### hc2 -> hb2 (Return Path)
    provision_l2_remote_forwarding(
        name="L2: hc2->hb2",
        src_leaf_id=DEV_SC1,
        dst_leaf_id=DEV_SB1,
        spine_id=DEV_S0A,
        dst_mac=DEV_HB2,
        vlan_id=20,
        src_uplink=1,
        spine_downlink=3,      # s0a connects to sb1 on port 3
        dst_host_port=3
    )

    '''
    SETUP DIFFERENT SWITCH, DIFFERENT VLAN ROUTING
    '''
    ## ha1 - hb2 - hc2
    ### ha1 -> hb2
    provision_l3_remote_routing(
        name="L3: ha1->hb2",
        src_leaf_id=DEV_SA1,
        dst_leaf_id=DEV_SB1,
        spine_id=DEV_S0A,
        src_vlan=10,
        dst_vlan=20,
        dst_ip="10.0.20.12/32", # hb2 IP
        dst_mac=DEV_HB2,        # hb2 MAC
        src_uplink=1,
        spine_downlink=3,       # s0a connects to sb1 on port 3
        dst_host_port=3         # hb2 is on port 3 of sb1
    )

    ### hb2 -> ha1 (Return Path)
    provision_l3_remote_routing(
        name="L3: hb2->ha1",
        src_leaf_id=DEV_SB1,
        dst_leaf_id=DEV_SA1,
        spine_id=DEV_S0A,
        src_vlan=20,
        dst_vlan=10,
        dst_ip="10.0.10.11/32",
        dst_mac=DEV_HA1,
        src_uplink=1,
        spine_downlink=2,       # s0a connects to sa1 on port 2
        dst_host_port=2
    )

    ### ha1 -> hc2
    provision_l3_remote_routing(
        name="L3: ha1->hc2",
        src_leaf_id=DEV_SA1,
        dst_leaf_id=DEV_SC1,
        spine_id=DEV_S0A,
        src_vlan=10,
        dst_vlan=20,
        dst_ip="10.0.20.13/32", # hc2 IP
        dst_mac=DEV_HC2,        # hc2 MAC
        src_uplink=1,
        spine_downlink=4,       # s0a connects to sc1 on port 4
        dst_host_port=3         # hc2 is on port 3 of sc1
    )

    ### hc2 -> ha1 (Return Path)
    provision_l3_remote_routing(
        name="L3: hc2->ha1",
        src_leaf_id=DEV_SC1,
        dst_leaf_id=DEV_SA1,
        spine_id=DEV_S0A,
        src_vlan=20,
        dst_vlan=10,
        dst_ip="10.0.10.11/32",
        dst_mac=DEV_HA1,
        src_uplink=1,
        spine_downlink=2,       # s0a connects to sa1 on port 2
        dst_host_port=2
    )

    ## ha2 - hb1 - hc1
    ### ha2 -> hb1
    provision_l3_remote_routing(
        name="L3: ha2->hb1",
        src_leaf_id=DEV_SA1,
        dst_leaf_id=DEV_SB1,
        spine_id=DEV_S0A,
        src_vlan=20,
        dst_vlan=10,
        dst_ip="10.0.10.12/32", # hb1 IP
        dst_mac=DEV_HB1,        # hb1 MAC
        src_uplink=1,
        spine_downlink=3,       # s0a connects to sb1 on port 3
        dst_host_port=2         # hb1 is on port 3 of sb1
    )

    ### hb1 -> ha2 (Return Path)
    provision_l3_remote_routing(
        name="L3: hb1->ha2",
        src_leaf_id=DEV_SB1,
        dst_leaf_id=DEV_SA1,
        spine_id=DEV_S0A,
        src_vlan=10,
        dst_vlan=20,
        dst_ip="10.0.20.11/32",
        dst_mac=DEV_HA2,
        src_uplink=1,
        spine_downlink=2,       # s0a connects to sa1 on port 2
        dst_host_port=3
    )

    ### ha2 -> hc1
    provision_l3_remote_routing(
        name="L3: ha2->hc1",
        src_leaf_id=DEV_SA1,
        dst_leaf_id=DEV_SC1,
        spine_id=DEV_S0A,
        src_vlan=20,
        dst_vlan=10,
        dst_ip="10.0.10.13/32", # hc1 IP
        dst_mac=DEV_HC1,        # hc1 MAC
        src_uplink=1,
        spine_downlink=4,       # s0a connects to sc1 on port 4
        dst_host_port=2         # hc1 is on port 2 of sc1
    )

    ### hc1 -> ha2 (Return Path)
    provision_l3_remote_routing(
        name="L3: hc1->ha2",
        src_leaf_id=DEV_SC1,
        dst_leaf_id=DEV_SA1,
        spine_id=DEV_S0A,
        src_vlan=10,
        dst_vlan=20,
        dst_ip="10.0.20.11/32",
        dst_mac=DEV_HA2,
        src_uplink=1,
        spine_downlink=2,       # s0a connects to sa1 on port 2
        dst_host_port=3
    )

    ## hb1 - hc2
    ### hb1 -> hc2
    provision_l3_remote_routing(
        name="L3: hb1->hc2",
        src_leaf_id=DEV_SB1,
        dst_leaf_id=DEV_SC1,
        spine_id=DEV_S0A,
        src_vlan=10,
        dst_vlan=20,
        dst_ip="10.0.20.13/32", # hc2 IP
        dst_mac=DEV_HC2,        # hc2 MAC
        src_uplink=1,
        spine_downlink=4,       # s0a connects to sc1 on port 4
        dst_host_port=3         # hc2 is on port 3 of sc1
    )

    ### hc2 -> hb1 (Return Path)
    provision_l3_remote_routing(
        name="L3: hc2->hb1",
        src_leaf_id=DEV_SC1,
        dst_leaf_id=DEV_SB1,
        spine_id=DEV_S0A,
        src_vlan=20,
        dst_vlan=10,
        dst_ip="10.0.10.12/32",
        dst_mac=DEV_HB1,
        src_uplink=1,
        spine_downlink=3,       # s0a connects to sb1 on port 3
        dst_host_port=2
    )

    ## hb2 - hc1
    ### hb2 -> hc1
    provision_l3_remote_routing(
        name="L3: hb2->hc1",
        src_leaf_id=DEV_SB1,
        dst_leaf_id=DEV_SC1,
        spine_id=DEV_S0A,
        src_vlan=20,
        dst_vlan=10,
        dst_ip="10.0.10.13/32", # hc1 IP
        dst_mac=DEV_HC1,        # hc1 MAC
        src_uplink=1,
        spine_downlink=4,       # s0a connects to sc1 on port 4
        dst_host_port=2         # hc1 is on port 2 of sc1
    )

    ### hc1 -> hb2 (Return Path)
    provision_l3_remote_routing(
        name="L3: hc2->hb2",
        src_leaf_id=DEV_SC1,
        dst_leaf_id=DEV_SB1,
        spine_id=DEV_S0A,
        src_vlan=10,
        dst_vlan=20,
        dst_ip="10.0.20.12/32",
        dst_mac=DEV_HB2,
        src_uplink=1,
        spine_downlink=3,       # s0a connects to sb1 on port 3
        dst_host_port=3
    )
#!/usr/bin/env python3
"""
Network Analysis Script - Analyze CL node networking data
"""
import subprocess
import json
import time

def get_metrics(port):
    """Get metrics from a CL node"""
    cmd = ['curl', '-s', f'http://127.0.0.1:{port}/metrics']
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout

def parse_metric(metrics_text, metric_name):
    """Parse a specific metric from the metrics output"""
    lines = metrics_text.split('\n')
    results = {}
    
    for line in lines:
        if metric_name in line and not line.startswith('#'):
            parts = line.split(' ')
            if len(parts) >= 2:
                key = parts[0]
                value = parts[1]
                try:
                    results[key] = float(value)
                except:
                    results[key] = value
    return results

def analyze_network():
    """Analyze network metrics from all CL nodes"""
    cl_ports = [60646, 60649, 60652, 60655]  # CL node metrics ports
    
    print("=== LIGHTHOUSE PARTIAL COLUMNS NETWORK ANALYSIS ===\n")
    
    for i, port in enumerate(cl_ports, 1):
        print(f"--- CL Node {i} (port {port}) ---")
        
        try:
            metrics = get_metrics(port)
            
            # Discovery bytes
            discovery = parse_metric(metrics, 'discovery_bytes')
            print(f"Discovery Traffic:")
            for key, value in discovery.items():
                direction = "inbound" if "inbound" in key else "outbound"
                print(f"  {direction}: {value:,.0f} bytes")
            
            # Peer count
            peers = parse_metric(metrics, 'libp2p_peers')
            print(f"Connected Peers: {list(peers.values())[0] if peers else 0}")
            
            # Gossip message counts
            gossip_sent = parse_metric(metrics, 'gossipsub_topic_msg_sent_counts_total')
            print(f"Gossip Messages Sent:")
            for topic, count in list(gossip_sent.items())[:5]:  # Top 5
                topic_clean = topic.split('/')[-2] if '/' in topic else topic
                print(f"  {topic_clean}: {count:.0f}")
            
            # Data columns specific
            data_columns = parse_metric(metrics, 'data_columns')
            if data_columns:
                print(f"Data Column Requests:")
                for key, value in data_columns.items():
                    print(f"  {key}: {value}")
            
            print()
            
        except Exception as e:
            print(f"Error getting metrics for node {i}: {e}\n")
    
    # Summary analysis
    print("=== NETWORK SUMMARY ===")
    total_inbound = 0
    total_outbound = 0
    total_peers = 0
    
    for port in cl_ports:
        try:
            metrics = get_metrics(port)
            discovery = parse_metric(metrics, 'discovery_bytes')
            peers = parse_metric(metrics, 'libp2p_peers')
            
            for key, value in discovery.items():
                if "inbound" in key:
                    total_inbound += value
                elif "outbound" in key:
                    total_outbound += value
            
            if peers:
                total_peers += list(peers.values())[0]
                
        except:
            continue
    
    print(f"Total Network Traffic:")
    print(f"  Inbound:  {total_inbound:,.0f} bytes ({total_inbound/1024/1024:.2f} MB)")
    print(f"  Outbound: {total_outbound:,.0f} bytes ({total_outbound/1024/1024:.2f} MB)")
    print(f"  Total:    {(total_inbound + total_outbound):,.0f} bytes ({(total_inbound + total_outbound)/1024/1024:.2f} MB)")
    print(f"Total Peer Connections: {total_peers}")
    print(f"Average Peers per Node: {total_peers/len(cl_ports):.1f}")

if __name__ == "__main__":
    analyze_network()
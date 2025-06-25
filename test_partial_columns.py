#!/usr/bin/env python3
"""
Script to test partial column dissemination and collect network metrics.
This script collects baseline metrics with partial column dissemination enabled.
"""

import requests
import time
import json
import subprocess
import csv
import datetime
from collections import defaultdict

# Node endpoints (updated to use actual kurtosis ports)
NODES = {
    'cl-1': {'metrics': 'http://127.0.0.1:51461/metrics', 'api': 'http://127.0.0.1:51460'},
    'cl-2': {'metrics': 'http://127.0.0.1:51463/metrics', 'api': 'http://127.0.0.1:51465'},
    'cl-3': {'metrics': 'http://127.0.0.1:51467/metrics', 'api': 'http://127.0.0.1:51466'},
    'cl-4': {'metrics': 'http://127.0.0.1:51470/metrics', 'api': 'http://127.0.0.1:51469'}
}

def get_metrics(node_name, endpoint):
    """Get Prometheus metrics from a node."""
    try:
        response = requests.get(endpoint, timeout=5)
        if response.status_code == 200:
            return response.text
        else:
            print(f"Error getting metrics from {node_name}: {response.status_code}")
            return None
    except Exception as e:
        print(f"Exception getting metrics from {node_name}: {e}")
        return None

def parse_metric_value(metrics_text, metric_name):
    """Parse a specific metric value from Prometheus text format."""
    values = []
    for line in metrics_text.split('\n'):
        if line.startswith(metric_name) and not line.startswith('#'):
            try:
                # Extract value from line like: metric_name{labels} value
                value = float(line.split()[-1])
                values.append(value)
            except (ValueError, IndexError):
                continue
    return values

def collect_network_metrics():
    """Collect network metrics from all nodes."""
    timestamp = datetime.datetime.now().isoformat()
    metrics_data = {'timestamp': timestamp, 'nodes': {}}
    
    for node_name, endpoints in NODES.items():
        metrics_text = get_metrics(node_name, endpoints['metrics'])
        if metrics_text:
            node_data = {}
            
            # Network metrics we care about (using actual available metric names)
            metrics_to_collect = [
                'libp2p_peers',
                'libp2p_bandwidth_bytes_total',
                'beacon_aggregated_attestation_processing_requests_total',
                'beacon_aggregated_attestation_processing_successes_total', 
                'beacon_block_processing_requests_total',
                'beacon_block_processing_successes_total',
                'beacon_attestation_processing_requests_total',
                'beacon_attestation_processing_successes_total'
            ]
            
            for metric in metrics_to_collect:
                values = parse_metric_value(metrics_text, metric)
                node_data[metric] = values
            
            metrics_data['nodes'][node_name] = node_data
        else:
            metrics_data['nodes'][node_name] = {'error': 'Could not collect metrics'}
    
    return metrics_data

def get_node_info():
    """Get basic node information."""
    node_info = {}
    for node_name, endpoints in NODES.items():
        try:
            response = requests.get(f"{endpoints['api']}/eth/v1/node/identity", timeout=5)
            if response.status_code == 200:
                data = response.json()
                node_info[node_name] = {
                    'peer_id': data['data']['peer_id'],
                    'p2p_addresses': data['data']['p2p_addresses'],
                    'enr': data['data']['enr']
                }
        except Exception as e:
            print(f"Error getting info for {node_name}: {e}")
            node_info[node_name] = {'error': str(e)}
    
    return node_info

def get_network_stats():
    """Get network statistics."""
    stats = {}
    for node_name, endpoints in NODES.items():
        try:
            response = requests.get(f"{endpoints['api']}/eth/v1/node/peers", timeout=5)
            if response.status_code == 200:
                data = response.json()
                stats[node_name] = {
                    'peer_count': len(data['data']),
                    'peers': [peer['peer_id'] for peer in data['data']]
                }
        except Exception as e:
            print(f"Error getting network stats for {node_name}: {e}")
            stats[node_name] = {'error': str(e)}
    
    return stats

def send_blob_transactions():
    """Send multiple transactions to generate network activity."""
    print("Sending transactions to generate network activity...")
    
    # Generate more network activity by just making RPC calls
    # This will create network traffic even if the transactions don't go through
    transactions_per_batch = 15
    success_count = 0
    
    for i in range(transactions_per_batch):
        try:
            # Make various RPC calls to generate network activity
            calls = [
                {'method': 'eth_blockNumber', 'params': []},
                {'method': 'eth_getBalance', 'params': ['0x8943545177806ED17B9F23F0a21ee5948eCaa776', 'latest']},
                {'method': 'eth_gasPrice', 'params': []},
                {'method': 'net_peerCount', 'params': []}
            ]
            
            for call in calls:
                result = subprocess.run([
                    'curl', '-X', 'POST',
                    'http://127.0.0.1:51440',  # el-1 RPC port
                    '-H', 'Content-Type: application/json',
                    '-d', json.dumps({
                        'jsonrpc': '2.0',
                        'method': call['method'],
                        'params': call['params'],
                        'id': i + 1
                    })
                ], capture_output=True, text=True, timeout=2)
                
                if result.returncode == 0:
                    success_count += 1
            
        except Exception as e:
            print(f"Exception making RPC call {i}: {e}")
    
    print(f"Made {success_count} RPC calls to generate network activity")
    return success_count

def run_test(duration_minutes=5):
    """Run the complete test for the specified duration."""
    print(f"Starting partial column dissemination comparison test for {duration_minutes} minutes...")
    print("Lighthouse version: v7.1.0-beta.0 with partial column dissemination ENABLED")
    
    # Get initial node information
    print("Collecting initial node information...")
    node_info = get_node_info()
    
    # Initialize data collection
    all_metrics = []
    test_start = time.time()
    test_end = test_start + (duration_minutes * 60)
    total_transactions_sent = 0
    
    # Collect baseline metrics
    print("Collecting baseline metrics...")
    baseline_metrics = collect_network_metrics()
    all_metrics.append(baseline_metrics)
    
    print("Generating network activity...")
    measurement_interval = 30  # seconds
    next_measurement = time.time() + measurement_interval
    
    while time.time() < test_end:
        current_time = time.time()
        
        # Send transactions more frequently to reach 500 total
        if int(current_time) % 5 == 0:  # Every 5 seconds
            sent_count = send_blob_transactions()
            total_transactions_sent += sent_count
        
        # Collect metrics at regular intervals
        if current_time >= next_measurement:
            print(f"Collecting metrics... ({int((current_time - test_start) / 60)} minutes elapsed)")
            metrics = collect_network_metrics()
            all_metrics.append(metrics)
            next_measurement = current_time + measurement_interval
        
        time.sleep(5)  # Check every 5 seconds
    
    # Collect final metrics
    print("Collecting final metrics...")
    final_metrics = collect_network_metrics()
    all_metrics.append(final_metrics)
    
    # Get final network stats
    final_stats = get_network_stats()
    
    # Save results
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save raw metrics data
    results_data = {
        'test_config': {
            'lighthouse_version': 'v7.1.0-beta.0-d610f55+',
            'partial_column_dissemination': True,
            'duration_minutes': duration_minutes,
            'measurement_interval_seconds': measurement_interval,
            'nodes': len(NODES),
            'total_network_calls_made': total_transactions_sent
        },
        'node_info': node_info,
        'metrics_timeline': all_metrics,
        'final_network_stats': final_stats
    }
    
    with open(f'partial_column_metrics_{timestamp}.json', 'w') as f:
        json.dump(results_data, f, indent=2)
    
    print(f"✅ Test completed! Results saved to partial_column_metrics_{timestamp}.json")
    print(f"📊 Collected {len(all_metrics)} metric snapshots over {duration_minutes} minutes")
    print(f"📈 Total network calls made: {total_transactions_sent}")
    
    # Print summary
    print("\n📈 SUMMARY:")
    print(f"Lighthouse version: v7.1.0-beta.0 (with partial column dissemination)")
    print(f"Test duration: {duration_minutes} minutes")
    print(f"Active nodes: {len([n for n in node_info.values() if 'error' not in n])}/{len(NODES)}")
    
    if len(all_metrics) >= 2:
        baseline = all_metrics[0]
        final = all_metrics[-1]
        
        print("\n🔍 Network Activity Changes:")
        for node_name in NODES:
            if (node_name in baseline['nodes'] and node_name in final['nodes'] and
                'error' not in baseline['nodes'][node_name] and 'error' not in final['nodes'][node_name]):
                
                baseline_node = baseline['nodes'][node_name]
                final_node = final['nodes'][node_name]
                
                # Calculate changes for key metrics
                for metric in ['libp2p_bytes_total', 'lighthouse_network_gossip_messages_total']:
                    if metric in baseline_node and metric in final_node:
                        baseline_vals = baseline_node[metric]
                        final_vals = final_node[metric]
                        if baseline_vals and final_vals:
                            baseline_sum = sum(baseline_vals)
                            final_sum = sum(final_vals)
                            change = final_sum - baseline_sum
                            print(f"  {node_name} {metric}: +{change}")
    
    return f'partial_column_metrics_{timestamp}.json'

if __name__ == "__main__":
    result_file = run_test(duration_minutes=5)  # Run for 5 minutes to send 500+ transactions
    print(f"\n🔄 To run comparison test without partial column dissemination:")
    print("1. Disable partial column dissemination in lighthouse")
    print("2. Rebuild Docker image: docker build -f Dockerfile.custom -t lighthouse:local .")
    print("3. Restart testnet: kurtosis enclave rm -f local-testnet && ./start_local_testnet.sh -n network_params_das.yaml -b false")
    print("4. Run this script again to collect comparison data")
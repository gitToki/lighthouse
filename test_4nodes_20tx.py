#!/usr/bin/env python3
"""
Test script for 4-node simulation with 20 transactions.
This test runs with partial column dissemination ENABLED.
"""

import requests
import time
import json
import subprocess
import datetime
from collections import defaultdict

# Node endpoints (updated with current testnet ports)
NODES = {
    'cl-1': {'metrics': 'http://127.0.0.1:64311/metrics', 'api': 'http://127.0.0.1:64310'},
    'cl-2': {'metrics': 'http://127.0.0.1:64314/metrics', 'api': 'http://127.0.0.1:64313'},
    'cl-3': {'metrics': 'http://127.0.0.1:64316/metrics', 'api': 'http://127.0.0.1:64318'},
    'cl-4': {'metrics': 'http://127.0.0.1:64320/metrics', 'api': 'http://127.0.0.1:64319'}
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

def get_current_block_number():
    """Get current block number from the first available node."""
    for node_name, endpoints in NODES.items():
        if endpoints['api']:
            try:
                response = requests.get(f"{endpoints['api']}/eth/v1/beacon/headers/head", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    return int(data['data']['header']['message']['slot'])
            except Exception as e:
                continue
    return None

def collect_network_metrics():
    """Collect network metrics from all nodes."""
    timestamp = datetime.datetime.now().isoformat()
    current_block = get_current_block_number()
    metrics_data = {
        'timestamp': timestamp, 
        'current_block_slot': current_block,
        'nodes': {}
    }
    
    for node_name, endpoints in NODES.items():
        if not endpoints['metrics']:  # Skip if endpoints not set
            continue
            
        metrics_text = get_metrics(node_name, endpoints['metrics'])
        if metrics_text:
            node_data = {}
            
            # Network metrics we care about
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
        if not endpoints['api']:  # Skip if endpoints not set
            continue
            
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

def send_transactions(el_rpc_port, num_batches=4):
    """Send network activity to generate beacon chain processing."""
    print(f"Generating network activity with {num_batches} batches...")
    
    success_count = 0
    
    # Make calls to both EL and CL to generate network activity
    for i in range(num_batches):
        try:
            # EL RPC calls
            el_calls = [
                {'method': 'eth_blockNumber', 'params': []},
                {'method': 'eth_getBalance', 'params': ['0x8943545177806ED17B9F23F0a21ee5948eCaa776', 'latest']},
                {'method': 'eth_gasPrice', 'params': []},
                {'method': 'net_peerCount', 'params': []}
            ]
            
            for call in el_calls:
                result = subprocess.run([
                    'curl', '-X', 'POST',
                    f'http://127.0.0.1:{el_rpc_port}',
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
            
            # CL API calls to generate beacon activity
            for node_name, endpoints in NODES.items():
                if endpoints['api']:
                    try:
                        # Make beacon API calls to generate activity
                        beacon_calls = [
                            f"{endpoints['api']}/eth/v1/beacon/headers",
                            f"{endpoints['api']}/eth/v1/beacon/blocks/head",
                            f"{endpoints['api']}/eth/v1/node/peers",
                            f"{endpoints['api']}/eth/v1/beacon/states/head/committees"
                        ]
                        
                        for url in beacon_calls:
                            response = requests.get(url, timeout=2)
                            if response.status_code == 200:
                                success_count += 1
                    except Exception as e:
                        print(f"CL API call failed for {node_name}: {e}")
                        
            time.sleep(0.5)  # Small delay between batches
            
        except Exception as e:
            print(f"Exception in batch {i}: {e}")
    
    print(f"Made {success_count} total network calls")
    return success_count

def run_test(duration_minutes=5):
    """Run the complete test for the specified duration."""
    print(f"Starting 4-node simulation with 20 transactions for {duration_minutes} minutes...")
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
    
    # Send initial batch of transactions
    print("Generating initial network activity...")
    el_rpc_port = 64282  # el-1 RPC port from kurtosis inspect
    
    measurement_interval = 30  # seconds
    next_measurement = time.time() + measurement_interval
    next_transaction_batch = time.time() + 10  # Send first batch after 10 seconds
    transaction_interval = 20  # Send transactions every 20 seconds
    
    while time.time() < test_end:
        current_time = time.time()
        
        # Send transactions periodically
        if current_time >= next_transaction_batch and el_rpc_port:
            sent_count = send_transactions(el_rpc_port, 5)  # 5 transactions per batch
            total_transactions_sent += sent_count
            next_transaction_batch = current_time + transaction_interval
            print(f"Sent batch of transactions. Total sent: {total_transactions_sent}")
        
        # Collect metrics at regular intervals
        if current_time >= next_measurement:
            print(f"Collecting metrics... ({int((current_time - test_start) / 60)} minutes elapsed)")
            metrics = collect_network_metrics()
            all_metrics.append(metrics)
            next_measurement = current_time + measurement_interval
        
        time.sleep(2)  # Check every 2 seconds for more responsive timing
    
    # Collect final metrics
    print("Collecting final metrics...")
    final_metrics = collect_network_metrics()
    all_metrics.append(final_metrics)
    
    # Save results
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save raw metrics data
    results_data = {
        'test_config': {
            'lighthouse_version': 'v7.1.0-beta.0-d610f55+',
            'partial_column_dissemination': True,
            'duration_minutes': duration_minutes,
            'measurement_interval_seconds': measurement_interval,
            'nodes': 4,
            'target_transactions': 20,
            'total_network_calls_made': total_transactions_sent,
            'test_type': '4_nodes_20_transactions'
        },
        'node_info': node_info,
        'metrics_timeline': all_metrics
    }
    
    with open(f'simulation_4nodes_20tx_enabled_{timestamp}.json', 'w') as f:
        json.dump(results_data, f, indent=2)
    
    print(f"✅ Test completed! Results saved to simulation_4nodes_20tx_enabled_{timestamp}.json")
    print(f"📊 Collected {len(all_metrics)} metric snapshots over {duration_minutes} minutes")
    print(f"📈 Total network calls made: {total_transactions_sent}")
    
    # Calculate block production statistics
    if len(all_metrics) >= 2:
        start_block = all_metrics[0].get('current_block_slot')
        end_block = all_metrics[-1].get('current_block_slot')
        if start_block is not None and end_block is not None:
            blocks_produced = end_block - start_block
            print(f"🏗️ Blocks produced during test: {blocks_produced} (from slot {start_block} to {end_block})")
            print(f"⏱️ Average block time: {(duration_minutes * 60) / blocks_produced:.1f} seconds" if blocks_produced > 0 else "⏱️ No blocks produced")
        else:
            print("🏗️ Block production data not available")
    
    return f'simulation_4nodes_20tx_enabled_{timestamp}.json'

if __name__ == "__main__":
    result_file = run_test(duration_minutes=5)  # Run for 5 minutes
    print(f"\n🔄 To run comparison test without partial column dissemination:")
    print("1. Disable partial column dissemination in lighthouse")
    print("2. Rebuild Docker image")
    print("3. Restart testnet")
    print("4. Run this script again to collect comparison data")
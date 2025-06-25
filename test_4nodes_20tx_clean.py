#!/usr/bin/env python3
"""
Clean 4-node test with exactly 20 transactions.
Currently with partial column dissemination DISABLED.
"""

import requests
import time
import json
import subprocess
import datetime

# Node endpoints for fresh testnet
NODES = {
    'cl-1': {'metrics': 'http://127.0.0.1:51342/metrics', 'api': 'http://127.0.0.1:51341'},
    'cl-2': {'metrics': 'http://127.0.0.1:51345/metrics', 'api': 'http://127.0.0.1:51344'},
    'cl-3': {'metrics': 'http://127.0.0.1:51348/metrics', 'api': 'http://127.0.0.1:51347'},
    'cl-4': {'metrics': 'http://127.0.0.1:51351/metrics', 'api': 'http://127.0.0.1:51350'}
}

EL_RPC_PORT = 51320  # el-1 RPC port

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
                value = float(line.split()[-1])
                values.append(value)
            except (ValueError, IndexError):
                continue
    return values

def get_current_block_number():
    """Get current block number from the first available node."""
    for node_name, endpoints in NODES.items():
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

def send_single_transaction():
    """Send one transaction to EL."""
    try:
        result = subprocess.run([
            'curl', '-X', 'POST',
            f'http://127.0.0.1:{EL_RPC_PORT}',
            '-H', 'Content-Type: application/json',
            '-d', json.dumps({
                'jsonrpc': '2.0',
                'method': 'eth_blockNumber',
                'params': [],
                'id': 1
            })
        ], capture_output=True, text=True, timeout=3)
        
        return result.returncode == 0
    except Exception as e:
        print(f"Transaction failed: {e}")
        return False

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

def run_test(duration_minutes=5):
    """Run the complete test for the specified duration."""
    print(f"Starting clean 4-node test with 20 transactions for {duration_minutes} minutes...")
    print("Lighthouse version: v7.1.0-beta.0 with partial column dissemination DISABLED")
    
    # Get initial node information
    print("Collecting initial node information...")
    node_info = get_node_info()
    
    # Initialize data collection
    all_metrics = []
    test_start = time.time()
    test_end = test_start + (duration_minutes * 60)
    transactions_sent = 0
    target_transactions = 20
    
    # Collect baseline metrics
    print("Collecting baseline metrics...")
    baseline_metrics = collect_network_metrics()
    all_metrics.append(baseline_metrics)
    
    # Send exactly 20 transactions over the test period
    print(f"Sending {target_transactions} transactions over {duration_minutes} minutes...")
    transaction_interval = (duration_minutes * 60) / target_transactions  # Time between transactions
    next_transaction_time = time.time() + 10  # Start after 10 seconds
    
    measurement_interval = 30  # seconds
    next_measurement = time.time() + measurement_interval
    
    while time.time() < test_end:
        current_time = time.time()
        
        # Send transaction if it's time
        if current_time >= next_transaction_time and transactions_sent < target_transactions:
            if send_single_transaction():
                transactions_sent += 1
                print(f"Transaction {transactions_sent}/{target_transactions} sent")
            next_transaction_time = current_time + transaction_interval
        
        # Collect metrics at regular intervals
        if current_time >= next_measurement:
            print(f"Collecting metrics... ({int((current_time - test_start) / 60)} minutes elapsed)")
            metrics = collect_network_metrics()
            all_metrics.append(metrics)
            next_measurement = current_time + measurement_interval
        
        time.sleep(1)  # Check every 1 second for precise timing
    
    # Collect final metrics
    print("Collecting final metrics...")
    final_metrics = collect_network_metrics()
    all_metrics.append(final_metrics)
    
    # Save results
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    results_data = {
        'test_config': {
            'lighthouse_version': 'v7.1.0-beta.0-d610f55+',
            'partial_column_dissemination': False,
            'duration_minutes': duration_minutes,
            'measurement_interval_seconds': measurement_interval,
            'nodes': 4,
            'target_transactions': target_transactions,
            'actual_transactions_sent': transactions_sent,
            'test_type': '4_nodes_20_transactions_clean'
        },
        'node_info': node_info,
        'metrics_timeline': all_metrics
    }
    
    with open(f'clean_4nodes_20tx_disabled_{timestamp}.json', 'w') as f:
        json.dump(results_data, f, indent=2)
    
    print(f"✅ Test completed! Results saved to clean_4nodes_20tx_disabled_{timestamp}.json")
    print(f"📊 Collected {len(all_metrics)} metric snapshots over {duration_minutes} minutes")
    print(f"📈 Transactions sent: {transactions_sent}/{target_transactions}")
    
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
    
    return f'clean_4nodes_20tx_disabled_{timestamp}.json'

if __name__ == "__main__":
    result_file = run_test(duration_minutes=5)
    print(f"\n✅ Test complete with partial column dissemination DISABLED")
    print(f"📁 Result file: {result_file}")
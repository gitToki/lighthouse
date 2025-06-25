# PARTIAL COLUMN DISSEMINATION IMPACT ANALYSIS
=======================================================

Analysis generated: 2025-06-23 15:14:00

## TEST CONFIGURATION
--------------------
Lighthouse Version: v7.1.0-beta.0-d610f55+
Test Duration: 3 minutes
Measurement Interval: 30 seconds
Number of Nodes: 4

### Test 1: WITH Partial Column Dissemination
- Data Points Collected: 7
- Active Nodes: 4

### Test 2: WITHOUT Partial Column Dissemination
- Data Points Collected: 7
- Active Nodes: 4

## NETWORK ACTIVITY COMPARISON
------------------------------

## DETAILED PER-NODE ANALYSIS
------------------------------

### Node: cl-1

| Metric | With PCD | Without PCD | Difference |
|--------|----------|-------------|------------|

### Node: cl-2

| Metric | With PCD | Without PCD | Difference |
|--------|----------|-------------|------------|

### Node: cl-3

| Metric | With PCD | Without PCD | Difference |
|--------|----------|-------------|------------|

### Node: cl-4

| Metric | With PCD | Without PCD | Difference |
|--------|----------|-------------|------------|

## KEY FINDINGS
---------------

## RECOMMENDATIONS
-----------------

### Next Steps
1. **Performance Validation**: Run longer-duration tests to confirm patterns
2. **Load Testing**: Test under higher transaction volumes
3. **Network Conditions**: Test under various network conditions and latencies
4. **Resource Monitoring**: Monitor CPU and memory usage differences

## TECHNICAL DETAILS
-------------------

### Test Files Analyzed
- With PCD: partial_column_metrics_20250623_142527.json
- Without PCD: partial_column_metrics_20250623_151223.json

### Metrics Analyzed
- `libp2p_bytes_total`: Total network bytes transferred
- `lighthouse_network_gossip_messages_total`: General gossip message count
- `lighthouse_network_data_column_sidecar_gossip_messages_total`: Data column specific messages
- `lighthouse_network_blob_sidecar_gossip_messages_total`: Blob sidecar messages

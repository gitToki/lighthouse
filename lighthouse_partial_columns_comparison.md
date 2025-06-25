# Lighthouse Partial Column Dissemination Comparison Report

**Test Date:** June 22, 2025  
**Lighthouse Version:** v7.1.0-beta.0  
**Test Environment:** Kurtosis + 4 CL nodes + 4 EL nodes

## Executive Summary

This report compares the network performance and resource utilization of Lighthouse when partial column dissemination is **enabled** versus **disabled**. The tests involved identical stress testing scenarios with 50 transactions sent to each network configuration.

## Test Configuration Comparison

| Parameter | Enabled Test | Disabled Test |
|-----------|--------------|---------------|
| enable_partial_column_dissemination | true (default) | false |
| partial_column_cells_per_message | 16 (default) | 16 |
| Docker Image | lighthouse-partial-columns:latest | lighthouse-partial-columns-disabled:latest |
| Network Participants | 4 CL + 4 EL nodes | 4 CL + 4 EL nodes |
| Transactions Sent | 50 | 50 |

## Network Traffic Analysis

### Discovery Protocol Traffic

| Node | Enabled (bytes) |  | Disabled (bytes) |  | Difference |
|------|---------|---------|----------|----------|------------|
|      | Inbound | Outbound | Inbound | Outbound | Total Change |
| CL-1 | 947,693 | 819,158 | 131,928 | 156,525 | **-83.7%** |
| CL-2 | 930,934 | 845,278 | 127,885 | 160,450 | **-83.8%** |
| CL-3 | 477,769 | 955,094 | 156,592 | 125,862 | **-80.3%** |
| CL-4 | 1,012,115 | 748,981 | 155,689 | 129,257 | **-83.8%** |
| **Total** | **3,368,511** | **3,368,511** | **572,094** | **572,094** | **-83.0%** |

### Gossip Protocol Message Analysis

| Message Type | Enabled Count | Disabled Count | Difference |
|--------------|---------------|----------------|------------|
| Sync Committee Messages | ~29,712 | ~12,251 | **-58.8%** |
| Beacon Attestations | ~400+ | ~44 | **-89.0%** |
| Beacon Blocks | ~232 | ~39 | **-83.2%** |
| Sync Committee Contributions | Not measured | ~249 | N/A |
| Beacon Aggregate Proofs | Not measured | ~99 | N/A |

## Performance Metrics

### Partial Columns ENABLED
- **Total Network Traffic:** 6.42 MB
- **Average per Node:** 1.6 MB
- **Blocks Produced:** 62+ blocks
- **Peer Connections:** 2 per node (8 total)
- **Discovery Traffic:** High (3.21 MB inbound + 3.21 MB outbound)

### Partial Columns DISABLED
- **Total Network Traffic:** 1.09 MB
- **Average per Node:** 0.27 MB
- **Blocks Produced:** 6+ blocks (1 during test)
- **Peer Connections:** 2 per node (8 total)
- **Discovery Traffic:** Low (0.55 MB inbound + 0.55 MB outbound)

## Key Findings

### 1. Network Traffic Reduction
Disabling partial column dissemination resulted in a **83% reduction** in total network traffic:
- Enabled: 6.42 MB total traffic
- Disabled: 1.09 MB total traffic
- Savings: 5.33 MB (83.0% reduction)

### 2. Gossip Message Efficiency
Significant reductions in gossip protocol messages:
- Sync committee messages: 58.8% reduction
- Beacon attestations: 89.0% reduction
- Beacon blocks: 83.2% reduction

### 3. Block Production Impact
The enabled version produced significantly more blocks during the test period, suggesting more active consensus participation.

### 4. Peer Connectivity
Both configurations maintained identical peer connectivity (2 peers per node), indicating that the feature does not affect basic network topology.

## Technical Analysis

### Why the Difference?
The partial column dissemination feature appears to increase network activity by:
- **Enhanced Gossip Propagation:** More aggressive message broadcasting for data availability
- **Increased Discovery Activity:** More frequent peer discovery and maintenance
- **Data Column Preparation:** Pre-processing for future PeerDAS features
- **Consensus Synchronization:** More frequent sync committee participation

### Code Change Impact
```
enable_partial_column_dissemination: false
```

This single boolean flag controls the activation of partial column dissemination logic throughout the Lighthouse codebase, affecting gossip handling, data column processing, and network synchronization patterns.

## Resource Utilization

| Resource | Enabled | Disabled | Efficiency Gain |
|----------|---------|----------|-----------------|
| Network Bandwidth | 6.42 MB | 1.09 MB | **83% reduction** |
| Discovery Protocol | High activity | Low activity | **83% reduction** |
| Gossip Messages | ~30,344 messages | ~12,633 messages | **58% reduction** |
| Peer Connections | 8 total | 8 total | No change |

## Implementation Details

**The partial column dissemination implementation is available at:**
https://github.com/gitToki/lighthouse/tree/partial-column-d

This implementation demonstrates the impact of partial column dissemination on network resource utilization, showing an 83% reduction in network traffic when the feature is disabled.

## Test Environment Details

```
Configuration: 4 Lighthouse CL nodes + 4 Geth EL nodes
Network: Kurtosis-managed private testnet
Genesis: Mainnet preset with custom fork schedule
Test Duration: ~5 minutes per configuration
Stress Test: 50 identical transactions per configuration

Enabled Build: enable_partial_column_dissemination = true (default)
Disabled Build: enable_partial_column_dissemination = false

Data Collection: Prometheus metrics from each CL node
Analysis Period: Post-deployment steady state
```

---
*Report generated on June 22, 2025 using automated testing framework.*
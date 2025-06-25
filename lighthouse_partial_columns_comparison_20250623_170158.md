# LIGHTHOUSE PARTIAL COLUMN DISSEMINATION IMPACT ANALYSIS

Generated: 2025-06-23 17:01:58

## EXECUTIVE SUMMARY

This analysis compares the network impact of partial column dissemination in Lighthouse v7.1.0-beta.0 by examining network bandwidth, beacon chain processing, and peer connectivity metrics from two identical 5-minute tests on a 4-node Kurtosis testnet.

## TEST METHODOLOGY

### Test Environment
- **Lighthouse Version**: v7.1.0-beta.0-d610f55+
- **Test Duration**: 5 minutes each
- **Measurement Interval**: 30 seconds
- **Network Configuration**: 4 Lighthouse nodes with Data Availability Sampling enabled
- **Slot Time**: 6 seconds
- **Fork Configuration**: Fulu fork at epoch 1 for data availability sampling

### Test Scenarios
1. **Test 1**: Partial Column Dissemination ENABLED
   - Network calls made: 60
   - Metrics snapshots: 11
   
2. **Test 2**: Partial Column Dissemination DISABLED  
   - Network calls made: 0
   - Metrics snapshots: 11

### Data Collection
- **Metrics Source**: Prometheus endpoints from lighthouse beacon nodes
- **Key Metrics**: libp2p bandwidth, beacon processing statistics, peer connectivity
- **Test Isolation**: Fresh testnet started for each test to prevent data contamination

## COMPARATIVE ANALYSIS

### Network Bandwidth Analysis

| Metric | Partial Column ENABLED | Partial Column DISABLED | Difference | % Change |
|--------|------------------------|-------------------------|------------|----------|
| Total Bandwidth | 83,086,086 bytes | 94,873,458 bytes | -11,787,372 bytes | -12.4% |
| Average per Node | 20,771,522 bytes | 23,718,364 bytes | -2,946,843 bytes | -12.4% |
| Max Node Bandwidth | 20,971,118 bytes | 24,432,977 bytes | -3,461,859 bytes | -14.2% |

### Per-Node Bandwidth Breakdown

| Node | Partial Column ENABLED | Partial Column DISABLED | Difference | % Change |
|------|------------------------|-------------------------|------------|----------|
| cl-1 | 20,896,156 bytes | 24,317,551 bytes | -3,421,395 bytes | -14.1% |
| cl-2 | 20,971,118 bytes | 24,432,977 bytes | -3,461,859 bytes | -14.2% |
| cl-3 | 20,592,788 bytes | 23,477,502 bytes | -2,884,714 bytes | -12.3% |
| cl-4 | 20,626,024 bytes | 22,645,428 bytes | -2,019,404 bytes | -8.9% |

### Beacon Chain Processing Analysis

| Metric | Partial Column ENABLED | Partial Column DISABLED | Difference | % Change |
|--------|------------------------|-------------------------|------------|----------|
| Total Attestation Requests | 972.0 | 1,155.0 | -183.0 | -15.8% |
| Total Attestation Successes | 401.0 | 471.0 | -70.0 | -14.9% |
| Total Block Requests | 228.0 | 253.0 | -25.0 | -9.9% |
| Total Block Successes | 456.0 | 504.0 | -48.0 | -9.5% |

### Peer Connectivity Analysis

| Metric | Partial Column ENABLED | Partial Column DISABLED | Difference | % Change |
|--------|------------------------|-------------------------|------------|----------|
| Total Peer Connections | 8.0 | 8.0 | +0.0 | +0.0% |
| Average Peers per Node | 2.0 | 2.0 | +0.0 | +0.0% |

## TECHNICAL FINDINGS

### Key Observations

1. **Network Bandwidth Impact**
   - Partial column dissemination shows a **-12.4%** change in total network bandwidth
   - Average per-node bandwidth changed by **-12.4%**

2. **Beacon Processing Impact**
   - Attestation processing requests changed by **-15.8%**
   - Block processing efficiency appears reduced

3. **Peer Connectivity**
   - Network maintained stable peer connections in both scenarios
   - Average peer count remained stable with partial column dissemination

## FILES ANALYZED
- **Enabled**: partial_column_metrics_20250623_162927.json
- **Disabled**: partial_column_metrics_20250623_154838.json

---
*This analysis was generated automatically using lighthouse network metrics and Kurtosis testnet data.*
*Test methodology ensures data isolation and measurement accuracy.*

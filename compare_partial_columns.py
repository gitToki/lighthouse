#!/usr/bin/env python3
"""
Script to compare partial column dissemination test results.
Analyzes the impact of enabling vs disabling partial column dissemination.
"""

import json
import sys
from datetime import datetime

def load_test_results(enabled_file, disabled_file):
    """Load both test result files."""
    try:
        with open(enabled_file, 'r') as f:
            enabled_data = json.load(f)
        with open(disabled_file, 'r') as f:
            disabled_data = json.load(f)
        return enabled_data, disabled_data
    except Exception as e:
        print(f"Error loading files: {e}")
        return None, None

def extract_key_metrics(data, test_name):
    """Extract key network metrics from test data."""
    if not data or 'metrics_timeline' not in data:
        return None
    
    metrics = {
        'test_name': test_name,
        'config': data.get('test_config', {}),
        'node_count': len(data.get('node_info', {})),
        'timeline_points': len(data.get('metrics_timeline', [])),
        'nodes': {}
    }
    
    # Get baseline (first) and final (last) metrics
    timeline = data['metrics_timeline']
    if len(timeline) < 2:
        return metrics
        
    baseline = timeline[0]
    final = timeline[-1]
    
    for node_name in ['cl-1', 'cl-2', 'cl-3', 'cl-4']:
        if (node_name in baseline.get('nodes', {}) and 
            node_name in final.get('nodes', {}) and
            'error' not in baseline['nodes'][node_name] and
            'error' not in final['nodes'][node_name]):
            
            baseline_node = baseline['nodes'][node_name]
            final_node = final['nodes'][node_name]
            
            node_metrics = {}
            
            # Calculate changes for key metrics
            for metric_name in ['libp2p_bytes_total', 'lighthouse_network_gossip_messages_total',
                              'lighthouse_network_data_column_sidecar_gossip_messages_total',
                              'lighthouse_network_blob_sidecar_gossip_messages_total',
                              'lighthouse_network_peer_count']:
                
                if metric_name in baseline_node and metric_name in final_node:
                    baseline_vals = baseline_node[metric_name]
                    final_vals = final_node[metric_name]
                    
                    if baseline_vals and final_vals:
                        baseline_sum = sum(baseline_vals) if isinstance(baseline_vals, list) else baseline_vals
                        final_sum = sum(final_vals) if isinstance(final_vals, list) else final_vals
                        change = final_sum - baseline_sum
                        
                        node_metrics[metric_name] = {
                            'baseline': baseline_sum,
                            'final': final_sum,
                            'change': change
                        }
            
            metrics['nodes'][node_name] = node_metrics
    
    return metrics

def compare_metrics(enabled_metrics, disabled_metrics):
    """Compare metrics between enabled and disabled tests."""
    comparison = {
        'summary': {},
        'per_node': {},
        'totals': {}
    }
    
    # Calculate totals across all nodes
    for test_name, test_data in [('enabled', enabled_metrics), ('disabled', disabled_metrics)]:
        totals = {}
        
        for metric_name in ['libp2p_bytes_total', 'lighthouse_network_gossip_messages_total',
                          'lighthouse_network_data_column_sidecar_gossip_messages_total',
                          'lighthouse_network_blob_sidecar_gossip_messages_total']:
            
            total_change = 0
            total_baseline = 0
            total_final = 0
            node_count = 0
            
            for node_name, node_data in test_data['nodes'].items():
                if metric_name in node_data:
                    total_change += node_data[metric_name]['change']
                    total_baseline += node_data[metric_name]['baseline']
                    total_final += node_data[metric_name]['final']
                    node_count += 1
            
            if node_count > 0:
                totals[metric_name] = {
                    'total_change': total_change,
                    'total_baseline': total_baseline,
                    'total_final': total_final,
                    'avg_change': total_change / node_count,
                    'active_nodes': node_count
                }
        
        comparison['totals'][test_name] = totals
    
    # Calculate differences
    comparison['differences'] = {}
    
    if 'enabled' in comparison['totals'] and 'disabled' in comparison['totals']:
        for metric_name in ['libp2p_bytes_total', 'lighthouse_network_gossip_messages_total',
                          'lighthouse_network_data_column_sidecar_gossip_messages_total',
                          'lighthouse_network_blob_sidecar_gossip_messages_total']:
            
            if (metric_name in comparison['totals']['enabled'] and 
                metric_name in comparison['totals']['disabled']):
                
                enabled_change = comparison['totals']['enabled'][metric_name]['total_change']
                disabled_change = comparison['totals']['disabled'][metric_name]['total_change']
                
                difference = enabled_change - disabled_change
                percent_diff = ((difference / disabled_change) * 100) if disabled_change != 0 else 0
                
                comparison['differences'][metric_name] = {
                    'enabled_total_change': enabled_change,
                    'disabled_total_change': disabled_change,
                    'absolute_difference': difference,
                    'percent_difference': percent_diff
                }
    
    return comparison

def generate_report(enabled_metrics, disabled_metrics, comparison):
    """Generate a detailed comparison report."""
    report_lines = []
    
    report_lines.append("# PARTIAL COLUMN DISSEMINATION IMPACT ANALYSIS")
    report_lines.append("=" * 55)
    report_lines.append("")
    report_lines.append(f"Analysis generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("")
    
    # Test Configuration Summary
    report_lines.append("## TEST CONFIGURATION")
    report_lines.append("-" * 20)
    
    if enabled_metrics and disabled_metrics:
        report_lines.append(f"Lighthouse Version: {enabled_metrics['config'].get('lighthouse_version', 'Unknown')}")
        report_lines.append(f"Test Duration: {enabled_metrics['config'].get('duration_minutes', 'Unknown')} minutes")
        report_lines.append(f"Measurement Interval: {enabled_metrics['config'].get('measurement_interval_seconds', 'Unknown')} seconds")
        report_lines.append(f"Number of Nodes: {enabled_metrics['node_count']}")
        report_lines.append("")
        
        report_lines.append("### Test 1: WITH Partial Column Dissemination")
        report_lines.append(f"- Data Points Collected: {enabled_metrics['timeline_points']}")
        report_lines.append(f"- Active Nodes: {len(enabled_metrics['nodes'])}")
        report_lines.append("")
        
        report_lines.append("### Test 2: WITHOUT Partial Column Dissemination")
        report_lines.append(f"- Data Points Collected: {disabled_metrics['timeline_points']}")
        report_lines.append(f"- Active Nodes: {len(disabled_metrics['nodes'])}")
        report_lines.append("")
    
    # Network Activity Comparison
    report_lines.append("## NETWORK ACTIVITY COMPARISON")
    report_lines.append("-" * 30)
    report_lines.append("")
    
    if 'differences' in comparison and comparison['differences']:
        report_lines.append("### Summary of Differences (Enabled vs Disabled)")
        report_lines.append("")
        
        for metric_name, diff_data in comparison['differences'].items():
            metric_display = metric_name.replace('_', ' ').title()
            
            report_lines.append(f"#### {metric_display}")
            report_lines.append(f"- **WITH Partial Column Dissemination**: {diff_data['enabled_total_change']:,} total change")
            report_lines.append(f"- **WITHOUT Partial Column Dissemination**: {diff_data['disabled_total_change']:,} total change")
            report_lines.append(f"- **Absolute Difference**: {diff_data['absolute_difference']:,}")
            report_lines.append(f"- **Percentage Difference**: {diff_data['percent_difference']:.2f}%")
            
            if diff_data['absolute_difference'] > 0:
                report_lines.append(f"- **Impact**: Partial column dissemination INCREASED {metric_display.lower()} by {diff_data['absolute_difference']:,}")
            elif diff_data['absolute_difference'] < 0:
                report_lines.append(f"- **Impact**: Partial column dissemination DECREASED {metric_display.lower()} by {abs(diff_data['absolute_difference']):,}")
            else:
                report_lines.append(f"- **Impact**: No significant difference in {metric_display.lower()}")
            
            report_lines.append("")
    
    # Detailed Per-Node Analysis
    report_lines.append("## DETAILED PER-NODE ANALYSIS")
    report_lines.append("-" * 30)
    report_lines.append("")
    
    for node_name in ['cl-1', 'cl-2', 'cl-3', 'cl-4']:
        report_lines.append(f"### Node: {node_name}")
        report_lines.append("")
        
        # Create comparison table for this node
        if (enabled_metrics and node_name in enabled_metrics['nodes'] and
            disabled_metrics and node_name in disabled_metrics['nodes']):
            
            enabled_node = enabled_metrics['nodes'][node_name]
            disabled_node = disabled_metrics['nodes'][node_name]
            
            report_lines.append("| Metric | With PCD | Without PCD | Difference |")
            report_lines.append("|--------|----------|-------------|------------|")
            
            for metric_name in ['libp2p_bytes_total', 'lighthouse_network_gossip_messages_total',
                              'lighthouse_network_data_column_sidecar_gossip_messages_total',
                              'lighthouse_network_blob_sidecar_gossip_messages_total']:
                
                if metric_name in enabled_node and metric_name in disabled_node:
                    enabled_change = enabled_node[metric_name]['change']
                    disabled_change = disabled_node[metric_name]['change']
                    difference = enabled_change - disabled_change
                    
                    metric_display = metric_name.replace('lighthouse_network_', '').replace('_', ' ').title()
                    
                    report_lines.append(f"| {metric_display} | {enabled_change:,} | {disabled_change:,} | {difference:,} |")
            
            report_lines.append("")
        else:
            report_lines.append("*Node data not available for comparison*")
            report_lines.append("")
    
    # Key Findings
    report_lines.append("## KEY FINDINGS")
    report_lines.append("-" * 15)
    report_lines.append("")
    
    if 'differences' in comparison and comparison['differences']:
        # Find most impacted metrics
        max_impact_metric = None
        max_impact_value = 0
        
        for metric_name, diff_data in comparison['differences'].items():
            abs_diff = abs(diff_data['absolute_difference'])
            if abs_diff > max_impact_value:
                max_impact_value = abs_diff
                max_impact_metric = metric_name
        
        if max_impact_metric:
            metric_display = max_impact_metric.replace('_', ' ').title()
            impact_data = comparison['differences'][max_impact_metric]
            
            report_lines.append(f"### Most Impacted Metric: {metric_display}")
            report_lines.append(f"- Absolute difference: {impact_data['absolute_difference']:,}")
            report_lines.append(f"- Percentage difference: {impact_data['percent_difference']:.2f}%")
            report_lines.append("")
        
        # Data column specific analysis
        data_column_metric = 'lighthouse_network_data_column_sidecar_gossip_messages_total'
        if data_column_metric in comparison['differences']:
            dc_data = comparison['differences'][data_column_metric]
            report_lines.append("### Data Column Sidecar Messages")
            report_lines.append("This metric directly reflects the impact of partial column dissemination:")
            report_lines.append(f"- Change with PCD: {dc_data['enabled_total_change']:,}")
            report_lines.append(f"- Change without PCD: {dc_data['disabled_total_change']:,}")
            
            if dc_data['absolute_difference'] != 0:
                direction = "increased" if dc_data['absolute_difference'] > 0 else "decreased"
                report_lines.append(f"- **Result**: Partial column dissemination {direction} data column messages by {abs(dc_data['absolute_difference']):,}")
            else:
                report_lines.append("- **Result**: No significant difference in data column message activity")
            report_lines.append("")
    
    # Recommendations
    report_lines.append("## RECOMMENDATIONS")
    report_lines.append("-" * 17)
    report_lines.append("")
    
    if 'differences' in comparison and comparison['differences']:
        total_bytes_diff = comparison['differences'].get('libp2p_bytes_total', {}).get('absolute_difference', 0)
        
        if total_bytes_diff > 0:
            report_lines.append("### Network Impact Assessment")
            report_lines.append(f"- Partial column dissemination increases network traffic by {total_bytes_diff:,} bytes over the test period")
            report_lines.append("- This represents the trade-off between bandwidth usage and data availability benefits")
            report_lines.append("")
        elif total_bytes_diff < 0:
            report_lines.append("### Network Impact Assessment")
            report_lines.append(f"- Partial column dissemination reduces network traffic by {abs(total_bytes_diff):,} bytes over the test period")
            report_lines.append("- This suggests efficiency gains from the partial column dissemination approach")
            report_lines.append("")
    
    report_lines.append("### Next Steps")
    report_lines.append("1. **Performance Validation**: Run longer-duration tests to confirm patterns")
    report_lines.append("2. **Load Testing**: Test under higher transaction volumes")
    report_lines.append("3. **Network Conditions**: Test under various network conditions and latencies")
    report_lines.append("4. **Resource Monitoring**: Monitor CPU and memory usage differences")
    report_lines.append("")
    
    # Technical Details
    report_lines.append("## TECHNICAL DETAILS")
    report_lines.append("-" * 19)
    report_lines.append("")
    report_lines.append("### Test Files Analyzed")
    report_lines.append("- With PCD: partial_column_metrics_20250623_142527.json")
    report_lines.append("- Without PCD: partial_column_metrics_20250623_151223.json")
    report_lines.append("")
    report_lines.append("### Metrics Analyzed")
    report_lines.append("- `libp2p_bytes_total`: Total network bytes transferred")
    report_lines.append("- `lighthouse_network_gossip_messages_total`: General gossip message count")
    report_lines.append("- `lighthouse_network_data_column_sidecar_gossip_messages_total`: Data column specific messages")
    report_lines.append("- `lighthouse_network_blob_sidecar_gossip_messages_total`: Blob sidecar messages")
    report_lines.append("")
    
    return "\n".join(report_lines)

def main():
    # File names for the two test results
    enabled_file = "partial_column_metrics_20250623_142527.json"  # WITH partial column dissemination
    disabled_file = "partial_column_metrics_20250623_151223.json"  # WITHOUT partial column dissemination
    
    print("Loading test results...")
    enabled_data, disabled_data = load_test_results(enabled_file, disabled_file)
    
    if not enabled_data or not disabled_data:
        print("Error: Could not load test result files")
        return 1
    
    print("Extracting metrics...")
    enabled_metrics = extract_key_metrics(enabled_data, "WITH partial column dissemination")
    disabled_metrics = extract_key_metrics(disabled_data, "WITHOUT partial column dissemination")
    
    if not enabled_metrics or not disabled_metrics:
        print("Error: Could not extract metrics from test files")
        return 1
    
    print("Comparing results...")
    comparison = compare_metrics(enabled_metrics, disabled_metrics)
    
    print("Generating report...")
    report = generate_report(enabled_metrics, disabled_metrics, comparison)
    
    # Save report to file
    report_filename = f"partial_column_comparison_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    with open(report_filename, 'w') as f:
        f.write(report)
    
    print(f"✅ Analysis complete! Report saved to: {report_filename}")
    print("\n" + "="*60)
    print("QUICK SUMMARY:")
    print("="*60)
    
    # Print quick summary
    if 'differences' in comparison and comparison['differences']:
        for metric_name, diff_data in comparison['differences'].items():
            metric_display = metric_name.replace('_', ' ').title()
            print(f"{metric_display}:")
            print(f"  With PCD: {diff_data['enabled_total_change']:,}")
            print(f"  Without PCD: {diff_data['disabled_total_change']:,}")
            print(f"  Difference: {diff_data['absolute_difference']:,} ({diff_data['percent_difference']:.2f}%)")
            print()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
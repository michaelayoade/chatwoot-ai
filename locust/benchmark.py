#!/usr/bin/env python3
"""
Benchmark testing script for LangChain-Chatwoot integration.
This script establishes performance baselines before and after changes.
"""

import argparse
import json
import time
import requests
import statistics
import datetime
import csv
import os
from concurrent.futures import ThreadPoolExecutor

# Sample queries for benchmarking
BENCHMARK_QUERIES = {
    "simple": [
        "What internet plans do you offer?",
        "How do I reset my password?",
        "When is my next bill due?",
        "What's your customer service number?",
        "Do you offer fiber internet?"
    ],
    "complex": [
        "I'm having trouble with my internet connection. It was working fine yesterday but now it's very slow and keeps disconnecting. I've tried restarting my router but it didn't help.",
        "I want to upgrade my current plan to include more data and faster speeds. I currently have the basic package but need something better for working from home. What options do you have?",
        "Can you explain the difference between your fiber plans and regular broadband? I'm trying to decide which one would be better for streaming and gaming.",
        "I noticed an unusual charge on my last bill. It shows $49.99 for 'Premium Service' but I don't remember signing up for anything like that. Can you check what this is?",
        "I'm moving to a new address next month and need to transfer my service. The new address is 123 Main Street, Anytown. What do I need to do to ensure I don't lose service during the move?"
    ],
    "api_intensive": [
        "Check my account balance for customer CUS-12345",
        "What's my current data usage for this month? My account is CUS-23456",
        "When is my next payment due for customer ID CUS-34567?",
        "Show me my billing history for the past 6 months. Account: CUS-45678",
        "What's my current plan details for customer ID CUS-56789?"
    ]
}

class BenchmarkRunner:
    def __init__(self, base_url, output_dir="benchmark_results"):
        self.base_url = base_url
        self.output_dir = output_dir
        self.timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Initialize results dictionary
        self.results = {
            "timestamp": self.timestamp,
            "simple_queries": {},
            "complex_queries": {},
            "api_intensive_queries": {},
            "summary": {}
        }
    
    def run_single_query(self, query, query_type, index):
        """Run a single query and measure performance metrics"""
        conversation_id = f"benchmark-{query_type}-{index}-{self.timestamp}"
        
        payload = {
            "message": query,
            "conversation_id": conversation_id,
            "role": "benchmark"
        }
        
        start_time = time.time()
        try:
            response = requests.post(
                f"{self.base_url}/api/process_message",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            end_time = time.time()
            duration = (end_time - start_time) * 1000  # Convert to milliseconds
            
            # Extract headers related to reliability components
            reliability_headers = {
                key: response.headers.get(key) 
                for key in response.headers 
                if key.startswith("X-") and key in [
                    "X-Cache-Hit", "X-Circuit-Open", "X-Rate-Limited", 
                    "X-Response-Time", "X-API-Calls"
                ]
            }
            
            return {
                "query": query,
                "status_code": response.status_code,
                "duration_ms": duration,
                "response_length": len(response.text) if response.text else 0,
                "reliability_headers": reliability_headers
            }
        except Exception as e:
            end_time = time.time()
            duration = (end_time - start_time) * 1000  # Convert to milliseconds
            return {
                "query": query,
                "status_code": -1,
                "duration_ms": duration,
                "error": str(e),
                "reliability_headers": {}
            }
    
    def run_benchmark(self, concurrency=1):
        """Run the benchmark with specified concurrency"""
        print(f"Starting benchmark with concurrency {concurrency}...")
        
        # Run benchmarks for each query type
        for query_type, queries in [
            ("simple", BENCHMARK_QUERIES["simple"]),
            ("complex", BENCHMARK_QUERIES["complex"]),
            ("api_intensive", BENCHMARK_QUERIES["api_intensive"])
        ]:
            print(f"Running {query_type} queries...")
            results_key = f"{query_type}_queries"
            self.results[results_key]["individual_results"] = []
            
            # Run queries in parallel based on concurrency
            with ThreadPoolExecutor(max_workers=concurrency) as executor:
                futures = [
                    executor.submit(self.run_single_query, query, query_type, i)
                    for i, query in enumerate(queries)
                ]
                
                for future in futures:
                    result = future.result()
                    self.results[results_key]["individual_results"].append(result)
            
            # Calculate statistics
            durations = [r["duration_ms"] for r in self.results[results_key]["individual_results"]]
            success_count = sum(1 for r in self.results[results_key]["individual_results"] if 200 <= r["status_code"] < 300)
            
            self.results[results_key]["summary"] = {
                "total_queries": len(queries),
                "successful_queries": success_count,
                "success_rate": success_count / len(queries) if queries else 0,
                "min_duration_ms": min(durations) if durations else 0,
                "max_duration_ms": max(durations) if durations else 0,
                "avg_duration_ms": statistics.mean(durations) if durations else 0,
                "median_duration_ms": statistics.median(durations) if durations else 0,
                "p95_duration_ms": sorted(durations)[int(0.95 * len(durations)) - 1] if len(durations) >= 20 else max(durations) if durations else 0
            }
            
            print(f"  Completed {query_type} queries: Avg {self.results[results_key]['summary']['avg_duration_ms']:.2f}ms, Success rate: {self.results[results_key]['summary']['success_rate'] * 100:.1f}%")
        
        # Calculate overall summary
        all_durations = []
        total_success = 0
        total_queries = 0
        
        for query_type in ["simple_queries", "complex_queries", "api_intensive_queries"]:
            all_durations.extend([r["duration_ms"] for r in self.results[query_type]["individual_results"]])
            total_success += self.results[query_type]["summary"]["successful_queries"]
            total_queries += self.results[query_type]["summary"]["total_queries"]
        
        self.results["summary"] = {
            "total_queries": total_queries,
            "successful_queries": total_success,
            "success_rate": total_success / total_queries if total_queries else 0,
            "min_duration_ms": min(all_durations) if all_durations else 0,
            "max_duration_ms": max(all_durations) if all_durations else 0,
            "avg_duration_ms": statistics.mean(all_durations) if all_durations else 0,
            "median_duration_ms": statistics.median(all_durations) if all_durations else 0,
            "p95_duration_ms": sorted(all_durations)[int(0.95 * len(all_durations)) - 1] if len(all_durations) >= 20 else max(all_durations) if all_durations else 0
        }
        
        print("\nBenchmark Summary:")
        print(f"Total Queries: {total_queries}")
        print(f"Success Rate: {self.results['summary']['success_rate'] * 100:.1f}%")
        print(f"Average Response Time: {self.results['summary']['avg_duration_ms']:.2f}ms")
        print(f"95th Percentile Response Time: {self.results['summary']['p95_duration_ms']:.2f}ms")
        
        # Save results
        self.save_results()
    
    def save_results(self):
        """Save benchmark results to files"""
        # Save detailed JSON results
        json_filename = f"{self.output_dir}/benchmark_{self.timestamp}.json"
        with open(json_filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        # Save summary CSV for easy comparison
        csv_filename = f"{self.output_dir}/benchmark_summary_{self.timestamp}.csv"
        with open(csv_filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Query Type", "Success Rate", "Avg Duration (ms)", "Median Duration (ms)", "P95 Duration (ms)"])
            
            for query_type in ["simple_queries", "complex_queries", "api_intensive_queries"]:
                summary = self.results[query_type]["summary"]
                writer.writerow([
                    query_type.replace("_queries", ""),
                    f"{summary['success_rate'] * 100:.1f}%",
                    f"{summary['avg_duration_ms']:.2f}",
                    f"{summary['median_duration_ms']:.2f}",
                    f"{summary['p95_duration_ms']:.2f}"
                ])
            
            # Add overall summary
            writer.writerow([])
            writer.writerow([
                "OVERALL",
                f"{self.results['summary']['success_rate'] * 100:.1f}%",
                f"{self.results['summary']['avg_duration_ms']:.2f}",
                f"{self.results['summary']['median_duration_ms']:.2f}",
                f"{self.results['summary']['p95_duration_ms']:.2f}"
            ])
        
        print(f"\nResults saved to {json_filename} and {csv_filename}")

def compare_benchmarks(before_file, after_file, output_file=None):
    """Compare two benchmark results and generate a comparison report"""
    with open(before_file, 'r') as f:
        before_data = json.load(f)
    
    with open(after_file, 'r') as f:
        after_data = json.load(f)
    
    comparison = {
        "before_timestamp": before_data["timestamp"],
        "after_timestamp": after_data["timestamp"],
        "query_types": {},
        "overall": {}
    }
    
    # Compare each query type
    for query_type in ["simple_queries", "complex_queries", "api_intensive_queries"]:
        before_summary = before_data[query_type]["summary"]
        after_summary = after_data[query_type]["summary"]
        
        comparison["query_types"][query_type] = {
            "success_rate": {
                "before": before_summary["success_rate"],
                "after": after_summary["success_rate"],
                "change": after_summary["success_rate"] - before_summary["success_rate"],
                "percent_change": ((after_summary["success_rate"] / before_summary["success_rate"]) - 1) * 100 if before_summary["success_rate"] else float('inf')
            },
            "avg_duration_ms": {
                "before": before_summary["avg_duration_ms"],
                "after": after_summary["avg_duration_ms"],
                "change": after_summary["avg_duration_ms"] - before_summary["avg_duration_ms"],
                "percent_change": ((after_summary["avg_duration_ms"] / before_summary["avg_duration_ms"]) - 1) * 100 if before_summary["avg_duration_ms"] else float('inf')
            },
            "p95_duration_ms": {
                "before": before_summary["p95_duration_ms"],
                "after": after_summary["p95_duration_ms"],
                "change": after_summary["p95_duration_ms"] - before_summary["p95_duration_ms"],
                "percent_change": ((after_summary["p95_duration_ms"] / before_summary["p95_duration_ms"]) - 1) * 100 if before_summary["p95_duration_ms"] else float('inf')
            }
        }
    
    # Compare overall results
    before_overall = before_data["summary"]
    after_overall = after_data["summary"]
    
    comparison["overall"] = {
        "success_rate": {
            "before": before_overall["success_rate"],
            "after": after_overall["success_rate"],
            "change": after_overall["success_rate"] - before_overall["success_rate"],
            "percent_change": ((after_overall["success_rate"] / before_overall["success_rate"]) - 1) * 100 if before_overall["success_rate"] else float('inf')
        },
        "avg_duration_ms": {
            "before": before_overall["avg_duration_ms"],
            "after": after_overall["avg_duration_ms"],
            "change": after_overall["avg_duration_ms"] - before_overall["avg_duration_ms"],
            "percent_change": ((after_overall["avg_duration_ms"] / before_overall["avg_duration_ms"]) - 1) * 100 if before_overall["avg_duration_ms"] else float('inf')
        },
        "p95_duration_ms": {
            "before": before_overall["p95_duration_ms"],
            "after": after_overall["p95_duration_ms"],
            "change": after_overall["p95_duration_ms"] - before_overall["p95_duration_ms"],
            "percent_change": ((after_overall["p95_duration_ms"] / before_overall["p95_duration_ms"]) - 1) * 100 if before_overall["p95_duration_ms"] else float('inf')
        }
    }
    
    # Generate report
    report = []
    report.append(f"Benchmark Comparison: {before_data['timestamp']} vs {after_data['timestamp']}")
    report.append("=" * 80)
    report.append("")
    
    report.append("Overall Performance Changes:")
    report.append("-" * 40)
    success_change = comparison["overall"]["success_rate"]["percent_change"]
    avg_dur_change = comparison["overall"]["avg_duration_ms"]["percent_change"]
    p95_dur_change = comparison["overall"]["p95_duration_ms"]["percent_change"]
    
    report.append(f"Success Rate: {before_overall['success_rate']*100:.1f}% → {after_overall['success_rate']*100:.1f}% ({success_change:+.1f}%)")
    report.append(f"Avg Duration: {before_overall['avg_duration_ms']:.2f}ms → {after_overall['avg_duration_ms']:.2f}ms ({avg_dur_change:+.1f}%)")
    report.append(f"P95 Duration: {before_overall['p95_duration_ms']:.2f}ms → {after_overall['p95_duration_ms']:.2f}ms ({p95_dur_change:+.1f}%)")
    report.append("")
    
    for query_type in ["simple_queries", "complex_queries", "api_intensive_queries"]:
        display_name = query_type.replace("_queries", "").title()
        report.append(f"{display_name} Queries:")
        report.append("-" * 40)
        
        comp = comparison["query_types"][query_type]
        before_summary = before_data[query_type]["summary"]
        after_summary = after_data[query_type]["summary"]
        
        success_change = comp["success_rate"]["percent_change"]
        avg_dur_change = comp["avg_duration_ms"]["percent_change"]
        p95_dur_change = comp["p95_duration_ms"]["percent_change"]
        
        report.append(f"Success Rate: {before_summary['success_rate']*100:.1f}% → {after_summary['success_rate']*100:.1f}% ({success_change:+.1f}%)")
        report.append(f"Avg Duration: {before_summary['avg_duration_ms']:.2f}ms → {after_summary['avg_duration_ms']:.2f}ms ({avg_dur_change:+.1f}%)")
        report.append(f"P95 Duration: {before_summary['p95_duration_ms']:.2f}ms → {after_summary['p95_duration_ms']:.2f}ms ({p95_dur_change:+.1f}%)")
        report.append("")
    
    report_text = "\n".join(report)
    print(report_text)
    
    if output_file:
        with open(output_file, 'w') as f:
            f.write(report_text)
        print(f"Comparison report saved to {output_file}")
    
    return comparison

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Benchmark testing for LangChain-Chatwoot integration")
    parser.add_argument("--url", default="http://localhost:5001", help="Base URL of the API")
    parser.add_argument("--concurrency", type=int, default=2, help="Number of concurrent requests")
    parser.add_argument("--output-dir", default="benchmark_results", help="Directory to save results")
    parser.add_argument("--compare", nargs=2, metavar=("BEFORE_FILE", "AFTER_FILE"), help="Compare two benchmark result files")
    parser.add_argument("--compare-output", help="Output file for comparison report")
    
    args = parser.parse_args()
    
    if args.compare:
        compare_benchmarks(args.compare[0], args.compare[1], args.compare_output)
    else:
        benchmark = BenchmarkRunner(args.url, args.output_dir)
        benchmark.run_benchmark(args.concurrency)

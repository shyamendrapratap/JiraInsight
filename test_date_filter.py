#!/usr/bin/env python3
"""
Test Date Filter
Verify date range filtering produces different results
"""

import sys
from pathlib import Path
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent / "src"))

from config_loader import ConfigLoader
from database import DatabaseService
from kpi_calculator_db import KPICalculatorDB


def main():
    """Test date range filtering"""

    load_dotenv()

    config_loader = ConfigLoader()
    config = config_loader.load()

    db = DatabaseService("./data/kpi_data.db")
    calculator = KPICalculatorDB(db, config)

    print("\n" + "="*60)
    print("DATE RANGE FILTER TEST")
    print("="*60)

    date_ranges = [30, 60, 90, 180, 365]
    project = "CCT"

    print(f"\nTesting date ranges for project: {project}")
    print("-"*60)

    results = []
    for days in date_ranges:
        print(f"\n📅 Date Range: {days} days")
        kpi_data = calculator.calculate_all_kpis(
            date_range_days=days,
            projects=[project]
        )

        kpis = kpi_data.get('kpis', {})
        cycle_time = kpis.get('cycle_time', {})
        work_mix = kpis.get('work_mix', {})

        result = {
            'days': days,
            'work_mix_issues': work_mix.get('total_issues', 0),
            'cycle_time_avg': cycle_time.get('average_cycle_time_days', 0),
            'cycle_time_issues': cycle_time.get('issues_analyzed', 0)
        }
        results.append(result)

        print(f"  Work Mix: {result['work_mix_issues']} issues")
        print(f"  Cycle Time: {result['cycle_time_avg']:.1f} days ({result['cycle_time_issues']} issues)")

    print("\n" + "="*60)
    print("COMPARISON TABLE")
    print("="*60)
    print(f"{'Days':<10} {'Work Mix':<15} {'Cycle Time':<15} {'Issues Analyzed':<15}")
    print("-"*60)
    for r in results:
        print(f"{r['days']:<10} {r['work_mix_issues']:<15} {r['cycle_time_avg']:<15.1f} {r['cycle_time_issues']:<15}")

    print("\n" + "="*60)
    print("ANALYSIS")
    print("="*60)

    # Check if values are different
    work_mix_values = [r['work_mix_issues'] for r in results]
    cycle_time_values = [r['cycle_time_issues'] for r in results]

    if len(set(work_mix_values)) > 1:
        print("✅ Work Mix CHANGES with date range (filtering working!)")
    else:
        print("❌ Work Mix SAME for all date ranges (filtering NOT working)")

    if len(set(cycle_time_values)) > 1:
        print("✅ Cycle Time issues CHANGE with date range (filtering working!)")
    else:
        print("❌ Cycle Time issues SAME for all date ranges (filtering NOT working)")

    print("\n" + "="*60)


if __name__ == "__main__":
    main()

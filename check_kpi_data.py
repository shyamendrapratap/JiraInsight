#!/usr/bin/env python3
"""
Check KPI Data
Debug script to see what KPIs are being calculated
"""

import sys
from pathlib import Path
from dotenv import load_dotenv
import json

sys.path.insert(0, str(Path(__file__).parent / "src"))

from config_loader import ConfigLoader
from database import DatabaseService
from kpi_calculator_db import KPICalculatorDB


def main():
    """Check KPI data"""

    load_dotenv()

    config_loader = ConfigLoader()
    config = config_loader.load()

    db = DatabaseService("./data/kpi_data.db")
    calculator = KPICalculatorDB(db, config)

    print("\n" + "="*60)
    print("KPI DATA CHECK")
    print("="*60)

    # Calculate KPIs
    print("\n🔄 Calculating KPIs...")
    kpi_data = calculator.calculate_all_kpis()

    # Show overall KPIs
    print("\n" + "="*60)
    print("OVERALL KPIs")
    print("="*60)

    kpis = kpi_data.get('kpis', {})

    for kpi_name, kpi_values in kpis.items():
        print(f"\n{kpi_name.upper()}")
        print("-" * 40)
        if isinstance(kpi_values, dict):
            for key, value in kpi_values.items():
                if key not in ['sprints', 'spillover_issues', 'cycle_times', 'reopened_issues', 'distribution']:
                    print(f"  {key}: {value}")

    # Show per-project KPIs
    print("\n" + "="*60)
    print("PER-PROJECT KPIs")
    print("="*60)

    kpis_by_project = kpi_data.get('kpis_by_project', {})

    for project, project_kpis in kpis_by_project.items():
        if project not in ['CCT', 'SCPX', 'CCEN']:
            continue

        print(f"\n{project}:")
        print("-" * 40)

        for kpi_name, kpi_values in project_kpis.items():
            if isinstance(kpi_values, dict):
                print(f"  {kpi_name}:")
                for key, value in kpi_values.items():
                    if key not in ['sprints', 'spillover_issues', 'cycle_times', 'reopened_issues', 'distribution']:
                        print(f"    {key}: {value}")

    # Database stats
    print("\n" + "="*60)
    print("DATABASE STATS")
    print("="*60)
    stats = kpi_data.get('database_stats', {})
    print(json.dumps(stats, indent=2))

    print("\n" + "="*60)


if __name__ == "__main__":
    main()

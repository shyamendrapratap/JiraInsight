#!/usr/bin/env python3
"""
Platform Engineering KPI Dashboard - Main Application
Entry point for the dashboard application
"""

import os
import sys
import logging
import argparse
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from config_loader import ConfigLoader
from jira_client import JiraClient
from kpi_calculator import KPICalculator
from kpi_calculator_db import KPICalculatorDB
from database import DatabaseService
from dashboard import KPIDashboard


def setup_logging(config: dict):
    """Setup logging configuration"""
    log_config = config.get("logging", {})
    log_level = log_config.get("level", "INFO")
    log_file = log_config.get("file", "./logs/kpi_dashboard.log")

    # Create logs directory if it doesn't exist
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )

    return logging.getLogger(__name__)


def test_jira_connection(jira_client: JiraClient) -> bool:
    """
    Test JIRA connection

    Args:
        jira_client: JiraClient instance

    Returns:
        True if connection successful
    """
    print("\n" + "="*60)
    print("Testing JIRA Connection...")
    print("="*60)

    try:
        if jira_client.test_connection():
            print("✓ JIRA connection successful!")
            return True
        else:
            print("✗ JIRA connection failed!")
            return False
    except Exception as e:
        print(f"✗ JIRA connection error: {e}")
        return False


def collect_kpi_data(config: dict, jira_client: JiraClient) -> dict:
    """
    Collect KPI data from JIRA

    Args:
        config: Configuration dictionary
        jira_client: JiraClient instance

    Returns:
        Dictionary containing all KPI data
    """
    print("\n" + "="*60)
    print("Collecting KPI Data from JIRA...")
    print("="*60)

    calculator = KPICalculator(jira_client, config)

    print("\nCalculating KPIs...")
    kpi_data = calculator.calculate_all_kpis()

    print(f"\n✓ KPI calculation complete!")
    print(f"  - Generated at: {kpi_data.get('generated_at')}")
    print(f"  - Projects analyzed: {', '.join(kpi_data.get('projects', []))}")
    print(f"  - KPIs calculated: {len(kpi_data.get('kpis', {}))}")

    return kpi_data


def save_kpi_data(kpi_data: dict, output_path: str = None):
    """
    Save KPI data to JSON file

    Args:
        kpi_data: KPI data dictionary
        output_path: Output file path
    """
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"./data/exports/kpi_data_{timestamp}.json"

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(kpi_data, f, indent=2, default=str)

    print(f"\n✓ KPI data saved to: {output_path}")


def load_kpi_data(input_path: str) -> dict:
    """
    Load KPI data from JSON file

    Args:
        input_path: Input file path

    Returns:
        KPI data dictionary
    """
    with open(input_path, 'r') as f:
        return json.load(f)


def run_dashboard(config: dict, kpi_data: dict = None, db=None, calculator=None):
    """
    Run the dashboard application

    Args:
        config: Configuration dictionary
        kpi_data: Pre-loaded KPI data (optional)
        db: Database service (optional)
        calculator: KPI calculator (optional)
    """
    dashboard_config = config.get("dashboard", {})
    host = dashboard_config.get("host", "127.0.0.1")
    port = dashboard_config.get("port", 8050)
    debug = dashboard_config.get("debug", False)

    print("\n" + "="*60)
    print("Starting Platform Engineering KPI Dashboard")
    print("="*60)
    print(f"\nDashboard URL: http://{host}:{port}")
    print("\nPress CTRL+C to stop the dashboard\n")

    dashboard = KPIDashboard(config, kpi_data=kpi_data, db=db, calculator=calculator)
    dashboard.run(host=host, port=port, debug=debug)


def print_kpi_summary(kpi_data: dict):
    """
    Print KPI summary to console

    Args:
        kpi_data: KPI data dictionary
    """
    print("\n" + "="*60)
    print("KPI SUMMARY")
    print("="*60)

    kpis = kpi_data.get("kpis", {})

    # Sprint Predictability
    if "sprint_predictability" in kpis:
        sp = kpis["sprint_predictability"]
        print(f"\n📊 Sprint Predictability: {sp.get('overall_average', 0)}%")
        print(f"   Sprints analyzed: {len(sp.get('sprints', []))}")

    # Story Spillover
    if "story_spillover" in kpis:
        ss = kpis["story_spillover"]
        print(f"\n📈 Story Spillover: {ss.get('spillover_percentage', 0)}%")
        print(f"   Spillover issues: {ss.get('spillover_count', 0)} / {ss.get('total_analyzed', 0)}")

    # Cycle Time
    if "cycle_time" in kpis:
        ct = kpis["cycle_time"]
        print(f"\n⏱️  Average Cycle Time: {ct.get('average_cycle_time_days', 0)} days")
        print(f"   Median: {ct.get('median_cycle_time_days', 0)} days")
        print(f"   Issues analyzed: {ct.get('issues_analyzed', 0)}")

    # Work Mix
    if "work_mix" in kpis:
        wm = kpis["work_mix"]
        print(f"\n🔀 Work Mix Distribution (Total: {wm.get('total_issues', 0)} issues):")
        for category, data in wm.get("distribution", {}).items():
            print(f"   {category}: {data.get('percentage', 0)}% ({data.get('count', 0)} issues)")

    # Unplanned Work
    if "unplanned_work" in kpis:
        uw = kpis["unplanned_work"]
        print(f"\n⚠️  Unplanned Work: {uw.get('overall_average', 0)}%")
        print(f"   Sprints analyzed: {len(uw.get('sprints', []))}")

    # Reopened Stories
    if "reopened_stories" in kpis:
        rs = kpis["reopened_stories"]
        print(f"\n🔄 Reopened Stories: {rs.get('reopened_percentage', 0)}%")
        print(f"   Reopened: {rs.get('reopened_count', 0)} / {rs.get('total_completed', 0)}")

    print("\n" + "="*60 + "\n")


def main():
    """Main application entry point"""

    # Load environment variables from .env file
    load_dotenv()

    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Platform Engineering KPI Dashboard",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to configuration YAML file (default: config/config.yaml)"
    )

    parser.add_argument(
        "--test-connection",
        action="store_true",
        help="Test JIRA connection and exit"
    )

    parser.add_argument(
        "--collect-only",
        action="store_true",
        help="Collect KPI data and save to file without starting dashboard"
    )

    parser.add_argument(
        "--load-data",
        type=str,
        help="Load KPI data from JSON file instead of fetching from JIRA"
    )

    parser.add_argument(
        "--output",
        type=str,
        help="Output path for KPI data JSON file (used with --collect-only)"
    )

    parser.add_argument(
        "--summary",
        action="store_true",
        help="Print KPI summary to console"
    )

    parser.add_argument(
        "--use-db",
        action="store_true",
        help="Use local database instead of fetching from JIRA (run sync_data.py first)"
    )

    parser.add_argument(
        "--db",
        type=str,
        default="./data/kpi_data.db",
        help="Path to database file (default: ./data/kpi_data.db)"
    )

    args = parser.parse_args()

    # Load configuration
    try:
        config_loader = ConfigLoader(args.config)
        config = config_loader.load()
    except Exception as e:
        print(f"\n❌ Configuration error: {e}")
        print("\nPlease check your configuration file and environment variables.")
        print("See config/config.yaml and .env.example for reference.")
        sys.exit(1)

    # Setup logging
    logger = setup_logging(config)
    logger.info("Platform Engineering KPI Dashboard starting...")

    # Initialize JIRA client
    jira_config = config.get("jira", {})
    jira_urls = jira_config.get("urls", [])

    if not jira_urls:
        print("\n❌ No JIRA URLs configured!")
        sys.exit(1)

    # Use first JIRA URL
    jira_url = jira_urls[0]
    jira_email = jira_config.get("email")
    jira_token = jira_config.get("token")

    jira_client = JiraClient(jira_url, jira_email, jira_token)

    # Test connection mode
    if args.test_connection:
        success = test_jira_connection(jira_client)
        sys.exit(0 if success else 1)

    # Load or collect KPI data
    kpi_data = None
    db = None
    calculator = None

    if args.use_db:
        # Use database
        print(f"\n📊 Loading KPI data from database: {args.db}")
        try:
            db = DatabaseService(args.db)
            stats = db.get_stats()

            if stats['issues_count'] == 0:
                print("\n⚠️  Database is empty!")
                print("Please run the sync script first:")
                print("  python sync_data.py --full")
                sys.exit(1)

            print(f"✓ Database loaded")
            print(f"  - Issues: {stats['issues_count']}")
            print(f"  - Sprints: {stats['sprints_count']}")
            print(f"  - Projects: {stats['projects_count']}")

            if stats['last_sync']:
                print(f"  - Last sync: {stats['last_sync']['completed_at']}")

            print("\n🔄 Calculating KPIs from database...")
            calculator = KPICalculatorDB(db, config)
            kpi_data = calculator.calculate_all_kpis()
            print("✓ KPI calculation complete!")

        except Exception as e:
            logger.error(f"Error loading from database: {e}", exc_info=True)
            print(f"\n❌ Error loading from database: {e}")
            sys.exit(1)

    elif args.load_data:
        # Load from file
        print(f"\n📂 Loading KPI data from: {args.load_data}")
        try:
            kpi_data = load_kpi_data(args.load_data)
            print(f"✓ KPI data loaded successfully!")
        except Exception as e:
            print(f"❌ Error loading KPI data: {e}")
            sys.exit(1)
    else:
        # Collect from JIRA
        try:
            if not test_jira_connection(jira_client):
                print("\n❌ Cannot proceed without JIRA connection!")
                print("\n💡 Tip: Use --use-db to load from local database instead")
                print("   First run: python sync_data.py --full")
                sys.exit(1)

            kpi_data = collect_kpi_data(config, jira_client)

            # Save data if requested
            if args.collect_only or args.output:
                save_kpi_data(kpi_data, args.output)

        except Exception as e:
            logger.error(f"Error collecting KPI data: {e}", exc_info=True)
            print(f"\n❌ Error collecting KPI data: {e}")
            print("\n💡 Tip: Use --use-db to load from local database instead")
            sys.exit(1)

    # Print summary if requested
    if args.summary and kpi_data:
        print_kpi_summary(kpi_data)

    # Exit if collect-only mode
    if args.collect_only:
        print("\n✓ Data collection complete. Exiting (--collect-only mode)")
        sys.exit(0)

    # Run dashboard
    try:
        run_dashboard(config, kpi_data, db=db, calculator=calculator)
    except KeyboardInterrupt:
        print("\n\n👋 Dashboard stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Dashboard error: {e}", exc_info=True)
        print(f"\n❌ Dashboard error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

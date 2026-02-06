"""
Platform Engineering KPI Dashboard
A comprehensive KPI tracking system for platform engineering teams using JIRA data.
"""

__version__ = "1.0.0"
__author__ = "Platform Engineering Team"
__description__ = "JIRA-based KPI Dashboard for Platform Engineering"

from .jira_client import JiraClient
from .kpi_calculator import KPICalculator
from .dashboard import KPIDashboard
from .config_loader import ConfigLoader

__all__ = [
    "JiraClient",
    "KPICalculator",
    "KPIDashboard",
    "ConfigLoader"
]

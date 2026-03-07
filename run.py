#!/usr/bin/env python3
"""
BlackHole Engine - Command-line system for managing your zero-to-$20K pipeline.

Usage:
    python run.py crm <command> [args]
    python run.py outreach <type> [args]
    python run.py proposal create [args]
    python run.py invoice create [args]
    python run.py content <type> [args]
    python run.py leads find [args]
    python run.py dashboard
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def print_banner():
    print("""
    ____  __    ___   ________ __  ______  __    ______
   / __ )/ /   /   | / ____/ //_/ / / / / / /   / ____/
  / __  / /   / /| |/ /   / ,<  / /_/ / / /   / __/
 / /_/ / /___/ ___ / /___/ /| |/ __  / / /___/ /___
/_____/_____/_/  |_\\____/_/ |_/_/ /_/ /_____/_____/

    Zero-Capital Wealth Engine v1.0
    """)

def print_help():
    print("""
COMMANDS:

  crm         Manage leads, clients, and pipeline
    add       <company> <contact> <email> <source> <deal_value>
    list      [--status STATUS]
    update    <id> <status>
    pipeline  Show pipeline overview
    revenue   Show revenue summary
    note      <id> <note text>

  outreach    Generate personalized outreach messages
    upwork    <job_description>
    linkedin  <name> <company> <role>
    cold-email <company> <pain_point>
    followup  <crm_id>

  proposal    Generate client proposals
    create    <client> <project> --value VALUE

  invoice     Generate and track invoices
    create    <client> <description> <amount>
    list      Show all invoices
    mark-paid <id>

  content     Generate content drafts
    blog      <topic>
    linkedin  <topic>
    twitter   <topic>

  leads       Research potential clients
    find      <industry> <location>

  dashboard   Show overall business dashboard
    """)

def main():
    if len(sys.argv) < 2:
        print_banner()
        print_help()
        return

    command = sys.argv[1].lower()

    if command == "crm":
        from engine.crm import main as crm_main
        crm_main(sys.argv[2:])
    elif command == "outreach":
        from engine.outreach import main as outreach_main
        outreach_main(sys.argv[2:])
    elif command == "proposal":
        from engine.proposals import main as proposals_main
        proposals_main(sys.argv[2:])
    elif command == "invoice":
        from engine.invoices import main as invoices_main
        invoices_main(sys.argv[2:])
    elif command == "content":
        from engine.content import main as content_main
        content_main(sys.argv[2:])
    elif command == "leads":
        from engine.leads import main as leads_main
        leads_main(sys.argv[2:])
    elif command == "dashboard":
        from engine.crm import show_dashboard
        show_dashboard()
    elif command in ("help", "--help", "-h"):
        print_banner()
        print_help()
    else:
        print(f"Unknown command: {command}")
        print_help()

if __name__ == "__main__":
    main()

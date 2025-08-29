#!/usr/bin/env python3
"""
DaVinci Resolve Environment Diagnostic Script
This script checks the Python environment being used by DaVinci Resolve
and prints diagnostic information to the console.
"""

import sys
import os

print("="*60)
print("=== DaVinci Resolve Environment Diagnostic Report ===")
print("="*60)

# --- Python Executable and Version ---
print("\n--- Python Interpreter Details ---")
print(f"Executable Path: {sys.executable}")
print(f"Version: {sys.version}")

# --- Python Path ---
print("\n--- Python Search Paths (sys.path) ---")
for i, path in enumerate(sys.path):
    print(f"  [{i}] {path}")

# --- DaVinci Resolve API Check ---
print("\n--- DaVinci Resolve API Import Test ---")
try:
    import DaVinciResolveScript as dvs
    print("✅ Successfully imported 'DaVinciResolveScript' module.")

    try:
        resolve = dvs.scriptapp("Resolve")
        if resolve:
            print("✅ Successfully connected to DaVinci Resolve API.")
            print(f"   - Resolve Version: {resolve.GetVersionString()}")
            pm = resolve.GetProjectManager()
            proj = pm.GetCurrentProject()
            if proj:
                print(f"   - Current Project: {proj.GetName()}")
            else:
                print("   - Warning: No project is currently open.")
        else:
            print("❌ ERROR: 'dvs.scriptapp(\"Resolve\")' returned None.")
            print("   - This suggests the script is not running in a context where it can connect to the main application.")

    except Exception as e:
        print(f"❌ ERROR: An exception occurred while trying to connect to the Resolve API.")
        print(f"   - Details: {e}")

except ImportError:
    print("❌ ERROR: Could not import the 'DaVinciResolveScript' module.")
    print("   - This is the main reason for the failure.")
    print("   - It means the Python environment Resolve is using does not have access to the API.")
    print("   - Please check your DaVinci Resolve scripting settings in Preferences.")

except Exception as e:
    print(f"❌ ERROR: An unexpected exception occurred during the import test.")
    print(f"   - Details: {e}")

print("\n" + "="*60)
print("=== End of Report ===")
print("="*60)
print("\nPlease copy the entire content of this report (from the top '===' line to the bottom '===' line) and provide it in your response.")

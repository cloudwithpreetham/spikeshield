#!/usr/bin/env python3
"""
SpikeShield AWS Blue/Green CNAME Swapper (make aws-swap)
Executes a zero-downtime Blue/Green CNAME swap between spikeshield-staging and spikeshield-prod.
"""
import sys
import os

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
sys.path.insert(0, BACKEND_DIR)

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

import boto3
from app.config import settings

def main():
    print("=" * 65)
    print(" 🔄  SPIKESHIELD ZERO-DOWNTIME BLUE/GREEN CNAME SWAP")
    print("=" * 65)

    sess = boto3.Session(
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION
    )

    eb = sess.client("elasticbeanstalk")

    print("\nQuerying current CNAMEs...")
    try:
        envs = eb.describe_environments(
            ApplicationName="spikeshield-app",
            EnvironmentNames=["spikeshield-prod", "spikeshield-staging"]
        ).get("Environments", [])

        for e in envs:
            print(f"   • {e['EnvironmentName']} -> http://{e.get('CNAME')}")

        print("\nExecuting CNAME Swap: spikeshield-staging ↔ spikeshield-prod...")
        eb.swap_environment_cnames(
            SourceEnvironmentName="spikeshield-staging",
            DestinationEnvironmentName="spikeshield-prod"
        )
        print("   ✓ CNAME swap command issued successfully!")
        print("   DNS will propagate in 10-30 seconds with 0 downtime.")

    except Exception as ex:
        print(f"   Error executing CNAME swap: {ex}")

    print("\n" + "=" * 65)

if __name__ == "__main__":
    main()

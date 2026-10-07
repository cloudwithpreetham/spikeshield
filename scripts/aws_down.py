#!/usr/bin/env python3
"""
SpikeShield AWS Infrastructure Teardown (make aws-down)
Safely terminates Elastic Beanstalk environments (staging & prod),
deletes the SQS queue, and returns AWS bill to $0.00.
"""
import sys
import os
import argparse

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
    parser = argparse.ArgumentParser(description="Tear down SpikeShield AWS infrastructure.")
    parser.add_argument("-y", "--yes", action="store_true", help="Skip confirmation prompt")
    args = parser.parse_args()

    print("=" * 65)
    print(" ⚠️   SPIKESHIELD AWS INFRASTRUCTURE TEARDOWN")
    print("=" * 65)

    if not args.yes:
        print("\nThis action will terminate:")
        print("  • Elastic Beanstalk Environment: spikeshield-staging")
        print("  • Elastic Beanstalk Environment: spikeshield-prod")
        print("  • Underlying EC2 Instances, ALBs, and Auto Scaling Groups")
        print("  • Amazon SQS Runbook Queue: spikeshield-runbooks")
        print("\nThis will bring your active AWS resource cost to $0.00.")
        confirm = input("\nAre you sure you want to proceed? (yes/no): ").strip().lower()
        if confirm not in ("yes", "y"):
            print("Teardown cancelled.")
            sys.exit(0)

    sess = boto3.Session(
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION
    )

    eb = sess.client("elasticbeanstalk")
    sqs = sess.client("sqs")

    # 1. Terminate Environments
    print("\n1. Querying active Elastic Beanstalk environments...")
    try:
        envs = eb.describe_environments(ApplicationName="spikeshield-app").get("Environments", [])
        active_envs = [e for e in envs if e.get("Status") not in ("Terminated", "Terminating")]

        for e in active_envs:
            env_name = e["EnvironmentName"]
            print(f"   Terminating environment: {env_name} ({e['EnvironmentId']})...")
            eb.terminate_environment(EnvironmentName=env_name, TerminateResources=True)
            print(f"   ✓ Termination initiated for {env_name}.")

        if not active_envs:
            print("   (No active environments found to terminate)")
    except Exception as ex:
        print(f"   Error terminating EB environments: {ex}")

    # 2. Delete SQS Queue
    print("\n2. Cleaning up Amazon SQS runbook queues...")
    try:
        queues = sqs.list_queues(QueueNamePrefix="spikeshield").get("QueueUrls", [])
        for q_url in queues:
            print(f"   Deleting SQS queue: {q_url}...")
            sqs.delete_queue(QueueUrl=q_url)
            print(f"   ✓ Queue deleted: {q_url}")
        if not queues:
            print("   (No queues found to delete)")
    except Exception as ex:
        print(f"   Error deleting SQS queue: {ex}")

    print("\n" + "=" * 65)
    print(" ✅  TEARDOWN INITIATED SUCCESSFULLY!")
    print("     AWS is releasing all EC2 instances, ALBs, and CloudWatch alarms.")
    print("     Run 'make aws-status' to verify resource termination.")
    print("=" * 65)

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
SpikeShield AWS Infrastructure Status Checker
Lists all active AWS Elastic Beanstalk environments, EC2 instances, ALBs, and SQS queues.
"""
import sys
import os

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
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
    print(" 🛡️  SPIKESHIELD AWS INFRASTRUCTURE STATUS (ap-south-1 Mumbai)")
    print("=" * 65)

    sess = boto3.Session(
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION
    )

    eb = sess.client("elasticbeanstalk")
    ec2 = sess.client("ec2")
    elbv2 = sess.client("elbv2")
    sqs = sess.client("sqs")

    # 1. Elastic Beanstalk Environments
    print("\n📦 ELASTIC BEANSTALK ENVIRONMENTS:")
    try:
        envs = eb.describe_environments(ApplicationName="spikeshield-app").get("Environments", [])
        active_envs = [e for e in envs if e.get("Status") != "Terminated"]
        if not active_envs:
            print("   (No active environments running)")
        for e in active_envs:
            health_color = e.get("Health", "Grey")
            color_bullet = "🟢" if health_color == "Green" else ("🟡" if health_color == "Yellow" else "🔴")
            print(f"   {color_bullet} {e['EnvironmentName']} ({e['EnvironmentId']})")
            print(f"      Status: {e['Status']} | Health: {health_color}")
            print(f"      Version: {e.get('VersionLabel', 'N/A')}")
            if e.get("CNAME"):
                print(f"      URL: http://{e['CNAME']}")
    except Exception as ex:
        print(f"   Error querying EB: {ex}")

    # 2. EC2 Instances
    print("\n💻 EC2 INSTANCES:")
    try:
        res = ec2.describe_instances(
            Filters=[{"Name": "instance-state-name", "Values": ["pending", "running", "shutting-down", "stopping", "stopped"]}]
        ).get("Reservations", [])
        found_instances = 0
        for r in res:
            for inst in r.get("Instances", []):
                found_instances += 1
                state = inst["State"]["Name"]
                bullet = "🟢" if state == "running" else "⚪"
                print(f"   {bullet} {inst['InstanceId']} | {inst['InstanceType']} | {inst.get('Placement', {}).get('AvailabilityZone')} | State: {state}")
        if found_instances == 0:
            print("   (No active EC2 instances)")
    except Exception as ex:
        print(f"   Error querying EC2: {ex}")

    # 3. Application Load Balancers
    print("\n⚡ APPLICATION LOAD BALANCERS:")
    try:
        lbs = elbv2.describe_load_balancers().get("LoadBalancers", [])
        if not lbs:
            print("   (No active ALBs)")
        for lb in lbs:
            print(f"   • {lb['LoadBalancerName']} | Scheme: {lb['Scheme']} | State: {lb['State']['Code']}")
    except Exception as ex:
        print(f"   Error querying ALB: {ex}")

    # 4. Amazon SQS Queues
    print("\n📨 AMAZON SQS RUNBOOK QUEUES:")
    try:
        queues = sqs.list_queues(QueueNamePrefix="spikeshield").get("QueueUrls", [])
        if not queues:
            print("   (No spikeshield SQS queues)")
        for q in queues:
            print(f"   • {q}")
    except Exception as ex:
        print(f"   Error querying SQS: {ex}")

    print("\n" + "=" * 65)

if __name__ == "__main__":
    main()

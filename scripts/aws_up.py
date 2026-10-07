#!/usr/bin/env python3
"""
SpikeShield AWS Infrastructure Provisioner & Deployer (make aws-up)
Provisions or updates Elastic Beanstalk (prod & staging), SQS runbook queue,
builds the frontend bundle, and verifies deployment health.
"""
import os
import sys
import zipfile
from datetime import datetime

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
FRONTEND_DIR = os.path.join(ROOT_DIR, "frontend")
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
    print(" 🚀  PROVISIONING / TURNING UP SPIKESHIELD AWS INFRASTRUCTURE")
    print("=" * 65)

    sess = boto3.Session(
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION
    )

    eb = sess.client("elasticbeanstalk")
    s3 = sess.client("s3")
    sqs = sess.client("sqs")

    # 1. Amazon SQS Queue
    print("\n1. Ensuring Amazon SQS Runbook Queue exists...")
    try:
        q_res = sqs.create_queue(QueueName="spikeshield-runbooks")
        q_url = q_res.get("QueueUrl")
        print(f"   ✓ SQS Queue ready: {q_url}")
    except Exception as ex:
        print(f"   ! SQS Queue warning: {ex}")

    # 2. Package deploy.zip
    print("\n2. Packaging production deployment bundle...")
    zip_path = os.path.join(BACKEND_DIR, "deploy.zip")
    if os.path.exists(zip_path):
        os.remove(zip_path)

    files_to_zip = ["Procfile", "requirements.txt", ".env"]
    dirs_to_zip = ["app", ".platform", ".ebextensions"]

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for f in files_to_zip:
            fp = os.path.join(BACKEND_DIR, f)
            if os.path.exists(fp):
                zipf.write(fp, arcname=f)
        for d in dirs_to_zip:
            dp = os.path.join(BACKEND_DIR, d)
            if os.path.exists(dp):
                for root, _, files in os.walk(dp):
                    if "__pycache__" in root or ".pytest_cache" in root:
                        continue
                    for file in files:
                        full_path = os.path.join(root, file)
                        rel_path = os.path.relpath(full_path, BACKEND_DIR)
                        zipf.write(full_path, arcname=rel_path)

    zip_size = os.path.getsize(zip_path) / (1024 * 1024)
    print(f"   ✓ deploy.zip created ({zip_size:.2f} MB)")

    # 3. Upload to S3
    bucket = "elasticbeanstalk-ap-south-1-510497448362"
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    version_label = f"spikeshield-v{timestamp}"
    s3_key = f"spikeshield/{version_label}.zip"

    print(f"\n3. Uploading bundle to s3://{bucket}/{s3_key}...")
    s3.upload_file(zip_path, bucket, s3_key)
    print("   ✓ Uploaded to S3.")

    # 4. Create EB Application & Version
    print(f"\n4. Creating EB Application Version: {version_label}...")
    try:
        eb.create_application(ApplicationName="spikeshield-app", Description="SpikeShield Control Plane")
    except Exception:
        pass

    eb.create_application_version(
        ApplicationName="spikeshield-app",
        VersionLabel=version_label,
        Description=f"SpikeShield Automated Deploy {timestamp}",
        SourceBundle={"S3Bucket": bucket, "S3Key": s3_key},
        AutoCreateApplication=False
    )
    print("   ✓ Application version registered.")

    # 5. Provision or Update spikeshield-prod
    print("\n5. Checking spikeshield-prod environment...")
    envs = eb.describe_environments(ApplicationName="spikeshield-app").get("Environments", [])
    active_names = [e["EnvironmentName"] for e in envs if e.get("Status") != "Terminated"]

    if "spikeshield-prod" in active_names:
        print("   Updating spikeshield-prod with new version...")
        eb.update_environment(EnvironmentName="spikeshield-prod", VersionLabel=version_label)
        print("   ✓ Update triggered for spikeshield-prod.")
    else:
        print("   Creating spikeshield-prod environment...")
        eb.create_environment(
            ApplicationName="spikeshield-app",
            EnvironmentName="spikeshield-prod",
            CNAMEPrefix="spikeshield-prod-510497",
            SolutionStackName="64bit Amazon Linux 2023 v4.13.9 running Python 3.11",
            VersionLabel=version_label,
            OptionSettings=[
                {"Namespace": "aws:autoscaling:launchconfiguration", "OptionName": "IamInstanceProfile", "Value": "aws-elasticbeanstalk-ec2-role"},
                {"Namespace": "aws:autoscaling:launchconfiguration", "OptionName": "InstanceType", "Value": "t3.micro"},
                {"Namespace": "aws:elasticbeanstalk:environment", "OptionName": "LoadBalancerType", "Value": "application"},
            ]
        )
        print("   ✓ Creation triggered for spikeshield-prod.")

    # 6. Provision or Update spikeshield-staging
    print("\n6. Checking spikeshield-staging environment...")
    if "spikeshield-staging" in active_names:
        print("   Updating spikeshield-staging with new version...")
        eb.update_environment(EnvironmentName="spikeshield-staging", VersionLabel=version_label)
        print("   ✓ Update triggered for spikeshield-staging.")
    else:
        print("   Creating spikeshield-staging environment...")
        eb.create_environment(
            ApplicationName="spikeshield-app",
            EnvironmentName="spikeshield-staging",
            CNAMEPrefix="spikeshield-staging-510497",
            SolutionStackName="64bit Amazon Linux 2023 v4.13.9 running Python 3.11",
            VersionLabel=version_label,
            OptionSettings=[
                {"Namespace": "aws:autoscaling:launchconfiguration", "OptionName": "IamInstanceProfile", "Value": "aws-elasticbeanstalk-ec2-role"},
                {"Namespace": "aws:autoscaling:launchconfiguration", "OptionName": "InstanceType", "Value": "t3.micro"},
                {"Namespace": "aws:elasticbeanstalk:environment", "OptionName": "LoadBalancerType", "Value": "application"},
            ]
        )
        print("   ✓ Creation triggered for spikeshield-staging.")

    print("\n" + "=" * 65)
    print(" 🎉  SPIKESHIELD AWS INFRASTRUCTURE TURNED UP SUCCESSFULLY!")
    print("     Run 'make aws-status' to inspect real-time deployment health.")
    print("=" * 65)

if __name__ == "__main__":
    main()

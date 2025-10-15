"""
Create S3 Bucket for Financial Trading Pipeline
==============================================

Creates the S3 bucket with proper configuration
"""

import boto3
from botocore.exceptions import ClientError
import sys
from pathlib import Path

# Add project root
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config import get_config

def create_s3_bucket():
    """Create S3 bucket with proper configuration"""
    
    config = get_config()
    
    print("=" * 70)
    print("  📦 CREATE S3 BUCKET")
    print("=" * 70)
    
    print(f"\n☁️  Configuration:")
    print(f"   Bucket: {config.s3.bucket_name}")
    print(f"   Region: {config.s3.region}")
    
    try:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=config.s3.access_key_id,
            aws_secret_access_key=config.s3.secret_access_key,
            region_name=config.s3.region
        )
        
        # Check if bucket exists
        try:
            s3_client.head_bucket(Bucket=config.s3.bucket_name)
            print(f"\n✅ Bucket already exists: {config.s3.bucket_name}")
            return True
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                print(f"\n📦 Creating bucket...")
            else:
                raise
        
        # Create bucket
        if config.s3.region == 'us-east-1':
            s3_client.create_bucket(Bucket=config.s3.bucket_name)
        else:
            s3_client.create_bucket(
                Bucket=config.s3.bucket_name,
                CreateBucketConfiguration={'LocationConstraint': config.s3.region}
            )
        
        print(f"✅ Bucket created: {config.s3.bucket_name}")
        
        # Enable versioning
        print(f"\n🔄 Enabling versioning...")
        s3_client.put_bucket_versioning(
            Bucket=config.s3.bucket_name,
            VersioningConfiguration={'Status': 'Enabled'}
        )
        print("✅ Versioning enabled")
        
        # Set lifecycle policy
        if config.s3.transition_to_ia_days or config.s3.transition_to_glacier_days:
            print(f"\n📅 Setting lifecycle policy...")
            
            rules = []
            
            if config.s3.transition_to_ia_days:
                rules.append({
                    'ID': 'TransitionToIA',
                    'Status': 'Enabled',
                    'Prefix': '',
                    'Transitions': [{
                        'Days': config.s3.transition_to_ia_days,
                        'StorageClass': 'STANDARD_IA'
                    }]
                })
            
            if config.s3.transition_to_glacier_days:
                rules.append({
                    'ID': 'TransitionToGlacier',
                    'Status': 'Enabled',
                    'Prefix': '',
                    'Transitions': [{
                        'Days': config.s3.transition_to_glacier_days,
                        'StorageClass': 'GLACIER'
                    }]
                })
            
            if rules:
                s3_client.put_bucket_lifecycle_configuration(
                    Bucket=config.s3.bucket_name,
                    LifecycleConfiguration={'Rules': rules}
                )
                print("✅ Lifecycle policy set")
        
        # Create folder structure
        print(f"\n📁 Creating folder structure...")
        folders = [
            f"{config.s3.raw_prefix}/crypto/",
            f"{config.s3.raw_prefix}/stock/",
            f"{config.s3.processed_prefix}/crypto/",
            f"{config.s3.processed_prefix}/stock/",
            f"{config.s3.analytics_prefix}/"
        ]
        
        for folder in folders:
            s3_client.put_object(Bucket=config.s3.bucket_name, Key=folder)
        
        print(f"✅ Created {len(folders)} folders")
        
        print("\n🎉 S3 bucket setup complete!")
        print(f"\n📍 Bucket URL: https://s3.console.aws.amazon.com/s3/buckets/{config.s3.bucket_name}")
        print(f"\n💡 Next steps:")
        print(f"   1. Run the pipeline test again: python utilities/testing/full_pipeline_test.py")
        print(f"   2. Data will be automatically uploaded to S3")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print(f"\n💡 Troubleshooting:")
        print(f"   • Check AWS credentials in config.json")
        print(f"   • Verify IAM permissions for S3")
        print(f"   • Bucket name must be globally unique")
        print(f"   • Try a different bucket name in user_config.py")
        return False

if __name__ == "__main__":
    success = create_s3_bucket()
    sys.exit(0 if success else 1)

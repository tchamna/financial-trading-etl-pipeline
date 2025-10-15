"""
Check S3 Bucket Access
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import get_config
import boto3
from botocore.exceptions import ClientError

config = get_config()

print("=" * 70)
print("🪣 CHECKING S3 BUCKET ACCESS")
print("=" * 70)

target_bucket = config.s3.bucket_name

try:
    s3_client = boto3.client(
        's3',
        aws_access_key_id=config.s3.access_key_id,
        aws_secret_access_key=config.s3.secret_access_key,
        region_name=config.s3.region
    )
    
    print(f"\n🔍 Checking bucket: {target_bucket}")
    
    # Try to access the bucket directly (doesn't require ListAllMyBuckets permission)
    try:
        # Check if bucket exists by trying to get its location
        location = s3_client.get_bucket_location(Bucket=target_bucket)
        region = location['LocationConstraint'] or 'us-east-1'
        print(f"✅ Bucket exists!")
        print(f"   Region: {region}")
        
        # Try to list objects
        result = s3_client.list_objects_v2(Bucket=target_bucket, MaxKeys=10)
        if 'Contents' in result:
            count = result['KeyCount']
            print(f"   Objects in bucket: {count}")
            print(f"\n   📁 Recent files:")
            for obj in result.get('Contents', [])[:10]:
                size_kb = obj['Size'] / 1024
                print(f"      • {obj['Key']} ({size_kb:.1f} KB)")
        else:
            print(f"   📭 Bucket is empty")
        
        # Try to upload a test file
        print(f"\n🧪 Testing write access...")
        test_key = "test/pipeline_test.txt"
        test_content = f"Pipeline test - {config.config_file}"
        
        s3_client.put_object(
            Bucket=target_bucket,
            Key=test_key,
            Body=test_content.encode('utf-8')
        )
        print(f"✅ Write access confirmed!")
        print(f"   Test file: s3://{target_bucket}/{test_key}")
        
        # Clean up test file
        s3_client.delete_object(Bucket=target_bucket, Key=test_key)
        print(f"   Test file cleaned up")
        
        print(f"\n✅✅ Bucket '{target_bucket}' is ready to use!")
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'NoSuchBucket':
            print(f"❌ Bucket does not exist")
            print(f"\n💡 Creating bucket '{target_bucket}'...")
            try:
                if config.s3.region == 'us-east-1':
                    s3_client.create_bucket(Bucket=target_bucket)
                else:
                    s3_client.create_bucket(
                        Bucket=target_bucket,
                        CreateBucketConfiguration={'LocationConstraint': config.s3.region}
                    )
                print(f"✅ Bucket created successfully!")
            except ClientError as create_error:
                if create_error.response['Error']['Code'] == 'BucketAlreadyExists':
                    print(f"❌ Bucket name is taken by another AWS account")
                    print(f"\n💡 Solution: Change S3_BUCKET_NAME in user_config.py to:")
                    print(f"   S3_BUCKET_NAME = 'financial-trading-tchamna-{config.s3.region}'")
                else:
                    print(f"❌ Could not create bucket: {create_error}")
        elif error_code == 'AccessDenied':
            print(f"❌ Access denied to bucket")
            print(f"   Your IAM user may not have permissions")
        else:
            print(f"❌ Error accessing bucket: {e}")
    
except ClientError as e:
    print(f"\n❌ AWS Error: {e}")
    print(f"\n💡 Check:")
    print(f"   • AWS credentials in config.json")
    print(f"   • IAM permissions for S3")
    
except Exception as e:
    print(f"\n❌ Error: {e}")

print("=" * 70)

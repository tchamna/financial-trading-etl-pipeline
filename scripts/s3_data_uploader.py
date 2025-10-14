"""
AWS S3 Data Uploader for Financial Trading ETL Pipeline
======================================================

Author: Shck Tchamna (tchamna@gmail.com)
Inspired by: https://github.com/ravishankar324/Washington-state-electric-vehicles-ETL-pipeline
Transformed using Agentic AI assistance

This module handles uploading processed financial data to AWS S3 for cloud storage
and integration with other AWS services like EMR, Athena, and Snowflake.
"""

import os
import sys
import json
import boto3
import pandas as pd
from datetime import datetime, timezone
from typing import Dict, List, Optional, Union
import logging
from botocore.exceptions import ClientError, NoCredentialsError
import gzip
import io

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import configuration
from config import get_config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class S3DataUploader:
    """Handles uploading financial data to AWS S3 with proper partitioning and compression."""
    
    def __init__(self, 
                 bucket_name: str,
                 aws_access_key_id: Optional[str] = None,
                 aws_secret_access_key: Optional[str] = None,
                 region_name: str = 'us-east-1'):
        """
        Initialize S3 uploader with AWS credentials
        
        Args:
            bucket_name: S3 bucket name for storing data
            aws_access_key_id: AWS access key (optional, can use env vars)
            aws_secret_access_key: AWS secret key (optional, can use env vars)
            region_name: AWS region
        """
        self.bucket_name = bucket_name
        self.region_name = region_name
        
        # Initialize S3 client
        try:
            session_kwargs = {'region_name': region_name}
            if aws_access_key_id and aws_secret_access_key:
                session_kwargs.update({
                    'aws_access_key_id': aws_access_key_id,
                    'aws_secret_access_key': aws_secret_access_key
                })
            
            self.s3_client = boto3.client('s3', **session_kwargs)
            self.s3_resource = boto3.resource('s3', **session_kwargs)
            
            # Verify bucket access
            self._verify_bucket_access()
            
        except NoCredentialsError:
            logger.error("AWS credentials not found. Please configure credentials.")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize S3 client: {e}")
            raise

    def _verify_bucket_access(self) -> bool:
        """Verify that the S3 bucket exists and is accessible"""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            logger.info(f"✅ Successfully connected to S3 bucket: {self.bucket_name}")
            return True
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                logger.warning(f"Bucket {self.bucket_name} not found. Attempting to create...")
                return self._create_bucket()
            else:
                logger.error(f"Error accessing bucket {self.bucket_name}: {e}")
                raise

    def _create_bucket(self) -> bool:
        """Create S3 bucket if it doesn't exist"""
        try:
            if self.region_name == 'us-east-1':
                self.s3_client.create_bucket(Bucket=self.bucket_name)
            else:
                self.s3_client.create_bucket(
                    Bucket=self.bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': self.region_name}
                )
            
            # Enable versioning for data protection
            self.s3_client.put_bucket_versioning(
                Bucket=self.bucket_name,
                VersioningConfiguration={'Status': 'Enabled'}
            )
            
            # Set lifecycle policy for cost optimization
            self._set_lifecycle_policy()
            
            logger.info(f"✅ Created S3 bucket: {self.bucket_name}")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to create bucket {self.bucket_name}: {e}")
            return False

    def _set_lifecycle_policy(self):
        """Set lifecycle policy for cost optimization"""
        lifecycle_policy = {
            'Rules': [
                {
                    'ID': 'financial_data_lifecycle',
                    'Status': 'Enabled',
                    'Filter': {'Prefix': 'processed/'},
                    'Transitions': [
                        {
                            'Days': 30,
                            'StorageClass': 'STANDARD_IA'  # Move to Infrequent Access after 30 days
                        },
                        {
                            'Days': 90,
                            'StorageClass': 'GLACIER'  # Archive after 90 days
                        }
                    ]
                },
                {
                    'ID': 'raw_data_lifecycle',
                    'Status': 'Enabled',
                    'Filter': {'Prefix': 'raw/'},
                    'Transitions': [
                        {
                            'Days': 7,
                            'StorageClass': 'STANDARD_IA'
                        },
                        {
                            'Days': 30,
                            'StorageClass': 'GLACIER'
                        }
                    ]
                }
            ]
        }
        
        try:
            self.s3_client.put_bucket_lifecycle_configuration(
                Bucket=self.bucket_name,
                LifecycleConfiguration=lifecycle_policy
            )
            logger.info("✅ Lifecycle policy configured for cost optimization")
        except ClientError as e:
            logger.warning(f"Could not set lifecycle policy: {e}")

    def upload_stock_data(self, 
                         stock_data: Union[pd.DataFrame, Dict, List],
                         data_type: str = 'processed',
                         compress: bool = True) -> str:
        """
        Upload stock market data to S3
        
        Args:
            stock_data: Stock data as DataFrame, dict, or list
            data_type: 'raw' or 'processed'
            compress: Whether to compress the data
            
        Returns:
            S3 key path where data was uploaded
        """
        timestamp = datetime.now(timezone.utc)
        
        # Create partitioned path: data_type/year/month/day/hour/
        s3_key = (
            f"{data_type}/stocks/"
            f"year={timestamp.year}/"
            f"month={timestamp.month:02d}/"
            f"day={timestamp.day:02d}/"
            f"hour={timestamp.hour:02d}/"
            f"stock_data_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        )
        
        if compress:
            s3_key += '.gz'
        
        return self._upload_json_data(stock_data, s3_key, compress)

    def upload_crypto_data(self, 
                          crypto_data: Union[pd.DataFrame, Dict, List],
                          data_type: str = 'processed',
                          compress: bool = True) -> str:
        """
        Upload cryptocurrency data to S3
        
        Args:
            crypto_data: Crypto data as DataFrame, dict, or list
            data_type: 'raw' or 'processed'
            compress: Whether to compress the data
            
        Returns:
            S3 key path where data was uploaded
        """
        timestamp = datetime.now(timezone.utc)
        
        s3_key = (
            f"{data_type}/crypto/"
            f"year={timestamp.year}/"
            f"month={timestamp.month:02d}/"
            f"day={timestamp.day:02d}/"
            f"hour={timestamp.hour:02d}/"
            f"crypto_data_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        )
        
        if compress:
            s3_key += '.gz'
        
        return self._upload_json_data(crypto_data, s3_key, compress)

    def upload_technical_analysis(self, 
                                analysis_data: Union[pd.DataFrame, Dict, List],
                                asset_type: str = 'mixed',
                                compress: bool = True) -> str:
        """
        Upload technical analysis results to S3
        
        Args:
            analysis_data: Technical analysis data
            asset_type: 'stocks', 'crypto', or 'mixed'
            compress: Whether to compress the data
            
        Returns:
            S3 key path where data was uploaded
        """
        timestamp = datetime.now(timezone.utc)
        
        s3_key = (
            f"processed/technical_analysis/{asset_type}/"
            f"year={timestamp.year}/"
            f"month={timestamp.month:02d}/"
            f"day={timestamp.day:02d}/"
            f"technical_analysis_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        )
        
        if compress:
            s3_key += '.gz'
        
        return self._upload_json_data(analysis_data, s3_key, compress)

    def upload_portfolio_data(self, 
                            portfolio_data: Union[pd.DataFrame, Dict, List],
                            portfolio_name: str = 'default',
                            compress: bool = True) -> str:
        """
        Upload portfolio analysis data to S3
        
        Args:
            portfolio_data: Portfolio data
            portfolio_name: Name of the portfolio
            compress: Whether to compress the data
            
        Returns:
            S3 key path where data was uploaded
        """
        timestamp = datetime.now(timezone.utc)
        
        s3_key = (
            f"processed/portfolios/{portfolio_name}/"
            f"year={timestamp.year}/"
            f"month={timestamp.month:02d}/"
            f"day={timestamp.day:02d}/"
            f"portfolio_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        )
        
        if compress:
            s3_key += '.gz'
        
        return self._upload_json_data(portfolio_data, s3_key, compress)

    def _upload_json_data(self, 
                         data: Union[pd.DataFrame, Dict, List],
                         s3_key: str,
                         compress: bool = True) -> str:
        """
        Helper method to upload JSON data to S3
        
        Args:
            data: Data to upload
            s3_key: S3 object key
            compress: Whether to compress the data
            
        Returns:
            S3 key path where data was uploaded
        """
        try:
            # Convert data to JSON format
            if isinstance(data, pd.DataFrame):
                json_data = data.to_json(orient='records', date_format='iso')
            else:
                json_data = json.dumps(data, default=str, indent=2)
            
            # Prepare data for upload
            if compress:
                # Compress data using gzip
                buffer = io.BytesIO()
                with gzip.GzipFile(fileobj=buffer, mode='wb') as gz_file:
                    gz_file.write(json_data.encode('utf-8'))
                data_to_upload = buffer.getvalue()
                content_encoding = 'gzip'
                content_type = 'application/json'
            else:
                data_to_upload = json_data.encode('utf-8')
                content_encoding = None
                content_type = 'application/json'
            
            # Upload to S3
            extra_args = {
                'ContentType': content_type,
                'Metadata': {
                    'upload_timestamp': datetime.now(timezone.utc).isoformat(),
                    'data_format': 'json',
                    'source': 'financial_etl_pipeline'
                }
            }
            
            if content_encoding:
                extra_args['ContentEncoding'] = content_encoding
            
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=data_to_upload,
                **extra_args
            )
            
            s3_path = f"s3://{self.bucket_name}/{s3_key}"
            file_size = len(data_to_upload) / 1024  # Size in KB
            
            logger.info(f"✅ Uploaded to S3: {s3_path} ({file_size:.2f} KB)")
            return s3_path
            
        except Exception as e:
            logger.error(f"Failed to upload data to S3: {e}")
            raise

    def upload_parquet_data(self, 
                           df: pd.DataFrame,
                           s3_key: str,
                           compression: str = 'snappy') -> str:
        """
        Upload DataFrame as Parquet format for better performance with analytics tools
        
        Args:
            df: Pandas DataFrame to upload
            s3_key: S3 object key (without .parquet extension)
            compression: Parquet compression algorithm
            
        Returns:
            S3 key path where data was uploaded
        """
        try:
            # Add .parquet extension
            if not s3_key.endswith('.parquet'):
                s3_key += '.parquet'
            
            # Convert to parquet in memory
            buffer = io.BytesIO()
            df.to_parquet(buffer, compression=compression, index=False)
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=buffer.getvalue(),
                ContentType='application/octet-stream',
                Metadata={
                    'upload_timestamp': datetime.now(timezone.utc).isoformat(),
                    'data_format': 'parquet',
                    'compression': compression,
                    'source': 'financial_etl_pipeline'
                }
            )
            
            s3_path = f"s3://{self.bucket_name}/{s3_key}"
            file_size = len(buffer.getvalue()) / 1024
            
            logger.info(f"✅ Uploaded Parquet to S3: {s3_path} ({file_size:.2f} KB)")
            return s3_path
            
        except Exception as e:
            logger.error(f"Failed to upload Parquet to S3: {e}")
            raise

    def list_objects(self, prefix: str = '', max_objects: int = 100) -> List[Dict]:
        """
        List objects in the S3 bucket with given prefix
        
        Args:
            prefix: S3 key prefix to filter objects
            max_objects: Maximum number of objects to return
            
        Returns:
            List of object information
        """
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix,
                MaxKeys=max_objects
            )
            
            objects = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    objects.append({
                        'key': obj['Key'],
                        'size': obj['Size'],
                        'last_modified': obj['LastModified'],
                        's3_path': f"s3://{self.bucket_name}/{obj['Key']}"
                    })
            
            return objects
            
        except Exception as e:
            logger.error(f"Failed to list S3 objects: {e}")
            return []

    def get_storage_metrics(self) -> Dict:
        """Get storage metrics for the bucket"""
        try:
            # Get bucket size and object count
            objects = self.list_objects(max_objects=1000)
            
            total_size = sum(obj['size'] for obj in objects)
            object_count = len(objects)
            
            # Group by data type
            metrics = {
                'total_objects': object_count,
                'total_size_mb': total_size / (1024 * 1024),
                'bucket_name': self.bucket_name,
                'by_data_type': {}
            }
            
            for obj in objects:
                data_type = obj['key'].split('/')[0] if '/' in obj['key'] else 'other'
                if data_type not in metrics['by_data_type']:
                    metrics['by_data_type'][data_type] = {'count': 0, 'size_mb': 0}
                
                metrics['by_data_type'][data_type]['count'] += 1
                metrics['by_data_type'][data_type]['size_mb'] += obj['size'] / (1024 * 1024)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to get storage metrics: {e}")
            return {}

def create_s3_uploader_from_env() -> S3DataUploader:
    """
    Create S3DataUploader instance using environment variables and configuration
    
    First tries to use configuration file, then falls back to environment variables:
    - AWS_S3_BUCKET_NAME: S3 bucket name
    - AWS_ACCESS_KEY_ID: AWS access key
    - AWS_SECRET_ACCESS_KEY: AWS secret key
    - AWS_DEFAULT_REGION: AWS region (optional, defaults to us-east-1)
    
    Returns:
        Configured S3DataUploader instance
    """
    # Try to use configuration first
    try:
        config = get_config()
        if config.s3.enabled:
            return S3DataUploader(
                bucket_name=config.s3.bucket_name,
                aws_access_key_id=config.s3.access_key_id,
                aws_secret_access_key=config.s3.secret_access_key,
                region_name=config.s3.region
            )
    except Exception as e:
        logger.warning(f"Could not use config for S3 setup: {e}")
    
    # Fall back to environment variables
    bucket_name = os.getenv('AWS_S3_BUCKET_NAME')
    if not bucket_name:
        raise ValueError("AWS_S3_BUCKET_NAME environment variable is required (or enable S3 in config)")
    
    aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
    aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
    region_name = os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
    
    return S3DataUploader(
        bucket_name=bucket_name,
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region_name=region_name
    )

# Example usage
if __name__ == "__main__":
    """Example usage of S3DataUploader"""
    
    # Sample financial data
    sample_stock_data = [
        {
            "symbol": "AAPL",
            "timestamp": "2025-10-13T14:30:00Z",
            "price": 245.40,
            "volume": 1500000,
            "market_cap": 3800000000000
        },
        {
            "symbol": "GOOGL", 
            "timestamp": "2025-10-13T14:30:00Z",
            "price": 235.77,
            "volume": 1200000,
            "market_cap": 2900000000000
        }
    ]
    
    try:
        # Initialize uploader
        uploader = create_s3_uploader_from_env()
        
        # Upload stock data
        s3_path = uploader.upload_stock_data(sample_stock_data)
        print(f"Uploaded stock data to: {s3_path}")
        
        # Get storage metrics
        metrics = uploader.get_storage_metrics()
        print(f"Storage metrics: {json.dumps(metrics, indent=2)}")
        
    except Exception as e:
        print(f"Error: {e}")
        print("\nMake sure to set the following environment variables:")
        print("- AWS_S3_BUCKET_NAME")
        print("- AWS_ACCESS_KEY_ID") 
        print("- AWS_SECRET_ACCESS_KEY")
        print("- AWS_DEFAULT_REGION (optional)")
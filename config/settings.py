"""
Configuration Management for Financial Trading ETL Pipeline

This module centralizes all configuration settings for the pipeline,
including database connections, API settings, S3 integration, and processing options.

Author: Shck Tchamna
Email: tchamna@gmail.com
"""

import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path
import json


@dataclass
class DatabaseConfig:
    """Database configuration settings"""
    host: str = "localhost"
    port: int = 5432
    database: str = "financial_data"
    username: str = "postgres"
    password: str = "password"
    schema: str = "public"
    
    @property
    def connection_string(self) -> str:
        """Get PostgreSQL connection string"""
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"


@dataclass
class StorageConfig:
    """Data storage configuration settings"""
    # Storage locations
    enable_local_storage: bool = True
    enable_s3_storage: bool = True
    
    # Local storage settings
    local_data_directory: str = "data"
    keep_local_days: int = 7  # How many days to keep local files
    
    # Format options
    save_json_format: bool = True
    save_parquet_format: bool = True
    
    def __post_init__(self):
        """Validate storage configuration"""
        if not self.enable_local_storage and not self.enable_s3_storage:
            raise ValueError("At least one storage option (local or S3) must be enabled")


@dataclass
class S3Config:
    """AWS S3 configuration settings"""
    enabled: bool = False
    bucket_name: str = "financial-trading-data-lake"
    region: str = "us-east-1"
    access_key_id: Optional[str] = None
    secret_access_key: Optional[str] = None
    
    # S3 path structure
    raw_prefix: str = "raw"
    processed_prefix: str = "processed"
    analytics_prefix: str = "analytics"
    
    # Storage settings
    enable_compression: bool = True
    enable_partitioning: bool = True
    storage_class: str = "STANDARD"
    
    # Lifecycle settings
    transition_to_ia_days: int = 30
    transition_to_glacier_days: int = 90
    
    def __post_init__(self):
        """Load AWS credentials from environment if not provided"""
        if not self.access_key_id:
            self.access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
        if not self.secret_access_key:
            self.secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')


@dataclass
class SnowflakeConfig:
    """Snowflake configuration settings"""
    account: str = ""
    username: str = ""
    password: str = ""
    database: str = "FINANCIAL_DATA"
    warehouse: str = "COMPUTE_WH"
    schema: str = "PUBLIC"
    role: str = "ACCOUNTADMIN"
    
    def __post_init__(self):
        """Load Snowflake credentials from environment if not provided"""
        if not self.account:
            self.account = os.getenv('SNOWFLAKE_ACCOUNT', self.account)
        if not self.username:
            self.username = os.getenv('SNOWFLAKE_USER', self.username)
        if not self.password:
            self.password = os.getenv('SNOWFLAKE_PASSWORD', self.password)


@dataclass
class APIConfig:
    """API configuration settings"""
    # Alpha Vantage
    alpha_vantage_api_key: Optional[str] = None
    alpha_vantage_base_url: str = "https://www.alphavantage.co/query"
    alpha_vantage_timeout: int = 30
    
    # CoinGecko
    coingecko_base_url: str = "https://api.coingecko.com/api/v3"
    coingecko_timeout: int = 30
    
    # Yahoo Finance
    yahoo_finance_timeout: int = 30
    
    # Rate limiting
    requests_per_minute: int = 5
    max_retries: int = 3
    retry_delay: int = 1
    
    def __post_init__(self):
        """Load API keys from environment if not provided"""
        if not self.alpha_vantage_api_key:
            self.alpha_vantage_api_key = os.getenv('ALPHA_VANTAGE_API_KEY')


@dataclass
@dataclass  
class CryptoMappingConfig:
    """Cryptocurrency symbol mappings for different APIs"""
    
    # Master symbol mappings - ticker to API identifiers
    symbol_mappings: Dict[str, Dict[str, str]] = None
    
    def __post_init__(self):
        """Initialize default symbol mappings"""
        if self.symbol_mappings is None:
            self.symbol_mappings = {
                # === MAJOR CRYPTOCURRENCIES (Top 10 by Market Cap) ===
                'BTC': {
                    'name': 'bitcoin',
                    'binance': 'BTCUSDT',
                    'cryptocompare': 'BTC',
                    'kraken': 'XXBTZUSD'
                },
                'ETH': {
                    'name': 'ethereum',
                    'binance': 'ETHUSDT',
                    'cryptocompare': 'ETH',
                    'kraken': 'XETHZUSD'
                },
                'USDT': {
                    'name': 'tether',
                    'binance': 'USDCUSDT',
                    'cryptocompare': 'USDT',
                    'kraken': 'USDTZUSD'
                },
                'BNB': {
                    'name': 'binancecoin',
                    'binance': 'BNBUSDT',
                    'cryptocompare': 'BNB',
                    'kraken': 'BNBUSD'
                },
                'SOL': {
                    'name': 'solana',
                    'binance': 'SOLUSDT',
                    'cryptocompare': 'SOL',
                    'kraken': 'SOLUSD'
                },
                'USDC': {
                    'name': 'usd-coin',
                    'binance': 'USDCUSDT',
                    'cryptocompare': 'USDC',
                    'kraken': 'USDCUSD'
                },
                'XRP': {
                    'name': 'ripple',
                    'binance': 'XRPUSDT',
                    'cryptocompare': 'XRP',
                    'kraken': 'XXRPZUSD'
                },
                'DOGE': {
                    'name': 'dogecoin',
                    'binance': 'DOGEUSDT',
                    'cryptocompare': 'DOGE',
                    'kraken': 'DOGEUSD'
                },
                'ADA': {
                    'name': 'cardano',
                    'binance': 'ADAUSDT',
                    'cryptocompare': 'ADA',
                    'kraken': 'ADAUSD'
                },
                'TRX': {
                    'name': 'tron',
                    'binance': 'TRXUSDT',
                    'cryptocompare': 'TRX',
                    'kraken': 'TRXUSD'
                },
                
                # === LAYER 1 BLOCKCHAINS ===
                'AVAX': {
                    'name': 'avalanche-2',
                    'binance': 'AVAXUSDT',
                    'cryptocompare': 'AVAX',
                    'kraken': 'AVAXUSD'
                },
                'DOT': {
                    'name': 'polkadot',
                    'binance': 'DOTUSDT',
                    'cryptocompare': 'DOT',
                    'kraken': 'DOTUSD'
                },
                'MATIC': {
                    'name': 'matic-network',
                    'binance': 'MATICUSDT',
                    'cryptocompare': 'MATIC',
                    'kraken': 'MATICUSD'
                },
                'ALGO': {
                    'name': 'algorand',
                    'binance': 'ALGOUSDT',
                    'cryptocompare': 'ALGO',
                    'kraken': 'ALGOUSD'
                },
                'ATOM': {
                    'name': 'cosmos',
                    'binance': 'ATOMUSDT',
                    'cryptocompare': 'ATOM',
                    'kraken': 'ATOMUSD'
                },
                'NEAR': {
                    'name': 'near',
                    'binance': 'NEARUSDT',
                    'cryptocompare': 'NEAR',
                    'kraken': 'NEARUSD'
                },
                'FTM': {
                    'name': 'fantom',
                    'binance': 'FTMUSDT',
                    'cryptocompare': 'FTM',
                    'kraken': 'FTMUSD'
                },
                
                # === DEFI TOKENS ===
                'UNI': {
                    'name': 'uniswap',
                    'binance': 'UNIUSDT',
                    'cryptocompare': 'UNI',
                    'kraken': 'UNIUSD'
                },
                'LINK': {
                    'name': 'chainlink',
                    'binance': 'LINKUSDT',
                    'cryptocompare': 'LINK',
                    'kraken': 'LINKUSD'
                },
                'AAVE': {
                    'name': 'aave',
                    'binance': 'AAVEUSDT',
                    'cryptocompare': 'AAVE',
                    'kraken': 'AAVEUSD'
                },
                'CRV': {
                    'name': 'curve-dao-token',
                    'binance': 'CRVUSDT',
                    'cryptocompare': 'CRV',
                    'kraken': 'CRVUSD'
                },
                'COMP': {
                    'name': 'compound-governance-token',
                    'binance': 'COMPUSDT',
                    'cryptocompare': 'COMP',
                    'kraken': 'COMPUSD'
                },
                'SUSHI': {
                    'name': 'sushi',
                    'binance': 'SUSHIUSDT',
                    'cryptocompare': 'SUSHI',
                    'kraken': 'SUSHIUSD'
                },
                '1INCH': {
                    'name': '1inch',
                    'binance': '1INCHUSDT',
                    'cryptocompare': '1INCH',
                    'kraken': '1INCHUSD'
                },
                
                # === LEGACY/ESTABLISHED COINS ===
                'LTC': {
                    'name': 'litecoin',
                    'binance': 'LTCUSDT',
                    'cryptocompare': 'LTC',
                    'kraken': 'XLTCZUSD'
                },
                'BCH': {
                    'name': 'bitcoin-cash',
                    'binance': 'BCHUSDT',
                    'cryptocompare': 'BCH',
                    'kraken': 'BCHEUR'
                },
                'ETC': {
                    'name': 'ethereum-classic',
                    'binance': 'ETCUSDT',
                    'cryptocompare': 'ETC',
                    'kraken': 'XETCZUSD'
                },
                'XMR': {
                    'name': 'monero',
                    'binance': 'XMRUSDT',
                    'cryptocompare': 'XMR',
                    'kraken': 'XXMRZUSD'
                },
                'ZEC': {
                    'name': 'zcash',
                    'binance': 'ZECUSDT',
                    'cryptocompare': 'ZEC',
                    'kraken': 'XZECZUSD'
                },
                'DASH': {
                    'name': 'dash',
                    'binance': 'DASHUSDT',
                    'cryptocompare': 'DASH',
                    'kraken': 'DASHUSD'
                },
                
                # === LAYER 2 & SCALING SOLUTIONS ===
                'ARB': {
                    'name': 'arbitrum',
                    'binance': 'ARBUSDT',
                    'cryptocompare': 'ARB',
                    'kraken': 'ARBUSD'
                },
                'OP': {
                    'name': 'optimism',
                    'binance': 'OPUSDT',
                    'cryptocompare': 'OP',
                    'kraken': 'OPUSD'
                },
                
                # === MEME COINS (Popular Trading) ===
                'SHIB': {
                    'name': 'shiba-inu',
                    'binance': 'SHIBUSDT',
                    'cryptocompare': 'SHIB',
                    'kraken': 'SHIBUSD'
                },
                'PEPE': {
                    'name': 'pepe',
                    'binance': 'PEPEUSDT',
                    'cryptocompare': 'PEPE',
                    'kraken': 'PEPEUSD'
                },
                
                # === AI & TECHNOLOGY TOKENS ===
                'FET': {
                    'name': 'fetch-ai',
                    'binance': 'FETUSDT',
                    'cryptocompare': 'FET',
                    'kraken': 'FETUSD'
                },
                'RENDER': {
                    'name': 'render-token',
                    'binance': 'RENDERUSDT',
                    'cryptocompare': 'RENDER',
                    'kraken': 'RENDERUSD'
                },
                
                # === GAMING & NFT TOKENS ===
                'SAND': {
                    'name': 'the-sandbox',
                    'binance': 'SANDUSDT',
                    'cryptocompare': 'SAND',
                    'kraken': 'SANDUSD'
                },
                'MANA': {
                    'name': 'decentraland',
                    'binance': 'MANAUSDT',
                    'cryptocompare': 'MANA',
                    'kraken': 'MANAUSD'
                },
                'AXS': {
                    'name': 'axie-infinity',
                    'binance': 'AXSUSDT',
                    'cryptocompare': 'AXS',
                    'kraken': 'AXSUSD'
                },
                
                # === EXCHANGE TOKENS ===
                'KCS': {
                    'name': 'kucoin-shares',
                    'binance': 'KCSUSDT',
                    'cryptocompare': 'KCS',
                    'kraken': 'KCSUSD'
                },
                'CRO': {
                    'name': 'crypto-com-chain',
                    'binance': 'CROUSDT',
                    'cryptocompare': 'CRO',
                    'kraken': 'CROUSD'
                }
            }
    
    def get_api_symbol(self, ticker: str) -> Optional[str]:
        """Get the API symbol (name) for a ticker"""
        if ticker in self.symbol_mappings:
            return self.symbol_mappings[ticker]['name']
        return None
    
    def get_binance_symbol(self, api_symbol: str) -> Optional[str]:
        """Get Binance symbol for an API symbol (name)"""
        for ticker, mappings in self.symbol_mappings.items():
            if mappings['name'] == api_symbol:
                return mappings['binance']
        return None
    
    def get_cryptocompare_symbol(self, api_symbol: str) -> Optional[str]:
        """Get CryptoCompare symbol for an API symbol (name)"""
        for ticker, mappings in self.symbol_mappings.items():
            if mappings['name'] == api_symbol:
                return mappings['cryptocompare']
        return None
    
    def get_kraken_symbol(self, api_symbol: str) -> Optional[str]:
        """Get Kraken symbol for an API symbol (name)"""
        for ticker, mappings in self.symbol_mappings.items():
            if mappings['name'] == api_symbol:
                return mappings['kraken']
        return None
    
    def get_supported_symbols(self) -> List[str]:
        """Get list of all supported cryptocurrency symbols"""
        return list(self.symbol_mappings.keys())
    
    def is_supported(self, symbol: str) -> bool:
        """Check if a cryptocurrency symbol is supported"""
        return symbol.upper() in self.symbol_mappings
    
    def get_mapping(self, symbol: str) -> Dict[str, str]:
        """Get complete mapping for a cryptocurrency symbol"""
        symbol = symbol.upper()
        if not self.is_supported(symbol):
            raise ValueError(f"Cryptocurrency symbol '{symbol}' is not supported. "
                           f"Supported symbols: {', '.join(self.get_supported_symbols())}")
        return self.symbol_mappings[symbol]


@dataclass
class ProcessingConfig:
    """Data processing configuration"""
    # Stock symbols to track
    stock_symbols: List[str] = None
    crypto_symbols: List[str] = None
    
    # Data collection settings
    collection_interval_seconds: int = 300  # 5 minutes
    batch_size: int = 100
    
    # Technical indicators
    enable_technical_analysis: bool = True
    sma_periods: List[int] = None
    ema_periods: List[int] = None
    
    # Data quality
    enable_data_validation: bool = True
    max_price_change_percent: float = 50.0  # Alert if price changes more than 50%
    
    # Portfolio settings
    enable_portfolio_tracking: bool = True
    default_portfolio_name: str = "tech_growth"
    
    def __post_init__(self):
        """Set default values for lists"""
        if self.stock_symbols is None:
            self.stock_symbols = ["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN", "NVDA", "META"]
        
        if self.crypto_symbols is None:
            self.crypto_symbols = ["BTC", "ETH", "SOL", "ADA", "DOT", "LINK", "UNI", "AVAX"]
        
        if self.sma_periods is None:
            self.sma_periods = [20, 50, 200]
        
        if self.ema_periods is None:
            self.ema_periods = [12, 26]


@dataclass
class LoggingConfig:
    """Logging configuration"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_to_file: bool = True
    log_file_path: str = "logs/pipeline.log"
    max_file_size_mb: int = 100
    backup_count: int = 5
    
    # Console logging
    log_to_console: bool = True
    console_level: str = "INFO"


@dataclass
class AirflowConfig:
    """Airflow configuration"""
    dag_id: str = "financial_data_pipeline"
    schedule_interval: str = "*/5 * * * *"  # Every 5 minutes
    max_active_runs: int = 1
    catchup: bool = False
    
    # Email notifications
    email_on_failure: bool = True
    email_on_retry: bool = False
    email_list: List[str] = None
    
    # Retries
    retries: int = 2
    retry_delay_minutes: int = 5
    
    def __post_init__(self):
        if self.email_list is None:
            self.email_list = ["tchamna@gmail.com"]


@dataclass
class MonitoringConfig:
    """Monitoring and alerting configuration"""
    enable_metrics: bool = True
    metrics_port: int = 8080
    
    # Performance thresholds
    max_processing_time_seconds: int = 600  # 10 minutes
    max_memory_usage_mb: int = 2048  # 2GB
    
    # Alerting
    enable_email_alerts: bool = True
    enable_slack_alerts: bool = False
    slack_webhook_url: Optional[str] = None


class PipelineConfig:
    """Main configuration class for the Financial Trading ETL Pipeline"""
    
    def __init__(self, config_file: Optional[str] = None):
        """Initialize configuration from file or environment variables"""
        self.config_file = config_file or os.getenv('PIPELINE_CONFIG_FILE', 'config/config.json')
        
        # Initialize all configuration sections
        self.storage = StorageConfig()
        self.database = DatabaseConfig()
        self.s3 = S3Config()
        self.snowflake = SnowflakeConfig()
        self.api = APIConfig()
        self.crypto_mappings = CryptoMappingConfig()
        self.processing = ProcessingConfig()
        self.logging = LoggingConfig()
        self.airflow = AirflowConfig()
        self.monitoring = MonitoringConfig()
        
        # Load configuration from file first (system defaults)
        self.load_from_file()
        
        # Load user configuration (user preferences override system defaults)  
        self.load_user_config()
        
        # Override with environment variables (highest priority)
        self.load_from_environment()
    
    def load_user_config(self):
        """Load user-friendly configuration from user_config.py"""
        try:
            from config.user import get_user_config
            user_config = get_user_config()
            
            # Apply user config to relevant sections
            if 'stock_symbols' in user_config:
                self.processing.stock_symbols = user_config['stock_symbols']
            
            if 'crypto_symbols' in user_config:
                self.processing.crypto_symbols = user_config['crypto_symbols']
            
            if 'collection_interval_minutes' in user_config:
                self.processing.collection_interval_seconds = user_config['collection_interval_minutes'] * 60
            
            if 'enable_local_storage' in user_config:
                self.storage.enable_local_storage = user_config['enable_local_storage']
            
            if 'enable_s3_storage' in user_config:
                self.storage.enable_s3_storage = user_config['enable_s3_storage']
                self.s3.enabled = user_config['enable_s3_storage']
            
            if 'save_json_format' in user_config:
                self.storage.save_json_format = user_config['save_json_format']
            
            if 'save_parquet_format' in user_config:
                self.storage.save_parquet_format = user_config['save_parquet_format']
            
            if 'local_data_directory' in user_config:
                self.storage.local_data_directory = user_config['local_data_directory']
            
            if 'keep_local_files_days' in user_config:
                self.storage.keep_local_days = user_config['keep_local_files_days']
            
            if 'enable_technical_analysis' in user_config:
                self.processing.enable_technical_analysis = user_config['enable_technical_analysis']
            
            if 'simple_moving_averages' in user_config:
                self.processing.sma_periods = user_config['simple_moving_averages']
            
            if 'exponential_moving_averages' in user_config:
                self.processing.ema_periods = user_config['exponential_moving_averages']
            
            if 'enable_portfolio_tracking' in user_config:
                self.processing.enable_portfolio_tracking = user_config['enable_portfolio_tracking']
            
            if 'default_portfolio_name' in user_config:
                self.processing.default_portfolio_name = user_config['default_portfolio_name']
            
            if 'price_alert_threshold' in user_config:
                self.processing.max_price_change_percent = user_config['price_alert_threshold']
            
            if 'api_requests_per_minute' in user_config:
                self.api.requests_per_minute = user_config['api_requests_per_minute']
            
            if 'max_api_retries' in user_config:
                self.api.max_retries = user_config['max_api_retries']
            
            if 's3_bucket_name' in user_config:
                self.s3.bucket_name = user_config['s3_bucket_name']
            
            if 'aws_region' in user_config:
                self.s3.region = user_config['aws_region']
            
            if 's3_storage_class' in user_config:
                self.s3.storage_class = user_config['s3_storage_class']
            
            if 'collection_schedule' in user_config:
                self.airflow.schedule_interval = user_config['collection_schedule']
            
            if 'enable_email_alerts' in user_config:
                self.airflow.email_on_failure = user_config['enable_email_alerts']
                self.monitoring.enable_email_alerts = user_config['enable_email_alerts']
            
            if 'email_addresses' in user_config:
                self.airflow.email_list = user_config['email_addresses']
            
            print("[OK] User configuration loaded from user_config.py")
            
        except ImportError:
            print("[WARN] user_config.py not found, using config.json defaults")
        except Exception as e:
            print(f"[WARN] Error loading user configuration: {e}")
            print("Using config.json defaults")
    
    def load_from_file(self):
        """Load configuration from JSON file"""
        config_path = Path(self.config_file)
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                # Update configuration sections
                if 'storage' in config_data:
                    self._update_dataclass(self.storage, config_data['storage'])
                
                if 'database' in config_data:
                    self._update_dataclass(self.database, config_data['database'])
                
                if 's3' in config_data:
                    self._update_dataclass(self.s3, config_data['s3'])
                
                if 'snowflake' in config_data:
                    self._update_dataclass(self.snowflake, config_data['snowflake'])
                
                if 'crypto_mappings' in config_data:
                    self._update_dataclass(self.crypto_mappings, config_data['crypto_mappings'])
                
                if 'api' in config_data:
                    self._update_dataclass(self.api, config_data['api'])
                
                if 'processing' in config_data:
                    self._update_dataclass(self.processing, config_data['processing'])
                
                if 'logging' in config_data:
                    self._update_dataclass(self.logging, config_data['logging'])
                
                if 'airflow' in config_data:
                    self._update_dataclass(self.airflow, config_data['airflow'])
                
                if 'monitoring' in config_data:
                    self._update_dataclass(self.monitoring, config_data['monitoring'])
                    
                print(f"Configuration loaded from {self.config_file}")
                
            except Exception as e:
                print(f"Error loading configuration file {self.config_file}: {e}")
                print("Using default configuration with environment variables")
    
    def load_from_environment(self):
        """Load configuration from environment variables"""
        # Database settings
        self.database.host = os.getenv('DB_HOST', self.database.host)
        self.database.port = int(os.getenv('DB_PORT', self.database.port))
        self.database.database = os.getenv('DB_NAME', self.database.database)
        self.database.username = os.getenv('DB_USER', self.database.username)
        self.database.password = os.getenv('DB_PASSWORD', self.database.password)
        
        # S3 settings (only override if env var is set)
        if os.getenv('S3_ENABLED'):
            self.s3.enabled = os.getenv('S3_ENABLED').lower() == 'true'
        self.s3.bucket_name = os.getenv('AWS_S3_BUCKET_NAME', self.s3.bucket_name)
        self.s3.region = os.getenv('AWS_DEFAULT_REGION', self.s3.region)
        
        # Processing settings
        if os.getenv('STOCK_SYMBOLS'):
            self.processing.stock_symbols = os.getenv('STOCK_SYMBOLS').split(',')
        
        if os.getenv('CRYPTO_SYMBOLS'):
            self.processing.crypto_symbols = os.getenv('CRYPTO_SYMBOLS').split(',')
        
        # Collection interval
        if os.getenv('COLLECTION_INTERVAL_SECONDS'):
            self.processing.collection_interval_seconds = int(os.getenv('COLLECTION_INTERVAL_SECONDS'))
    
    def _update_dataclass(self, dataclass_instance: Any, config_dict: Dict[str, Any]):
        """Update dataclass fields from dictionary"""
        for key, value in config_dict.items():
            if hasattr(dataclass_instance, key):
                setattr(dataclass_instance, key, value)
    
    def save_to_file(self, file_path: Optional[str] = None):
        """Save current configuration to JSON file"""
        file_path = file_path or self.config_file
        
        config_data = {
            'database': self._dataclass_to_dict(self.database),
            's3': self._dataclass_to_dict(self.s3),
            'api': self._dataclass_to_dict(self.api),
            'processing': self._dataclass_to_dict(self.processing),
            'logging': self._dataclass_to_dict(self.logging),
            'airflow': self._dataclass_to_dict(self.airflow),
            'monitoring': self._dataclass_to_dict(self.monitoring)
        }
        
        # Create directory if it doesn't exist
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w') as f:
            json.dump(config_data, f, indent=2, default=str)
        
        print(f"Configuration saved to {file_path}")
    
    def _dataclass_to_dict(self, dataclass_instance: Any) -> Dict[str, Any]:
        """Convert dataclass to dictionary"""
        result = {}
        for field_name, field_value in dataclass_instance.__dict__.items():
            if not field_name.startswith('_'):
                result[field_name] = field_value
        return result
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of issues"""
        issues = []
        
        # Validate required API keys
        if not self.api.alpha_vantage_api_key:
            issues.append("Alpha Vantage API key is required")
        
        # Validate S3 configuration if enabled
        if self.s3.enabled:
            if not self.s3.access_key_id:
                issues.append("AWS Access Key ID is required when S3 is enabled")
            if not self.s3.secret_access_key:
                issues.append("AWS Secret Access Key is required when S3 is enabled")
            if not self.s3.bucket_name:
                issues.append("S3 bucket name is required when S3 is enabled")
        
        # Validate database configuration
        if not self.database.password:
            issues.append("Database password is required")
        
        # Validate symbols lists
        if not self.processing.stock_symbols:
            issues.append("At least one stock symbol must be configured")
        
        if not self.processing.crypto_symbols:
            issues.append("At least one crypto symbol must be configured")
        
        return issues
    
    def get_summary(self) -> str:
        """Get configuration summary"""
        summary = f"""
Financial Trading ETL Pipeline Configuration Summary
==================================================

Database: {self.database.host}:{self.database.port}/{self.database.database}
S3 Integration: {'Enabled' if self.s3.enabled else 'Disabled'}
Stock Symbols: {', '.join(self.processing.stock_symbols[:5])}{'...' if len(self.processing.stock_symbols) > 5 else ''}
Crypto Symbols: {', '.join(self.processing.crypto_symbols[:5])}{'...' if len(self.processing.crypto_symbols) > 5 else ''}
Collection Interval: {self.processing.collection_interval_seconds} seconds
Technical Analysis: {'Enabled' if self.processing.enable_technical_analysis else 'Disabled'}
Portfolio Tracking: {'Enabled' if self.processing.enable_portfolio_tracking else 'Disabled'}

S3 Configuration:
- Bucket: {self.s3.bucket_name if self.s3.enabled else 'N/A'}
- Region: {self.s3.region if self.s3.enabled else 'N/A'}
- Compression: {'Enabled' if self.s3.enable_compression and self.s3.enabled else 'Disabled'}
- Partitioning: {'Enabled' if self.s3.enable_partitioning and self.s3.enabled else 'Disabled'}

Logging Level: {self.logging.level}
Airflow Schedule: {self.airflow.schedule_interval}
"""
        return summary


# Global configuration instance
config = PipelineConfig()


def get_config() -> PipelineConfig:
    """Get the global configuration instance"""
    return config


def reload_config(config_file: Optional[str] = None) -> PipelineConfig:
    """Reload configuration from file"""
    global config
    config = PipelineConfig(config_file)
    return config


# Convenience functions for common configuration access
def is_s3_enabled() -> bool:
    """Check if S3 integration is enabled"""
    return config.s3.enabled


def get_database_connection_string() -> str:
    """Get database connection string"""
    return config.database.connection_string


def get_stock_symbols() -> List[str]:
    """Get list of stock symbols to track"""
    return config.processing.stock_symbols


def get_crypto_symbols() -> List[str]:
    """Get list of crypto symbols to track"""
    return config.processing.crypto_symbols


if __name__ == "__main__":
    # Command line interface for configuration management
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "validate":
            issues = config.validate()
            if issues:
                print("Configuration Issues:")
                for issue in issues:
                    print(f"  - {issue}")
                sys.exit(1)
            else:
                print("Configuration is valid!")
        
        elif command == "summary":
            print(config.get_summary())
        
        elif command == "save":
            file_path = sys.argv[2] if len(sys.argv) > 2 else "config.json"
            config.save_to_file(file_path)
        
        else:
            print("Usage: python config.py [validate|summary|save [file_path]]")
    
    else:
        print(config.get_summary())
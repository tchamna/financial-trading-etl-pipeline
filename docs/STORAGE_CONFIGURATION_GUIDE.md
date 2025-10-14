# Storage Configuration Guide

## 📦 **Flexible Data Storage Options**

Your pipeline now supports multiple storage configurations to meet different needs:

### 🔧 **Configuration Options**

Edit `config.json` to customize your storage preferences:

```json
{
  "storage": {
    "enable_local_storage": true,
    "enable_s3_storage": true,
    "local_data_directory": "data",
    "keep_local_days": 7,
    "save_json_format": true,
    "save_parquet_format": true
  }
}
```

## ⚙️ **Storage Options Explained**

### **📍 Local Storage**
- **`enable_local_storage`**: Keep data files on your computer
  - `true` = Save files locally for immediate access
  - `false` = Don't keep local copies (S3 only)

### **☁️ S3 Cloud Storage**  
- **`enable_s3_storage`**: Upload data to AWS S3
  - `true` = Upload to cloud for scalability and analytics
  - `false` = Local storage only

### **📁 Local Settings**
- **`local_data_directory`**: Folder for local files (default: "data")
- **`keep_local_days`**: Auto-cleanup after X days (default: 7)

### **📄 Format Options**
- **`save_json_format`**: Human-readable JSON files
  - Great for debugging and data inspection
- **`save_parquet_format`**: Analytics-optimized Parquet files
  - Perfect for data analysis and visualization tools

## 🎯 **Common Use Cases**

### **🏠 Local Development**
```json
{
  "storage": {
    "enable_local_storage": true,
    "enable_s3_storage": false,
    "save_json_format": true,
    "save_parquet_format": true
  }
}
```
**Best for**: Testing, development, offline analysis

### **☁️ Production Cloud**
```json
{
  "storage": {
    "enable_local_storage": false,
    "enable_s3_storage": true,
    "save_json_format": true,
    "save_parquet_format": true
  }
}
```
**Best for**: Production deployments, serverless environments

### **🔄 Hybrid (Recommended)**
```json
{
  "storage": {
    "enable_local_storage": true,
    "enable_s3_storage": true,
    "keep_local_days": 3,
    "save_json_format": true,
    "save_parquet_format": true
  }
}
```
**Best for**: Development with cloud backup, quick local access

### **💰 Cost Optimization**
```json
{
  "storage": {
    "enable_local_storage": true,
    "enable_s3_storage": true,
    "save_json_format": false,
    "save_parquet_format": true,
    "keep_local_days": 1
  }
}
```
**Best for**: Minimal S3 costs, analytics focus

## 📊 **File Formats Comparison**

| Format | Size | Speed | Analytics | Human-Readable |
|--------|------|-------|-----------|----------------|
| **JSON** | Larger | Slower | Basic | ✅ Yes |
| **Parquet** | Smaller | Faster | Excellent | ❌ No |

## 🗂️ **S3 Storage Structure**

When S3 is enabled, files are organized by format and date:

```
s3://your-bucket/
├── processed/crypto-minute/
│   ├── json/
│   │   └── year=2025/month=10/day=12/
│   │       └── crypto_minute_data_20251012.json.gz
│   └── parquet/
│       └── year=2025/month=10/day=12/
│           └── crypto_minute_data_20251012.parquet
```

## 📁 **Local Storage Structure**

```
data/
├── crypto_minute_data_20251012.json     # Raw JSON data
├── crypto_minute_data_20251012.parquet  # Optimized Parquet
└── [older files automatically cleaned]
```

## ⚡ **Performance Tips**

1. **For Analytics**: Enable Parquet format - it's 2-3x faster for queries
2. **For Development**: Keep JSON format for easy inspection
3. **For Production**: Use S3 + local cache (hybrid approach)
4. **For Cost Savings**: Reduce `keep_local_days` and disable JSON in S3

## 🔧 **Advanced Configuration**

### **Environment Variables Override**
```bash
export ENABLE_LOCAL_STORAGE=true
export ENABLE_S3_STORAGE=false
export LOCAL_DATA_DIRECTORY=/custom/path
```

### **Runtime Configuration Check**
```python
python -c "from config import get_config; c=get_config(); print(f'Local: {c.storage.enable_local_storage}, S3: {c.storage.enable_s3_storage}')"
```

## 📊 **Storage Statistics**

Your pipeline automatically shows storage statistics:

```
💾 DATA STORAGE MANAGER
========================================
📍 Local Storage: ✅ Enabled  
☁️ S3 Storage: ✅ Enabled
📄 JSON Format: ✅
📊 Parquet Format: ✅
```

Choose the configuration that best fits your needs! 🚀
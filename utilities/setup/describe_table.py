import snowflake.connector, sys
sys.path.append('/opt/airflow')
from config import PipelineConfig

config = PipelineConfig()
sf = config.snowflake

conn = snowflake.connector.connect(
    account=sf.account, 
    user=sf.username, 
    password=sf.password, 
    warehouse=sf.warehouse, 
    database=sf.database, 
    schema=sf.schema
)

cursor = conn.cursor()
cursor.execute('DESCRIBE TABLE CRYPTO_MINUTE_DATA')

print('\n📋 CRYPTO_MINUTE_DATA Table Columns:')
print('='*80)
for row in cursor.fetchall():
    print(f'  {row[0]:20} - {row[1]}')

cursor.close()
conn.close()

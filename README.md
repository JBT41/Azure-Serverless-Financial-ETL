# FinanceETL: Azure Serverless Data Pipeline
Serverless Transaction Data Pipeline Using Azure Functions, Azure SQL, and GoCardless API, Application Insights

# Project Overview
This project illustates a custom-built Financial ETL pipeline designed and developed around Cloud Technologies.
It automates the extraction, normalisation and ingestion of Financial Data using GoCardLess API, Python, Azure Functions, Azure SQL

# Goals
- Provision Azure SQL and build Schema
- Automatically refresh GoCardLess Access Tokens
- Automatically retrieve Bank account Ids 
- Automatically Retrieve Transaction data per account ID
- Normalise the Json and prepare for the Azure SQL Schema
- Insert transactions into Azure SQL
- Deploy to azure function



# **Azure Function** </br>
The Azure Function is operating on top of a Flex Consumption App with 512Mb of Instance memory to maintain low cost since its billed for executions we can stay within the free tier usage.
The Flex Consumption Model can be ran based on Linux allowing us to orchestrate the script via CRON. </br>
Runtime Stack: Python - 3.13</br>

<img width="2547" height="787" alt="image" src="https://github.com/user-attachments/assets/f60466d1-7008-4fd7-98bb-eb3518dd45d9" />


Managed Identity is enabled for Secure connection to SQL Database

<img width="2554" height="471" alt="image" src="https://github.com/user-attachments/assets/6620a37a-5300-4722-a16d-3e56e509651d" />


```
conn_str = (
        f"Driver={{ODBC Driver 18 for SQL Server}};"
        f"Server=tcp:{server},1433;"
        f"Database={database};"
        f"Uid={username};"
        f"Pwd={password};"
        "Encrypt=yes;"
        "TrustServerCertificate=no;"
    )

    for attempt in range(1, retries + 1):
        try:
            logging.info(f"SQL connection attempt {attempt}/{retries}...")
            conn = pyodbc.connect(conn_str, timeout=timeout)
            logging.info("SQL connection established.")
            return conn
        except Exception as e:
            if attempt == retries:
                logging.error(f"SQL connection failed on final attempt: {e}")
                raise
            wait = attempt * 5
            logging.warning(f"SQL connection failed: {e}. Retrying in {wait} seconds...")
            time.sleep(wait)
```

<img width="2085" height="159" alt="image" src="https://github.com/user-attachments/assets/6a408839-cb66-4c74-a45e-f561a1f3bc28" />


# **Azure SQL Database** </br>
**Azure SQL Database** is running serverless with a max storage of 32Gb, and 2 Vcores which is more than enough for a small scale personal ETL. </br>
A user has been created for the azure function to allow connection through **Managed Identity**
<img width="2558" height="1275" alt="image" src="https://github.com/user-attachments/assets/0a251d7d-14f3-47f4-bbbe-88752093ce1c" />

# Data Model
The schema design below shows how the **Azure SQL** Database was setup. Transactions are linked with accounts based on account_id Foreign key.
The subcategory is linked to the category baed on catergory_ID Foreign Key. This will provide a solid foundation for data analysis to be conducted.
<img width="2084" height="762" alt="image" src="https://github.com/user-attachments/assets/01376ff6-60d1-4682-9136-ab950309812b" />


# **Application Insights** </br>
Application Insights has been configured to allow for obvservability
<img width="2559" height="622" alt="image" src="https://github.com/user-attachments/assets/e2c7aa01-8fbe-4ab6-aff0-e3eeed3ca9f3" />

<img width="2558" height="1277" alt="image" src="https://github.com/user-attachments/assets/c142c8fa-34a0-447e-a9e2-dbd2b7b1649a" />


Custom metrics dashboard created using Workbooks and python logging

<img width="2556" height="1277" alt="image" src="https://github.com/user-attachments/assets/4538a21b-d938-44f9-8544-3153af468fa2" />







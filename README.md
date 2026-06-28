# FinanceETL: Azure Serverless Data Pipeline
Serverless Transaction Data Pipeline Using Azure Functions, Azure SQL, and GoCardless API, Application Insights</br>

This project illustates a custom-built Financial ETL pipeline designed and developed around Cloud Technologies.
It automates the extraction, normalisation and ingestion of Financial Data using GoCardLess API, Python, Azure Functions, Azure SQL

<img width="1777" height="885" alt="image" src="https://github.com/user-attachments/assets/5b1abbb0-76fe-4f18-ab0f-81e8cb4ba716" />


# Goals
- Provision Azure SQL and build Schema
- Automatically refresh GoCardLess Access Tokens
- Automatically retrieve Bank account Ids 
- Automatically Retrieve Transaction data per account ID
- Normalise the Json and prepare for the Azure SQL Schema
- Insert transactions into Azure SQL
- Deploy to azure function



# **Azure Function (Compute Later)** </br>
The Azure Function is deployed on a Flex Consumption Plan using Python 3.13. This allows event-driven execution while maintaining low operational cost. </br>

The Function is triggered by a CRON timer, scheduled for 07:00 AM, daily.</br>

This design eliminates the need for VM provisioning and ensures execution-based billing

<img width="2547" height="787" alt="image" src="https://github.com/user-attachments/assets/f60466d1-7008-4fd7-98bb-eb3518dd45d9" />

# Secure Authentication via Managed Identity (Authentication Layer)
Managed Identity is enabled for Secure connection to SQL Databas. A user has been created for the azure function to allow connection through **Managed Identity**</br>
DB connection retry logging added to handle Serverless SQL cold start times

<img width="2554" height="471" alt="image" src="https://github.com/user-attachments/assets/6620a37a-5300-4722-a16d-3e56e509651d" />


```
conn_str = (
        f"Driver={{ODBC Driver 18 for SQL Server}};"
        f"Server=tcp:{server},1433;"
        f"Database={database};"
        "Authentication=ActiveDirectoryMsi;"
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


# **Azure SQL Database (Data Layer)** </br>
**Azure SQL Database**
Azure SQL Database is configured in Serverless mode, enabling automatic compute scaling and pause/resume behaviour. This reduces cost while maintaining full SQL Server compatibility </br>
<img width="2558" height="1275" alt="image" src="https://github.com/user-attachments/assets/0a251d7d-14f3-47f4-bbbe-88752093ce1c" />

# Data Model
The schema design below shows how the **Azure SQL** Database was setup. Transactions are linked with accounts based on account_id Foreign key.
The subcategory is linked to the category baed on catergory_ID Foreign Key. This will provide a solid foundation for data analysis to be conducted.
<img width="2084" height="762" alt="image" src="https://github.com/user-attachments/assets/01376ff6-60d1-4682-9136-ab950309812b" />


# **Observability with Application Insights & Custom Workbook Dashboard** </br>
To ensure the reliability and operability of the FinanceETL pipeline, Azure Application Insights was used as the central observability layer. This provides end-to-end visibility into function execution, performance, and failure behaviour.

<img width="2559" height="622" alt="image" src="https://github.com/user-attachments/assets/e2c7aa01-8fbe-4ab6-aff0-e3eeed3ca9f3" />

# Function Invocations (Request Telemetry)
Each execution of the Azure Function is recorded as an invocation (request telemetry) within Application Insights. This captures key operational metrics including:

- Execution start time
- Duration of each run
- Success or failure status
- Trigger type (Timer-based execution)
- Correlation IDs for tracing execution flows</br>

This allows the pipeline to be monitored at a high level, making it easy to verify that scheduled ETL jobs are running consistently and within expected performance thresholds.

<img width="2558" height="1277" alt="image" src="https://github.com/user-attachments/assets/c142c8fa-34a0-447e-a9e2-dbd2b7b1649a" />


# Application Logs (Trace Telemetry)

In addition to invocation data, custom Python logging is used throughout the ETL process to capture detailed runtime behaviour. These logs are sent to Application Insights as trace telemetry, including:

- SQL connection attempts and retries
- API request status and failures
 -Data transformation steps
- Error handling and exception details</br>

This provides deeper debugging capability beyond invocation-level monitoring.

# Custom Workbook Dashboard (Observability Layer)

A custom Azure Monitor Workbook dashboard was created to provide a consolidated operational view of the pipeline.</br>
https://github.com/JBT41/Azure-Serverless-Financial-ETL/tree/main/src/monitoring/queries

This dashboard aggregates telemetry from Application Insights and presents key operational metrics such as:


- Success vs failure rates
- Error frequency and breakdown
- API and database-related failures</br>

By combining request telemetry (invocations) and trace logs (application logs), the dashboard enables both high-level monitoring and granular troubleshooting from a single interface.


<img width="2554" height="1277" alt="image" src="https://github.com/user-attachments/assets/8b7b3a36-b6ca-4d14-a9f6-470ca67f6005" />




import logging
import traceback
import azure.functions as func
import pyodbc
import os
import requests
import time
from datetime import date, timedelta

app = func.FunctionApp()


def get_sql_connection_with_retry(retries: int = 5, timeout: int = 5):
    server = os.environ.get("SQL_SERVER")
    database = os.environ.get("SQL_DATABASE")
    username = os.environ.get("SQL_USER")
    password = os.environ.get("SQL_PASSWORD")

    if not all([server, database]):
        raise RuntimeError("Missing one of SQL_SERVER, SQL_DATABASE, SQL_USER, SQL_PASSWORD environment variables.")

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

def refresh_access_token(refresh_token: str) -> str:
    url = "https://bankaccountdata.gocardless.com/api/v2/token/refresh/"
    response = requests.post(url, json={"refresh": refresh_token}, timeout=10)
    response.raise_for_status()
    return response.json()["access"]

def get_account_ids(access_token: str, requisition_id: str):
    url = f"https://bankaccountdata.gocardless.com/api/v2/requisitions/{requisition_id}/"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    return response.json().get("accounts", [])

def get_transactions(access_token: str, account_id: str):
    yesterday = (date.today() - timedelta(days=1)).strftime('%Y-%m-%d')
    url = (
        f"https://bankaccountdata.gocardless.com/api/v2/accounts/"
        f"{account_id}/transactions/"
    )
    headers = {"Authorization": f"Bearer {access_token}"}

    for attempt in range(1, 6):
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 429:
            wait = attempt * 2
            logging.warning(f"429 rate limit hit for account {account_id}. Retrying in {wait}s...")
            time.sleep(wait)
            continue
        resp.raise_for_status()
        return resp.json().get("transactions", {}).get("booked", [])
    raise Exception("Exceeded retry attempts due to repeated 429 responses.")

def insert_transactions(transactions, account_id):
    logging.info(
        f"Preparing to insert {len(transactions)} transactions for account {account_id}..."
    )

    conn = get_sql_connection_with_retry()
    cur = None

    try:
        cur = conn.cursor()

        insert_query = """
        IF NOT EXISTS (
            SELECT 1
            FROM transactions
            WHERE transactionID = ?
        )
        INSERT INTO transactions (
            transactionID,
            account_id,
            entryReference,
            bookingDate,
            valueDate,
            amount,
            currency,
            debtorName,
            creditorName,
            remittanceInformationU,
            proprietaryBankTransact,
            internalTransactionId
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        for tx in transactions:
            tx_id = tx.get("transactionId")

            data = (
                tx_id,  # IF NOT EXISTS check
                tx_id,  # transactionID
                account_id,
                tx.get("entryReference"),
                tx.get("bookingDate"),
                tx.get("valueDate"),
                tx.get("transactionAmount", {}).get("amount"),
                tx.get("transactionAmount", {}).get("currency"),
                tx.get("debtorName"),
                tx.get("creditorName"),
                tx.get("remittanceInformationUnstructured"),
                tx.get("proprietaryBankTransactionCode"),
                tx.get("internalTransactionId"),
            )
            try:
                
                cur.execute(insert_query, data)
            except pyodbc.IntegrityError:
                continue

        conn.commit()

        logging.info(
            f"Committed {len(transactions)} transactions for account {account_id}."
        )

    finally:
        if cur is not None:
            try:
                cur.close()
            except Exception:
                pass

        conn.close()

@app.timer_trigger(schedule="0 0 7 * * *", arg_name="myTimer", run_on_startup=False)
def FinanceETL(myTimer: func.TimerRequest) -> None:
    logging.info("FinanceETL trigger initialized.")
    try:
        refresh_token = os.environ.get("refresh_token")
        requisition_id = os.environ.get("requisition_id")

        if not refresh_token or not requisition_id:
            logging.error("Missing refresh_token or requisition_id environment variables.")
            return


        try:
            conn = get_sql_connection_with_retry()
            conn.close()
            logging.info("SQL connection test successful. Proceeding with API calls.")
        except Exception as e:
            logging.error(f"SQL connection test failed — aborting ETL: {e}")
            return

        access_token = refresh_access_token(refresh_token)
        account_ids = get_account_ids(access_token, requisition_id)

        if not account_ids:
            logging.info("No accounts returned by GoCardless for this requisition.")
            return

        for acc_id in account_ids:
            try:
                transactions = get_transactions(access_token, acc_id)
                if transactions:
                    insert_transactions(transactions, acc_id)
                else:
                    logging.info(f"No transactions found for account {acc_id}.")
            except Exception as e:
                logging.error(f"Failed processing account {acc_id}: {e}")
                logging.error(traceback.format_exc())

    except Exception:
        logging.error("CRITICAL FAILURE in FinanceETL:")
        logging.error(traceback.format_exc())
        raise


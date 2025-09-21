import sqlite3
import json
from datetime import datetime, date
from typing import List, Dict, Any
from openai import OpenAI

def parse_json(data):
    if isinstance(data, dict):
        return data
    
    if not isinstance(data, str):
        return {}
    
    if data.strip().startswith('```'):
        import re
        match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', data, re.DOTALL)
        if match:
            data = match.group(1).strip()
        else:
            data = re.sub(r'^```(?:json)?\s*\n?', '', data)
            data = re.sub(r'\n?```$', '', data)
    
    try:
        return json.loads(data)
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
        return {}

class DatabaseManager:
    def __init__(self, db_path: str = "receipts.db"):
        self.db_path = db_path
        self.client = OpenAI()
        self.init_database()
    
    def init_database(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS receipts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            raw_text TEXT,
            extracted_data TEXT, 
            upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            processed_date TIMESTAMP,
            receipt_date DATE
        )
        """)
        
        conn.commit()
        conn.close()

    def insert_receipt(self, filename: str, raw_text: str, extracted_data: Dict[str, Any]):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        parsed_data = parse_json(extracted_data)
        receipt_date = parsed_data.get('date')
        
        if not receipt_date:
            receipt_date = date.today().isoformat()
            print(f"No date found in receipt, using current date: {receipt_date}")
        else:
            print(f"Using extracted date: {receipt_date}")

        cursor.execute("""
        INSERT INTO receipts (filename, raw_text, extracted_data, upload_date, processed_date, receipt_date) 
        VALUES (?, ?, ?, ?, ?, ?)
        """, (filename, raw_text, json.dumps(parsed_data), datetime.now(), datetime.now(), receipt_date))

        receipt_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return receipt_id
    
    def delete_receipt(self, receipt_id: int):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM receipts WHERE id = ?", (receipt_id,))
        if not cursor.fetchone():
            conn.close()
            return False
        
        cursor.execute("DELETE FROM receipts WHERE id = ?", (receipt_id,))
        conn.commit()
        conn.close()
        return True
    
    def generate_sql_query(self, user_query: str):
        schema_info = """
        receipts table has the following columns:
        - id: integer
        - filename: string
        - raw_text: string
        - extracted_data: string (JSON)
        - upload_date: timestamp
        - processed_date: timestamp
        - receipt_date: date (YYYY-MM-DD format)

        the extracted_data is a JSON object with the following fields:
        - store_name: string
        - items: list of objects { "name": string, "quantity": int, "price": float }
        - total_amount: float
        - payment_method: string (if available, else null)

        IMPORTANT: 
        - Use receipt_date column for date queries, not JSON_EXTRACT
        - Use JSON_EXTRACT to access other JSON fields
        - For total amount queries, use JSON_EXTRACT(extracted_data, '$.total_amount')
        - For specific food items, use JSON_EXTRACT(extracted_data, '$.items') LIKE '%item_name%'
        - For general food queries, don't filter by items, just sum all total_amount
        - For specific item spending, sum the price of that specific item across all receipts
        - For time-based queries, use receipt_date for today/yesterday queries
        - Always SELECT * to get all receipt data, not just specific fields
        """

        prompt = f"""
        Convert this natural language query to SQL for the receipts database.
        
        {schema_info}
        
        Query: "{user_query}"
        
        Rules:
        1. Return ONLY the SQL query, no explanations
        2. Use proper SQLite syntax
        3. Use receipt_date column for date queries, not JSON_EXTRACT
        4. Use JSON_EXTRACT to access JSON fields: JSON_EXTRACT(extracted_data, '$.field_name')
        5. For total amount queries, use JSON_EXTRACT(extracted_data, '$.total_amount')
        6. For specific food items, use JSON_EXTRACT(extracted_data, '$.items') LIKE '%item_name%'
        7. For general food spending, sum all total_amount without filtering
        8. For specific item spending, sum the price of that specific item across all receipts
        9. For time-based queries, use receipt_date for today/yesterday queries
        10. Always SELECT * to get all receipt data, not just specific fields
        11. Handle date comparisons correctly
        12. Use LIKE for text searches
        13. DO NOT use JSON_EACH, JSON_TABLE, or other unsupported functions
        14. DO NOT reference columns that don't exist in the receipts table
        
        Examples:
        - "What food did I buy today?" -> SELECT * FROM receipts WHERE DATE(receipt_date) = DATE('now')
        - "How much spent on chicken burrito?" -> SELECT * FROM receipts WHERE JSON_EXTRACT(extracted_data, '$.items') LIKE '%chicken burrito%'
        - "Total food spending" -> SELECT SUM(JSON_EXTRACT(extracted_data, '$.total_amount')) FROM receipts
        
        SQL Query:
        """

        response = self.client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that generates SQL queries. Use receipt_date column for date queries and always SELECT * to get complete receipt data."},
                {"role": "user", "content": prompt}
            ]
        )
        sql_query = response.choices[0].message.content

        if sql_query.startswith("```sql"):
            sql_query = sql_query.split("```sql")[1].split("```")[0]
        if sql_query.endswith("```"):
            sql_query = sql_query.split("```")[0]

        return sql_query.strip()
    
    def _execute_sql_query(self, sql_query: str):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            cursor.execute(sql_query)
            results = []
            for row in cursor.fetchall():
                result = dict(row)
                if 'extracted_data' in result and result['extracted_data']:
                    try:
                        result['extracted_data'] = json.loads(result['extracted_data'])
                    except:
                        pass
                results.append(result)
            conn.close()
            return results
        except Exception as e:
            print(f"SQL Error: {e}")
            conn.close()
            return []

    def execute_user_query(self, user_query: str):
        sql_query = self.generate_sql_query(user_query)
        return self._execute_sql_query(sql_query)

    def get_all_receipts(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM receipts ORDER BY upload_date DESC")
        results = []
        for row in cursor.fetchall():
            result = dict(row)
            if result['extracted_data']:
                try:
                    result['extracted_data'] = json.loads(result['extracted_data'])
                except:
                    pass
            results.append(result)
        conn.close()
        return results

db = DatabaseManager()
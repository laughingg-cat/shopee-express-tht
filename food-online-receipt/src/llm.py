from db import db
from openai import OpenAI
from typing import List, Dict, Any
import json

class FoodOnlineReceiptLLM:
    def __init__(self):
        self.client = OpenAI()

    def _format_response(self, user_query: str, query_result: List[Dict[str, Any]]):
        if query_result is None or len(query_result) == 0:
            return f"No results found for the query: {user_query}"

        prompt = f"""
        Format the following query result into a readable and informative answer to the user's query:
        User's query: {user_query}
        Query result: {query_result}

        Response:
        """

        response = self.client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that formats query results into readable and informative answers."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content


    def ask_ai(self, user_query: str):
        query_result = db.execute_user_query(user_query)
        return self._format_response(user_query, query_result)

llm = FoodOnlineReceiptLLM()
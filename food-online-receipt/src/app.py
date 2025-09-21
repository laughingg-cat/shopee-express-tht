import gradio as gr
from ocr import extract_receipt
from db import db
from llm import llm
import os
import json
import re

def parse_json(data):
    if isinstance(data, dict):
        return data
    
    if not isinstance(data, str):
        return {}
    
    if data.strip().startswith('```'):
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

def upload_and_process(file):
    if file is None:
        return "Please upload a receipt image.", ""
    
    text, structured = extract_receipt(file)
    filename = os.path.basename(file)
    db.insert_receipt(filename, text, structured)
    
    structured_data = parse_json(structured)
    
    result = f"Processed: {filename}\n\n"
    result += f"Store: {structured_data.get('store_name', 'Unknown')}\n"
    result += f"Date: {structured_data.get('date', 'Unknown')}\n"
    result += f"Total: ${structured_data.get('total_amount', 0)}\n"
    result += f"Payment: {structured_data.get('payment_method', 'Unknown')}\n\n"
    
    if 'items' in structured_data and structured_data['items']:
        result += "Items:\n"
        for item in structured_data['items']:
            result += f"  - {item.get('name', 'Unknown')} x{item.get('quantity', 1)} ${item.get('price', 0)}\n"
    
    return result, text

def chat_function(message, history):
    """Chat function for gr.ChatInterface"""
    sql_query = db.generate_sql_query(message)
    
    receipt_data = db._execute_sql_query(sql_query)
    
    result = llm.ask_ai(message)
    
    if receipt_data:
        result += f"\n\n **Receipts used for this answer:**\n"
        for receipt in receipt_data:
            result += f"• ID: {receipt['id']} - {receipt['filename']}\n"
            if receipt['extracted_data']:
                data = parse_json(receipt['extracted_data'])
                result += f"  Store: {data.get('store_name', 'Unknown')}\n"
                if 'items' in data and data['items']:
                    for item in data['items']:
                        result += f"  - {item.get('name', 'Unknown')} x{item.get('quantity', 1)} ${item.get('price', 0)}\n"
    else:
        result += "\n\n**No receipts found matching your query.**"
    
    return result

def get_receipts():
    receipts = db.get_all_receipts()
    if not receipts:
        return "No receipts found."
    
    result = "Receipts:\n\n"
    for receipt in receipts:
        result += f"ID: {receipt['id']}\n"
        result += f"File: {receipt['filename']}\n"
        result += f"Upload Date: {receipt['upload_date']}\n"
        result += f"Receipt Date: {receipt.get('receipt_date', 'Unknown')}\n"
        if receipt['extracted_data']:
            data = parse_json(receipt['extracted_data'])
            result += f"Store: {data.get('store_name', 'Unknown')}\n"
            result += f"Total: ${data.get('total_amount', 0)}\n"
            if 'items' in data and data['items']:
                result += "Items:\n"
                for item in data['items']:
                    result += f"  - {item.get('name', 'Unknown')} x{item.get('quantity', 1)} ${item.get('price', 0)}\n"
        result += "\n"
    return result

def execute_custom_query(query):
    """Execute custom SQL query and format results"""
    if not query.strip():
        return "Please enter a SQL query."
    
    try:
        results = db._execute_sql_query(query)
        if not results:
            return "No results found."
        
        result = f"Query: {query}\n\n"
        result += f"Results ({len(results)} rows):\n\n"
        
        for i, row in enumerate(results, 1):
            result += f"Row {i}:\n"
            for key, value in row.items():
                if key == 'extracted_data' and value:
                    data = parse_json(value)
                    result += f"  {key}: {json.dumps(data, indent=2)}\n"
                else:
                    result += f"  {key}: {value}\n"
            result += "\n"
        
        return result
    except Exception as e:
        return f"Error executing query: {str(e)}"

def delete_receipt(receipt_id):
    if not receipt_id:
        return "Please enter a receipt ID."
    
    try:
        receipt_id = int(receipt_id)
        success = db.delete_receipt(receipt_id)
        if success:
            return f"Receipt {receipt_id} deleted successfully."
        else:
            return f"Receipt {receipt_id} not found."
    except ValueError:
        return "Please enter a valid receipt ID (number)."

with gr.Blocks() as demo:
    gr.Markdown("# Food Expense AI")
    
    with gr.Tab("Upload Receipt"):
        receipt_file = gr.File(label="Upload receipt image", type="filepath")
        output = gr.Textbox(label="Extracted Data", lines=15)
        raw_text = gr.Textbox(label="Raw Text", lines=8)
        receipt_file.change(upload_and_process, receipt_file, [output, raw_text])
    
    with gr.Tab("Ask AI"):
        # Use gr.ChatInterface following the official guide
        chat_interface = gr.ChatInterface(
            fn=chat_function,
            title="Food Expense AI Chat",
            description="Ask me anything about your food expenses!",
            examples=[
                "What food did i buy yesterday?",
                "Give me total expenses for food on 20 June",
                "Where did i buy hamburger from last 7 days"
            ],
            type="messages",
            flagging_mode="manual",
            flagging_options=["Like", "Dislike", "Incorrect", "Helpful"],
            save_history=True
        )
    
    with gr.Tab("View Receipts"):
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### All Receipts")
                refresh_btn = gr.Button("Refresh All Receipts")
                receipts_output = gr.Textbox(label="All Receipts", lines=20)
                refresh_btn.click(get_receipts, outputs=receipts_output)
                demo.load(get_receipts, outputs=receipts_output)
            
            with gr.Column(scale=1):
                gr.Markdown("### Custom SQL Query")
                query_input = gr.Textbox(
                    label="Enter SQL Query", 
                    placeholder="SELECT * FROM receipts WHERE receipt_date = '2021-02-25'",
                    lines=3
                )
                execute_btn = gr.Button("Execute Query")
                query_output = gr.Textbox(label="Query Results", lines=20)
                execute_btn.click(execute_custom_query, inputs=query_input, outputs=query_output)
    
    with gr.Tab("Delete Receipt"):
        receipt_id_input = gr.Textbox(label="Receipt ID to delete")
        delete_btn = gr.Button("Delete")
        delete_output = gr.Textbox(label="Status")
        delete_btn.click(delete_receipt, inputs=receipt_id_input, outputs=delete_output)

demo.launch()
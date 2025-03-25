"""
Main application entry point for the LangChain-Chatwoot integration.
"""
import os
import json
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import our modules
from utils.conversation_context import ConversationContextManager
from handlers.chatwoot_handler import ChatwootHandler
import langchain_integration

# Initialize Flask app
app = Flask(__name__)

# Initialize conversation context manager
context_manager = ConversationContextManager(storage_path="./data/contexts")

# Set the context manager for the Chatwoot handler
langchain_integration.chatwoot_handler.context_manager = context_manager

@app.route("/", methods=["GET"])
def index():
    """Root endpoint for health check"""
    return jsonify({
        "status": "ok",
        "message": "LangChain-Chatwoot integration is running",
        "test_mode": os.getenv("TEST_MODE", "").lower() == "true"
    })

@app.route("/webhook", methods=["POST"])
def webhook():
    """Webhook endpoint for Chatwoot"""
    try:
        # Get webhook data
        webhook_data = request.json
        
        # Process webhook data
        result = langchain_integration.chatwoot_handler.process_webhook(webhook_data)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/webhook/chatwoot", methods=["POST"])
def chatwoot_webhook():
    """Specific webhook endpoint for Chatwoot"""
    try:
        # Get webhook data
        webhook_data = request.json
        
        # Log the incoming webhook data
        print(f"Received Chatwoot webhook: {json.dumps(webhook_data)[:200]}...")
        
        # Process webhook data
        result = langchain_integration.chatwoot_handler.process_webhook(webhook_data)
        
        return jsonify(result)
    except Exception as e:
        print(f"Error in Chatwoot webhook: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/test", methods=["POST"])
def test_endpoint():
    """Test endpoint for simulating conversations"""
    try:
        # Get test data
        test_data = request.json
        message = test_data.get("message", "")
        conversation_id = test_data.get("conversation_id", "test-conversation")
        role = test_data.get("role", None)
        
        # Set role if provided
        if role and role in ["sales", "support"]:
            context_manager.set_role(conversation_id, role)
        
        # Process message
        response = langchain_integration.process_message(message, conversation_id, context_manager)
        
        return jsonify({
            "conversation_id": conversation_id,
            "message": message,
            "response": response,
            "role": context_manager.get_current_role(conversation_id),
            "context": context_manager.get_conversation_summary(conversation_id)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    # Create data directory if it doesn't exist
    os.makedirs("./data/contexts", exist_ok=True)
    
    # Run the app
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080)), debug=True)

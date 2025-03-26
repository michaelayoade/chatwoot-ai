"""
Test script to verify the functionality of the refactored modular structure.
"""
import os
import sys
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set test mode
os.environ["TEST_MODE"] = "true"

# Import our modules
from utils.conversation_context import ConversationContextManager
from tools.erp_tool import ERPNextTool
from tools.splynx_tool import SplynxTool
from tools.unms_tool import UNMSTool
import langchain_integration

def test_conversation_context_manager():
    """Test the conversation context manager"""
    print("\n=== Testing ConversationContextManager ===")
    
    # Initialize context manager
    context_manager = ConversationContextManager()
    
    # Test conversation ID
    conversation_id = "test-conversation-1"
    
    # Test role detection and setting
    print("Testing role detection and setting...")
    
    # Default role should be support
    assert context_manager.get_current_role(conversation_id) == "support"
    print("✓ Default role is support")
    
    # Test setting role to sales
    context_manager.set_role(conversation_id, "sales")
    assert context_manager.get_current_role(conversation_id) == "sales"
    print("✓ Role successfully set to sales")
    
    # Test entity tracking
    print("\nTesting entity tracking...")
    
    # Add entities
    entities = {
        "customer_id": "CUS-12345",
        "order_id": "ORD-67890"
    }
    context_manager.update_entities(conversation_id, entities)
    
    # Verify entities
    stored_entities = context_manager.get_entities(conversation_id)
    assert stored_entities.get("customer_id") == "CUS-12345"
    assert stored_entities.get("order_id") == "ORD-67890"
    print("✓ Entities successfully stored and retrieved")
    
    # Test context summary
    print("\nTesting context summary...")
    
    # Update summary
    context_manager.update_summary(conversation_id, "Customer inquiring about fiber plans")
    
    # Get summary
    summary = context_manager.get_conversation_summary(conversation_id)
    assert summary.get("role") == "sales"
    assert summary.get("summary") == "Customer inquiring about fiber plans"
    assert "customer_id" in summary.get("entities", {})
    print("✓ Context summary successfully retrieved")
    
    # Test context clearing
    print("\nTesting context clearing...")
    
    # Clear context
    context_manager.clear_context(conversation_id)
    
    # Verify context is cleared
    new_context = context_manager.get_conversation_context(conversation_id)
    assert new_context.get("role") == "support"  # Back to default
    assert not new_context.get("entities")
    print("✓ Context successfully cleared")
    
    print("\nConversationContextManager tests passed!\n")

def test_erp_tool():
    """Test the ERPNextTool functionality"""
    print("\n=== Testing ERPNextTool ===")
    
    # Initialize ERP tool
    erp_tool = ERPNextTool(
        api_key="test_key",
        api_secret="test_secret",
        base_url="https://erp.example.com"
    )
    
    # Test customer info
    print("Testing get_customer_info...")
    customer_info = erp_tool.get_customer_info("CUS-12345")
    assert customer_info.get("id") == "CUS-12345"
    assert "name" in customer_info
    assert "email" in customer_info
    print("✓ Customer info successfully retrieved")
    
    # Test service plans
    print("\nTesting get_service_plans...")
    service_plans = erp_tool.get_service_plans()
    assert isinstance(service_plans, list)
    assert len(service_plans) > 0
    assert "id" in service_plans[0]
    assert "name" in service_plans[0]
    assert "price" in service_plans[0]
    print("✓ Service plans successfully retrieved")
    
    # Test promotions
    print("\nTesting get_promotions...")
    promotions = erp_tool.get_promotions()
    assert isinstance(promotions, list)
    assert len(promotions) > 0
    assert "id" in promotions[0]
    assert "name" in promotions[0]
    assert "description" in promotions[0]
    print("✓ Promotions successfully retrieved")
    
    # Test order status
    print("\nTesting get_order_status...")
    order_status = erp_tool.get_order_status("ORD-67890")
    assert order_status.get("id") == "ORD-67890"
    assert "status" in order_status
    assert "created_at" in order_status
    print("✓ Order status successfully retrieved")
    
    print("\nERPNextTool tests passed!\n")

def test_splynx_tool():
    """Test the SplynxTool functionality"""
    print("\n=== Testing SplynxTool ===")
    
    # Initialize Splynx tool
    splynx_tool = SplynxTool(
        api_key="test_key",
        api_secret="test_secret",
        base_url="https://splynx.example.com"
    )
    
    # Test internet status
    print("Testing get_customer_internet_status...")
    internet_status = splynx_tool.get_customer_internet_status("CUS-12345")
    assert "status" in internet_status
    assert "plan" in internet_status
    assert "usage" in internet_status
    print("✓ Internet status successfully retrieved")
    
    # Test payment history
    print("\nTesting get_payment_history...")
    payment_history = splynx_tool.get_payment_history("CUS-12345")
    assert isinstance(payment_history, list)
    assert len(payment_history) > 0
    assert "id" in payment_history[0]
    assert "amount" in payment_history[0]
    assert "date" in payment_history[0]
    print("✓ Payment history successfully retrieved")
    
    print("\nSplynxTool tests passed!\n")

def test_unms_tool():
    """Test the UNMSTool functionality"""
    print("\n=== Testing UNMSTool ===")
    
    # Initialize UNMS tool
    unms_tool = UNMSTool(
        api_key="test_key",
        base_url="https://unms.example.com"
    )
    
    # Test device status
    print("Testing get_device_status...")
    device_status = unms_tool.get_device_status("DEV-12345")
    assert "id" in device_status
    assert "name" in device_status
    assert "status" in device_status
    assert "interfaces" in device_status
    print("✓ Device status successfully retrieved")
    
    # Test site status
    print("\nTesting get_site_status...")
    site_status = unms_tool.get_site_status("SITE-12345")
    assert "id" in site_status
    assert "name" in site_status
    assert "status" in site_status
    print("✓ Site status successfully retrieved")
    
    # Test outage info
    print("\nTesting get_outage_info...")
    outage_info = unms_tool.get_outage_info()
    assert "outages" in outage_info
    print("✓ Outage info successfully retrieved")
    
    print("\nUNMSTool tests passed!\n")

def test_dual_role_agent():
    """Test the dual-role agent functionality"""
    print("\n=== Testing Dual-Role Agent ===")
    
    # Initialize context manager
    context_manager = ConversationContextManager()
    
    # Test conversation IDs
    sales_conversation_id = "test-sales-conversation"
    support_conversation_id = "test-support-conversation"
    
    # Set roles
    context_manager.set_role(sales_conversation_id, "sales")
    context_manager.set_role(support_conversation_id, "support")
    
    # Test sales query
    print("Testing sales query processing...")
    sales_query = "I'm interested in your fiber internet plans. What options do you have?"
    sales_response = langchain_integration.process_message(sales_query, sales_conversation_id, context_manager)
    assert sales_response
    print(f"Sales response: {sales_response[:100]}...")
    print("✓ Sales query successfully processed")
    
    # Test support query
    print("\nTesting support query processing...")
    support_query = "My internet is down. Can you help me troubleshoot?"
    support_response = langchain_integration.process_message(support_query, support_conversation_id, context_manager)
    assert support_response
    print(f"Support response: {support_response[:100]}...")
    print("✓ Support query successfully processed")
    
    # Test entity extraction
    print("\nTesting entity extraction...")
    entity_query = "My customer ID is CUS-54321 and I'm having issues with my order ORD-98765"
    entity_ids = langchain_integration.extract_entity_ids(entity_query)
    assert entity_ids.get("customer_id") == "CUS-54321"
    assert entity_ids.get("order_id") == "ORD-98765"
    print("✓ Entities successfully extracted")
    
    print("\nDual-Role Agent tests passed!\n")

def main():
    """Main test function"""
    print("Starting tests for modular structure...")
    
    try:
        # Test conversation context manager
        test_conversation_context_manager()
        
        # Test ERP tool
        test_erp_tool()
        
        # Test Splynx tool
        test_splynx_tool()
        
        # Test UNMS tool
        test_unms_tool()
        
        # Test dual-role agent
        test_dual_role_agent()
        
        print("\n=== All tests passed! ===")
        return 0
    except Exception as e:
        print(f"\n=== Test failed: {str(e)} ===")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())

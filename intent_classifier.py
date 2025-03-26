import json
from langchain.chat_models import ChatDeepseek

class IntentClassifier:
    def __init__(self):
        self.llm = ChatDeepseek(model="deepseek-chat")
        
    def classify_intent(self, message):
        prompt = """Classify this message into sales, support, or other:
        Message: {message}
        
        Return JSON with classification and confidence scores:
        {
            "classification": "sales|support|other",
            "scores": {
                "sales": 0.0-1.0,
                "support": 0.0-1.0,
                "other": 0.0-1.0
            }
        }"""
        
        response = self.llm.generate(prompt.format(message=message))
        return json.loads(response)

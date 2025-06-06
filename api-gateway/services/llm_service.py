import asyncio
import time
from typing import List, Dict, Optional
import structlog
from openai import AsyncAzureOpenAI
from config import settings

logger = structlog.get_logger()

class LLMService:
    """Service for Azure OpenAI LLM interactions"""
    
    def __init__(self):
        self.client = AsyncAzureOpenAI(
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT
        )
        self.deployment = settings.AZURE_OPENAI_DEPLOYMENT
        
        # System prompts for different contexts
        self.system_prompts = {
            "general": """You are a helpful AI customer service agent. You provide accurate, concise, and friendly responses to customer inquiries.

Key guidelines:
- Be professional but warm in tone
- Provide specific, actionable information when possible
- If you don't know something, admit it and offer to escalate
- Keep responses under 150 words unless more detail is specifically needed
- Always aim to resolve the customer's issue in the first response
- Use proper English grammar and spelling

Context: You are handling customer communications across email, chat, and voice channels for a business.""",
            
            "technical": """You are a technical support AI agent specializing in troubleshooting and technical assistance.

Key guidelines:
- Provide step-by-step solutions when appropriate
- Ask clarifying questions to better understand the issue
- Explain technical concepts in simple terms
- Offer multiple solution approaches when available
- If the issue is complex, recommend escalation to human technical support
- Always prioritize customer safety and data security

Context: You are handling technical support requests across multiple communication channels.""",
            
            "sales": """You are a sales-oriented AI agent focused on helping customers with product information and purchase decisions.

Key guidelines:
- Be helpful and informative without being pushy
- Provide accurate product information and pricing
- Understand customer needs before making recommendations
- Handle objections professionally
- Know when to escalate to human sales representatives
- Focus on building customer relationships

Context: You are handling sales inquiries and product questions across communication channels."""
        }
    
    async def generate_response(
        self,
        message: str,
        conversation_history: Optional[List[Dict]] = None,
        context: str = "general",
        user_metadata: Optional[Dict] = None,
        max_tokens: int = 300
    ) -> Dict:
        """Generate AI response to user message"""
        start_time = time.time()
        
        try:
            # Build messages array
            messages = [
                {"role": "system", "content": self.system_prompts.get(context, self.system_prompts["general"])}
            ]
            
            # Add conversation history if available
            if conversation_history:
                for msg in conversation_history[-10:]:  # Last 10 messages for context
                    messages.append({
                        "role": "user" if msg["sender_type"] == "user" else "assistant",
                        "content": msg["content"]
                    })
            
            # Add current message
            messages.append({"role": "user", "content": message})
            
            # Add user context if available
            if user_metadata:
                context_info = f"\nUser context: {user_metadata.get('preferences', '')}"
                messages[0]["content"] += context_info
            
            # Generate response
            response = await self.client.chat.completions.create(
                model=self.deployment,
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.7,
                top_p=0.9,
                frequency_penalty=0.1,
                presence_penalty=0.1
            )
            
            response_time = (time.time() - start_time) * 1000
            
            # Calculate confidence score based on response characteristics
            confidence_score = self._calculate_confidence(response, message)
            
            # Determine if escalation is needed
            should_escalate = self._should_escalate(message, response.choices[0].message.content, confidence_score)
            
            result = {
                "content": response.choices[0].message.content.strip(),
                "confidence_score": confidence_score,
                "should_escalate": should_escalate,
                "response_time_ms": response_time,
                "tokens_used": response.usage.total_tokens,
                "model": self.deployment
            }
            
            logger.info(
                "Generated LLM response",
                response_time_ms=response_time,
                confidence_score=confidence_score,
                tokens_used=response.usage.total_tokens,
                should_escalate=should_escalate
            )
            
            return result
            
        except Exception as e:
            logger.error("LLM generation failed", error=str(e))
            
            # Return fallback response
            return {
                "content": "I apologize, but I'm experiencing technical difficulties. Let me connect you with a human agent who can assist you better.",
                "confidence_score": 0.0,
                "should_escalate": True,
                "response_time_ms": (time.time() - start_time) * 1000,
                "tokens_used": 0,
                "model": self.deployment,
                "error": str(e)
            }
    
    def _calculate_confidence(self, response, original_message: str) -> float:
        """Calculate confidence score based on response characteristics"""
        try:
            # Base confidence from token probability (if available)
            base_confidence = 0.8  # Default high confidence
            
            response_text = response.choices[0].message.content
            
            # Reduce confidence for certain phrases that indicate uncertainty
            uncertainty_phrases = [
                "i don't know",
                "i'm not sure",
                "i can't help",
                "contact support",
                "escalate",
                "not certain",
                "might be",
                "possibly",
                "perhaps"
            ]
            
            response_lower = response_text.lower()
            uncertainty_count = sum(1 for phrase in uncertainty_phrases if phrase in response_lower)
            confidence_penalty = uncertainty_count * 0.2
            
            # Bonus for specific, actionable responses
            if any(word in response_lower for word in ["step", "first", "next", "here's how", "solution"]):
                base_confidence += 0.1
            
            # Penalty for very short responses (might indicate confusion)
            if len(response_text.split()) < 10:
                base_confidence -= 0.1
            
            # Penalty for very long responses (might indicate rambling)
            if len(response_text.split()) > 200:
                base_confidence -= 0.1
            
            final_confidence = max(0.0, min(1.0, base_confidence - confidence_penalty))
            
            return round(final_confidence, 2)
            
        except Exception as e:
            logger.error("Confidence calculation failed", error=str(e))
            return 0.5  # Default moderate confidence
    
    def _should_escalate(self, original_message: str, response: str, confidence_score: float) -> bool:
        """Determine if the conversation should be escalated to human"""
        
        # Escalate if confidence is too low
        if confidence_score < 0.6:
            return True
        
        # Escalate for explicit requests
        escalation_keywords = [
            "speak to human",
            "talk to manager", 
            "human agent",
            "real person",
            "customer service representative",
            "escalate",
            "complaint",
            "urgent",
            "emergency"
        ]
        
        message_lower = original_message.lower()
        if any(keyword in message_lower for keyword in escalation_keywords):
            return True
        
        # Escalate for sensitive topics
        sensitive_keywords = [
            "refund",
            "billing issue",
            "account closed",
            "legal",
            "lawsuit",
            "fraud",
            "security breach",
            "data breach",
            "privacy concern"
        ]
        
        if any(keyword in message_lower for keyword in sensitive_keywords):
            return True
        
        # Escalate if response suggests escalation
        response_lower = response.lower()
        if any(phrase in response_lower for phrase in ["contact support", "human agent", "escalate"]):
            return True
        
        return False
    
    async def summarize_conversation(self, messages: List[Dict]) -> str:
        """Generate a summary of the conversation for context"""
        try:
            if not messages:
                return "No conversation history available."
            
            # Prepare conversation text
            conversation_text = "\n".join([
                f"{msg['sender_type']}: {msg['content']}" 
                for msg in messages[-20:]  # Last 20 messages
            ])
            
            summary_prompt = f"""Please provide a concise summary of this customer conversation:

{conversation_text}

Summary should include:
- Main customer issue/question
- Key points discussed
- Current status/resolution
- Any important context for future interactions

Keep summary under 100 words."""

            response = await self.client.chat.completions.create(
                model=self.deployment,
                messages=[{"role": "user", "content": summary_prompt}],
                max_tokens=150,
                temperature=0.3
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error("Conversation summarization failed", error=str(e))
            return "Unable to generate conversation summary."
    
    async def health_check(self) -> bool:
        """Check if LLM service is healthy"""
        try:
            response = await self.client.chat.completions.create(
                model=self.deployment,
                messages=[{"role": "user", "content": "Health check"}],
                max_tokens=10
            )
            return True
        except Exception as e:
            logger.error("LLM health check failed", error=str(e))
            return False 
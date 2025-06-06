import asyncio
import json
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
import structlog
import redis.asyncio as redis

from config import settings
from services.llm_service import LLMService
from services.vector_service import VectorService
from database import get_db_session, create_message, update_agent_status, get_active_agents

logger = structlog.get_logger()

class Agent:
    """Individual AI agent worker"""
    
    def __init__(self, agent_id: str, orchestrator: 'AgentOrchestrator'):
        self.id = agent_id
        self.orchestrator = orchestrator
        self.status = "idle"  # idle, busy, error
        self.current_task = None
        self.total_processed = 0
        self.errors = 0
        self.last_activity = datetime.utcnow()
        self.specialization = "general"  # general, technical, sales
        
    async def process_message(self, message_data: Dict) -> Dict:
        """Process a single message"""
        self.status = "busy"
        self.current_task = message_data["id"]
        start_time = time.time()
        
        try:
            # Get conversation context from vector DB
            context = await self.orchestrator.vector_service.retrieve_relevant_context(
                message_data["conversation_id"],
                message_data["content"],
                top_k=3
            )
            
            # Build conversation history
            conversation_history = []
            for ctx in context:
                conversation_history.append({
                    "sender_type": "user",
                    "content": ctx["user_message"]
                })
                conversation_history.append({
                    "sender_type": "agent", 
                    "content": ctx["assistant_response"]
                })
            
            # Generate response using LLM
            llm_result = await self.orchestrator.llm_service.generate_response(
                message=message_data["content"],
                conversation_history=conversation_history,
                context=self.specialization,
                user_metadata=message_data.get("metadata", {})
            )
            
            # Store new context in vector DB
            if not llm_result.get("should_escalate"):
                await self.orchestrator.vector_service.store_conversation_context(
                    message_data["conversation_id"],
                    message_data["content"],
                    llm_result["content"],
                    message_data.get("metadata", {})
                )
            
            # Prepare result
            result = {
                "id": message_data["id"],
                "conversation_id": message_data["conversation_id"],
                "content": llm_result["content"],
                "confidence_score": llm_result["confidence_score"],
                "escalated": llm_result["should_escalate"],
                "agent_id": self.id,
                "processing_time_ms": (time.time() - start_time) * 1000,
                "tokens_used": llm_result.get("tokens_used", 0)
            }
            
            # Update agent stats
            self.total_processed += 1
            self.last_activity = datetime.utcnow()
            self.status = "idle"
            self.current_task = None
            
            logger.info(
                "Agent processed message",
                agent_id=self.id,
                message_id=message_data["id"],
                processing_time_ms=result["processing_time_ms"],
                escalated=result["escalated"]
            )
            
            return result
            
        except Exception as e:
            self.errors += 1
            self.status = "error"
            self.current_task = None
            
            logger.error(
                "Agent processing failed",
                agent_id=self.id,
                message_id=message_data["id"],
                error=str(e)
            )
            
            # Return error response with escalation
            return {
                "id": message_data["id"],
                "conversation_id": message_data["conversation_id"],
                "content": "I apologize, but I'm experiencing technical difficulties. Let me connect you with a human agent.",
                "confidence_score": 0.0,
                "escalated": True,
                "agent_id": self.id,
                "processing_time_ms": (time.time() - start_time) * 1000,
                "error": str(e)
            }

class AgentOrchestrator:
    """Orchestrates multiple AI agents with Redis queue and auto-scaling"""
    
    def __init__(self, redis_client: redis.Redis, llm_service: LLMService, vector_service: VectorService):
        self.redis = redis_client
        self.llm_service = llm_service
        self.vector_service = vector_service
        
        # Agent management
        self.agents: Dict[str, Agent] = {}
        self.max_agents = settings.MAX_CONCURRENT_AGENTS
        self.target_agents = settings.WORKER_POOL_SIZE
        
        # Queue configuration
        self.input_stream = "agent_input_stream"
        self.result_stream = "agent_result_stream"
        self.consumer_group = "agent_processors"
        self.batch_size = settings.REDIS_STREAM_BATCH_SIZE
        
        # Statistics
        self.total_messages_processed = 0
        self.total_escalations = 0
        self.average_response_time = 0.0
        self.started_at = datetime.utcnow()
        
        # Control flags
        self.running = False
        self.processing_task = None
        self.scaling_task = None
        
    async def start(self):
        """Start the agent orchestrator"""
        logger.info("Starting agent orchestrator")
        
        # Initialize Redis streams
        await self._initialize_streams()
        
        # Create initial agent pool
        await self._scale_to_target()
        
        # Start processing loop
        self.running = True
        self.processing_task = asyncio.create_task(self._processing_loop())
        self.scaling_task = asyncio.create_task(self._auto_scaling_loop())
        
        logger.info(f"Agent orchestrator started with {len(self.agents)} agents")
    
    async def stop(self):
        """Stop the agent orchestrator"""
        logger.info("Stopping agent orchestrator")
        
        self.running = False
        
        if self.processing_task:
            self.processing_task.cancel()
        
        if self.scaling_task:
            self.scaling_task.cancel()
        
        # Clear agents
        self.agents.clear()
        
        logger.info("Agent orchestrator stopped")
    
    async def _initialize_streams(self):
        """Initialize Redis streams and consumer groups"""
        try:
            # Create consumer group for input stream
            await self.redis.xgroup_create(
                self.input_stream,
                self.consumer_group,
                id="0",
                mkstream=True
            )
        except redis.ResponseError as e:
            if "BUSYGROUP" not in str(e):
                raise
        
        try:
            # Create consumer group for result stream
            await self.redis.xgroup_create(
                self.result_stream,
                self.consumer_group,
                id="0", 
                mkstream=True
            )
        except redis.ResponseError as e:
            if "BUSYGROUP" not in str(e):
                raise
    
    async def _processing_loop(self):
        """Main processing loop for handling messages"""
        consumer_id = f"orchestrator_{uuid.uuid4().hex[:8]}"
        
        while self.running:
            try:
                # Read messages from input stream
                messages = await self.redis.xreadgroup(
                    self.consumer_group,
                    consumer_id,
                    {self.input_stream: ">"},
                    count=self.batch_size,
                    block=1000  # 1 second timeout
                )
                
                if messages:
                    # Process messages in parallel
                    tasks = []
                    for stream, stream_messages in messages:
                        for message_id, fields in stream_messages:
                            task = asyncio.create_task(
                                self._handle_message(message_id, fields)
                            )
                            tasks.append(task)
                    
                    if tasks:
                        await asyncio.gather(*tasks, return_exceptions=True)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Processing loop error", error=str(e))
                await asyncio.sleep(1)
    
    async def _handle_message(self, message_id: bytes, fields: Dict):
        """Handle a single message from the queue"""
        try:
            # Parse message data
            message_data = json.loads(fields[b"data"])
            
            # Find available agent
            agent = await self._get_available_agent()
            
            if not agent:
                # If no agents available, requeue the message
                await asyncio.sleep(0.1)
                return
            
            # Process message
            result = await agent.process_message(message_data)
            
            # Store result in result stream
            await self.redis.xadd(
                self.result_stream,
                {
                    "message_id": message_id.decode(),
                    "result": json.dumps(result)
                }
            )
            
            # Acknowledge message processing
            await self.redis.xack(self.input_stream, self.consumer_group, message_id)
            
            # Update statistics
            self.total_messages_processed += 1
            if result.get("escalated"):
                self.total_escalations += 1
            
            # Update average response time
            response_time = result.get("processing_time_ms", 0)
            self.average_response_time = (
                (self.average_response_time * (self.total_messages_processed - 1) + response_time) /
                self.total_messages_processed
            )
            
        except Exception as e:
            logger.error("Message handling failed", error=str(e), message_id=message_id)
    
    async def _get_available_agent(self) -> Optional[Agent]:
        """Get an available agent for processing"""
        for agent in self.agents.values():
            if agent.status == "idle":
                return agent
        return None
    
    async def _auto_scaling_loop(self):
        """Auto-scaling loop to adjust agent count based on load"""
        while self.running:
            try:
                # Get queue length
                queue_info = await self.redis.xinfo_stream(self.input_stream)
                pending_messages = queue_info.get("length", 0)
                
                # Calculate desired agent count
                if pending_messages > len(self.agents) * 2:
                    # Scale up
                    desired_count = min(
                        len(self.agents) + max(1, pending_messages // 10),
                        self.max_agents
                    )
                elif pending_messages == 0 and len(self.agents) > self.target_agents:
                    # Scale down gradually
                    desired_count = max(
                        len(self.agents) - 1,
                        self.target_agents
                    )
                else:
                    desired_count = len(self.agents)
                
                # Apply scaling
                if desired_count != len(self.agents):
                    await self._scale_to_count(desired_count)
                
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Auto-scaling error", error=str(e))
                await asyncio.sleep(5)
    
    async def _scale_to_target(self):
        """Scale to target agent count"""
        await self._scale_to_count(self.target_agents)
    
    async def _scale_to_count(self, target_count: int):
        """Scale to specific agent count"""
        current_count = len(self.agents)
        
        if target_count > current_count:
            # Scale up
            for i in range(target_count - current_count):
                agent_id = f"agent_{uuid.uuid4().hex[:8]}"
                agent = Agent(agent_id, self)
                self.agents[agent_id] = agent
                
                logger.info(f"Added agent {agent_id}")
        
        elif target_count < current_count:
            # Scale down
            agents_to_remove = list(self.agents.keys())[:current_count - target_count]
            for agent_id in agents_to_remove:
                agent = self.agents[agent_id]
                if agent.status == "idle":
                    del self.agents[agent_id]
                    logger.info(f"Removed agent {agent_id}")
        
        logger.info(f"Scaled to {len(self.agents)} agents (target: {target_count})")
    
    async def process_message(self, message_data: Dict) -> Dict:
        """Add message to processing queue and wait for result"""
        try:
            # Add to input stream
            message_id = await self.redis.xadd(
                self.input_stream,
                {"data": json.dumps(message_data)}
            )
            
            # Wait for result with timeout
            timeout = settings.MAX_RESPONSE_TIME_MS / 1000  # Convert to seconds
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                # Check result stream
                results = await self.redis.xread(
                    {self.result_stream: "0"},
                    count=1000,
                    block=100
                )
                
                for stream, stream_messages in results:
                    for result_id, fields in stream_messages:
                        if fields.get(b"message_id") == message_id:
                            result = json.loads(fields[b"result"])
                            
                            # Clean up result from stream
                            await self.redis.xdel(self.result_stream, result_id)
                            
                            return result
                
                await asyncio.sleep(0.1)
            
            # Timeout reached
            raise TimeoutError(f"Message processing timeout after {timeout}s")
            
        except Exception as e:
            logger.error("Message processing failed", error=str(e))
            raise
    
    async def get_active_agent_count(self) -> int:
        """Get number of active agents"""
        return len(self.agents)
    
    async def get_dashboard_stats(self) -> Dict:
        """Get dashboard statistics"""
        uptime = datetime.utcnow() - self.started_at
        
        # Get queue info
        try:
            queue_info = await self.redis.xinfo_stream(self.input_stream)
            pending_messages = queue_info.get("length", 0)
        except:
            pending_messages = 0
        
        # Calculate agent distribution
        agent_status_count = {}
        for agent in self.agents.values():
            status = agent.status
            agent_status_count[status] = agent_status_count.get(status, 0) + 1
        
        # Calculate resolution rate
        resolution_rate = 1.0 - (self.total_escalations / max(1, self.total_messages_processed))
        
        return {
            "total_agents": len(self.agents),
            "agent_status": agent_status_count,
            "total_messages_processed": self.total_messages_processed,
            "total_escalations": self.total_escalations,
            "resolution_rate": round(resolution_rate, 3),
            "average_response_time_ms": round(self.average_response_time, 2),
            "pending_messages": pending_messages,
            "uptime_seconds": uptime.total_seconds(),
            "messages_per_minute": round(
                self.total_messages_processed / max(1, uptime.total_seconds() / 60), 2
            )
        }
    
    async def get_agents_status(self) -> List[Dict]:
        """Get detailed status of all agents"""
        agents_status = []
        
        for agent in self.agents.values():
            agents_status.append({
                "id": agent.id,
                "status": agent.status,
                "specialization": agent.specialization,
                "total_processed": agent.total_processed,
                "errors": agent.errors,
                "current_task": agent.current_task,
                "last_activity": agent.last_activity.isoformat(),
                "success_rate": round(
                    (agent.total_processed - agent.errors) / max(1, agent.total_processed), 3
                )
            })
        
        return agents_status
    
    async def scale_agents(self, target_count: int):
        """Manually scale agents to target count"""
        target_count = max(1, min(target_count, self.max_agents))
        await self._scale_to_count(target_count)
    
    async def get_conversations(self, limit: int = 50, offset: int = 0, channel: Optional[str] = None) -> List[Dict]:
        """Get conversation summaries - placeholder implementation"""
        # This would typically query the database
        # For now, return mock data
        return []
    
    async def get_conversation_details(self, conversation_id: str) -> Optional[Dict]:
        """Get conversation details - placeholder implementation"""
        # This would typically query the database and vector store
        return None 
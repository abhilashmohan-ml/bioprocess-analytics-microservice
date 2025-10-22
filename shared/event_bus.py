"""Event bus for microservices communication"""
import json
import redis
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable
from enum import Enum
import uuid
import asyncio
from functools import wraps
import logging

logger = logging.getLogger(__name__)

class EventType(Enum):
    """Defined event types for the system"""
    USER_CREATED = "user.created"
    USER_UPDATED = "user.updated" 
    USER_DELETED = "user.deleted"
    USER_LOGIN_SUCCESS = "user.login.success"
    USER_LOGIN_FAILED = "user.login.failed"
    BATCH_CREATED = "batch.created"
    BATCH_UPDATED = "batch.updated"
    BATCH_DELETED = "batch.deleted"
    QC_BATCH_CREATED = "qc_batch.created"
    QC_BATCH_APPROVED = "qc_batch.approved"
    QC_BATCH_REJECTED = "qc_batch.rejected"
    SYSTEM_ERROR = "system.error"
    SECURITY_ALERT = "security.alert"

class EventBus:
    """Redis-based event bus for distributed event handling"""
    
    def __init__(self, redis_url: str = "redis://redis:6379/0"):
        """Initialize event bus with Redis connection"""
        try:
            self.redis_client = redis.Redis.from_url(
                redis_url, 
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            # Test connection
            self.redis_client.ping()
            logger.info("Event bus connected to Redis successfully")
        except redis.ConnectionError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
            
        self.subscribers: Dict[str, List[Callable]] = {}
        self._running = False
        
    def publish_event(self, event_type: EventType, data: Dict[str, Any], 
                     correlation_id: Optional[str] = None) -> str:
        """
        Publish an event to the bus
        
        Args:
            event_type: Type of event
            data: Event data
            correlation_id: Optional correlation ID for tracing
            
        Returns:
            Event ID
        """
        event_id = str(uuid.uuid4())
        
        event = {
            "id": event_id,
            "type": event_type.value,
            "timestamp": datetime.utcnow().isoformat(),
            "correlation_id": correlation_id or event_id,
            "source": "bioprocess-service",
            "data": data,
            "version": "1.0"
        }
        
        try:
            # Publish to Redis pub/sub for real-time events
            self.redis_client.publish(
                f"events:{event_type.value}", 
                json.dumps(event, default=str)
            )
            
            # Store for replay capability (keep last 1000 events per type)
            event_key = f"event_log:{event_type.value}"
            self.redis_client.lpush(event_key, json.dumps(event, default=str))
            self.redis_client.ltrim(event_key, 0, 999)
            
            # Set expiration on event log (7 days)
            self.redis_client.expire(event_key, 7 * 24 * 3600)
            
            logger.info(f"Published event {event_id} of type {event_type.value}")
            return event_id
            
        except redis.RedisError as e:
            logger.error(f"Failed to publish event: {e}")
            raise
            
    def subscribe(self, event_type: EventType, handler: Callable):
        """Subscribe to events of a specific type"""
        if event_type.value not in self.subscribers:
            self.subscribers[event_type.value] = []
        self.subscribers[event_type.value].append(handler)
        logger.info(f"Handler subscribed to {event_type.value}")
        
    def unsubscribe(self, event_type: EventType, handler: Callable):
        """Unsubscribe a handler from events"""
        if event_type.value in self.subscribers:
            self.subscribers[event_type.value].remove(handler)
            logger.info(f"Handler unsubscribed from {event_type.value}")
            
    async def process_events(self):
        """Process incoming events (run in separate task)"""
        pubsub = self.redis_client.pubsub()
        
        # Subscribe to all event types
        channels = [f"events:{et.value}" for et in EventType]
        pubsub.subscribe(*channels)
        
        self._running = True
        logger.info("Event processor started")
        
        try:
            for message in pubsub.listen():
                if not self._running:
                    break
                    
                if message['type'] == 'message':
                    try:
                        event = json.loads(message['data'])
                        event_type = event['type']
                        
                        logger.debug(f"Processing event {event['id']} of type {event_type}")
                        
                        # Call registered handlers
                        if event_type in self.subscribers:
                            for handler in self.subscribers[event_type]:
                                try:
                                    # Handle both sync and async handlers
                                    if asyncio.iscoroutinefunction(handler):
                                        await handler(event)
                                    else:
                                        handler(event)
                                except Exception as e:
                                    logger.error(f"Handler error for {event_type}: {e}")
                                    
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to decode event message: {e}")
                    except Exception as e:
                        logger.error(f"Error processing event: {e}")
                        
        except Exception as e:
            logger.error(f"Event processor error: {e}")
        finally:
            pubsub.close()
            logger.info("Event processor stopped")
            
    def stop_processing(self):
        """Stop the event processor"""
        self._running = False
        
    def get_event_history(self, event_type: EventType, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent events of a specific type"""
        try:
            events = self.redis_client.lrange(f"event_log:{event_type.value}", 0, limit - 1)
            return [json.loads(event) for event in events]
        except redis.RedisError as e:
            logger.error(f"Failed to get event history: {e}")
            return []

# Global event bus instance
event_bus = EventBus()

# Decorator for event handlers
def event_handler(event_type: EventType):
    """Decorator to register event handlers"""
    def decorator(func: Callable):
        event_bus.subscribe(event_type, func)
        return func
    return decorator
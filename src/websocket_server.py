import asyncio
import json
from typing import Dict, Any
from fastapi import WebSocket, WebSocketDisconnect
from ..config.logger import logger
from ..analyzers import HybridAnalyzer
from ..models import AnalysisRequest


class WebSocketManager:
    """Manages WebSocket connections for real-time analysis."""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.analyzer = HybridAnalyzer()
    
    async def connect(self, websocket: WebSocket, client_id: str):
        """Accept WebSocket connection."""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"🔌 WebSocket connected: {client_id}")
    
    def disconnect(self, client_id: str):
        """Disconnect WebSocket client."""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"🔌 WebSocket disconnected: {client_id}")
    
    async def broadcast_analysis(self, result: Dict[str, Any]):
        """Broadcast analysis result to all connected clients."""
        message = {
            "type": "analysis_result",
            "data": result,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        disconnected = []
        for client_id, websocket in self.active_connections.items():
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.warning(f"Failed to send to {client_id}: {e}")
                disconnected.append(client_id)
        
        # Clean up disconnected clients
        for client_id in disconnected:
            self.disconnect(client_id)


websocket_manager = WebSocketManager()


@app.websocket("/ws/prompt-assist")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time prompt analysis."""
    client_id = str(uuid.uuid4())
    
    try:
        await websocket_manager.connect(websocket, client_id)
        
        while True:
            # Receive message
            data = await websocket.receive_text()
            request = json.loads(data)
            
            logger.info(f"[WS] Analyzing prompt from {client_id}: {request.get('text', '')[:50]}...")
            
            # Perform analysis
            analysis_request = AnalysisRequest(
                text=request.get("text", ""),
                use_llm=request.get("use_llm", False)
            )
            
            issues = await websocket_manager.analyzer.analyze(
                analysis_request.text,
                analysis_request.use_llm
            )
            
            result = {
                "issues": [issue.model_dump() for issue in issues],
                "quality_score": websocket_manager.analyzer.calculate_quality_score(
                    analysis_request.text, issues
                ),
                "token_count": token_counter.count_tokens(analysis_request.text)
            }
            
            # Broadcast result
            await websocket_manager.broadcast_analysis(result)
            
    except WebSocketDisconnect:
        logger.info(f"[WS] Client {client_id} disconnected")
    except Exception as e:
        logger.error(f"[WS] Error with client {client_id}: {e}")
    finally:
        websocket_manager.disconnect(client_id)

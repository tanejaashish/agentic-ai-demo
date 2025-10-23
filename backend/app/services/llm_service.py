"""
LLM Service for Ollama integration
Handles text generation using local LLM
"""

import asyncio
import aiohttp
import json
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class LLMService:
    """
    Service for managing LLM interactions with Ollama
    """
    
    def __init__(
        self,
        host: str = "http://localhost:11434",
        model: str = "llama3.2:3b",
        timeout: int = 60
    ):
        self.host = host
        self.model = model
        self.timeout = timeout
        self.session = None
        
        logger.info(f"LLMService initialized with model: {model}")
    
    async def _ensure_session(self):
        """Ensure aiohttp session exists"""
        if self.session is None:
            self.session = aiohttp.ClientSession()
    
    async def generate(
        self,
        prompt: str,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        top_p: float = 0.9,
        stream: bool = False
    ) -> str:
        """
        Generate text using Ollama
        """
        await self._ensure_session()
        
        try:
            # Prepare request payload
            payload = {
                "model": self.model,
                "prompt": prompt,
                "options": {
                    "temperature": temperature,
                    "top_p": top_p,
                    "num_predict": max_tokens
                },
                "stream": stream
            }
            
            # Make request to Ollama
            url = f"{self.host}/api/generate"
            
            async with self.session.post(
                url,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            ) as response:
                if response.status == 200:
                    if stream:
                        # Handle streaming response
                        full_response = ""
                        async for line in response.content:
                            if line:
                                try:
                                    data = json.loads(line)
                                    if "response" in data:
                                        full_response += data["response"]
                                except json.JSONDecodeError:
                                    continue
                        return full_response
                    else:
                        # Handle non-streaming response
                        data = await response.json()
                        return data.get("response", "")
                else:
                    error_text = await response.text()
                    logger.error(f"Ollama API error: {response.status} - {error_text}")
                    return self._get_fallback_response(prompt)
                    
        except asyncio.TimeoutError:
            logger.error("Ollama request timed out")
            return self._get_fallback_response(prompt)
        except Exception as e:
            logger.error(f"Failed to generate text: {e}")
            return self._get_fallback_response(prompt)
    
    async def generate_json(
        self,
        prompt: str,
        max_tokens: int = 1024,
        temperature: float = 0.3
    ) -> Dict[str, Any]:
        """
        Generate JSON response from LLM
        """
        # Append JSON instruction to prompt
        json_prompt = f"{prompt}\n\nRespond with valid JSON only, no other text."
        
        response = await self.generate(
            prompt=json_prompt,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        # Try to parse JSON from response
        try:
            # Clean response
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]
            
            return json.loads(response)
        except json.JSONDecodeError:
            logger.warning("Failed to parse JSON from LLM response")
            # Return a default structure
            return {
                "solution_steps": [response],
                "confidence": 0.5
            }
    
    async def check_health(self) -> bool:
        """
        Check if Ollama service is healthy
        """
        await self._ensure_session()
        
        try:
            url = f"{self.host}/api/version"
            async with self.session.get(
                url,
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                return response.status == 200
        except:
            return False
    
    async def list_models(self) -> List[str]:
        """
        List available models in Ollama
        """
        await self._ensure_session()
        
        try:
            url = f"{self.host}/api/tags"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return [model["name"] for model in data.get("models", [])]
                return []
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            return []
    
    async def pull_model(self, model_name: str):
        """
        Pull a model from Ollama registry
        """
        await self._ensure_session()
        
        try:
            url = f"{self.host}/api/pull"
            payload = {"name": model_name}
            
            async with self.session.post(url, json=payload) as response:
                async for line in response.content:
                    if line:
                        data = json.loads(line)
                        if "status" in data:
                            logger.info(f"Pulling {model_name}: {data['status']}")
                            
        except Exception as e:
            logger.error(f"Failed to pull model: {e}")
    
    def _get_fallback_response(self, prompt: str) -> str:
        """
        Generate a fallback response when LLM is unavailable
        """
        # Simple rule-based fallback for demo
        if "database" in prompt.lower():
            return """
            1. Check database connection settings
            2. Verify network connectivity to database server
            3. Review connection pool configuration
            4. Check for any recent configuration changes
            5. Monitor database server resources
            """
        elif "api" in prompt.lower():
            return """
            1. Check API gateway status
            2. Verify upstream service health
            3. Review rate limiting settings
            4. Check SSL certificates
            5. Monitor API response times
            """
        elif "memory" in prompt.lower():
            return """
            1. Analyze memory usage patterns
            2. Check for memory leaks
            3. Review heap dump if available
            4. Optimize memory allocation
            5. Consider scaling resources
            """
        else:
            return """
            1. Gather more information about the issue
            2. Check system logs for errors
            3. Review recent changes
            4. Escalate to appropriate team if needed
            5. Document findings for future reference
            """
    
    async def close(self):
        """
        Close the aiohttp session
        """
        if self.session:
            await self.session.close()
            self.session = None
            logger.info("LLMService closed")
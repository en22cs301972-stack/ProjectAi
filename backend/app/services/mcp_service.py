"""
Model Context Protocol (MCP) Service
Manages tool discovery and execution for AI agents
"""
import json
import asyncio
from typing import Any, Dict, List, Optional
import structlog

logger = structlog.get_logger()


# MCP Tool Registry
MCP_TOOLS = {
    "gmail": {
        "name": "gmail",
        "description": "Read and send Gmail emails",
        "parameters": {
            "action": {"type": "string", "enum": ["list", "read", "send", "reply"]},
            "query": {"type": "string", "description": "Search query for list action"},
            "message_id": {"type": "string", "description": "Email ID for read/reply"},
            "to": {"type": "string", "description": "Recipient for send action"},
            "subject": {"type": "string"},
            "body": {"type": "string"},
        },
        "required_keys": ["gmail_credentials"],
    },
    "stock_market": {
        "name": "stock_market",
        "description": "Get stock market data",
        "parameters": {
            "action": {"type": "string", "enum": ["quote", "history", "search"]},
            "symbol": {"type": "string", "description": "Stock ticker symbol"},
            "period": {"type": "string", "description": "Time period for history"},
        },
        "required_keys": ["market_api_key"],
    },
    "crypto": {
        "name": "crypto",
        "description": "Get cryptocurrency data",
        "parameters": {
            "action": {"type": "string", "enum": ["price", "history", "market_cap"]},
            "symbol": {"type": "string", "description": "Crypto symbol (BTC, ETH, etc.)"},
        },
        "required_keys": [],
    },
    "web_search": {
        "name": "web_search",
        "description": "Search the web for information",
        "parameters": {
            "query": {"type": "string", "description": "Search query"},
            "num_results": {"type": "integer", "default": 5},
        },
        "required_keys": ["search_api_key"],
    },
    "code_executor": {
        "name": "code_executor",
        "description": "Execute code in sandbox",
        "parameters": {
            "code": {"type": "string"},
            "language": {"type": "string", "enum": ["python", "javascript", "sql"]},
        },
        "required_keys": [],
    },
}


class MCPService:
    """Model Context Protocol service for managing agent tools."""

    def __init__(self, api_keys: Dict[str, str] = None):
        self.api_keys = api_keys or {}
        self.available_tools = []
        self._discover_tools()

    def _discover_tools(self):
        """Dynamically discover available tools based on API keys."""
        self.available_tools = []
        for tool_name, tool_config in MCP_TOOLS.items():
            required_keys = tool_config.get("required_keys", [])
            if all(key in self.api_keys for key in required_keys):
                self.available_tools.append(tool_name)
        logger.info("MCP tools discovered", tools=self.available_tools)

    def list_tools(self) -> List[Dict]:
        """List all available tools with their schemas."""
        tools = []
        for tool_name in self.available_tools:
            if tool_name in MCP_TOOLS:
                tools.append(MCP_TOOLS[tool_name])
        return tools

    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool with given parameters."""
        if tool_name not in self.available_tools:
            return {
                "success": False,
                "error": f"Tool '{tool_name}' not available or not configured",
            }

        try:
            if tool_name == "gmail":
                return await self._execute_gmail(parameters)
            elif tool_name == "stock_market":
                return await self._execute_stock_market(parameters)
            elif tool_name == "crypto":
                return await self._execute_crypto(parameters)
            elif tool_name == "web_search":
                return await self._execute_web_search(parameters)
            elif tool_name == "code_executor":
                return await self._execute_code(parameters)
            else:
                return {"success": False, "error": f"Tool '{tool_name}' not implemented"}
        except Exception as e:
            logger.error("Tool execution error", tool=tool_name, error=str(e))
            return {"success": False, "error": str(e)}

    async def _execute_gmail(self, params: Dict) -> Dict:
        """Execute Gmail tool."""
        from googleapiclient.discovery import build
        from google.oauth2.credentials import Credentials
        import base64
        from email.mime.text import MIMEText

        try:
            creds_data = json.loads(self.api_keys.get("gmail_credentials", "{}"))
            creds = Credentials(**creds_data)
            service = build("gmail", "v1", credentials=creds)

            action = params.get("action")

            if action == "list":
                query = params.get("query", "is:unread")
                results = service.users().messages().list(
                    userId="me", q=query, maxResults=10
                ).execute()
                messages = results.get("messages", [])
                return {"success": True, "messages": messages, "count": len(messages)}

            elif action == "read":
                msg_id = params.get("message_id")
                msg = service.users().messages().get(userId="me", id=msg_id).execute()
                return {"success": True, "message": msg}

            elif action == "send":
                message = MIMEText(params.get("body", ""))
                message["to"] = params.get("to")
                message["subject"] = params.get("subject", "")
                raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
                sent = service.users().messages().send(
                    userId="me", body={"raw": raw}
                ).execute()
                return {"success": True, "message_id": sent["id"]}

            return {"success": False, "error": f"Unknown action: {action}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _execute_stock_market(self, params: Dict) -> Dict:
        """Execute stock market tool using free APIs."""
        import httpx

        try:
            symbol = params.get("symbol", "AAPL").upper()
            action = params.get("action", "quote")
            api_key = self.api_keys.get("market_api_key", "demo")

            url = f"https://www.alphavantage.co/query"

            if action == "quote":
                response_data = httpx.get(url, params={
                    "function": "GLOBAL_QUOTE",
                    "symbol": symbol,
                    "apikey": api_key,
                }).json()
                return {"success": True, "data": response_data}

            return {"success": False, "error": f"Unknown action: {action}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _execute_crypto(self, params: Dict) -> Dict:
        """Execute crypto tool using CoinGecko free API."""
        import httpx

        try:
            symbol = params.get("symbol", "bitcoin").lower()
            action = params.get("action", "price")

            coin_map = {
                "btc": "bitcoin", "eth": "ethereum", "usdt": "tether",
                "bnb": "binancecoin", "sol": "solana",
            }
            coin_id = coin_map.get(symbol.lower(), symbol)

            if action == "price":
                url = "https://api.coingecko.com/api/v3/simple/price"
                response = httpx.get(url, params={
                    "ids": coin_id,
                    "vs_currencies": "usd",
                    "include_24hr_change": "true",
                })
                return {"success": True, "data": response.json()}

            return {"success": False, "error": f"Unknown action: {action}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _execute_web_search(self, params: Dict) -> Dict:
        """Execute web search."""
        # Placeholder - would use DuckDuckGo or similar
        return {
            "success": True,
            "results": [
                {"title": "Search result placeholder", "url": "https://example.com", "snippet": "Web search not fully configured"}
            ],
        }

    async def _execute_code(self, params: Dict) -> Dict:
        """Execute code using the code execution service."""
        from app.services.code_execution import execute_code

        result = await execute_code(
            code=params.get("code", ""),
            language=params.get("language", "python"),
        )
        return {"success": result["status"] == "success", **result}


async def run_agent_task(
    agent_config: Dict,
    api_keys: Dict[str, str],
    task: str,
    custom_ai_key: str = None,
) -> Dict[str, Any]:
    """Run an agent task using MCP tools."""
    from app.services.ai_service import get_ai_response

    mcp = MCPService(api_keys=api_keys)
    available_tools = mcp.list_tools()

    tools_description = "\n".join([
        f"- {t['name']}: {t['description']}" for t in available_tools
    ])

    system_prompt = f"""You are an autonomous AI agent with access to the following tools:
{tools_description}

When you need to use a tool, respond with JSON in this format:
{{"tool": "tool_name", "parameters": {{"param1": "value1"}}}}

When you have completed the task, respond with:
{{"done": true, "result": "your final answer"}}

Agent config: {json.dumps(agent_config)}"""

    messages = [{"role": "user", "content": task}]
    results = []
    max_iterations = 10

    for i in range(max_iterations):
        response = await get_ai_response(
            messages=messages,
            system_prompt=system_prompt,
            temperature=0.3,
            custom_api_key=custom_ai_key,
        )

        messages.append({"role": "assistant", "content": response})

        # Check if response is a tool call
        try:
            start = response.find("{")
            end = response.rfind("}") + 1
            if start != -1 and end > start:
                data = json.loads(response[start:end])

                if data.get("done"):
                    return {
                        "success": True,
                        "result": data.get("result"),
                        "iterations": i + 1,
                        "tool_results": results,
                    }

                if data.get("tool"):
                    tool_result = await mcp.execute_tool(data["tool"], data.get("parameters", {}))
                    results.append({"tool": data["tool"], "result": tool_result})
                    messages.append({
                        "role": "user",
                        "content": f"Tool result: {json.dumps(tool_result)}",
                    })
                    continue
        except json.JSONDecodeError:
            pass

        # If no structured response, return the text response
        return {
            "success": True,
            "result": response,
            "iterations": i + 1,
            "tool_results": results,
        }

    return {
        "success": False,
        "result": "Max iterations reached",
        "iterations": max_iterations,
        "tool_results": results,
    }

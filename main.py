import os
import requests
import asyncio
from mcp.server.fastmcp import FastMCP
from mcp.server.stdio import stdio_server

ENFORMION_URL = "https://devapi.enformion.com/Contact/Enrich"

async def call_enformion_api(request_body: dict):
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "galaxy-ap-name": os.getenv("GALAXY_AP_NAME"),
        "galaxy-ap-password": os.getenv("GALAXY_AP_PASSWORD"),
        "galaxy-search-type": "DevAPIContactEnrich",
    }
    try:
        response = requests.post(ENFORMION_URL, headers=headers, json=request_body)
        response.raise_for_status()
        return {"success": True, "data": response.json()}
    except requests.RequestException as e:
        return {"success": False, "error": str(e)}

async def main():
    server = FastMCP("enformion-mcp")

    @server.tool(
        name="enformion_contact_enrich",
        description="Call Enformion's Contact Enrich API. Pass JSON with keys like FirstName, LastName, Address."
    )
    async def enrich_tool(body: dict):
        return await call_enformion_api(body)


if __name__ == "__main__":
    asyncio.run(main())

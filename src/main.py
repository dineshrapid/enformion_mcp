from fastmcp import FastMCP
import os
import json
import httpx
import asyncio
from dotenv import load_dotenv

load_dotenv()

ENFORMION_URL = "https://devapi.enformion.com/Contact/Enrich"
app = FastMCP("enformion-fastmcp")


def check_and_raise_on_error(result: dict) -> dict:
    if not result.get("success", True):
        raise Exception(result.get("error", "Unknown error occurred"))
    return result


async def call_enformion_api(request_body: dict) -> dict:
    if not os.getenv("GALAXY_AP_NAME") or not os.getenv("GALAXY_AP_PASSWORD"):
        raise EnvironmentError("Missing required Enformion API credentials in .env")

    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "galaxy-ap-name": os.getenv("GALAXY_AP_NAME", ""),
        "galaxy-ap-password": os.getenv("GALAXY_AP_PASSWORD", ""),
        "galaxy-search-type": "DevAPIContactEnrich",
    }

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            response = await client.post(ENFORMION_URL, headers=headers, json=request_body)
            response.raise_for_status()
            return {"success": True, "data": response.json()}
        except httpx.RequestError as e:
            return {"success": False, "error": f"Request failed: {e}"}
        except httpx.HTTPStatusError as e:
            return {
                "success": False,
                "error": f"HTTP error: {e.response.status_code} - {e.response.text}",
            }


@app.tool(name="enformion_contact_enrich")
async def enformion_contact_enrich(arguments: dict):
    """
    Call Enformion's Contact Enrich API to enrich contact details.
    """
    result = await call_enformion_api(arguments)
    result = check_and_raise_on_error(result)
    return json.dumps(result, indent=2)


@app.tool
def hello():
    """Simple test tool."""
    return "Hello from Enformion FastMCP"


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(transport="http", host="0.0.0.0", port=port)

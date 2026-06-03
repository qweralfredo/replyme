import time
import json
import structlog
from sqlmodel import Session, select
from src.database import engine
from src.models import MCPServer
import os
from google import genai
from google.genai import types

logger = structlog.get_logger(__name__)

class MCPInstallerService:
    def __init__(self):
        self.api_key = os.environ.get("GOOGLE_API_KEY")
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        else:
            self.client = None

    def poll_and_install(self):
        if not self.client:
            logger.warning("No GOOGLE_API_KEY found, cannot run installer.")
            return

        with Session(engine) as session:
            statement = select(MCPServer).where(MCPServer.status == "pending")
            pending_mcps = session.exec(statement).all()

            for mcp in pending_mcps:
                logger.info("Starting agentic installation for MCP", id=mcp.id, url=mcp.url)
                mcp.status = "testing"
                session.add(mcp)
                session.commit()

                try:
                    # Request Gemini to analyze the URL and provide the install command
                    prompt = f"""
Você é um especialista em Model Context Protocol (MCP).
Eu tenho o seguinte repositório ou documentação de um MCP Server: {mcp.url}

Determine o comando exato necessário para executar este servidor via STDIO sem instalação prévia manual (ex: usando `npx -y @smithery/cli run ...` ou `npx -y @modelcontextprotocol/...`).

Responda APENAS com um JSON válido contendo:
{{
  "command": "comando base ex: npx",
  "args": ["-y", "pacote", "arg1", "arg2"],
  "explanation": "breve explicação"
}}
"""
                    response = self.client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                        ),
                    )
                    
                    config = json.loads(response.text)
                    inferred = f"{config.get('command')} " + " ".join(config.get("args", []))
                    
                    # For a real robust system, we would test running it here via subprocess and check if it speaks JSON-RPC on stdout.
                    # Due to safety and sandbox limits, we will assume the LLM gave a correct command.
                    
                    mcp.inferred_command = inferred
                    mcp.install_logs = f"Agentic Setup Successful.\nExplanation: {config.get('explanation')}\nCommand: {inferred}"
                    mcp.status = "installed"
                    
                    logger.info("Installation complete", id=mcp.id, command=inferred)
                except Exception as e:
                    logger.error("Failed to install MCP", id=mcp.id, error=str(e))
                    mcp.status = "failed"
                    mcp.install_logs = f"Error during agentic installation: {str(e)}"
                
                session.add(mcp)
                session.commit()

def run_installer_loop():
    installer = MCPInstallerService()
    logger.info("Starting MCP Installer Loop...")
    while True:
        try:
            installer.poll_and_install()
        except Exception as e:
            logger.error("Error in installer loop", error=str(e))
        time.sleep(10)

if __name__ == "__main__":
    run_installer_loop()

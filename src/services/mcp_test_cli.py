import sys
import json
import asyncio
from src.database import engine
from sqlmodel import Session
from src.models import MCPServer
from src.services.mcp_agent import run_mcp_agent
import traceback

def main():
    if len(sys.argv) < 3:
        print(json.dumps({"error": "Parâmetros insuficientes"}))
        sys.exit(1)

    mcp_id = int(sys.argv[1])
    prompt = sys.argv[2]
    
    try:
        with Session(engine) as session:
            mcp = session.get(MCPServer, mcp_id)
            if not mcp or not mcp.inferred_command:
                print(json.dumps({"error": "MCP não encontrado ou comando não configurado."}))
                sys.exit(1)
                
            command = mcp.inferred_command
            
        result = asyncio.run(run_mcp_agent({}, prompt, command))
        print(json.dumps({"result": result}))
    except Exception as e:
        print(json.dumps({"error": f"Erro interno: {str(e)}\n{traceback.format_exc()}"}))
        sys.exit(1)

if __name__ == "__main__":
    main()

import asyncio
import os

# Configuração Gemini
from dotenv import load_dotenv
from mcp.client.sse import sse_client

load_dotenv()

import asyncio
import logging
from datetime import datetime

from google import genai
from google.genai import types
from mcp import ClientSession

log_name = datetime.now().strftime("./logs/client_running_%H-%M-%S_%d-%m-%Y.log")
logging.basicConfig(
    filename=log_name,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
    encoding="utf-8",
)

logging.info("Starting client...")
client = genai.Client()


async def run_chatbot():
    # 1. Configura o Servidor MCP (ajuste o caminho para o seu script de servidor)
    mcp_url = os.getenv("MCP_SERVER_URL")
    async with sse_client(mcp_url) as (read, write):
        # 3. Create a session over that transport
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Busca ferramentas do MCP
            mcp_tools_response = await session.list_tools()

            # 2. Converte para o formato da biblioteca google-genai
            gemini_tools = []
            for tool in mcp_tools_response.tools:
                gemini_tools.append(
                    types.FunctionDeclaration(
                        name=tool.name,
                        description=tool.description,
                        parameters=tool.inputSchema,
                    )
                )

            # Define o objeto Tool
            tool_config = types.Tool(function_declarations=gemini_tools)

            logging.info("Chatbot Conectado (google-genai + MCP)!")

            # Histórico do chat
            chat_history = []

            while True:
                user_input = ""
                while len(user_input) < 4:
                    user_input = input("\nDigite: ")

                if user_input.lower() in ["sair", "exit"]:
                    break

                chat_history.append(
                    types.Content(role="user", parts=[types.Part(text=user_input)])
                )

                print("ChatCar Agent: ...")
                response = client.models.generate_content(
                    model="gemini-3.1-flash-lite-preview",
                    contents=chat_history,
                    config=types.GenerateContentConfig(tools=[tool_config]),
                )

                for part in response.candidates[0].content.parts:
                    if part.function_call:
                        call = part.function_call
                        logging.info(
                            f"--- Executing in MCP: {call.name} {call.args} ---"
                        )

                        # Executa no servidor MCP real
                        mcp_result = await session.call_tool(
                            call.name, arguments=call.args
                        )
                        logging.info(f"--- Result: {mcp_result} ---")

                        # Adiciona a chamada e a resposta ao histórico
                        chat_history.append(response.candidates[0].content)
                        chat_history.append(
                            types.Content(
                                role="tool",
                                parts=[
                                    types.Part.from_function_response(
                                        name=call.name,
                                        response={"result": mcp_result.content},
                                    )
                                ],
                            )
                        )

                        # Pede ao modelo para finalizar a resposta com os dados do MCP
                        response = client.models.generate_content(
                            model="gemini-3.1-flash-lite-preview",
                            contents=chat_history,
                            config=types.GenerateContentConfig(tools=[tool_config]),
                        )

                if response.text != None:
                    print(f"ChatCar Agent: {response.text}")
                else:
                    # breakpoint()
                    print("ChatCar Agent: Não consegui processar sua solicitação.")

                chat_history.append(response.candidates[0].content)


if __name__ == "__main__":
    car = (
        """
                  _____       _____
     .........   {     }     {     }
    (>>\zzzzzz [======================]
    ( <<<\lllll_\\ _        _____    \\
   _,`-,\<   __#:\\::_    __#:::_:__  \\
  /    . `--,#::::\\:::___#::::/__+_\ _\\
 /  _  .`-    `--,/_~~~~~~~~~~~~~~~~~~~~  -,_
:,// \ .         .  '--,____________   ______`-,
 :: o |.         .  ___ \_____||____\+/     ||~ \\
 :;   ;-,_       . ,' _`,"""
        """"""
        """"""
        """"""
        """\\
 \ \_/ _ :`-,_   . ; / \\ ====================== /
  \__/~ /     `-,.; ; o |\___[~~~]_ASCII__[~~~]__:
     ~~~          ; :   ;~ ;  ~~~         ;~~~::;
                   \ \_/ ~/               ::::::;
                    \_/~~/                 \:::/
                      ~~~                   ~~~
BEM VINDO AO CHAT DE BUSCA DE CARROS! - Digite 'sair' para encerrar a conversa.
"""
    )
    print(car)
    print("ChatCar Agent: Heeeyy! Qual carro você procura?\n")
    asyncio.run(run_chatbot())

"""Example client."""
import asyncio
import getpass
import json
import os
import time


import websockets

# student imports
from DigDugAI_Stable import DigDugAgent

"""
STUDENTS:
Bernardo Figueiredo - 108073
Alexandre Cotorobai - 107849
"""


async def agent_loop(server_address="localhost:8000", agent_name="student"):
    """Example client loop."""
    async with websockets.connect(f"ws://{server_address}/player") as websocket:
        # Receive information about static game properties
        await websocket.send(json.dumps({"cmd": "join", "name": agent_name}))

        state = json.loads(await websocket.recv())

        digdug = DigDugAgent(state)

        while True:
            try:
                state = json.loads(await websocket.recv())

                # receive game update, this must be called timely or your game will get out of sync with the server

                # Next lines are only for the Human Agent, the key values are nonetheless the correct ones!
                if "map" in state:
                    digdug = DigDugAgent(state)

                if "digdug" not in state or len(state["enemies"]) == 0:
                    continue

                digdug.update_state(state)
                key = digdug.get_next_move()

                await websocket.send(
                    json.dumps({"cmd": "key", "key": key})
                )  # send key command to server - you must implement this send in the AI agent

            except websockets.exceptions.ConnectionClosedOK:
                print("Server has cleanly disconnected us")
                return


# DO NOT CHANGE THE LINES BELLOW
# You can change the default values using the command line, example:
# $ NAME='arrumador' python3 client.py
loop = asyncio.get_event_loop()
SERVER = os.environ.get("SERVER", "localhost")
PORT = os.environ.get("PORT", "8000")
NAME = os.environ.get("NAME", getpass.getuser())
loop.run_until_complete(agent_loop(f"{SERVER}:{PORT}", NAME))

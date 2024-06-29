#!/usr/bin/python3

import os
import requests
import json
import time
import argparse
import math

import threading

import game_utils 

LICHESS_TOKEN = None

def exibir_nome_programa(): 
    print(  """
    ███████╗██╗░░░██╗██╗███╗░░░███╗██████╗░░█████╗░░█████╗░██████╗░██████╗░
    ╚════██║██║░░░██║██║████╗░████║██╔══██╗██╔══██╗██╔══██╗██╔══██╗██╔══██╗
    ░░███╔═╝██║░░░██║██║██╔████╔██║██████╦╝██║░░██║███████║██████╔╝██║░░██║
    ██╔══╝░░██║░░░██║██║██║╚██╔╝██║██╔══██╗██║░░██║██╔══██║██╔══██╗██║░░██║
    ███████╗╚██████╔╝██║██║░╚═╝░██║██████╦╝╚█████╔╝██║░░██║██║░░██║██████╔╝
    ╚══════╝░╚═════╝░╚═╝╚═╝░░░░░╚═╝╚═════╝░░╚════╝░╚═╝░░╚═╝╚═╝░░╚═╝╚═════╝░
            """)

# Dictionary to store threads for each game
game_threads = {}
read_threads = {}

def stream_lichess_events():
    """
    Streams Lichess events indefinitely, handling changes and potential errors.
    """

    url = "https://lichess.org/api/stream/event"
    headers = {"Authorization": f"Bearer {LICHESS_TOKEN}"}

    os.system("clear")
    exibir_nome_programa()
    print("Aguardando iniciar a partida...")

    while True:
        try:
            with requests.get(url, headers=headers, stream=True, timeout=30) as response:
                response.raise_for_status()

                for line in response.iter_lines():
                    if line:
                        try:
                            event = json.loads(line)
                            print(f"Received event: {event}")

                            if event["type"] == "gameStart":
                                game_id = event["game"]["fullId"]
                                color = event["game"]["color"]
                                if game_id not in game_threads:
                                    os.system("clear")
                                    exibir_nome_programa()
                                    print(f"Acesse o jogo pela url: https://lichess.org/{game_id}")

                                    thread = threading.Thread(target=stream_game_status, args=(game_id,color))
                                    game_threads[game_id] = thread
                                    thread.start()

                            elif event["type"] == "gameFinish":
                                game_id = event["game"]["id"]  # gameFinish uses 'id' instead of 'fullId'
                                if game_id in game_threads:
                                    thread = game_threads.pop(game_id)
                                    thread.join()  # Wait for the thread to finish
                                    print(f"Stopped watching game {game_id}")

                        except json.JSONDecodeError as e:
                            print(f"Error decoding JSON: {e}")

        except requests.RequestException as e:
            print(f"Error making request: {e}")
            time.sleep(5)

        except KeyboardInterrupt:
            print("Exiting...")
            break

def encerra_partida(mensagem, game_id):
    print("---------------------------------------------------------------------------------")
    print("FIM DA PARTIDA: ")
    print("---------------------------------------------------------------------------------")
    print(f"Motivo: {mensagem}")
    print("---------------------------------------------------------------------------------")

def calcula_lance(lances):
    cores = ["Brancas", "Negras"]
    lances_arr = lances.split(" ")

    numero_lance = math.ceil((len(lances_arr)) / 2)
    
    print("---------------------------------------------------------------------------------")
    print(f"Lance: {numero_lance}")

    if lances_arr[-1] == "": 
        print(f"{cores[0]} jogam")
        return "white"
    else:
        if len(lances_arr) % 2 == 0:
            print(f"{cores[1]} jogaram {lances_arr[-1]}")
            print("---------------------------------------------------------------------------------")
            print(f"{cores[0]} jogam...")
            return "white"
        else:
            print(f"{cores[0]} jogaram {lances_arr[-1]}")
            print("---------------------------------------------------------------------------------")
            print(f"{cores[1]} jogam...")
            return "black"

def make_bot_move(game_id, move):
    url = f"https://lichess.org/api/bot/game/{game_id}/move/{move}?offeringDraw=false"
    headers = {"Authorization": f"Bearer {LICHESS_TOKEN}"}

    try:
        response = requests.post(url, headers=headers)

        if response.status_code == 200:
            print(f"Lance {move} feito na partida de ID {game_id}")
            return True
        elif response.status_code == 400:
            error_data = response.json()  # Parse the JSON response
            error_message = error_data.get("error", "Unknown error") 
            print(f"Erro ao fazer o lance {move} na partida de ID {game_id}: {error_message}")
            return False
        else:
            response.raise_for_status()  # Raise for other errors
            return False

    except requests.RequestException as e:
        print(f"General request error")
        return False

def your_turn(prev_read, cor_lance_atual, game_id, prev_moves_list_len, game_state):
    m_state = False
    while not m_state:
        if len(prev_read) != 0:
            read = game_utils.read_zuim()

            m = game_utils.get_move(read, prev_read, cor_lance_atual)
            print(f"Got move :{m}")
            m_state = make_bot_move(game_id, m)
            if m_state:
                prev_read = read
        else:
            print("Primeira leitura")
            read = game_utils.read_zuim()
            prev_read = read

    prev_moves_list_len += 1
    return prev_read, prev_moves_list_len

def op_turn(prev_read, cor_lance_atual, game_id, moves_list_len, prev_moves_list_len, game_state):
    op_check = False
    if game_utils.get_last_move(game_state["moves"]) != "":
        if moves_list_len != prev_moves_list_len:
            m_state = False
            op_m = game_utils.get_last_move(game_state["moves"])

            while not m_state:
                op_m = game_utils.get_last_move(game_state["moves"])
                print(f"Last move: {op_m}")

                if len(prev_read) != 0:
                    read = game_utils.read_zuim()

                    m = game_utils.get_move(read, prev_read, cor_lance_atual)
                    print(f"Got move :{m}")

                    if m == op_m:
                        prev_read = read
                        print("Ajuste está correto!")
                        op_check = True
                        cor_lance_atual = game_utils.shuffle(cor_lance_atual)
                        m_state = True
                    else:
                        print("Ajuste NÃO está correto!")
                else:
                    print("Primeira leitura")
                    read = game_utils.read_zuim()
                    prev_read = read
            prev_moves_list_len = moves_list_len

    return prev_read, prev_moves_list_len, op_check

def op_turn_2(prev_read, cor_lance_atual, game_id, moves_list_len, prev_moves_list_len, game_state):
    op_check = False
    if "moves" in game_state["state"]:
        if game_utils.get_last_move(game_state["state"]["moves"]) != "":
            if moves_list_len != prev_moves_list_len:
                m_state = False
                op_m = game_utils.get_last_move(game_state["state"]["moves"])

                while not m_state:
                    op_m = game_utils.get_last_move(game_state["state"]["moves"])
                    print(f"Last move: {op_m}")

                    if len(prev_read) != 0:
                        read = game_utils.read_zuim()

                        m = game_utils.get_move(read, prev_read, cor_lance_atual)
                        print(f"Got move :{m}")

                        if m == op_m:
                            prev_read = read
                            print("Ajuste está correto!")
                            cor_lance_atual = game_utils.shuffle(cor_lance_atual)
                            m_state = True
                        else:
                            print("Ajuste NÃO está correto!")
                    else:
                        print("Primeira leitura")
                        read = game_utils.read_zuim()
                        prev_read = read
                prev_moves_list_len = moves_list_len

    return prev_read, prev_moves_list_len, op_check

def stream_game_status(game_id, color):
    url = f"https://lichess.org/api/bot/game/stream/{game_id}"
    headers = {"Authorization": f"Bearer {LICHESS_TOKEN}"}
    
    prev_read = []
    prev_moves_list_len = 0

    while True:
        try:
            with requests.get(url, headers=headers, stream=True, timeout=30) as response:
                response.raise_for_status()

                for line in response.iter_lines():
                    if line:
                        try:
                            game_state = json.loads(line)

                            if "id" not in game_state:
                                if game_state["status"] != "started":
                                    if game_state["status"] == "resign": 
                                        encerra_partida("Abandono", game_id)
                                        return
                                    elif game_state["status"] == "mate":
                                        encerra_partida("Checkmate", game_id)
                                        return
                                    else:
                                        encerra_partida("Não especificado", game_id)
                                        return

                                cor_lance_atual = calcula_lance(game_state["moves"])
                                
                                moves_list_len = game_utils.get_moves_list_len(game_state["moves"])
                                if prev_moves_list_len == 0:
                                    prev_moves_list_len = moves_list_len
                                if prev_moves_list_len != moves_list_len:
                                    cor_lance_atual = game_utils.shuffle(cor_lance_atual)
                                print(f"Prev moves: {prev_moves_list_len}")
                                print(f"New moves: {moves_list_len}")

                                if cor_lance_atual == color:    # Sua vez
                                    prev_read, prev_moves_list_len = your_turn(prev_read, 
                                                                               cor_lance_atual, 
                                                                               game_id, 
                                                                               prev_moves_list_len,
                                                                               game_state)

                                else:   # Vez do oponente
                                    prev_read, prev_moves_list_len, op_check = op_turn(prev_read, 
                                                                               cor_lance_atual,
                                                                               game_id,
                                                                               moves_list_len,
                                                                               prev_moves_list_len,
                                                                               game_state)
                                    if (op_check):
                                        cor = game_utils.shuffle(cor_lance_atual)
                                        prev_read, prev_moves_list_len = your_turn(prev_read, 
                                                                                   game_utils.shuffle(cor_lance_atual), 
                                                                                   game_id, 
                                                                                   prev_moves_list_len,
                                                                                   game_state)

                            else:
                                if "moves" in game_state["state"]:
                                    cor_lance_atual = calcula_lance(game_state["state"]["moves"])

                                    moves_list_len = game_utils.get_moves_list_len(game_state["state"]["moves"])
                                    if prev_moves_list_len == 0:
                                        prev_moves_list_len = moves_list_len
                                    if prev_moves_list_len != moves_list_len:
                                        cor_lance_atual = game_utils.shuffle(cor_lance_atual)

                                    print(f"Prev moves: {prev_moves_list_len}")
                                    print(f"New moves: {moves_list_len}")

                                    if cor_lance_atual == color:    # Sua vez
                                        prev_read, prev_moves_list_len = your_turn(prev_read, 
                                                                                   cor_lance_atual, 
                                                                                   game_id, 
                                                                                   prev_moves_list_len,
                                                                                   game_state)
                                    else:       # Vez do oponente
                                        prev_read, prev_moves_list_len, op_check = op_turn_2(prev_read, 
                                                                                   cor_lance_atual,
                                                                                   game_id,
                                                                                   moves_list_len,
                                                                                   prev_moves_list_len,
                                                                                   game_state)

                                        if (op_check):
                                            cor = game_utils.shuffle(cor_lance_atual)
                                            prev_read, prev_moves_list_len = your_turn(prev_read, 
                                                                                       game_utils.shuffle(cor_lance_atual), 
                                                                                       game_id, 
                                                                                       prev_moves_list_len,
                                                                                       game_state)


                                if game_state["state"]["status"] == "aborted":
                                    encerra_partida("Jogo abortado", game_id)
                                    return

                        except json.JSONDecodeError as e:
                            print(f"Error decoding JSON in game stream: {e}")

        except requests.RequestException as e:
            print(f"Error making game status request: {e}")
            time.sleep(5)

        except KeyboardInterrupt:
            print("Exiting...")
            break

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Zuimboard")
    parser.add_argument("token", help="Token de altenticação do Lichess")
    args = parser.parse_args()
    
    LICHESS_TOKEN = args.token

    exibir_nome_programa()
    stream_lichess_events()

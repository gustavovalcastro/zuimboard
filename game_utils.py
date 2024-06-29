import serial
import time
import os
import sys

import json

ser = serial.Serial('/dev/ttyUSB0', 115200)
 
def read_zuim():
    print("Lendo estados do tabuleiro...")
    json_cb = None

    try:
        while True:
            if ser.in_waiting > 0:
                chessboard_state = ser.readline().decode('utf-8')

                json_cb = json.loads(chessboard_state) 

                break

            time.sleep(0.25)
    except KeyboardInterrupt:
        print("Program terminated!")
        return "Erro na leitura"
    finally:
        return json_cb

def get_last_move(lances):
        lances_arr = lances.split(" ")
        return lances_arr[-1]

def get_move(read, prev_read, color):
    print("Previous")
    for i, row in enumerate(prev_read):
        print(f"row {i}: {row}")

    print("New")
    for i, row in enumerate(read):
        print(f"row {i}: {row}")

    if color == "white":
        square_color = "w"
    else:
        square_color = "b"

    columns = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
    rows = ['8', '7', '6', '5', '4', '3', '2', '1']

    changes = ["", ""]

    for i in range(8):  # Rows
        for j in range(8):  # Columns
            if (prev_read[i][j] != read[i][j]) and (read[i][j] == square_color 
                                                    or prev_read[i][j] == square_color):
                # Convert the position to chess notation
                position = columns[j] + rows[i]
                # changes.append(position)

                if (prev_read[i][j] == square_color):
                    changes[0] = position
                elif (read[i][j] == square_color):
                    changes[1] = position

    return ''.join(changes)

def get_moves_list_len(moves):
    moves_list = moves.split(" ")
    return len(moves_list)

def shuffle(color):
    if color == "white":
        return "black"
    else:
        return "white"

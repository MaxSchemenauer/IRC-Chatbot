import random
import socket
import sys
import time

import pandas as pd

available_greetings = [
    'Hello',
    'Hi',
    'Hey',
    'Greetings',
    'Howdy',
    'What’s up',
    'Good day',
    'Salutations',
    'Yo',
    'Hello there',
    'Hey there',
    'Bonjour',
    'Hola',
    'Ahoy',
    "What's good",
    "Whats good",
    "Whats up",
]


class IRCBot:
    def __init__(self, nickname, server, port, channel):
        self.nickname = nickname
        self.server = server
        self.port = port
        self.channel = channel
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.user_list = []

    def connect(self):
        # Connect to the IRC server
        self.socket.connect((self.server, self.port))
        self.send_command(f"NICK {self.nickname}")
        self.send_command(f"USER {self.nickname} 0 * :{self.nickname}")
        self.send_command(f"JOIN {self.channel}")

    def send_command(self, command):
        # Send a command to the IRC server
        self.socket.send((command + "\r\n").encode())

    def listen(self):
        # Main loop for receiving messages
        while True:
            response = self.socket.recv(2048).decode()
            if response.startswith("PING"):
                # Respond to server PINGs to stay connected
                self.send_command("PONG :" + response.split(":")[1])
            else:
                print(response)
                self.handle_response(response)

    def request_user_list(self):
        """Send the NAMES command to request the list of users."""
        self.send_command(f"NAMES {self.channel}")

    def handle_response(self, message):
        # Process messages and check for commands
        if f"{self.nickname}:" in message:
            sender = message.split('!')[0][1:]
            command = message.split(f"{self.nickname}:")[1].strip()
            self.respond_to_command(command, sender)

        if " 353 " in message:
            # Parse and extract usernames from the message
            print("MESSAGE", message)
            user_names = message.split(f"{self.channel} :")[1]
            print("INITIAL:", user_names)
            user_names = user_names.split("\r")[0]
            print("USERNAMES", user_names)
            self.user_list = user_names.split(' ')  # Update the user list
            print("User list updated:", self.user_list)  # Debugging print

    def respond_to_command(self, command, sender):
        # Respond to recognized commands
        command = command.lower()
        response = None
        second_response = None
        die = False
        if command in [greeting.lower() for greeting in available_greetings]:
            response = f"{random.choice(available_greetings)} {sender}"
        elif "help" in command:
            response = "Available commands: help, hello, usage, die, users, forget"
        elif "usage" in command or "who are you" in command:
            response = f"I am KM-bot, a simple chatbot created by Kamran Bastani, and Max Schemenauer. CSC-482-01"
            second_response = "I can't answer any advanced questions right now."
        elif "forget" in command:
            response = "Memory Erased."
        elif "users" in command:
            # Send the list of users to the channel if it exists
            if self.user_list:
                user_list_message = "Users in channel: " + ", ".join(self.user_list)
                response = f"{self.channel} :{user_list_message}"
            else:
                response = "I couldn't retrieve the user list. Please try again."
            self.request_user_list()  # Refresh the user list
        elif "die" == command:
            response = "*death noises*"
            die = True
        elif "supplement" in command:
            supplement_recommendation()
        else:
            response = f"Unknown command: {command}. Try 'usage' to see available commands."
        if response is not None and "die" in response:
            response = "I can't kill another bot."

        time.sleep(0.75)
        if response:
            self.send_command(f"PRIVMSG {self.channel} :{response}")
        if second_response:
            self.send_command(f"PRIVMSG {self.channel} :{second_response}")
        if die:
            sys.exit()


def preprocess_data():
    data = pd.read_csv("Sports Supplements.csv")
    # Define custom aggregation functions
    def concatenate_strings(series):
        return '|'.join(series.dropna().unique())  # Remove duplicates and NaN

    def sum_values(series):
        return series.sum()

    def max_value(series):
        return series.max()

    def average(series):
        # Remove invalid entries (e.g., '-')
        valid_series = series[series != '-']

        if valid_series.empty:
            return None  # Return None or any placeholder for blank fields

        numeric_series = valid_series.str.rstrip('%').astype(float)
        return numeric_series.mean()

    def clean_fitness_aspects(fitness_column):
        # Split by pipes and remove any leading/trailing spaces
        return fitness_column.str.split('|').apply(lambda x: [item.strip() for item in x])

    # Define the aggregation rules for each column
    aggregation_rules = {
        'alt name': concatenate_strings,
        "evidence level - score. 0 = no evidence, 1,2 = slight, 3 = conflicting , 4 = promising, 5 = good, 6 = strong ": sum_values,
        "Claimed improved aspect of fitness": concatenate_strings,
        "fitness category": concatenate_strings,
        "sport or exercise type tested": concatenate_strings,
        "popularity": max_value,
        "number of studies examined": sum_values,
        "number of citations": max_value,
        "efficacy": concatenate_strings,
        "notes": concatenate_strings,
        "% positive studies/ trials": average
        # Add other columns and aggregation functions as needed
    }

    # Group by 'supplement' and apply the aggregation rules
    condensed_data = data.groupby('supplement').agg(aggregation_rules).reset_index()

    print(condensed_data.head())

    condensed_data.to_csv("Condensed_Sports_Supplements.csv", index=False)
    print("Condensed dataset has been written to 'Condensed_Sports_Supplements.csv'.")
    return condensed_data

def load_claims():
    supplement_claims = {
        row['supplement']: row['Claimed improved aspect of fitness'].split('|')
        for _, row in data.iterrows()
    }
    return supplement_claims

def supplement_recommendation(data):
    supplement_names = data['supplement'].tolist()
    supplement_names = set(supplement_names)
    print(supplement_names)


if __name__ == "__main__":

    bot = IRCBot("KM-bot", "irc.libera.chat", 6667, "#csc482")
    # bot.connect()
    # bot.listen()

    #data = preprocess_data()
    data = pd.read_csv("Condensed_Sports_Supplements.csv")

    supplement_claims = load_claims()
    supplements = list(supplement_claims.keys())

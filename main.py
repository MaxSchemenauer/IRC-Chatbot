import random
import socket
import sys
import threading
import time
import pandas as pd
from movieRecommender import recommend

from overlap import overlap
from supplements import supplement_recommendation, load_claims, preprocess_data

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
        self.state = "START"
        self.greeting_timer_started = False
        self.timer = None
        self.conversation_with = None

    def outreach(self, outreachNum):
        self.conversation_with = random.choice(self.user_list)
        if outreachNum == 1:
            self.send_command(f"PRIVMSG {self.channel} : Hello {self.conversation_with}!")
        else:
            self.send_command(f"PRIVMSG {self.channel} : Hello again {self.conversation_with}!")


    def handle_timer_end(self):
        print("\n___TIMER ENDED___\n")
        if self.state == 'START':
            self.state = '1_INITIAL_OUTREACH'
            self.outreach(1)
            self.start_greeting_timer(15)
        elif self.state == '1_INITIAL_OUTREACH':
            self.state = '2_INITIAL_OUTREACH'
            self.outreach(2)
            self.start_greeting_timer(15)
        elif self.state == '2_INITIAL_OUTREACH':
            self.state = 'GIVE_UP_FRUSTRATED'
            self.frustrated()
        elif self.state == '2_OUTREACH_REPLY':
            self.state = 'GIVE_UP_FRUSTRATED'
            self.frustrated()
        elif self.state == '1_INQUIRY':
            self.state = 'GIVE_UP_FRUSTRATED'
            self.frustrated()
        elif self.state == "2_INQUIRY":
            self.state = 'GIVE_UP_FRUSTRATED'
            self.frustrated()

    def start_greeting_timer(self, timer_length):
        if self.timer:  # Cancel any existing timer
            self.timer.cancel()
        self.greeting_timer_started = True
        self.timer = threading.Timer(timer_length, self.handle_timer_end)
        self.timer.start()
        print("___TIMER STARTED___")

    def connect(self):
        # Connect to the IRC server
        self.socket.connect((self.server, self.port))
        self.send_command(f"NICK {self.nickname}")
        self.send_command(f"USER {self.nickname} 0 * :{self.nickname}")
        self.send_command(f"JOIN {self.channel}")
        self.start_greeting_timer(20)


    def frustrated(self):
        self.send_command(f"PRIVMSG {self.channel} : Alright then don't respond.")
        self.state = 'START'

    def receive_inquiry(self, sender, command):
        print("RECEIVE INQUIRY")
        if sender != self.conversation_with:
            return
        if self.state == "2_OUTREACH_REPLY":
            self.send_command(f"PRIVMSG {self.channel} : I'm doing good.")
            self.state = '2_INQUIRY_REPLY'
        elif self.state == "2_INQUIRY_REPLY":
            self.send_command(f"PRIVMSG {self.channel} : I sat around in this channel getting tested.")
            self.state = '1_INQUIRY_REPLY'
            self.state = "STATE"

    def handle_inquiry_reply(self, sender, command):
        if sender != self.conversation_with:
            return
        self.send_command(f"PRIVMSG {self.channel} : What did you do today {sender}?")
        self.state = '2_INQUIRY'
        self.start_greeting_timer(15)

    def handle_greeting(self, sender, message):
        if self.state == 'START': # we receive the initial greeting
            self.conversation_with = sender
            self.state = '2_OUTREACH_REPLY'
            self.send_command(f"PRIVMSG {self.channel} : Hello! {sender}")
            self.start_greeting_timer(15)
        if "INITIAL_OUTREACH" in self.state: # we receive a greeting after we reached out
            if sender != self.conversation_with:
                return
            self.state = "1_INQUIRY"
            self.send_command(f"PRIVMSG {self.channel} : How are you {sender}?")
            self.start_greeting_timer(15)

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
        print("RECEIVED MESSAGE")

        if f"{self.nickname}:" in message:
            sender = message.split('!')[0][1:]
            command = message.split(f"{self.nickname}:")[1].strip()
            print("NAME IN MESSAGE")
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
        print("RESPONDING TO COMMAND")

        command = command.lower()
        response = None
        second_response = None
        die = False
        if "help" in command:
            response = "Available commands: help, hello, usage, die, users, forget"
        elif "usage" in command or "who are you" in command:
            response = f"I am KM-bot, a simple chatbot created by Kamran Bastani, and Max Schemenauer. CSC-482-01"
            second_response = "Try asking for supplement reccomendations. Make sure to use the word 'supplement'. For example, 'Give me a supplement to help with aerobic endurance and muscle recovery.' Feature made by Max Schemenauer."
        elif "forget" in command:
            response = "Memory Erased."
        elif "users" in command:
            # Send the list of users to the channel if it exists
            self.request_user_list()  # Refresh the user list
            if self.user_list:
                user_list_message = "Users in channel: " + ", ".join(self.user_list)
                response = f"{self.channel} :{user_list_message}"
            else:
                response = "I couldn't retrieve the user list. Please try again."
        elif "die" == command:
            response = "*death noises*"
            die = True
        elif "supplement" in command:
            response = supplement_recommendation(data, supplement_claims, command)
        elif "similar to" in command:
            response = recommend(command.split("similar to ")[1])
        elif command in [greeting.lower() for greeting in available_greetings] and self.state in ["START","1_INITIAL_OUTREACH", "2_INITIAL_OUTREACH"]: # PHASE II
            self.handle_greeting(sender, command)  # just received a greeting
        elif self.state == "2_OUTREACH_REPLY": # receiving an inquiry
            self.receive_inquiry(sender, command)
        elif self.state == "1_INQUIRY": # receiving inquiry reply
            self.handle_inquiry_reply(sender, command)
        elif self.state == "2_INQUIRY_REPLY": # just received second inquiry
            self.receive_inquiry(sender, command)
        elif self.state == "2_INQUIRY":
            self.state = "START"
            return
        else:
            response = f"Unknown command: {command}. Try 'usage' to see available commands."
        if response is not None and ("die" in response):
            response = "I can't kill another bot."

        time.sleep(0.75)
        if response:
            self.send_command(f"PRIVMSG {self.channel} :{response}")
        if second_response:
            self.send_command(f"PRIVMSG {self.channel} :{second_response}")
        if die:
            sys.exit()


if __name__ == "__main__":
    #data = preprocess_data()
    global data, supplement_claims
    data = pd.read_csv("Condensed_Sports_Supplements.csv")
    supplement_claims = load_claims(data)

    bot = IRCBot("KM-bot", "irc.libera.chat", 6667, "#csc482")
    bot.connect()
    bot.listen()



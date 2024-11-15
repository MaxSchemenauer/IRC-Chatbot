import random
import socket
import sys
import time

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
        elif "help" in command :
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
        else:
            response = f"Unknown command: {command}. Try 'usage' to see available commands."

        if "die" in response:
            response = "I can't kill another bot."

        time.sleep(0.75)
        self.send_command(f"PRIVMSG {self.channel} :{response}")
        if second_response:
            self.send_command(f"PRIVMSG {self.channel} :{second_response}")
        if die:
            sys.exit()

if __name__ == "__main__":
    bot = IRCBot("KM-bot", "irc.libera.chat", 6667, "#csc482")
    bot.connect()
    bot.listen()

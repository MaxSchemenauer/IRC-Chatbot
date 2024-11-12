import socket
import sys


class IRCBot:
    def __init__(self, nickname, server, port, channel):
        self.nickname = nickname
        self.server = server
        self.port = port
        self.channel = channel
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

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

    def handle_response(self, message):
        # Process messages and check for commands
        if f"{self.nickname}:" in message:
            sender = message.split('!')[0][1:]
            command = message.split(f"{self.nickname}:")[1].strip()
            self.respond_to_command(command, sender)

    def respond_to_command(self, command, sender):
        # Respond to recognized commands
        command = command.lower()
        response = ""
        if "hello" in command:
            response = f"Hello {sender}"
        elif "help" in command :
            response = "Available commands: help, hello, usage, die, users, forget"
        elif "usage" in command or "who are you" in command:
            self.send_command(f"PRIVMSG {self.channel} :I am KM-bot, a simple chatbot created by Kamran Bastani, and Max Schemenauer. CSC-482-01")
            response = "I can't answer any advanced questions right now."
        elif "forget" in command:
            response = "Memory Erased."
        elif "users" in command:
            self.send_command(f"PRIVMSG {self.channel} :{self.server.users}")
        elif "die" in command:
            response = "*death noises*"
            self.send_command(f"PRIVMSG {self.channel} :{response}")
            sys.exit()
        else:
            response = f"Unknown command: {command}. Try 'usage' to see available commands."

        self.send_command(f"PRIVMSG {self.channel} :{response}")

if __name__ == "__main__":
    bot = IRCBot("KM-bot", "irc.libera.chat", 6667, "#CSC482")
    bot.connect()
    bot.listen()

import socket
import select
import random
import sys
import time
from Question import Q
from _thread import *

MSG_LEN = 5
random.shuffle(Q)

server = socket.socket()
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

if len(sys.argv) != 3:
	print("Correct method: script, IP address, port number")
	exit()

number_of_participants = int(input("Please enter the number of participants (max allowed is 4): "))
number_joined = 0

if number_of_participants > 4 or number_of_participants < 1:
	while number_of_participants > 4 or number_of_participants < 1:
		number_of_participants = int(input("Please input valid number: "))

IP = str(sys.argv[1])
Port = int(sys.argv[2])
server.bind((IP, Port))
server.listen(10)
print("Server started!")

print(f"Waiting for connection on IP address and Port number: {IP}, {Port}")

clients_list = []
participants = {}
points = {}
mapping = {}
Person = [server]
answer = [-1]

def receive_message(client_socket):
	message = client_socket.recv(1024).decode('utf-8')
	return message

def send_to_one(receiver, message):
	message = f"{len(message):<{MSG_LEN}}" + message
	try:
		receiver.send(bytes(message, 'utf-8'))
	except:
		receiver.close()
		clients_list.remove(receiver)

def send_to_all(sender, message):
	message = f"{len(message):<{MSG_LEN}}" + message
	for socket in clients_list:
		if(socket != server and socket != sender):
			try:
				socket.send(bytes(message, 'utf-8'))
			except:
				socket.close()
				clients_list.remove(socket)

def quiz():
	Person[0] = server
	random.shuffle(Q)
	ask_question()
	keypress = select.select(clients_list, [], [], 10)
	if len(keypress[0]) > 0:
		who_buzzed = keypress[0][0]
		send_to_one(who_buzzed, "YOU PRESSED THE BUZZER")
		send_to_one(who_buzzed, "ENTER YOUR ANSWER: ")
		send_to_all(who_buzzed, "BUZZER PRESSED!")
		print("BUZZER PRESSED!")
		time.sleep(0.01)
		Person.pop(0)
		Person.append(who_buzzed)
		t0 = time.time()
		Q.pop(0)

		answering = select.select(Person, [], [], 10)
		if len(answering) > 0:
			if time.time() - t0 >= 20:
				send_to_one(who_buzzed, "NOT ANSWERED!")
				time.sleep(3)
				quiz()
			else:
				time.sleep(3)
				quiz()
	else:
		send_to_all(server, "BUZZER NOT PRESSED")
		print("BUZZER NOT PRESSED")
		time.sleep(3)
		Q.pop(0)
		quiz()

def ask_question():
	if len(Q) != 0:
		question_and_answer = Q[0]
		question = question_and_answer[0]
		options = question_and_answer[1]
		Answer = question_and_answer[2]

		random.shuffle(options)
		option_number = 1

		send_to_all(server, "\nQuestion. " + str(question))
		print("\nQuestion. " + str(question))
		for j in range(len(options)):
			send_to_all(server, "   " + str(option_number) + ")   " + str(options[j]))
			print("   " + str(option_number) + ")    " + str(options[j]))
			if options[j] == Answer:
				answer.pop(0)
				answer.append(int(option_number))
			option_number += 1
		send_to_all(server, "\nHit Enter to answer")
		print("answer: option number " + str(answer))
	else:
		send_to_all(server, "All question asked!")
		end_quiz()
		sys.exit()

def update_points(player, number):
	print(participants[mapping[player]])
	points[participants[mapping[player]]] += number
	print(points)
	send_to_all(server, "\nScore: ")
	for j in points:
		send_to_all(server, ">> " + str(j) + ": " + str(points[j]))

def end_quiz():
	send_to_all(server, "GAME OVER\n")
	print("GAME OVER\n")
	for i in points:
		if points[i] >= 5:
			send_to_all(server, "The WINNER is " + str(i))
		elif points[i] < 0:
			send_to_all(server, "The LOSER is " + str(i))
	send_to_all(server, "Scoreboard: ")
	print("Scoreboard: ")
	for i in points:
		send_to_all(server, ">> " + str(i) + ": " + str(points[i]))
		print(">> " + str(i) + ": " + str(points[i]))
	sys.exit()

clients_list.append(server)

while True:
	rList, wList, error_sockets = select.select(clients_list, [], [])
	for socket in rList:
		if socket == server:
			client_socket, client_address = server.accept()
			if number_joined == number_of_participants:
				send_to_one(client_socket, "Maximum number of players joined!")
				client_socket.close()
			else:
				username = receive_message(client_socket)
				if username in participants.values():
					send_to_one(client_socket, "Username already taken. Please choose a different one and join again!")
					client_socket.close()
				else:
					participants[client_address] = username
					points[username] = 0
					number_joined += 1
					mapping[client_socket] = client_address
					clients_list.append(client_socket)
					print("Participant connected: " + str(client_address) + "  [  " + participants[client_address] + "   ]" )
					if number_joined < number_of_participants:
						send_to_one(client_socket, "Welcome to the quiz " + username + "!\nPlease wait for other participants to join...")

					if number_joined == number_of_participants:
						send_to_all(server, "\nParticipant(s) joined:")
						for i in participants:
							send_to_all(server,">> " + participants[i])
						send_to_all(server, "\nThe quiz will begin in 30 seconds\n")
						print("\n" + str(number_of_participants) + "participant(s) connected!")
						time.sleep(30)
						start_new_thread(quiz, ())

		else:
			msg = receive_message(socket)
			print(msg)
			if socket == Person[0]:
				try:
					ans = int(msg)
					if ans == answer[0]:
						send_to_one(socket, "CORRECT ANSWER")
						send_to_all(server, str(participants[mapping[socket]]) + " +1 point")
						print(str(participants[mapping[socket]]) + " +1 point")
						update_points(socket, 1)
						Person[0] = server
						if points[participants[mapping[socket]]] >= 5:
							end_quiz()

					else:
						send_to_one(socket, "WRONG ANSWER")
						send_to_all(server, str(participants[mapping[socket]]) + " -0.5 point")
						print(str(participants[mapping[socket]]) + " -0.5 point")
						update_points(socket, -0.5)
						Person[0] = server
						if points[participants[mapping[socket]]] < 0:
							end_quiz()

				except ValueError:
					send_to_one(socket, "INVALID OPTION")
					send_to_all(server, str(participants[mapping[socket]]) + " -0.5 point")
					print(str(participants[mapping[socket]]) + " -0.5 point")
					update_points(socket, -0.5)
					Person[0] = server
					if points[participants[mapping[socket]]] < 0:
						end_quiz()

			elif Person[0] != server:
				send_to_one(socket, "TOO LATE!")

client_socket.close()
server.close() 

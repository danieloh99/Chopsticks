#!/usr/bin/env python3
from os import system, name
from copy import deepcopy

class Player:
	def __init__(self, game_world, id):
		self.game_world = game_world
		self.left = 1
		self.right = 1
		self.id = id
		self.opponent = None
	def setup(self):
		self.opponent = self.game_world.p2 \
			if self.id == 1 else self.game_world.p1

	def display(self):
		# If it's this Player's turn, draw an arrow before displaying stats.
		if (self.id==1 and self.game_world.p1_turn) \
				or (self.id==2 and not self.game_world.p1_turn):
			print("*Player %d*:\t L:%d R:%d" \
				% (self.id, self.left, self.right))
		else:
			print(" Player %d :\t L:%d R:%d" \
				% (self.id, self.left, self.right))

	def is_valid_attack(self, attack_hand, target_hand):
		# Identify attacking hand's value and check that it's not 0.
		attack_value = self.left if attack_hand == 'l' else self.right
		if attack_value == 0 : return False

		# Identify target hand's value and check that it's not 0.
		target_value = self.opponent.left \
			if target_hand == 'l' else self.opponent.right
		if target_value == 0 : return False

		# If reaching this point, the attack is valid.
		return True

	def is_valid_split(self, new_left, new_right):
		# If a new hand value is <= 0 or >= 5
		# or the sum of the new hand values is not equal to the
		# sum of the current hand values, or the new hands are the
		# same as the current hands, or the new hands are the
		# current hands swapped, the move is invalid.
		#
		# Otherwise, the move is valid.
		if new_left<0 or new_right<0 \
				or new_left>=5 or new_right>=5 \
				or new_left==self.left or new_right==self.right \
				or (new_left+new_right != self.left+self.right) \
				or (new_left==self.right and new_right==self.left):
			return False
		return True

	def get_move(self):

		def is_valid_move(move):
			# If input length is 1 word, must be 'h' or invalid.
			if len(move) == 1:
				if move[0] == 'h' : return True
				return False

			# Other moves are both 3 words
			if len(move) != 3 : return False

			if move[0] == 'a':
				# Check valid input form
				attacker = move[1]
				target = move[2]
				if (attacker != 'l' and attacker != 'r') \
						or (target != 'l' and target != 'r'):
					return False

				return self.is_valid_attack(attacker, target)

			elif move[0] == 's':
				# Check for valid input form
				new_left = None
				new_right = None
				try:
					new_left = int(move[1])
				except ValueError:
					return False
				try:
					new_right = int(move[2])
				except ValueError:
					return False

				return self.is_valid_split(new_left, new_right)
			else:
				return False

		# Back at get_move function
		move = input("What would you like to do? "
					"[Enter 'h' for help]: ").split()
		print("")

		if is_valid_move(move):
			return move
		else:
			print("Error. Invalid move.")
			return -1

	def move(self):
		def handle_help():
			print(self.game_world.rules)

		def handle_attack(attack_hand, target_hand):
			attack_value = self.left if attack_hand == 'l' else self.right
			target_value = self.opponent.left \
				if target_hand == 'l' else self.opponent.right

			# Do the attack, and if target hand's value >= 5, set it to 0.
			target_value += attack_value
			if target_value >= 5 : target_value = 0
			if target_hand == 'l':
				self.opponent.left = target_value
			else:
				self.opponent.right = target_value
		def handle_split(new_left, new_right):
			self.left = new_left
			self.right = new_right

		# back at move function
		while True:
			self.game_world.display()
			print("Player %d's turn." % (self.id))
			move = self.get_move()
			if move != -1:
				if move[0] == 'h':
					handle_help()
					return 1
				elif move[0] == 'a':
					self.game_world.previous_move = move
					handle_attack(move[1], move[2])
				else:
					self.game_world.previous_move = move
					handle_split(int(move[1]), int(move[2]))
				return 0


class AI(Player):
	def __init__(self, game_world, id):
		Player.__init__(self, game_world, id)
		self.opponent_hands = None
		self.seen_states = set()
		self.all_attacks = (('l', 'l'), ('l', 'r'), ('r', 'l'), ('r', 'r'))
		self.sum_to_valid_splits = {
			2: ((1, 1), (2, 0)),
			3: ((1, 2), (3, 0)),
			4: ((1, 3), (4, 0), (2, 2)),
			5: ((1, 4), (2, 3)),
			6: ((2, 4), (3, 3))
		}

	def setup(self):
		Player.setup(self)
		self.opponent_hands = [self.opponent.left, self.opponent.right]

	def is_valid_attack(self, current_state, index_offset, attack_type):
		# First compute attack_hand and target_hand values, assuming AI's turn.
		# Then swap their values if it's not the AI's turn.

		attack_value = current_state[0 + index_offset] \
			if attack_type[0] == 'l' else current_state[1 + index_offset]
		target_value = current_state[2 - index_offset] \
			if attack_type[1] == 'l' else current_state[3 - index_offset]

		if attack_value==0 or target_value==0:
			return False
		return True

	def get_valid_splits(self, current_state, index_offset):
		#return None
		cur_left = current_state[0 + index_offset]
		cur_right = current_state[1 + index_offset]
		sum_hands = cur_left + cur_right
		if sum_hands==1 or sum_hands>=7:
			return None

		valid_splits = list(self.sum_to_valid_splits.get(sum_hands))
		#print("get_valid_splits: current_state: %s\tcur_left and cur_right: %s, %s\tvalid_splits: %s" % (current_state, cur_left, cur_right, valid_splits))
		if (cur_left, cur_right) in valid_splits:
			valid_splits.remove((cur_left, cur_right))
		else : valid_splits.remove((cur_right, cur_left))
		return tuple(valid_splits)

	def handle_attack(self, current_state, index_offset, attack_type):
		attack_hand_index = 0 + index_offset \
			if attack_type[0] == 'l' else 1 + index_offset
		target_hand_index = 2 - index_offset \
			if attack_type[1] == 'l' else 3 - index_offset
		target_hand_orig_value = current_state[target_hand_index]
		orig_target = [target_hand_index, target_hand_orig_value]

		new_target_value = target_hand_orig_value \
			+ current_state[attack_hand_index]
		if new_target_value >= 5 : new_target_value = 0
		current_state[target_hand_index] = new_target_value
		current_state[4] = not current_state[4]  # switch turns

		return orig_target

	def undo_attack(self, current_state, target_index, target_value):
		current_state[target_index] = target_value
		current_state[4] = not current_state[4]

	def handle_split(self, current_state, index_offset, split_values):
		orig_left_index = 0 + index_offset
		orig_right_index = 1 + index_offset
		orig_left = current_state[orig_left_index]
		orig_right = current_state[orig_right_index]

		current_state[orig_left_index] = split_values[0]  # new left hand
		current_state[orig_right_index] = split_values[1]  # new right hand
		current_state[4] = not current_state[4]  # switch turns

		return [
			[orig_left_index, orig_right_index],
			[orig_left, orig_right]
		]

	def undo_split(self, current_state, hand_indices, hand_values):
		current_state[hand_indices[0]] = hand_values[0]
		current_state[hand_indices[1]] = hand_values[1]
		current_state[4] = not current_state[4]

	def minimax(self, current_state, seen_states, depth):
		"""Determines the best move given the current case.
		A case is defined as the current set of hands the AI and player have
		as well as whose turn it was.
			So an example case would be: AI: 1 2, Player: 1 3, AI's Turn
			Stored as (1, 2, 1, 3, True)
			Another case would be: 		 AI: 1 2, Player: 1 3, Player's Turn
			Stored as (1, 2, 1, 3, False)

		It is passed w/ the AI's hands as the first 2 in the list/tuple, and
		the Player's hands as the last 2 in the list/tuple (Left then Right for
		both cases).

		Remember: the AI is the MAXIMIZER and the Player is the MINIMIZER
		"""
		# First check current state. If AI won, return 1.
		# If Player won, return -1.
		# If the current state has been seen before, return 0.
		if current_state[2] == current_state[3] == 0:
			#print("minimax: returning 1, depth: %s" % depth)
			return 1
		if current_state[0] == current_state[1] == 0:
			#print("minimax: returning -1, depth: %s" % depth)
			return -1
		if tuple(current_state) in seen_states:
			print("minimax: returning 0, depth: %s" % depth)
			return 0

		# Reaching this point means that we haven't gotten to an end yet.
		seen_states.add(tuple(current_state))
		print("minimax: depth %s\t seen_states %s\t" % (depth, seen_states))
		ai_turn = current_state[4]
		min_or_max = None

		if ai_turn:
			best_score = -2
			min_or_max = max
			index_offset = 0
		else:
			best_score = 2
			min_or_max = min
			index_offset = 2

		# For each valid attack, get the state that would be reached after
		# handling the attack (remembering to switch turn). Then compare
		# the score returned from the minimax function, passing in that
		# next state, with the current best score.
		# Update the best score to be the larger of the two.
		#
		# Repeat but for all of the valid splits.

		#print("\nminimax: state before attack for loop: %s\tdepth: %s" % (current_state, depth))

		for attack_type in self.all_attacks:
			#print("minimax: analyzing attack_type: %s\t ai_turn: %s\t state: %s\tdepth: %s" % (attack_type, ai_turn, current_state, depth))
			if not self.is_valid_attack(current_state,
					index_offset, attack_type):  # TODO: must be overloaded
				#print("\tminimax: invalid attack. moving on.")
				continue
			target_orig_index_and_value = self.handle_attack(current_state, index_offset, attack_type)
			#print("minimax: state post attack: %s" % current_state)
			best_score = min_or_max(best_score,
							self.minimax(current_state, deepcopy(seen_states), depth + 1))
			self.undo_attack(current_state, target_orig_index_and_value[0], target_orig_index_and_value[1])
			#print("minimax: done attack_type: %s\tai_turn: %s\tstate: %s\tdepth: %s\tbest score: %s" % (attack_type, ai_turn, current_state, depth, best_score))

		# Determine the valid splits given the AI's hands  # new helper function
		valid_splits = self.get_valid_splits(current_state, index_offset)  # TODO: write new helper function
		if valid_splits is not None:
			#print("\nminimax: state before split for loop: %s\tdepth: %s\tvalid_splits: %s" % (current_state, depth, valid_splits))
			for curr_split in valid_splits:
				#print("minimax: analyzing split_type: %s\t ai_turn: %s\t state: %s\tdepth: %s" % (curr_split, ai_turn, current_state, depth))
				orig_hands_indices_and_values = self.handle_split(current_state, index_offset, curr_split)  # TODO: must be overloaded, return tuple
				#print("minimax: state post split: %s" % current_state)

				best_score = min_or_max(best_score,
								self.minimax(current_state, deepcopy(seen_states), depth + 1))
				self.undo_split(current_state,
					orig_hands_indices_and_values[0],
					orig_hands_indices_and_values[1])
				#print("minimax: done split_type: %s\tai_turn: %s\tstate: %s\tdepth: %s\tbest score: %s" % (curr_split, ai_turn, current_state, depth, best_score))

		#print("minimax: finished comparing moves. depth: %s\t best_score: %s" % (depth, best_score))
		return best_score


	def get_move(self):
		"""Returns the best move possible given the current board using minimax
			algorithm.
		"""
		best_move_type = None
		best_move = None
		best_score = -2
		current_state = [self.left, self.right,
			self.opponent.left, self.opponent.right, True]
		#next_state = current_state  # deep copy

		if tuple(current_state) not in self.seen_states:
			self.seen_states.add(tuple(current_state))
		seen_states = deepcopy(self.seen_states)  # deep copy

		#print("get_move: seen_states %s" % (self.seen_states,))
		for attack_type in self.all_attacks:
			print("get_move: current_state: %s" % current_state)
			print("get_move: checking attack: %s" % (attack_type,))
			if not self.is_valid_attack(current_state, 0, attack_type):
				continue
			target_orig_index_and_value = self.handle_attack(current_state, 0, attack_type)  # next_state gets modified after this.
			print("get_move: state post handle_attack: %s" % current_state)
			move_score = self.minimax(current_state, seen_states, 0)
			print("get_move: state post minimax: %s" % current_state)
			print("get_move: seen_states %s" % (self.seen_states,))

			if move_score > best_score:
				best_move_type = 'a'
				best_move = attack_type
				best_score = move_score
			#print("get_move: best minimax score so far: %s" % best_score)
			self.undo_attack(current_state, target_orig_index_and_value[0], target_orig_index_and_value[1])
			print("get_move: state post undo_attack: %s\n" % current_state)

		valid_splits = self.get_valid_splits(current_state, 0)  # TODO: write new helper function
		if valid_splits is not None:
			#print("minimax: current_state %s\tvalid splits: %s\tdepth %s" % (current_state, valid_splits, depth))
			for curr_split in valid_splits:
				print("get_move: current_state: %s" % current_state)
				print("get_move: checking split: %s" % (curr_split,))
				orig_hands_indices_and_values = self.handle_split(current_state, 0, curr_split)  # TODO: must be overloaded, return tuple
				print("get_move: state post handle_split: %s" % current_state)
				move_score = self.minimax(current_state, seen_states, 0)
				if move_score > best_score:
					best_move_type = 's'
					best_move = curr_split
					best_score = move_score
				self.undo_split(current_state,
					orig_hands_indices_and_values[0],
					orig_hands_indices_and_values[1])
				print("get_move: state post undo_split: %s\n" % current_state)

		move = [best_move_type, best_move[0], best_move[1]]
		return move

class Game:
	def __init__(self):
		self.p1 = Player(self, 1)
		self.p2 = AI(self, 2)
		self.p1.setup()
		self.p2.setup()
		self.p1_turn = True
		self.previous_move = None
		self.rules = "---------RULES---------\n" \
			"For all inputs, use 'l' to represent the LEFT hand and 'r' to \n" \
			"represent the RIGHT hand.\n" \
			"Here are the types of valid moves: \n\n" \
			"HELP input: 'h'\n" \
			"ATTACK input: 'a <attack hand> <target hand>'\n" \
			"SPLIT input: 's <new left hand value> <new right hand value>'\n"

	def welcome(self):
		print("Welcome to Chopsticks! Please read the rules below before " +
				"playing!\n")
		print(self.rules)
		input("Press ENTER to start the game!")

	def display(self):
		print("")
		self.p2.display()
		self.p1.display()
		print("")

	def clear_screen(self):
		if name == 'nt':  # for windows
			system('cls')
		else:  # for mac and linux (here, os.name is 'posix')
			system('clear')

	# function may not be necessary. used to print description of previous move.
	def print_previous_move(self):
		prev_player = None
		prev_opponent = None
		prev_move_msg = None
		if not self.p1_turn:
			prev_player = "Player 1"
			prev_opponent = "Player 2"
		else:
			prev_player = "Player 2"
			prev_opponent = "Player 1"

		if self.previous_move[0] == 'a':
			attack_hand = 'LEFT' if self.previous_move[1] == 'l' else 'RIGHT'
			target_hand = 'LEFT' if self.previous_move[2] == 'l' else 'RIGHT'
			prev_move_msg = prev_player + " ATTACKED " + prev_opponent \
							+ " using their " + attack_hand \
							+ " hand to attack the " + target_hand + " hand."
		else:
			prev_move_msg = prev_player + " SPLIT. Their new left hand is " \
							+ self.previous_move[1] + " and their right hand is " \
							+ self.previous_move[2] + "."
		print(prev_move_msg)


	def player_move(self):
		return self.p1.move() if self.p1_turn else self.p2.move()

	def check_win(self):
		if self.p1.left == self.p1.right == 0:
			return 2
		if self.p2.left == self.p2.right == 0:
			return 1
		return 0

	def end_of_game(self, who_won):
		self.display()
		if who_won == 1:
			print("Player 1 wins!")
		elif who_won == 2:
			print("Player 2 wins!")
		else:
			print("It was a tie...?")
		print("Thanks for playing!")

	def play(self):
		self.welcome()
		self.clear_screen()
		game_over = False
		while not game_over:
			if self.player_move() == 0: # User did not enter 'h' for help
				self.p1_turn = not self.p1_turn
				#self.clear_screen()
				self.print_previous_move()
				game_over = self.check_win()

		self.end_of_game(game_over)


obj = Game()
obj.play()

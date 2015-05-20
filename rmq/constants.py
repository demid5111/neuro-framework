__author__ = 'Administrator'



class Constants():
		body = "body"
		adjacency_matrix = "adjacency_matrix"
		message_key = "msg"
		directExchangeToAdmin = "my_direct_exchange_to_admin2"
		fanoutExchangeFromAdmin = "my_fanout_exchange_from_admin2"
		routing_key_from_admin = "from_admin"
		routing_key_to_admin = "to_admin"
		key_all_messages = "#"
		key_all_full_messages = "*.*.*"
		def __init__(self):
			pass

class Message():
	update_energy="update_energy"
	update_energies = "update_energies"
	update_punishment = "update_punishment"
	update_deltas = "update_deltas"
	calculate_energy = "calculate_energy"
	calculate_deltas = "calculate_deltas"
	calculate_punishment = "calculate_punishment"
	find_best_neighbour = "find_best_neighbour"
	report_best_neighbour = "report_best_neigbour"
	initializing = "initializing"
	kill_everyone = "kill_everyone"
	new_member = "new_member"
	new_id = "new_id"
	def __init__(self):
		pass

class Level():
	info = "info"
	report = "report"

class Field():
	myW = u"myW"
	myC = u"myC"
	mySize = u"mySize"	#that is the number of neurons on the tabu-machine
	myTabu = u"myTabu"
	myBeta = u"myBeta"
	mySizeVec = u"mySizeVec"
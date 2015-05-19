__author__ = 'Administrator'



class Constants():

		directExchangeToAdmin = "my_direct_exchange_to_admin"
		fanoutExchangeFromAdmin = "my_fanout_exchange_from_admin"
		routing_key_from_admin = "from_admin"
		routing_key_to_admin = "to_admin"

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
	new_member = "new_member"
	new_id = "new_id"
	def __init__(self):
		pass
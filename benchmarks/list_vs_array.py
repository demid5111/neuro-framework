__author__ = 'demid5111'

import numpy as np
import time

def iterate_through_list(my_list):
	for i in my_list:
		pass

def iterate_through_array(my_array):
	for i in np.nditer(my_array):
		pass

SIZE = 1





while(True):
	SIZE *= 10
	if SIZE > 10000000:
		break
	my_list = [0.0 for i in range(SIZE)]
	my_array = np.zeros(SIZE,dtype=np.float)
	begin = time.clock()
	iterate_through_list(my_list)
	end = time.clock()

	time_for_list = end - begin

	begin = time.clock()
	iterate_through_array(my_array)
	end = time.clock()

	time_for_array = end - begin

	print ("Size = {} \t list time = {} \t array time = {}".format(SIZE,time_for_list,time_for_array))

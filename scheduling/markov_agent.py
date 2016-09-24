import time
import pandas as pd
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
from networkx.readwrite import json_graph
import json

TIMER = 0

class Worker:
	def __init__(self, id, name):
		self.id = id
		self.name = name
		self.working = False
		self.machines = set()
		
	def add_machine(self, machine):
		self.machines.add(machine)
		
	def show(self):
		print('--------------------------')
		print('Worker[%d] %s' % (self.id,self.name))
		print('Machines')
		for machine in self.machines:
			print(' [%2d] : %s' % (machine.id, machine.name))
		
class Machine:
	def __init__(self, id, name, machine_type):
		self.id = id
		self.name = name
		self.machine_type = machine_type
		self.working = False
		self.workers = set()
	
	def add_worker(self, worker):
		self.workers.add(worker)

class Resources:
	workers = {}
	machines = {}
	machines_by_type = {}
	
	@staticmethod
	def load():
		
		# read workers database
		data = pd.read_csv('instances/workers.csv')
		for id, row in data.iterrows():
			Resources.workers[row.ID] = Worker(row.ID, row.NOME)
		
		# read machines database
		data = pd.read_csv('instances/machines.csv')
		for index, row in data.iterrows():
			for k in range(row.QTD):
				id += 1
				machine = Machine(id, row.NOME, row.ID)
				
				# add machine to machines list
				Resources.machines[id] = machine
				
				# add machine to machine_by_type dictionary
				if row.ID not in Resources.machines_by_type.keys():
					Resources.machines_by_type[row.ID] = set()
				Resources.machines_by_type[row.ID].add(machine)
		
		# read operators database
		data = pd.read_csv('instances/operatorsAll.csv')
		for index, row in data.iterrows():
			worker = Resources.workers[row.OPERADOR]
			for machine in Resources.machines_by_type[row.MAQUINA]:
				worker.add_machine(machine)
				machine.add_worker(worker)
				
	@staticmethod
	def show():
		print('Workers')
		for worker in Resources.workers.values():
			worker.show()
			
	@staticmethod
	def status():
		for worker in Resources.workers.values():
			print('Worker[%d]:%10s working: %s' % (worker.id, worker.name, worker.working))
				
class Item:
	def __init__(self, id, start_tasks):
		self.id = id
		self.next_tasks_id = set(start_tasks)
		self.tasks_done_id = set()
		self.current_task = None
		
	def update(self):
		# check if the current task is done
		if self.current_task != None and self.current_task.done():
			# print('Updating Item[%d] current_task %s' % (self.id, self.current_task.description))
			# print('Item[%2d] finishing Task[%d]' % (self.id, self.current_task.id))
			self.tasks_done_id.add(self.current_task.id)
			self.next_tasks_id.remove(self.current_task.id)
			# udpate the list of tasks ready to start
			for taskA_id in self.tasks_done_id:
				succA = TaskFactory.task_graph.successors(taskA_id)
				for taskB_id in succA:
					if taskB_id in self.next_tasks_id or taskB_id in self.tasks_done_id: continue
					predB = set(TaskFactory.task_graph.predecessors(taskB_id))
					if predB.issubset(self.tasks_done_id): 
						self.next_tasks_id.add(taskB_id)
					
			# print('Item[%2d] next_tasks_id: ' % self.id, self.next_tasks_id)
			self.current_task = None
		
	def start_next_task(self):
		# try to start a task
		if self.current_task == None:
			# prioritizing the initialization of the longest tasks
			tasks = [(TaskFactory.tasks[task_id].tproc, task_id) for task_id in self.next_tasks_id]
			tasks = sorted(tasks)
			tasks.reverse()
			for tproc, task_id in tasks:
				task = TaskFactory.get_task(task_id)
				if(task != None):
					machine, worker = task.current_resources
					# print('Starting, Item[%d], Task[%2d], %4f, Worker[%2d], %4f, Machine[%2d]' % (self.id, task.id, task.tproc, worker.id, task.tproc_start, machine.id))
					self.current_task = task
					break
		# print('Item[%d] Task[]%s' % (self.id, self.current_task))

	
	def done(self):
		return len(self.next_tasks_id) == 0
					
class Task:
	def __init__(self, id, description, machine_type, tproc):
		# unique identifier
		self.id = id
		# processing time
		self.tproc = tproc
		# list of (machine,worker) pairs
		self.machine_type = machine_type
		# processing start time
		self.tproc_start = None
		# current resources
		self.current_resources = None
		# next tasks
		self.next_tasks_id = set()
		# description
		self.description = description
	
	def add_next_task(self, task):
		self.next_tasks_id.add(task.id)
	
	def done(self):
		global TIMER
		#print('Checking if Task is done')
		if self.current_resources == None:
			raise Exception('Trying to check a task that has not available resources.')
		# avoiding rounding errors
		telapsed = TIMER - self.tproc_start
		if abs(telapsed - self.tproc) < 0.01:
			machine, worker = self.current_resources
			machine.working = False
			worker.working = False
			self.current_resources = None
			return True
		else:
			return False
		
	def request_resources(self):
		global TIMER
		for machine in Resources.machines_by_type[self.machine_type]:
			if not machine.working:
				for worker in machine.workers:
					if not worker.working:
						self.tproc_start = TIMER
						machine.working = True
						worker.working = True
						self.current_resources = (machine, worker)
						return True
		# print('Request denied Machine[%d]' % self.machine_type)
		return False
		
	def clone(self):
		task = Task(self.id, self.description, self.machine_type, self.tproc)
		task.tproc_start = self.tproc_start
		task.current_resources = self.current_resources
		task.next_tasks_id = self.next_tasks_id
		return task
		
class TaskFactory:
	tasks = {}
	task_graph = None
	
	@staticmethod
	def load():
		# read task database
		data = pd.read_csv('instances/tasks.csv')
		for index, row in data.iterrows():
			task = Task(row.ID, row.DESCRICAO, row.MAQUINA, row.TEMPO2)
			TaskFactory.tasks[task.id] = task
		
		# read task precedence
		data = pd.read_csv('instances/tasks_graph.csv').values
		for row in data:
			task = TaskFactory.tasks[row[0]]
			for task_id in row[1:]:
				if not pd.isnull(task_id):
					task.add_next_task(TaskFactory.tasks[task_id])
		
		# set task graph
		G = nx.DiGraph()
		for taskA in TaskFactory.tasks.values():
			for taskB_id in taskA.next_tasks_id:
				G.add_edge(taskA.id, taskB_id)
		TaskFactory.task_graph = G
		
	@staticmethod
	def get_task(task_id):
		task = TaskFactory.tasks[task_id]
		if task.request_resources():
			# print('Cloning Task[%2d]' % task_id)
			return task.clone()
		else:
			return None
	
	@staticmethod
	def to_csv():
		edges = dict(source=[], target=[])
		for e in TaskFactory.task_graph.edges():
			edges['source'].append(e[0])
			edges['target'].append(e[1])
		
		# d = json_graph.node_link_data(G)
		# json.dump(d, open('task_graph.json','w'))
		table = pd.DataFrame.from_dict(edges)
		table.to_csv('task_edges.csv', index=False)

class Scheduler:
	def __init__(self, nitems, time_span):
		self.time_span = time_span
		self.items = []
		self.total_time = 0
		
		# get all tasks without predecessors
		G = TaskFactory.task_graph
		next_tasks_id = []
		for task in G.nodes():
			if len(G.predecessors(task)) > 0: continue
			next_tasks_id.append(task)
		
		# creating items
		for i in range(nitems):
			self.items.append(Item(i, next_tasks_id))
			
	def execute(self):
		global TIMER
		TIMER = 0
		MAXIT = self.time_span
		niter = 0
		nitems = 0
		machine_efficiency = {}
		worker_efficiency = {}
		for machine in Resources.machines.values():
			machine_efficiency[machine] = 0.0
		for worker in Resources.workers.values():
			worker_efficiency[worker] = 0.0
			
		while len(self.items) > 0 and TIMER < MAXIT:
			niter += 1
			# print('----------------------------')
			# print('Time Step %d' % TIMER)
			
			# update task status
			for item in self.items:
				item.update()
				if item.done():
					nitems += 1
					self.items.remove(item)
					print('Removing Item[%3d] at %3.2fh remaing %d items' % (item.id, TIMER/3600, len(self.items)))
			
			# start next tasks
			for item in self.items:
				item.start_next_task()
				
			for machine in Resources.machines.values():
				if machine.working: machine_efficiency[machine] += 1
			for worker in Resources.workers.values():
				if worker.working: worker_efficiency[worker] += 1
				
			TIMER += 0.1
			# time.sleep(0.1)
			# Resources.status()
		
		self.total_time = TIMER/3600
		print('\nCompleted %d items after %3.2f hours' % (nitems, self.total_time))
		print('Efficiency')
		for machine in Resources.machines.values():
			print('%3.2f Machine[%2d] %s' %(machine_efficiency[machine]/niter,machine.id,machine.name))
		for worker in Resources.workers.values():
			print('%3.2f Worker[%2d] %s' %(worker_efficiency[worker]/niter,worker.id,worker.name))
		
# load resources (workers and machines)
Resources.load()
# Resources.show()

# load tasks
TaskFactory.load()
# TaskFactory.to_csv()

scheduler = Scheduler(1, 120 * 3600)
scheduler.execute()

# create scheduler
# nitems = range(1,121)
# ttimes = np.zeros(len(nitems))
# for k in range(len(nitems)):
# 	scheduler = Scheduler(nitems[k], 120 * 3600)
#	scheduler.execute()
#	ttimes[k] = scheduler.total_time
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
        self.active = False
        # machines that work operates
        self.machines = set()
        # current task
        self.current_task = None
        
    def add_machine(self, machine):
        self.machines.add(machine)
    
    def set_task(self, task):
        self.current_task = task
        self.active = True

    def update(self):
        if self.current_task is not None and self.current_task.done():
            self.current_task = None
            self.active = False
    
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
        self.active = False
        self.workers = set()
        self.current_task = None
    
    def add_operator(self, worker):
        self.workers.add(worker)

    def update(self):
        if self.current_task is not None and self.current_task.done():
            self.active = False
            self.current_task = None

    def set_task(self, task):
        self.current_task = task
        self.active = True

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
                machine.add_operator(worker)
                
    @staticmethod
    def show():
        print('Workers')
        for worker in Resources.workers.values():
            worker.show()
            
    @staticmethod
    def status():
        for worker in Resources.workers.values():
            print('Worker[%d]:%10s active: %s' % (worker.id, worker.name, worker.active))

class Item:
    def __init__(self, id, start_tasks):
        self.id = id
        self.next_tasks_id = set(start_tasks)
        self.tasks_done_id = set()
        self.current_task = None
        self.active = False
            
    def update(self):
        if self.current_task is not None and self.current_task.done():
            # print('Updating Item[%d] current_task %s' % (self.id, self.current_task.description))
            # print('Item[%2d] finishing Task[%d]' % (self.id, self.current_task.id))
            self.tasks_done_id.add(self.current_task.id)
            self.next_tasks_id.remove(self.current_task.id)
            # update the list of tasks ready to start
            for taskA_id in self.tasks_done_id:
                succA = TaskFactory.task_graph.successors(taskA_id)
                for taskB_id in succA:
                    if taskB_id in self.next_tasks_id or taskB_id in self.tasks_done_id: continue
                    predB = set(TaskFactory.task_graph.predecessors(taskB_id))
                    if predB.issubset(self.tasks_done_id): 
                        self.next_tasks_id.add(taskB_id)
                    
            # print('Item[%2d] tasks_done_id: ' % self.id, self.tasks_done_id)
            # print('Item[%2d] next_tasks_id: ' % self.id, self.next_tasks_id)

            self.current_task = None
            self.active = False
    
    def set_task(self, task):
        self.current_task = task
        self.active = True

    def done(self):
        is_done = len(self.next_tasks_id) == 0 
        return is_done

    def show(self):
        print('Show, Item[%2d] active: %s, next_tasks_id:' % (self.id, self.active), self.next_tasks_id)

class Task:
    def __init__(self, id, description, machine_type, processing_time, time_start=None, next_tasks_id=None):
        # unique identifier
        self.id = id
        # processing time
        self.processing_time = processing_time
        # list of (machine,worker) pairs
        self.machine_type = machine_type
        # processing start time
        self.time_start = time_start
        # next tasks
        if next_tasks_id is None:
            self.next_tasks_id = set()
        else:
            self.next_tasks_id = next_tasks_id
        # description
        self.description = description
        # item, machine, worker
        self.item = None
        self.machine = None
        self.worker = None
    
    def add_successor(self, task):
        self.next_tasks_id.add(task.id)
           
    def done(self):
        elapsed_time = TIMER - self.time_start
        is_done = abs(elapsed_time - self.processing_time) < 0.01 
        # if is_done: print('Task[%d] is done at %5.2f seconds' % (self.id, TIMER))
        return is_done
        
    def try_to_start(self, item):
        global TIMER
        # item.show()
        for machine in Resources.machines_by_type[self.machine_type]:
            if not machine.active:
                for worker in machine.workers:
                    if not worker.active:
                        self.time_start = TIMER
                        machine.set_task(self)
                        worker.set_task(self)
                        item.set_task(self)
                        self.machine = machine
                        self.worker = worker
                        self.item = item
                        # print('Starting, Task[%2d], %8.1f, Item[%3d], Worker[%2d], Machine[%2d], %8.1f' % (self.id, self.time_start, item.id, worker.id, machine.id, self.processing_time))
                        return True
        return False
        
    def clone(self):
        return Task(self.id, self.description, self.machine_type, self.processing_time, self.time_start,self.next_tasks_id)

    def show(self):
        print('Show, Task[%2d]' % (self.id))
        print('   machine   : %d' % self.machine_type)
        print('   proc_time : %5.2f' % self.processing_time)
        print('   successors:', self.next_tasks_id)

class TaskFactory:
    tasks = None
    task_graph = None
    
    @staticmethod
    def load():
        # read task database
        tasks = {}
        data = pd.read_csv('instances/tasks.csv')
        for index, row in data.iterrows():
            task = Task(row.ID, row.DESCRICAO, row.MAQUINA, row.TEMPO2)
            tasks[task.id] = task

        # read task precedence
        data = pd.read_csv('instances/tasks_graph.csv').values
        for row in data:
            taskA = tasks[row[0]]
            for taskB_id in row[1:]:
                if not pd.isnull(taskB_id):
                    taskB = tasks[taskB_id]
                    taskA.add_successor(taskB)

        # set task graph
        G = nx.DiGraph()
        for taskA in tasks.values():
            for taskB_id in taskA.next_tasks_id:
                G.add_edge(taskA.id, taskB_id)

        TaskFactory.tasks = tasks
        TaskFactory.task_graph = G
        
    @staticmethod
    def try_to_start(task_id, item):
        task = TaskFactory.tasks[task_id].clone()
        if task.try_to_start(item):
            return task
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
    def __init__(self, number_of_items, time_span):
        self.time_span = time_span
        self.items = []
        self.number_of_items = number_of_items
        
        # get all tasks without predecessors
        graph = TaskFactory.task_graph
        start_tasks_id = []
        for task in graph.nodes():
            if len(graph.predecessors(task)) > 0: continue
            start_tasks_id.append(task)
        
        # creating items
        for i in range(number_of_items):
            self.items.append(Item(i, start_tasks_id))

    def select_task_by_item(self, item):
        # try to start a task
        if not item.active:
            # item.show()
            # prioritizing (sorting by) the longest tasks
            tasks = [(TaskFactory.tasks[task_id].processing_time, task_id) for task_id in item.next_tasks_id]
            tasks = sorted(tasks)
            tasks.reverse()
            for processing_time, task_id in tasks:
                task = TaskFactory.try_to_start(task_id, item)
                if task is not None:
                    return task
        return None
    
    def select_task_by_worker(self):
        tasks = []
        for task in TaskFactory.tasks.values():
            if len(task.items) > 0:
                tasks.append((len(task.items),task))
        tasks = sorted(tasks)
        tasks.reverse()
        for nitems, tasks in tasks:
            task = TaskFactory.get_task(task_id)
            if(task != None):
                machine, worker = task.job
                # print('Starting, Item[%d], Task[%2d], %4f, Worker[%2d], %4f, Machine[%2d]' % (self.id, task.id, task.tproc, worker.id, task.time_start, machine.id))
                self.current_task = task
                break
        return self.current_task
            
    def update(self):
        global TIMER
        # check if the current task is done
        for item in self.items:
            item.update()
            if item.done():
                print('Item[%d] completed at %3.2f hours' % (item.id, TIMER/3600))
                self.items.remove(item)

        for machine in Resources.machines.values():
            machine.update()

        for worker in Resources.workers.values():
            worker.update()
            
    def execute(self):
        global TIMER
        TIMER = 0
        niter = 0
        tasks = []

        # init efficiency measurements
        machine_efficiency = {}
        worker_efficiency = {}
        for machine in Resources.machines.values():
            machine_efficiency[machine] = 0.0
        for worker in Resources.workers.values():
            worker_efficiency[worker] = 0.0
            
        while len(self.items) > 0 and TIMER < self.time_span:
            niter += 1
            self.update()

            for item in self.items:
                task = self.select_task_by_item(item)
                if task is not None:
                    tasks.append(task)

            # update efficieny measurements
            for machine in Resources.machines.values():
                if machine.active: machine_efficiency[machine] += 1
            for worker in Resources.workers.values():
                if worker.active: worker_efficiency[worker] += 1
                
            TIMER += 0.1
            # time.sleep(0.1)
            # Resources.status()
        
        number_of_completed_items = self.number_of_items - len(self.items)
        print('\nCompleted %d/%d items after %3.2f hours' % (number_of_completed_items, self.number_of_items, TIMER/3600))
        print('Efficiency')
        for machine in Resources.machines.values():
            print('%3.2f Machine[%2d] %s' %(machine_efficiency[machine]/niter,machine.id,machine.name))
        for worker in Resources.workers.values():
            print('%3.2f Worker[%2d] %s' %(worker_efficiency[worker]/niter,worker.id,worker.name))
            
        # plotting the solution
        with open('markov_agent.csv', 'w') as fid:
            fid.write('item,task,worker,tstart,tproc\n')
            for task in tasks:
                fid.write('%d,%d,%d,%f,%f\n' % (task.item.id, task.id, task.worker.id, task.time_start, task.processing_time))
        workers = Resources.workers.values()
        fig, ax = plt.subplots()
        ax.set_xlim(0, TIMER/3600) # in hours
        ax.set_xlabel('Hours')
        ax.set_yticks(range(10,15 + 10 * len(workers), 10))
        ax.set_yticklabels([work.name for work in workers])
        ax.set_ylim(0, 10 + 10 * len(workers)) 
        ax.grid(True)
        for task in tasks:
            tproc = task.processing_time / 3600 # in hours
            tstart = task.time_start / 3600 # in hours
            tend = tstart + tproc
            ycoord = 7.5 + 10 * task.worker.id 
            ax.broken_barh([(tstart,tend)], (ycoord, 5), facecolors='blue')
        plt.show()
        
        
# load resources (workers and machines)
Resources.load()
# Resources.show()

# load tasks
TaskFactory.load()
# TaskFactory.to_csv()

scheduler = Scheduler(120, 9 * 3600)
scheduler.execute()

# create scheduler
# nitems = range(1,121)
# ttimes = np.zeros(len(nitems))
# for k in range(len(nitems)):
#     scheduler = Scheduler(nitems[k], 120 * 3600)
#    scheduler.execute()
#    ttimes[k] = scheduler.total_time
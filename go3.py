import numpy as np
import random
import sys

def go3(m=10,n=5):
    # Problem: Find the first point whose the total score is positive
    # m :: number of rules
    # n :: number of variables

    # Get instance =======================================================
    data = DataSet.random(m,n)

def instance_random(m,n,dvars=0.1,bsignal=0.5,bscore=0.5):
    # m :: number of rules
    # n :: number of variables
    # dvars :: density of variables used by each rule
    # bsignal :: bias in the signs inside the rules
    # bscore  :: bias in the rules score

    # set rules[i,j]={0:ignored,-1,+1}
    rules  = np.zeros((m,n))
    for i in range(0,m):
        for j in range(0,n):            
            rules[i,j] = (random.uniform(0,1) < dvars) * ((-1) ** (bsignal<random.uniform(0,1)))
               
    # removing empty rules
    irow  = np.dot(np.abs(rules),np.ones(n)) > 0
    rules = rules[irow,:]    
    
    # removing variables ignored by all rules
    m     = np.sum(irow)
    icol  = np.dot(np.ones(m),np.abs(rules)) > 0
    rules = rules[:,icol]
    n     = np.sum(icol)
    
    # set the scores {-1,+1}
    scores = np.zeros(m)
    for i in range(0,m):
        scores[i] = (-1) ** (bscore < random.uniform(0,1))

    return DataSet(rules, scores)

class DataSet:
    def __init__(self, rules, scores):
        self.rules  = rules        
        self.scores = scores
        (self.m, self.n) = rules.shape
        self.display()
        
    def display(self):
        print('.. DataSet(%d,%d) ..' % (self.m, self.n))
        for i in range(0,self.m):            
            for j in range(0,self.n):
                sys.stdout.write('% d ' % self.rules[i,j])
            sys.stdout.write('| % d\n' % self.scores[i])
            
    @staticmethod
    def random(m,n,dvars=0.1,bsignal=0.5,bscore=0.5):
        # m :: number of rules
        # n :: number of variables
        # dvars :: density of variables used by each rule
        # bsignal :: bias in the signs inside the rules
        # bscore  :: bias in the rules score
    
        # set rules[i,j]={0:ignored,-1,+1}
        rules  = np.zeros((m,n))
        for i in range(0,m):
            for j in range(0,n):            
                rules[i,j] = (random.uniform(0,1) < dvars) * ((-1) ** (bsignal<random.uniform(0,1)))
                   
        # removing empty rules
        irow  = np.dot(np.abs(rules),np.ones(n)) > 0
        rules = rules[irow,:]    
        
        # removing variables ignored by all rules
        m     = np.sum(irow)
        icol  = np.dot(np.ones(m),np.abs(rules)) > 0
        rules = rules[:,icol]
        n     = np.sum(icol)
        
        # set the scores {-1,+1}
        scores = np.zeros(m)
        for i in range(0,m):
            scores[i] = (-1) ** (bscore < random.uniform(0,1))
    
        return DataSet(rules, scores)
    

go3()
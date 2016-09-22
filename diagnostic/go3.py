import numpy as np
import random
import sys
import time
# https://docs.python.org/3/library/argparse.html
import argparse
# http://www.grantjenks.com/docs/sortedcontainers/
from sortedcontainers import SortedList

class DataSet(object):
    # m :: number of rules
    # n :: number of variables
    def __init__(self, rules, scores):        
        self.rules  = self.mat2rules(rules)
        self.scores = scores
        (self.m, self.n) = rules.shape
        self.display()

    @staticmethod
    def mat2rules(mat):
        (m,n) = mat.shape
        rules = []; # empty list
        for i in range(0,m):
            rule = {}; # empty dictionary
            for j in range(0,n):
                if(mat[i,j] != 0): rule[j] = mat[i,j];
            rules.append(rule)
        return rules

    def display(self):
        print('>> DataSet(%d,%d)' % (self.m, self.n))
        for i in range(0,self.m):            
            for j in range(0,self.n):
                if(self.rules[i].has_key(j)):
                    sys.stdout.write('% d ' % self.rules[i][j])
                else:
                    sys.stdout.write(' 0 ')
            sys.stdout.write('| % d\n' % self.scores[i])
            
    def display_score(self,x):
        (s,sx) = self.score(x)

        # display x        
        sys.stdout.write('>> Solution\nx = ')
        for i in range(0,self.n): sys.stdout.write('% d ' % (x[i]))
        sys.stdout.write('\n')
        sys.stdout.write('s = %d\n' % (s))

        # display data set        
        self.display()
        
        # display rules
        print('>> Rules')
        for i in range(0,self.m):            
            for j in range(0,self.n):
                if(self.rules[i].has_key(j)):
                    sys.stdout.write('% d ' % self.rules[i][j])
                else:
                    sys.stdout.write(' 0 ')
            sys.stdout.write('| % d [% d]\n' % (self.scores[i], sx[i]))

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

    def score(self,x,rules=None,scores=None):
        # Set args
        if(rules == None): rules = self.rules
        if(scores == None): scores = self.scores
        m = len(rules)
        n = len(x)
        # eval score
        s = np.zeros(m);
        for i in range(0, m):
            sat = True;
            for j in rules[i].keys():
                if(rules[i][j] != x[j]): 
                    sat = False; break;
            if(sat):
                # sys.stdout.write('s      = '); print(s)
                # sys.stdout.write('scores = '); print(scores)
                # sys.stdout.write('i      = '); print(i)                
                # sys.stdout.write('m      = '); print(m)                
                s[i] = scores[i];

        return (np.sum(s),s)

    @staticmethod
    def load(filename):
        data = np.loadtxt(open(filename,"rb"),delimiter=" ")
        scores = data[:,-1]
        rules  = data[:,0:-1]
        return DataSet(rules,scores)

def SolverBruteForce(data,x):
    print('> Solver BruteForce ==================')
    n      = len(x); # number of variables    
    (sx,s) = data.score(x)
    tic    = time.clock()    
    # print('Level %3d/%d completed after %3.2f seconds' %(0,n,time.clock() - tic))    
    if(sx > 0): return (x,sx)
    for dist in range(1,(n+1)):
        hasnext = True;
        iset    = range(dist);
        tic = time.clock();        
        while((sx < 1) and hasnext):
            # move to next
            x[iset] = x[iset] * (-1); # flip

            # a solution has been found
            (sx,s) = data.score(x)
            if(sx > 0):
                # print('Level %3d/%d completed after %3.2f seconds' % (dist,n,tic - time.clock()));
                return (x,sx)
                
            # restore original solution
            x[iset] = x[iset] * (-1); # flip
            # next subset of indices
            j = len(iset) - 1; # last index
            while(j >= 0):
                # max value of iset[j]
                jmax = n-dist+j
                if(iset[j] < jmax):
                    hasnext  = True;
                    iset[j] += 1;
                    for k in range(j+1,dist):
                        iset[k] = iset[k-1] + 1;
                    break;
                else:
                    j = j - 1;
                hasnext = False;
        # print('Level %3d/%d completed after %3.2f seconds' % (dist,n,tic - time.clock()));

def SolverBB(data,x,level=None,flips=0,y=None):
    global xs # current solution
    global fl # number of flips in the current solution

    # if(y is not None):
        # sys.stdout.write('level = '); print(level)
        # sys.stdout.write('flips = '); print(flips)    
        # sys.stdout.write('y     = '); print(y[0:level])

    # root node
    if(y == None):
        print('>> Solver BranchAndBound =========')
        y  = np.zeros(len(x));
        xs = None
        fl = None
        for level in range(data.n):
            y[level] = (-1) * x[level] # flip
            SolverBB(data, x, 1, 1, y)
            y[level] = x[level]        # keep

        # returns final solution
        return(xs,data.score(xs))

    # cut 
    elif(fl != None and flips >= fl):
        # print('cut')
        return

    # eval complete solution
    elif(level == len(x)):
        # print('Evaluating')
        (sx,s) = data.score(y)
        # better solution found (update)
        if(sx > 0):
            # print('Solution updated')
            xs = y.copy()
            fl = flips
            # sys.stdout.write('xs = '); print(xs)
            # sys.stdout.write('fl = '); print(fl)
        else:
            return

    # binary branch
    else:
        # child(-1):flip
        y[level] =  (-1) * x[level] # flip  
        # print('Branch(-1)')      
        SolverBB(data, x, level + 1, flips + 1, y)
        
        # child(+1):keep
        y[level] = x[level]
        # print('Branch(+1)')      
        SolverBB(data, x, level + 1, flips, y)        


if __name__ == "__main__":
    # Parsing arguments
    # https://docs.python.org/2/howto/argparse.html
    # parser = argparse.ArgumentParser()
    # args = parser.parse_args()

    # read instance
    data = DataSet.load('forest2rules/basic.txt')

    # Set starting point
    x = np.ones(data.n);
    
    # Call solver BruteForce
    (z,s) = SolverBruteForce(data,x);

    # Display result
    data.display_score(z)

    # Call solver BranchAndBound
    (z,s) = SolverBB(data,x)
    data.display_score(z)

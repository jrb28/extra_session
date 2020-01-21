# -*- coding: utf-8 -*-
"""
Created on Wed Nov 02 11:15:53 2016

@author: james.bradley
"""

from gurobipy import *
import MySQLdb as mySQL
import matplotlib.pyplot as plt
#from matplotlib.backends.backend_pdf import PdfPages

def getDBData(commandString, connection):
    cursor = connection.cursor()
    cursor.execute(commandString)
    results = list(cursor.fetchall())
    cursor.close()
    return results

port_size = 100.0
#ret_vec = [0.25,0.15,0.3,0.05]
#var_covar = [[2,.05,-0.3,.05],[0.05,2,-.5,.4],[-0.3,-.5,2,.3],[0.05,.4,.3,2]]
#avg_return = [0.05,0.1,0.2,0.25]
#v_dim = len(var_covar)
max_risk = 5.0
max_risk_inc = 5.0
numRiskLevels = 19
numStocks = 15
results = []

#data = getDBData("CALL `spGetNStocksVarCovar`(%s);" % numStocks,cnx)
vc = {}
f = open('D:\\TeachingMaterials\\BusinessAnalytics\\Optimization\\QP\\Portfolio/PortDataVarCovar.csv', 'r')
for line in f:
       line = line.strip()
       line = line.strip("\n")
       pieces = line.split(",")
       stock1,stock2,covar = pieces
       stock1 = int(stock1)
       stock2 = int(stock2)
       covar = float(covar)
       vc[(stock1,stock2)] = covar
f.close()

avg_return= {}
f = open('D:\\TeachingMaterials\\BusinessAnalytics\\Optimization\\QP\\Portfolio/avgReturns.csv', 'r')
for line in f:
       line = line.strip()
       line = line.strip("\n")
       pieces = line.split(",")
       id_stock,avgReturn = pieces
       id_stock = int(id_stock)
       avgReturn = float(avgReturn)
       avg_return[id_stock] = avgReturn
f.close()

"""vc = {}
for i in range(v_dim):
    for j in range(v_dim):
        vc[(i,j)] = var_covar[i][j]
del var_covar
"""

m = Model("QP-Proto")
m.ModelSense = GRB.MAXIMIZE

x = {}
for i in avg_return.keys():
    x[i] = m.addVar(vtype=GRB.CONTINUOUS,lb=0.0,name="a"+str(i))

m.update()

m.addConstr(quicksum(x[i] for i in x.keys()),GRB.EQUAL,port_size,name="Fixed Portfolio Size")
"""m.addConstr(quicksum(ret_vec[i]*x[i]/port_size for i in x.keys()),GRB.GREATER_EQUAL,0.3)"""
m.addConstr(quicksum(x[i] * vc[(i,j)] * x[j]  for i in range(numStocks) for j in range(numStocks)),GRB.LESS_EQUAL, max_risk,name="Risk Constraint (Quadratic)")

"""m.setObjective(quicksum(x[i] * vc[(i,j)] * x[j] for i in range(v_dim) for j in range(v_dim)),GRB.MINIMIZE)"""
m.setObjective(quicksum(avg_return[i] * x[i] / port_size for i in range(numStocks)),GRB.MAXIMIZE)
m.update()
m.optimize()

if m.status == 2:
    results.append([max_risk,m.ObjVal])
    #print m.ObjVal
    for i in avg_return.keys():
        print "x["+str(i)+"] =",x[i].x
        
    print "Num. Constraints:", len(m.getConstrs())
    for constr in m.getConstrs():
        print constr.ConstrName
        
    print "Num. Quadratic Constraints:", m.NumQConstrs
    for constr in m.getQConstrs():
        print constr.QCName, constr.QCRHS
else:
    print "initial model infeasible"
    print
    print
    
for i in range(numRiskLevels):
    for constr in m.getQConstrs():
        if constr.QCName == "Risk Constraint (Quadratic)":
            """ Update RHS """
            max_risk = max_risk + max_risk_inc
            constr.QCRHS = max_risk
            m.update()
                        
            """ Alternate Loop Method """
            """
            m.remove(constr)
            m.update()
            max_risk = max_risk + max_risk_inc
            m.addConstr(quicksum(x[i] * vc[(i,j)] * x[j]  for i in range(numStocks) for j in range(numStocks)),GRB.LESS_EQUAL, max_risk,name="Risk Constraint (Quadratic)")
            m.update()
            """
    m.optimize()
    if m.status == 2:
        results.append([max_risk,m.ObjVal])
        #print m.ObjVal
    else:
        print "Model ",str(i)," Infeasible"
        
"""
print results
print zip(*results)
print
"""

""" Two ways to create separate lists of x,y data """
y,x = zip(*results) # the asterisk * indicates that the list is to be unzipped, that is, separated into multiple lists
#y1 = [d[0] for d in results]
#x1 = [d[1] for d in results]

for pair in results:
    pair[0] = (12*pair[0])**0.5/port_size
    pair[1] = (1.0 + pair[1]) ** 12.0 - 1.0

plt.figure(figsize = (10,7))
plt.plot(*zip(*results))
plt.scatter(*zip(*results))
plt.ylabel("Expected Portfolio Return")
plt.xlabel("Portfolio Return Standard Deviation Per Dollar")
plt.title('Annual Return vs. Risk of $100 Portfolio',fontsize = 22)
ax = plt.axes()
ax.xaxis.label.set_fontsize(20)
ax.yaxis.label.set_fontsize(20)
ax.xaxis
ax.tick_params(axis='both',labelsize =14)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.set_xlim([min([mp[0] for mp in results])*0.9,max([mp[0] for mp in results])*1.1])
plt.tick_params(axis='both',which='both',top='off',right='off')
plt.savefig('D:/TeachingMaterials/BusinessAnalytics/Optimization/QP/Portfolio/ef.jpg')
plt.show()
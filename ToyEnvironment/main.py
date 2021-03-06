import matplotlib.pyplot as plt
from Grid import *
from boltzmann_rational import *
from irrational_behavior import *
import numpy as np

print("Environment 1 initialization (boltzmann noisy-rational and irrational bias) ... \n")
oox = grid([5,6])
oox.add_end([2,5])
oox.add_danger([2,4])
oox.add_danger([2,3])
oox.add_danger([3,4])
oox.add_danger([4,4])
oox.add_danger([4,3])
oox.add_danger([4,2])
oox.add_danger([4,1])

oox.print_env()

step_, err_ = oox.q_learning(50,50000)

vi = value_iterate(oox)

print("Trajectories Boltzmann VI :")
beta = [0,0.5,1,10]
for b in beta:
    vB = boltz_rational(oox,b)
    print(vB)
    print("Beta = ",b," :",end=" ")
    generate_traj_v(oox,vB,[3,3])
    print("\n")

print("\nTrajectories Boltzmann noisy-rational :")
beta = [10000,2,0.1,0.02]
for b in beta:
    print("Beta = ",1/b," :",end=" ")
    demo, start_ = boltz_rational_noisy(oox,b,1,[3,3])
    oox.reset([3,3])
    print("Start =",start_,"-> ",len(demo[0]),"iterations",end="")
    print(action2str(demo[0]),"\n")


print("\n\nEnvironment 2 initialization (prospect bias) (...\n")

grid1 = grid([5,5])
grid1.add_end([0,4])

# for i in range(2):
#     for j in range(1,3):
#         grid1.add_danger([i,j])
#
# for i in range(1,2):
#     for j in range(2,4):
#         grid1.add_danger([i,j])

grid1.add_danger([0,1])
grid1.add_danger([0,2])
grid1.add_danger([1,1])
grid1.add_danger([1,2])
grid1.add_danger([2,2])
grid1.add_danger([3,2])
grid1.add_danger([3,3])

grid1.print_env()

step_, err_ = grid1.q_learning(50,50000)

print("Prospect bias :")
vP = prospect_bias(grid1,4)
vP1 = prospect_bias(grid1,5)
print("\n")
generate_traj_v(grid1,vP,[0,0])
generate_traj_v(grid1,vP1,[0,0])

print("\n\nEnvironment 3 initialization (extremal)...\n")

grid2 = grid([5,5])
grid2.add_end([1,4])
for i in [1,2]:
    for j in [1,2]:
        grid2.add_danger([i,j])
grid2.add_danger([0,1])
grid2.add_danger([3,1])
grid2.add_danger([4,3])
grid2.print_env()

step_, err_ = grid2.q_learning(200,50000)



print("\nExtremal :")
vE = extremal(grid2,0)
vE1 = extremal(grid2,1)

print("\n")
generate_traj_v(grid2,vE,[0,0])
generate_traj_v(grid2,vE1,[0,0])


"""
plt.plot(err_)
plt.title("Temporal difference")
plt.show()


n_demo = 10
tau = 0.02

oox.reset([3,3])
oox.reset(oox.start)
oox.print_env()

print("Tau = 0.02")
demonstration,start_= boltz_rational_noisy(oox,tau,n_demo,oox.start)
print("Mean demonstration length =",sum([np.size(s) for s in demonstration ])//n_demo)
print("Std demonstration length =",np.std([np.size(s) for s in demonstration ]))

oox.reset(oox.start)
oox.print_env()
print("Start =",start_,end="\n\n")
for k in range(n_demo):
    print("  * Demonstration #",k+1,"=",action2str(demonstration[k]))


print("\nTau = 0.1")
tau=0.1
demonstration,start_= boltz_rational_noisy(oox,tau,n_demo,oox.start)
print("Mean demonstration length =",sum([np.size(s) for s in demonstration ])//n_demo)
print("Std demonstration length =",np.std([np.size(s) for s in demonstration ]))

# oox.reset(oox.start)
# oox.print_env()
# print("Start =",start_,end="\n\n")
# for k in range(n_demo):
#     print("  * Demonstration #",k+1,"=",action2str(demonstration[k]))


print("\nTau = 1")
tau=1
demonstration,start_= boltz_rational_noisy(oox,tau,n_demo,oox.start)
print("Mean demonstration length =",sum([np.size(s) for s in demonstration ])//n_demo)
print("Std demonstration length =",np.std([np.size(s) for s in demonstration ]))

# oox.reset(oox.start)
# oox.print_env()
# print("Start =",start_,end="\n\n")
# for k in range(n_demo):
#     print("  * Demonstration #",k+1,"=",action2str(demonstration[k]))

"""

import gym
import gym_maze
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.lines as mlines
from tqdm import tqdm
import time


# LR = 0.05
# EPSILON = 0.02
MAX_EPISODE = 10000
MAX_STEP = 500
# DISCOUNT = 1
MIN_STREAK = MAX_EPISODE
RENDER = 0
SIMULATE = 0
RENDER_TIME = 0.05

DETERMINISTIC = True


def plot_v_value(fig,ax,maze,v_vector,title):

    _, walls_list = maze.edges_and_walls_list_extractor()

    ax.set_xlim(-1,maze.maze_size)
    ax.set_ylim(maze.maze_size,-1)
    ax.set_aspect('equal')


    im = ax.imshow(np.transpose(v_vector.reshape(maze.maze_size,maze.maze_size)))

    for state in range(0,maze.maze_size*maze.maze_size):
        i=state//maze.maze_size
        j=state%maze.maze_size
        text = ax.text(i,j, str(v_vector[i,j])[0:4],ha="center", va="center", color="black")


    for i in walls_list:
        ax.add_line(mlines.Line2D([i[1][0]-0.5,i[1][1]-0.5],[i[0][0]-0.5,i[0][1]-0.5],color='k'))

    for i in range(0,maze.maze_size):
        ax.add_line(mlines.Line2D([-0.5,-0.5],[i-0.5,i+0.5],color='k'))
        ax.add_line(mlines.Line2D([i-0.5,i+0.5],[-0.5,-0.5],color='k'))
        ax.add_line(mlines.Line2D([maze.maze_size-0.5,maze.maze_size-0.5],[i-0.5,i+0.5],color='k'))
        ax.add_line(mlines.Line2D([i-0.5,i+0.5],[maze.maze_size-0.5,maze.maze_size-0.5],color='k'))

    fig.suptitle(title)

def plot_traj(fig,ax,maze,v_vector,nb_traj,max_step,title,operator,beta):

    traj = np.zeros((maze.maze_size,maze.maze_size),dtype=int)
    total_length = []

    for epoch in tqdm(range(nb_traj)):
        maze.env.reset()
        state = [0,0]
        traj[tuple(state)]+=1
        length = 0
        
        while (maze.env.state!=maze.env.observation_space.high).any() and length < max_step:
            action = maze.select_action_from_v(state,v_vector,maze.reward_type,operator,beta)[0]
            new_s,reward,done,_ = maze.env.step(int(action))
            state = new_s
            traj[tuple(state)]+=1
            length+=1
        total_length.append(length)

    print("Mean length",int(np.array(total_length).mean()),"Standard deviation",int(np.array(total_length).std()))
    print(total_length)
    ax.set_xlim(-1,maze.maze_size)
    ax.set_ylim(maze.maze_size,-1)
    ax.set_aspect('equal')
    fig.suptitle(title)

    #Draw value table
    im = ax.imshow(np.transpose(traj.reshape(maze.maze_size,maze.maze_size)))
    for state in range(0,maze.maze_size*maze.maze_size):
        i=state//maze.maze_size
        j=state%maze.maze_size
        text = ax.text(i,j, str(traj[i,j])[0:4],ha="center", va="center", color="black")



def plot_policy(fig,ax,maze,v_vector,title,operator,beta):

    _, walls_list = maze.edges_and_walls_list_extractor()

    ax.set_xlim(-1,maze.maze_size)
    ax.set_ylim(maze.maze_size,-1)
    ax.set_aspect('equal')

    ax.scatter(0,0, marker="o", s=100,c="b")
    ax.scatter(maze.maze_size-1,maze.maze_size-1, marker="o", s=100,c="r")

    for i in range(maze.maze_size):
        for j in range(maze.maze_size):

            if ([i,j]==[maze.maze_size-1,maze.maze_size-1]):
                break

            action = maze.select_action_from_v([i,j],v_vector,maze.reward_type,operator,beta)[0]

            if action==0:
                ax.quiver(i,j,0,.05,color='c')#,width=0.01,headwidth=2,headlength=1)
            if action==1:
                ax.quiver(i,j,0,-.05,color='c')#,width=0.01,headwidth=2,headlength=1)
            if action==2:
                ax.quiver(i,j,.05,0,color='c')#,width=0.01,headwidth=2,headlength=1)
            if action==3:
                ax.quiver(i,j,-.05,0,color='c')#,width=0.01,headwidth=2,headlength=1)

    
    for i in walls_list:
        ax.add_line(mlines.Line2D([i[1][0]-0.5,i[1][1]-0.5],[i[0][0]-0.5,i[0][1]-0.5],color='k'))

    for i in range(0,maze.maze_size):
        ax.add_line(mlines.Line2D([-0.5,-0.5],[i-0.5,i+0.5],color='k'))
        ax.add_line(mlines.Line2D([i-0.5,i+0.5],[-0.5,-0.5],color='k'))
        ax.add_line(mlines.Line2D([maze.maze_size-0.5,maze.maze_size-0.5],[i-0.5,i+0.5],color='k'))
        ax.add_line(mlines.Line2D([i-0.5,i+0.5],[maze.maze_size-0.5,maze.maze_size-0.5],color='k'))

    fig.suptitle(title)


def compare_traj(traj_opti,traj,maze):

    distance_traj = np.zeros((maze.maze_size,maze.maze_size))

    for k in range(len(traj_opti)):

        state_opti = tuple(traj_opti[k])
        state = tuple(traj[k])

        distance_traj[tuple(state_opti)] = abs(state_opti[0]-state[0]) + abs(state_opti[1]-state[1])

    return np.transpose(distance_traj)


class MyMaze():

    def __init__(self,env_name,reward,lr=0.05,epsi=0.02,disc=0.99):

        self.env = gym.make(env_name)
        self.env.render()
        self.reward_type = reward

        self.maze_size = self.env.observation_space.high[0] + 1
        self.epsilon = epsi
        self.discount = disc
        self.lr = lr


        self.optimal_policy = []
        self.reward_table = [] 
        self.new_state_table = self.get_new_state()
        self.transition_table = self.get_transition_probalities()


        


        # MAX_SIZE = tuple((env.observation_space.high + np.ones(env.observation_space.shape)).astype(int))
        # NUM_BUCKETS = MAX_SIZE
        # NUM_ACTIONS = env.action_space.n
        # STATE_BOUNDS = list(zip(env.observation_space.low, env.observation_space.high))


        


    ################# HELPER FUNCTIONS #############################################

    def action2str(self,demo):
        #Turn action index into str

        res=[]
        for i in demo:
            if i==0:
                res.append("North")
            elif i==1:
                res.append("South")
            elif i==2:
                res.append("East")
            else :
                res.append("West")

        return res
    


    def get_new_state(self):

        # Outputs an array with every new state reached after executing action A from a state S

        new_state_tab = np.zeros((self.maze_size,self.maze_size,4),dtype=tuple)
        state = self.env.reset()
        state = tuple(state)

        dic_action = ["N","S","E","W"]

        for i in range(self.maze_size):
            for j in range(self.maze_size):

                state = np.array([i,j])

                for a in range(4):
                    self.env.env.reset(state)
                    new_s,r,_,_ = self.env.step(int(a))
                    #print(state,dic_action[a],new_s)
                    new_state_tab[tuple(state)+(a,)] = tuple(new_s)


        return new_state_tab

    def get_transition_probalities(self):

        # Outputs transition matrix T(s,a,s')

        transition_tab = np.zeros((self.maze_size*self.maze_size,self.maze_size*self.maze_size,4),dtype=tuple)

        if DETERMINISTIC:
            #Deterministic case


            dic_action = ["N","S","E","W"]
            for i in range(self.maze_size):
                for j in range(self.maze_size):

                    state = self.env.env.reset(np.array([i,j]))
                    state = tuple(state)

                    for a in range(4):
                        new_state = self.new_state_table[tuple(state)+(a,)]
                        lin_state = state[0]*self.maze_size+state[1]
                        #print(state,lin_state)
                        lin_new_state = new_state[0]*self.maze_size+new_state[1]
                        #print(state,"--",dic_action[a],"->",new_state)

                        if tuple(new_state)==state:
                            transition_tab[lin_state,lin_state,a] = 1  
                        else:
                            transition_tab[lin_state,lin_new_state,a] = 1
                    #print("\n")
        else:

            for i in range(self.maze_size):
                for j in range(self.maze_size):

                    for a in range(4):

                        for e in range(100):
                            state = self.env.env.reset(np.array([i,j]))
                            state = tuple(state)
                            new_state,reward,done,_ = self.env.step(a)
                            lin_state = state[0]*self.maze_size+state[1]
                            lin_new_state = new_state[0]*self.maze_size+new_state[1]
                            transition_tab[lin_state,lin_state,a]+=1

            transition_tab = transition_tab/100


        return transition_tab

                 



    def set_optimal_policy(self,q_table):

        # Sets optimal policy from a given Q-table

        optimal_policy = np.zeros((self.maze_size,self.maze_size),dtype=int)
        for i in range(self.maze_size):
            for j in range(self.maze_size):

                optimal_policy[i,j] = np.argmax(q_table[tuple([i,j])])


        self.optimal_policy = optimal_policy



    def set_reward(self,obstacle=[]):

        reward_table = np.zeros((self.maze_size,self.maze_size,4))

        end = tuple(self.env.observation_space.high)
        empty_obstacle = (obstacle==[])

        for i in range(self.maze_size):
            for j in range(self.maze_size):

                state = tuple([i,j])

                for action in range(4):

                    optimal_action = self.optimal_policy[state]
                    new_state = self.new_state_table[state+(action,)]

                    o = [(k==list(state)).all() for k in obstacle]
                    #print(o)
                    if not(empty_obstacle) and (True in o):
                        reward_table[state+(action,)] = -2
                    elif action==optimal_action:
                        if new_state==end:
                            reward_table[state+(action,)] = 10
                        else:
                            reward_table[state+(action,)] = 1
                    else:
                        reward_table[state+(action,)] = -1


            #time.sleep(0.5)


        self.reward_table = reward_table



    def get_entropy_map_v(self,v_table):


        entropy_map = np.zeros((self.maze_size,self.maze_size),dtype=float)

        for i in range(self.maze_size):
            for j in range(self.maze_size):


                state = tuple([i,j])
                lin_state = i*self.maze_size + j
                x = []

                for a in range(4):

                    non_zero_new_state = np.where(self.transition_table[lin_state,:,a]!=0)[0]
                        
                    for k in non_zero_new_state:

                        new_state = tuple([k//self.maze_size,k%self.maze_size])

                        if self.reward_type=="env":
                            if new_state == tuple(end):
                                reward = 1
                            else:
                                reward = -1/(self.maze_size**2)
                        else:
                            reward = self.reward_table[state+(a,)]

                        x.append(self.transition_table[lin_state,k,a]*(reward+self.discount*v_table[new_state]))

                x = np.array(x,dtype=float)
                b = np.max(x)
                p = np.exp((x-b)*2)/np.sum(np.exp((x-b)*2))
                entropy_map[i,j] = -np.sum(p*np.log(p))

        return entropy_map

    def get_entropy_map_q(self,q_table):


        entropy_map = np.zeros((self.maze_size,self.maze_size),dtype=float)

        for i in range(self.maze_size):
            for j in range(self.maze_size):

                state = tuple([i,j])
                b = np.max(q_table[state])
                p = np.exp((q_table[state]-b)*8)/np.sum(np.exp((q_table[state]-b)*8))
                entropy_map[i,j] = -np.sum(p*np.log(p))

        return entropy_map


    def select_action_from_v(self,state,v,reward_type,operator,beta):

        # Selects action following a policy given a Value-function v

        # -> reward_type: either "env" (reward given by GymMaze = -1/num_tile for every step) 
        #                 or "human" (+1 if action=optimal_action, -1 otherwise)

        # -> operator: selection operator, either "argmax" or "softmax" 
        #              "softmax" is mainly used for the boltzmann irrational bias which already uses a Boltzmann (or Gibbs, softmax) summary operator.
        #              Here, the softmax operator is used to turn expected rewards into a distribution over actions. 

        v_choice = []
        self.env.env.reset(np.array(state))


        for a in range(4):

            new_state = self.new_state_table[tuple(state) + (a,)]

            if reward_type=="human":

                optimal_action = self.optimal_policy[tuple(state)]
                reward = self.reward_table[tuple(state)+(a,)]

            elif reward_type=="env":

                if tuple(new_state)==tuple(self.env.observation_space.high):
                    reward = 1
                else:
                    reward = -1/(self.maze_size*self.maze_size)

            else:
                print("Unknown reward type")


            v_choice.append(reward + self.discount*v[tuple(new_state)])



        p = np.exp(v_choice)/np.sum(np.exp(v_choice))
        #print(p,v_choice)
        h = -np.sum(p*np.log(p))

        if operator=="argmax":
            action = np.argmax(v_choice)

        elif operator=="softmax":
            v_choice = np.array(v_choice)
            b = np.max(v_choice)
            x = np.exp((v_choice-b)*beta)/np.sum(np.exp((v_choice-b)*beta))
            action = np.random.choice([0,1,2,3],p=x)

        

        return action,h


    def generate_traj_v(self,v,operator,beta):

        # Generates trajectory following a policy derived from value function v
        # If RENDER=True, the trajectory is displayed on the GymMaze graphical environment
        # Also, if RENDER=TRUE, the entropy of expected rewards distribution at each step is displayed 

        done=False
        obv = self.env.env.reset([0,0])
        s = tuple(obv)
        it=0
        action_ = []
        entropy = []
        traj = []
        traj.append(list(s))

        #self.env.render()

        while not(done):# and it<1000:


            action, h = self.select_action_from_v(s,v,self.reward_type,operator,beta)
            entropy.append(h)
            new_s,reward,done,_ = self.env.step(int(action))

            it+=1
            action_.append(action)
            obv = new_s
            s = tuple(obv)
            traj.append(list(s))


            # if RENDER:
            #     self.env.render()
            #     time.sleep(RENDER_TIME)
                
        #print("Start ",self.env.reset(),"->",it,"iterations",self.action2str(action_))

        # if RENDER:
        #     plt.figure()
        #     plt.plot(entropy)
        #     plt.show()

        
        

        return action_, traj


    def edges_and_walls_list_extractor(self):

          edges_list = []
          walls_list = []
          maze = self.env.env.maze_view.maze

          
          # top line and left line
          for i in range(0,self.maze_size):
              walls_list.append([[0,0],[i,i+1]]) # north walls
              walls_list.append([[i,i+1],[0,0]]) # west walls

          # other matplotlib.lines
          for i in range(0,self.maze_size):
              for j in range(0,self.maze_size):
                  walls_list.append([[i+1,i+1],[j,j+1]]) # south walls
                  walls_list.append([[i,i+1],[j+1,j+1]]) # east walls


          for i in range(0,self.maze_size):
              for j in range(0,self.maze_size):
                  maze_cell = maze.get_walls_status(maze.maze_cells[j,i])
                  if maze_cell['N']==1 and [[i,i],[j,j+1]] in walls_list:
                      walls_list.remove([[i,i],[j,j+1]])
                  if maze_cell['S']==1 and [[i+1,i+1],[j,j+1]] in walls_list:
                      walls_list.remove([[i+1,i+1],[j,j+1]])
                  if maze_cell['E']==1 and [[i,i+1],[j+1,j+1]] in walls_list:
                      walls_list.remove([[i,i+1],[j+1,j+1]])
                  if maze_cell['W']==1 and [[i,i+1],[j,j]] in walls_list:
                      walls_list.remove([[i,i+1],[j,j]])

          for i in range(0,self.maze_size):
              for j in range(0,self.maze_size):
                  idx = i + j*self.maze_size
                  if [[i,i],[j,j+1]] not in walls_list:
                      edges_list.append((idx,idx-1,1))
                      #graph.add_edge(idx,idx-1,1)
                  if [[i+1,i+1],[j,j+1]] not in walls_list:
                      edges_list.append((idx,idx+1,1))
                      #graph.add_edge(idx,idx+1,1)
                  if [[i,i+1],[j+1,j+1]] not in walls_list:
                      edges_list.append((idx,idx+self.maze_size,1))
                      #graph.add_edge(idx,idx+maze_size,1)
                  if [[i,i+1],[j,j]] not in walls_list:
                      edges_list.append((idx,idx-self.maze_size,1))
                      #graph.add_edge(idx,idx-maze_size,1)

          return edges_list, walls_list

    
    ############################ Q-LEARNING ########################################

    def q_learning(self):

        q_table = np.zeros((self.maze_size,self.maze_size,4), dtype=float)
        streak = 0
        reach = 0

        for e in tqdm(range(MAX_EPISODE)):


            random_reset = np.random.randint(self.maze_size,size=2)
            obv = self.env.env.reset(random_reset)
            self.env._elapsed_steps = 0

            state = tuple(obv)

            if e%1000==0:
                print("Episode #",e,"(",reach,")")

            for k in range(MAX_STEP):

                epsi = self.get_epsilon(e)
                action = self.select_action(state,q_table,epsi)
                new_s, reward, done, _ = self.env.step(action)
                new_s = tuple(new_s)
                self.update_q(q_table,action,state,new_s,reward,done)
                state = new_s

                if done :
                    break

                if RENDER:
                    self.env.render()

            if done and k <= MAX_STEP:
                reach += 1
                streak += 1
            else:
                streak = 0

            if streak > MIN_STREAK:
                print(MIN_STREAK,"episode under",MAX_STEP,"!!")
                break

            #time.sleep(0.1)

        return  q_table



    def update_q(self,q_table,action,state,new_state,reward,done):

        state = tuple(state)
        new_state = tuple(new_state)

        if done:
            td = reward - q_table[state+(action,)]
            #print("IN")
        else:
            td = reward + self.discount*np.max(q_table[new_state]) - q_table[state+(action,)]

        q_table[state+(action,)] += self.lr*td


    def get_epsilon(self,e):

        return max(self.epsilon,0.3 - e*self.epsilon/(MAX_EPISODE*0.60))

    def select_action(self,state,q,e):
        e = np.random.rand(1)[0]
        epsi = self.get_epsilon(e)
        if e < self.epsilon:
            action = self.env.action_space.sample()
        else:
            action = int(np.argmax(q[state]))
        return action



    ##################### BOLTZMANN NOISY RATIONAL #################################

    def boltz_rational_noisy(self,q_table,beta):
        # Tau : temperature coefficient
        # n : number of demonstrations generated from the same start

        dic_action = ['N','S','E','W']
        obv = self.env.env.reset([0,0])
        state = tuple(obv)
        a=[]

        self.env.render()
        done=0
        a.append([])

        while not(done):

            actions = q_table[state]
            b = max(actions)
            boltz_distribution = np.exp((actions-b)/beta)/np.sum(np.exp((actions-b)/beta))

            noisy_behaviour = np.random.choice(dic_action,p=boltz_distribution)

            new_state,reward,done,_ = self.env.step(noisy_behaviour)

            state=tuple(new_state)
            a.append(noisy_behaviour)

            if RENDER:
                self.env.render()
                time.sleep(RENDER_TIME)

        return a


    ################################################################################
    #########################  IRRATIONAL BIASES  ##################################
    ################################################################################



    #########################  BOLTZMANN RATIONAL ##################################

    def v_from_q(self,q):

        v = np.zeros((self.maze_size,self.maze_size))

        for i in range(self.maze_size):
            for j in range(self.maze_size):
                state = tuple([i,j])
                v[i,j] = np.max(q[state])

        v[tuple(self.env.observation_space.high)] = 1

        return v


    def value_iteration(self):

        # Regular Value iteration

        v_vector = np.zeros((self.maze_size,self.maze_size))

        end = self.env.observation_space.high
        #v_vector[tuple(end)] = 1

        self.env.reset()
        threshold = 1e-5
        err = 2
        start = time.time()

        while err > threshold:

            v_temp = np.copy(v_vector)
            err = 0

            for i in range(self.maze_size):
                for j in range(self.maze_size):

                    state = tuple([i,j])
                    lin_state = i*self.maze_size+j

                    

                    if state == tuple(end):
                        break

                    else:
                        v = v_temp[state]
                        x = []
                        optimal_action = self.optimal_policy[state]

                        for a in range(4):

                            y = 0

                            non_zero_new_state = np.where(self.transition_table[lin_state,:,a]!=0)[0]

                            if len(non_zero_new_state)==0:
                                print("Multiple new state")
                            
                            for k in non_zero_new_state:

                                new_state = tuple([k//self.maze_size,k%self.maze_size])

                                if self.reward_type=="env":
                                    if new_state == tuple(end):
                                        reward = 1
                                    else:
                                        reward = -1/(self.maze_size**2)
                                else:
                                    reward = self.reward_table[state+(a,)]

                                y+=self.transition_table[lin_state,k,a]*(reward+self.discount*v_temp[new_state])

                                

                            x.append(y)


                        v_vector[state] = np.max(np.array(x))
                        

                        err = max(err,abs(v-v_vector[tuple(state)]))
            #print(err)

        
        print("duration",(time.time()-start))
        print("VI done")

        return v_vector


    

    def boltz_rational(self,beta):


        v_vector = np.zeros((self.maze_size,self.maze_size))

        end = self.env.observation_space.high

        #v_vector[tuple(end)] = 5

        self.env.reset()
        threshold = 1e-5
        err = 2

        start = time.time()

        while err > threshold:

            v_temp = np.copy(v_vector)
            err = 0

            for i in range(self.maze_size):
                for j in range(self.maze_size):

                    state = tuple([i,j])
                    lin_state = i*self.maze_size+j

                    if state == tuple(end):
                        break

                    else:
                        v = v_temp[state]
                        x = []
                        optimal_action = self.optimal_policy[state]

                        for a in range(4):

                            y = 0


                            non_zero_new_state = np.where(self.transition_table[lin_state,:,a]!=0)[0]

                            for k in non_zero_new_state:

                                new_state = tuple([k//self.maze_size,k%self.maze_size])

                                if self.reward_type=="env":
                                    if new_state == tuple(end):
                                        reward = 1
                                    else:
                                        reward = -1/(self.maze_size**2)
                                else:
                                    reward = self.reward_table[state+(a,)]

                                y+=self.transition_table[lin_state,k,a]*(reward+self.discount*v_temp[new_state])


                            x.append(y)


                        x = np.array(x)
                        b = np.max(x)
                        v_vector[tuple(state)] = np.sum(x*np.exp(beta*(x-b)))/(np.sum(np.exp(beta*(x-b))))

        
                        err = max(err,abs(v-v_vector[tuple(state)]))

            #print(err)


        print("duration",(time.time()-start))
        print("VI Boltz done")

        return v_vector


    def illusion_of_control(self,n,beta):


        v_vector = np.zeros((self.maze_size,self.maze_size))

        end = self.env.observation_space.high

        self.env.reset()
        threshold = 1e-8
        err = 2
        start = time.time()

        while err > threshold:

            v_temp = np.copy(v_vector)
            err = 0

            for i in range(self.maze_size):
                for j in range(self.maze_size):

                    state = tuple([i,j])
                    lin_state = i*self.maze_size+j

                    if state == tuple(end):
                        break

                    else:
                        v = v_temp[state]
                        x = []
                        optimal_action = self.optimal_policy[state]

                        for a in range(4):

                            y = 0

                            non_zero_new_state = np.where(self.transition_table[lin_state,:,a]!=0)[0]
                            
                            for k in non_zero_new_state:

                                new_state = tuple([k//self.maze_size,k%self.maze_size])

                                if self.reward_type=="env":
                                    if new_state == tuple(end):
                                        reward = 1
                                    else:
                                        reward = -1/(self.maze_size**2)
                                else:
                                    reward = self.reward_table[state+(a,)]

                                y+=((self.transition_table[lin_state,k,a])**n)*(reward+self.discount*v_temp[new_state])


                            x.append(y)

                        x = np.array(x)
                        b = np.max(x)
                        v_vector[tuple(state)] = np.sum(x*np.exp(beta*(x-b)))/(np.sum(np.exp(beta*(x-b))))

                        err = max(err,abs(v-v_vector[tuple(state)]))


        
        print("duration",(time.time()-start))
        print("Illusion of Control done")

        return v_vector


    def optimism_pessimism(self,omega,beta):


        v_vector = np.zeros((self.maze_size,self.maze_size))

        end = self.env.observation_space.high
        #v_vector[tuple(end)] = 5

        self.env.reset()
        threshold = 1e-8
        err = 2
        start = time.time()

        while err > threshold:

            v_temp = np.copy(v_vector)
            err = 0

            for i in range(self.maze_size):
                for j in range(self.maze_size):

                    state = tuple([i,j])
                    lin_state = i*self.maze_size+j

                    if state == tuple(end):
                        break

                    else:
                        v = v_temp[state]
                        x = []
                        optimal_action = self.optimal_policy[state]

                        for a in range(4):

                            y = 0


                            non_zero_new_state = np.where(self.transition_table[lin_state,:,a]!=0)[0]
                            
                            for k in non_zero_new_state:

                                new_state = tuple([k//self.maze_size,k%self.maze_size])

                                if self.reward_type=="env":
                                    if new_state == tuple(end):
                                        reward = 1
                                    else:
                                        reward = -1/(self.maze_size**2)
                                else:
                                    reward = self.reward_table[state+(a,)]

                                modified_transition_matrix = self.transition_table[lin_state,k,a]*np.exp(omega*(reward+self.discount*v_temp[state]))

                                y+= modified_transition_matrix*(reward+self.discount*v_temp[new_state])


                            x.append(y)

                        x = np.array(x)
                        b = np.max(x)
                        v_vector[tuple(state)] = np.sum(x*np.exp(beta*(x-b)))/(np.sum(np.exp(beta*(x-b))))

                        err = max(err,abs(v-v_vector[tuple(state)]))


        
        print("duration",(time.time()-start))
        print("Optimism/Pessimism done")

        return v_vector


    ####################### PROSPECT BIAS (loss aversion + scope insensitivity) ############################

    def prospect_bias(self,c,beta):
        #v_vector = np.random.rand(env.size[1]*env.size[0])
        v_vector = np.zeros((self.maze_size,self.maze_size))
        end = self.env.observation_space.high
        #v_vector[tuple(end)] = 5

        self.env.reset()
        self.env.render()

        threshold = 1e-3
        err=2

        start = time.time()

        while err>threshold:

            v_temp = np.copy(v_vector)
            err=0

            for i in range(self.maze_size):
                for j in range(self.maze_size):

                    state = tuple([i,j])
                    lin_state = i*self.maze_size+j

                    if state==tuple(end):
                        pass
                    else:
                        self.env.env.reset(np.array(state))
                        v = v_temp[state]
                        x = []
                        optimal_action = self.optimal_policy[state]

                        for a in range(4):


                            y = 0
                            # new_state = self.new_state_table[state + (a,)]
                            # reward = self.reward_table[state+(a,)]


                            non_zero_new_state = np.where(self.transition_table[lin_state,:,a]!=0)

                            for k in non_zero_new_state:

                                new_state = tuple([k//self.maze_size,k%self.maze_size])


                                if self.reward_type=="env":
                                    if new_state == tuple(end):
                                        reward = 1
                                    else:
                                        reward = -1/(self.maze_size**2)
                                else:
                                    reward = self.reward_table[state+(a,)]

                                if reward>0:
                                    reward = np.log(1+reward)
                                elif reward==0:
                                    reward = 0
                                else:
                                    reward = -c*np.log(1+abs(reward))


                                y+=self.transition_table[lin_state,k,a]*(reward+self.discount*v_temp[new_state])

                            x.append(y)

                        x = np.array(x,dtype=float)
                        b = np.max(x)
                        v_vector[tuple(state)] = np.sum(x*np.exp(beta*(x-b)))/(np.sum(np.exp(beta*(x-b))))


                        err = max(err,abs(v-v_vector[tuple(state)]))


            #print(err)

        print("duration",time.time()-start)
        print("Prospect bias done")
        return v_vector



    def extremal(self,alpha,beta):

        # Regular Value iteration

        v_vector = np.zeros((self.maze_size,self.maze_size))

        end = self.env.observation_space.high
        #v_vector[tuple(end)] = 5

        self.env.reset()
        threshold = 1e-3
        err = 2
        start = time.time()

        while err > threshold:

            v_temp = np.copy(v_vector)
            err = 0

            for i in range(self.maze_size):
                for j in range(self.maze_size):

                    state = tuple([i,j])
                    lin_state = i*self.maze_size+j

                    if state == tuple(end):
                        break

                    else:
                        v = v_temp[state]
                        x = []
                        optimal_action = self.optimal_policy[state]

                        for a in range(4):

                            y = 0


                            non_zero_new_state = np.where(self.transition_table[lin_state,:,a]!=0)[0]
                            
                            for k in non_zero_new_state:

                                new_state = tuple([k//self.maze_size,k%self.maze_size])

                                if self.reward_type=="env":
                                    if new_state == tuple(end):
                                        reward = 1
                                    else:
                                        reward = -1/(self.maze_size**2)
                                else:
                                    reward = self.reward_table[state+(a,)]

  
                                expected_reward = max(reward,(1-alpha)*reward+alpha*v_temp[new_state])

                                y+=self.transition_table[lin_state,k,a]*expected_reward


                            x.append(y)

                        x = np.array(x)
                        b = np.max(x)
                        v_vector[tuple(state)] = np.sum(x*np.exp(beta*(x-b)))/(np.sum(np.exp(beta*(x-b))))

                        err = max(err,abs(v-v_vector[tuple(state)]))


            #print(err)

        print("duration",(time.time()-start))
        print("Extremal done")

        return v_vector


    ######################### MYOPIC DISCOUNT ##########################################################

    def myopic_discount(self,disc,beta):


        #v_vector = np.random.rand(self.maze_size,self.maze_size)
        v_vector = np.zeros((self.maze_size,self.maze_size),dtype=float)
        end = self.env.observation_space.high
        #v_vector[tuple(end)] = 5

        self.env.reset()

        err=2
        threshold = 1e-5

        start = time.time()

        while err > threshold:

            
            err = 0
            v_temp = np.copy(v_vector)
            #print(v_vector)

            for i in range(self.maze_size):
                for j in range(self.maze_size):

                    

                    state = tuple([i,j])
                    lin_state = i*self.maze_size+j
                    
                    if (state==tuple([self.maze_size-1,self.maze_size-1])):
                        break

                    self.env.env.reset(np.array(state))
                    v = v_temp[state]
                    x = []

                    optimal_action = self.optimal_policy[state]


                    for a in range(4):

                        y = 0


                        non_zero_new_state = np.where(self.transition_table[lin_state,:,a]!=0)
                        for k in non_zero_new_state:

                            new_state = tuple([k//self.maze_size,k%self.maze_size])

                            if self.reward_type=="env":
                                if new_state == tuple(end):
                                    reward = 1
                                else:
                                    reward = -1/(self.maze_size**2)
                            else:
                                reward = self.reward_table[state+(a,)]

                            y+=self.transition_table[lin_state,k,a]*(reward+disc*v_temp[new_state])
                        
                        x.append(y)

 
                    x = np.array(x,dtype=float)
                    b = np.max(x)
                    v_vector[tuple(state)] = np.sum(x*np.exp(beta*(x-b)))/(np.sum(np.exp(beta*(x-b))))

                    err = max(err,abs(v-v_vector[tuple(state)]))
            #print(err)

        #end = self.env.observation_space.high
        #v_vector[tuple(end)] = 1
        print("duration ",time.time()-start)
        print("Myopic discount done")
        return v_vector


    
######################### MYOPIC VALUE ITERATION ##########################################################

    def myopic_value_iteration(self,h,beta):


        v_vector = np.zeros((self.maze_size,self.maze_size),dtype=float)
        end = self.env.observation_space.high
        #v_vector[tuple(end)] = 5

        self.env.reset()

        err=2
        threshold = 1e-8

        it = 0

        start = time.time()

        while err > threshold and it < h:

            
            err = 0
            v_temp = np.copy(v_vector)
            #print(v_vector)

            for i in range(self.maze_size):
                for j in range(self.maze_size):

                    

                    state = tuple([i,j])
                    lin_state = i*self.maze_size+j
                    
                    if (state==tuple([self.maze_size-1,self.maze_size-1])):
                        break

                    self.env.env.reset(np.array(state))
                    v = v_temp[state]
                    x = []

                    optimal_action = self.optimal_policy[state]


                    for a in range(4):

                        y = 0
                        non_zero_new_state = np.where(self.transition_table[lin_state,:,a]!=0)

                        for k in non_zero_new_state:

                            new_state = tuple([k//self.maze_size,k%self.maze_size])

                            if self.reward_type=="env":
                                if new_state == tuple(end):
                                    reward = 1
                                else:
                                    reward = -1/(self.maze_size**2)
                            else:
                                reward = self.reward_table[state+(a,)]

                            y+=self.transition_table[lin_state,k,a]*(reward+self.discount*v_temp[new_state])
                        
                        x.append(y)

 
                    x = np.array(x,dtype=float)
                    b = np.max(x)
                    v_vector[tuple(state)] = np.sum(x*np.exp(beta*(x-b)))/(np.sum(np.exp(beta*(x-b))))

                    err = max(err,abs(v-v_vector[tuple(state)]))
                    
            it+=1

        print("duration",(time.time()-start))
        print("Myopic value iteration done")
        return v_vector



######################### MYOPIC VALUE ITERATION ##########################################################

    def hyperbolic_discount(self,k_,beta):


        v_vector = np.zeros((self.maze_size,self.maze_size),dtype=float)
        end = self.env.observation_space.high
        #v_vector[tuple(end)] = 10

        self.env.reset()

        err=2
        threshold = 1e-8

        start = time.time()

        while err > threshold:

            
            err = 0
            v_temp = np.copy(v_vector)
            #print(v_vector)

            for i in range(self.maze_size):
                for j in range(self.maze_size):

                    

                    state = tuple([i,j])
                    lin_state = i*self.maze_size+j
                    
                    if (state==tuple([self.maze_size-1,self.maze_size-1])):
                        break

                    self.env.env.reset(np.array(state))
                    v = v_temp[state]
                    x = []

                    optimal_action = self.optimal_policy[state]


                    for a in range(4):

                        y = 0
                        new_state = self.new_state_table[state+(a,)]

                        if a!=optimal_action:
                            reward = -1
                        else:
                            reward = 1

                        non_zero_new_state = np.where(self.transition_table[lin_state,:,a]!=0)

                        for k in non_zero_new_state:

                            new_state = tuple([k//self.maze_size,k%self.maze_size])

                            if self.reward_type=="env":
                                if new_state == tuple(end):
                                    reward = 1
                                else:
                                    reward = -1/(self.maze_size**2)
                            else:
                                reward = self.reward_table[state+(a,)]

                            y+=self.transition_table[lin_state,k,a]*(reward+self.discount*v_temp[new_state])/(1+k_*v_temp[new_state])
                        
                        x.append(y)

 
                    x = np.array(x,dtype=float)
                    b = np.max(x)
                    v_vector[tuple(state)] = np.sum(x*np.exp(beta*(x-b)))/(np.sum(np.exp(beta*(x-b))))

                    err = max(err,abs(v-v_vector[tuple(state)]))

            print(err)

        print("duration",(time.time()-start))
        print("Hyperbolic discount done")
        return v_vector



####################### LOCAL UNCERTAINTY ################################################################

    def local_disount(self,uncertain_state,radius,beta):


        # uncertain_state = tuple(np.random.randint(0,self.maze_size,size=2))
        # radius = np.random.randint(0,6)

        v_vector = np.zeros((self.maze_size,self.maze_size),dtype=float)
        end = self.env.observation_space.high
        #v_vector[tuple(end)] = 10

        self.env.reset()

        err=2
        threshold = 1e-5


        while err > threshold:

            

            err = 0
            v_temp = np.copy(v_vector)
            #print(v_vector)

            for i in range(self.maze_size):
                for j in range(self.maze_size):

                    state = tuple([i,j])
                    lin_state = i*self.maze_size+j
                    
                    if (state==tuple([self.maze_size-1,self.maze_size-1])):
                        break

                    in_uncertain_area = False

                    distance_to_uncertain = np.sqrt((i-uncertain_state[0])**2+(j-uncertain_state[1])**2)

                    if distance_to_uncertain < radius:
                        in_uncertain_area = True

                        #print("In uncertain area",state)


                    self.env.env.reset(np.array(state))
                    v = v_temp[state]
                    x = []

                    optimal_action = self.optimal_policy[state]


                    for a in range(4):

                        y = 0
                        
                        
                        if not(in_uncertain_area):
                            disc=self.discount
                        else:
                            disc=self.discount/2


                        non_zero_new_state = np.where(self.transition_table[lin_state,:,a]!=0)
                        for k in non_zero_new_state:

                            new_state = tuple([k//self.maze_size,k%self.maze_size])

                            reward = self.reward_table[state+(a,)]

                            y+=self.transition_table[lin_state,k,a]*(reward+disc*v_vector[new_state])

                        x.append(y)

 
                    x = np.array(x,dtype=float)
                    b = np.max(x)
                    v_vector[tuple(state)] = np.sum(x*np.exp(beta*(x-b)))/(np.sum(np.exp(beta*(x-b))))

                    err = max(err,abs(v-v_vector[tuple(state)]))

            #print(err)

        print("Local uncertainty done")
        return v_vector


    def random_boltz_rational(self,beta_max,beta_min):


        v_vector = np.zeros((self.maze_size,self.maze_size))

        end = self.env.observation_space.high

        #v_vector[tuple(end)] = 5

        self.env.reset()
        threshold = 1e-5
        err = 2

        start = time.time()

        beta = beta_max*np.ones((self.maze_size,self.maze_size))
        p=0.2

        for i in range(self.maze_size):
            for j in range(self.maze_size):
                if np.random.rand() < p:
                    beta[i,j] = beta_min


        while err > threshold:
            v_temp = np.copy(v_vector)
            err = 0

            for i in range(self.maze_size):
                for j in range(self.maze_size):

                    state = tuple([i,j])
                    lin_state = i*self.maze_size+j

                    if state == tuple(end):
                        break

                    else:
                        v = v_temp[state]
                        x = []
                        optimal_action = self.optimal_policy[state]

                        for a in range(4):

                            y = 0


                            non_zero_new_state = np.where(self.transition_table[lin_state,:,a]!=0)[0]

                            for k in non_zero_new_state:

                                new_state = tuple([k//self.maze_size,k%self.maze_size])

                                if self.reward_type=="env":
                                    if new_state == tuple(end):
                                        reward = 1
                                    else:
                                        reward = -1/(self.maze_size**2)
                                else:
                                    reward = self.reward_table[state+(a,)]

                                y+=self.transition_table[lin_state,k,a]*(reward+self.discount*v_temp[new_state])


                            x.append(y)


                        x = np.array(x)
                        b = np.max(x)

                        v_vector[tuple(state)] = np.sum(x*np.exp(beta[state]*(x-b)))/(np.sum(np.exp(beta[state]*(x-b))))

        
                        err = max(err,abs(v-v_vector[tuple(state)]))

            #print(err)


        print("duration",(time.time()-start))
        print("Random boltzmann done")

        return v_vector



    def local_uncertainty(self,table):


        v_vector = np.zeros((self.maze_size,self.maze_size))

        end = self.env.observation_space.high

        #v_vector[tuple(end)] = 5

        self.env.reset()
        threshold = 1e-5
        err = 2

        start = time.time()

        beta = self.get_entropy_map_q(table)


        while err > threshold:
            v_temp = np.copy(v_vector)
            err = 0

            for i in range(self.maze_size):
                for j in range(self.maze_size):

                    state = tuple([i,j])
                    lin_state = i*self.maze_size+j

                    if state == tuple(end):
                        break

                    else:
                        v = v_temp[state]
                        x = []
                        optimal_action = self.optimal_policy[state]

                        for a in range(4):

                            y = 0


                            non_zero_new_state = np.where(self.transition_table[lin_state,:,a]!=0)[0]

                            for k in non_zero_new_state:

                                new_state = tuple([k//self.maze_size,k%self.maze_size])

                                if self.reward_type=="env":
                                    if new_state == tuple(end):
                                        reward = 1
                                    else:
                                        reward = -1/(self.maze_size**2)
                                else:
                                    reward = self.reward_table[state+(a,)]

                                y+=self.transition_table[lin_state,k,a]*(reward+self.discount*v_temp[new_state])


                            x.append(y)


                        x = np.array(x)
                        b = np.max(x)

                        v_vector[tuple(state)] = np.sum(x*np.exp(beta[state]*(x-b)))/(np.sum(np.exp(beta[state]*(x-b))))


                        err = max(err,abs(v-v_vector[tuple(state)]))

            #print(err)


        print("duration",(time.time()-start))
        print("Random boltzmann done")

        return v_vector

    """
    def value_iteration_dynamic_boltzmann(self,beta):

        v_vector = np.zeros((self.maze_size,self.maze_size))
        #v_vector = np.random.rand(self.maze_size,self.maze_size)
        q_table = np.zeros((self.maze_size,self.maze_size,4), dtype=float)

        end = self.env.observation_space.high

        self.env.reset()
        self.env.render()
        threshold = 1e-5
        err=2

        it=0

        while err>threshold:

            v_temp = np.copy(v_vector)
            err=0

            for i in range(self.maze_size):
                for j in range(self.maze_size):

                    state = tuple([i,j])

                    if state==tuple(end):
                        v_vector[state] = 1
                        break

                    self.env.env.reset(state)

                    v = v_temp[tuple(state)]

                    for action in range(4):
                        new_state = self.new_state_table[tuple(state) + (action,)]
                        reward = self.reward_table[tuple(state)+(action,)]
                        q_table[state+(action,)] = reward + self.discount*v_temp[new_state]

                    x = np.array(q_table[state])
                    b = np.max(x)
                    v_vector[state] = np.sum(x*np.exp((x-b)/beta))/np.sum(np.exp((x-b)/beta))
                    
                    err = max(err,abs(v-v_vector[tuple(state)]))

                    #print(x,v_vector[state])
                    #time.sleep(2)

            it+=1

            if it%1000==0:
                print("Iteration",it," err =",err)

        print("VI Boltz done")
        
        return v_vector, q_table

    def select_action_from_v(self,state,v):

        v_choice = []
        self.env.env.reset(np.array(state))


        for a in range(4):

            new_state = self.new_state_table[tuple(state) + (a,)]
            reward = self.reward_table[tuple(state)+(a,)]
            v_choice.append(reward + self.discount*v[tuple(new_state)])


        #print(v_choice)

        # v_choice = np.array(v_choice)
        # b = np.max(v_choice)
        # x = np.exp((v_choice-b))/np.sum(np.exp((v_choice-b)))
        # #print(x)
        # action = np.random.choice([0,1,2,3],p=x)

        action = np.argmax(v_choice)

        return action

    def select_action_from_v_human(self,state,v):

        v_choice = []
        self.env.env.reset(np.array(state))

        optimal_action = self.optimal_policy[state]


        for a in range(4):

            new_state = self.new_state_table[state+(a,)]

            if a!=optimal_action:
                reward = -1
            else:
                reward = self.reward_table[state+(a,)]

            
            v_choices.append(reward + disc*v_temp[new_state])
       

        #print(v_choice)

        # v_choice = np.array(v_choice)
        # b = np.max(v_choice)
        # x = np.exp((v_choice-b))/np.sum(np.exp((v_choice-b)))
        # #print(x)
        # action = np.random.choice([0,1,2,3],p=x)

        action = np.argmax(v_choice)

        return action

    def boltz_rational(self,beta):

        v_vector = np.zeros((self.maze_size,self.maze_size))
        #v_vector = np.random.rand(self.maze_size,self.maze_size)

        end = self.env.observation_space.high

        self.env.reset()
        self.env.render()
        threshold = 1e-5
        err=2

        it=0
        start = time.time()

        while err>threshold and it<2000:

            v_temp = np.copy(v_vector)
            err=0

            for i in range(self.maze_size):
                for j in range(self.maze_size):

                    state = tuple([i,j])

                    if state==tuple(end):
                        break

                    self.env.env.reset(np.array(state))

                    v = v_temp[tuple(state)]
                    x = []
                    for a in range(4):

                        new_state = self.new_state_table[tuple(state) + (a,)]
                        optimal_action = self.optimal_policy[state]


                        if a!=optimal_action:
                            reward = -1
                        else:
                            reward = 1 #self.reward_table[state+(a,)]

                        x.append(reward + self.discount*v_vector[tuple(new_state)])

                    x = np.array(x)
                    b = np.max(x)
                    v_vector[tuple(state)] = np.sum(x*np.exp((x-b)*beta))/np.sum(np.exp((x-b)*beta))

                    
                    err = max(err,abs(v-v_vector[tuple(state)]))

            it+=1

            if it%1000==0:
                print("Iteration",it," err =",err)

        print("duration",time.time()-start)
        print("VI Boltz done")
        
        v_vector[tuple(end)] = 1

        return v_vector
    """

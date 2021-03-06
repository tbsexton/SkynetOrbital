__author__ = 'Thurston Sexton, Max Yi Ren'
# This file defines the underlying physics

import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import odeint

class Simulation:

    def __init__(self, design):
        # self.mf0 = input('How much fuel (kg) to bring along (can change later)?')
        # print 'setting burn scheme (call change_design() to change)'
        # self.burn = b  # a piecewise func determining throttle @ some time t
        self.design = design

        # design parameters
        self.G = 6.672e-11
        # self.M = 5.2915793e22  # Mass of Kerbin
        self.M = 5.97219e24 # Mass of Earth
        # self.R = 6e5  # Radius of Kerbin
        self.R= 6.378e6  # mean Radius of Earth
        self.F = 189e5  # Thrust of the Engine, in N
        self.m0 = 13e4  # Weight of empty rocket, in kg
        self.mf = self.design.mf0  # initial fuel mass
        # self.V0 = 6.1e2  # initial speed
        self.V0 = 50
        self.gam0 = np.pi/2.-0.1  # initial angle
        self.r_0 = self.R+2.86875e2  # initial height
        # self.phi0 = -1.5  # ???
        self.time_interval = 1.0  # second
        self.Isp = 304  # sec ???

        self.state_space = np.array([[0, 11.2e3],
                                     [-np.pi/2., np.pi/2],
                                     [self.R, 42.2e6],
                                     [0., self.design.mf0],
                                     [0]])  # speed, gamma, height, fuel mass, phi
        self.action_space = np.array([[0, 13e3]])  # burn rate, needs to be discrete for now
        self.initial_state = np.array([self.V0, self.gam0, self.r_0, self.design.mf0, 0])
        self.current_state = self.initial_state
        self.current_altitude = self.current_state[2]
        self.trajectory = np.empty((0, self.initial_state.size))
        self.action = 0

    # change design
    def change_design(self, design):
        self.design = design
        # self.design.burn = design.b  # a piecewise func determining throttle @ some time t

    # check if should stop
    def running(self, state):
        # if fuel and no crash, continue
        if state[2] >= self.current_altitude:
            return True
        else:
            # set to initial condition
            self.current_state = self.initial_state
            self.current_altitude = self.current_state[2]
            return False


    # thrust:weight ratio, based on S-IC
    def T_w(self, g):
            if self.mf > self.action*self.time_interval: # if enough fuel to burn
                m_t = self.m0 + self.mf
                return self.action*g*self.Isp/(m_t*g)  # ???
            else:
                return 0.

    # gravity turn
    def g(self, y, t):
        V_i = y[0]
        gam_i = y[1]
        r_i = y[2]
        # phi_i = y[3]

        # assert r_i >= self.R, 'You have crashed'
        g = self.G*self.M/r_i**2
        f_v = -g*(np.sin(gam_i) - self.T_w(g))
        f_gam=(V_i/r_i - g/V_i)*np.cos(gam_i) # + drag/ ortho. term
        f_r = V_i*np.sin(gam_i)
        f_mf = -self.action
        f_phi = (V_i/r_i)*np.cos(gam_i)
        # return [f_v, f_gam, f_r, f_phi]
        return f_v, f_gam, f_r, f_mf, f_phi

    # simulate one step (self.time_interval)
    def step(self, state, action):
        self.current_state = state
        self.action = action
        self.current_altitude = state[2]

        soln = odeint(self.g, self.current_state, np.linspace(0, self.time_interval, 10))
        self.trajectory = np.concatenate((self.trajectory, soln), axis=0)
        new_state = soln[-1, :]

        v = new_state[0]
        gamma = new_state[1]
        r = new_state[2]
        mf = new_state[3]
        # reward = -(gamma/np.pi)**2 - (mf/self.design.mf0)**2 - (1 - self.G*self.M/r/v**2)**2

        reward = -1000.0*(gamma/np.pi*2)**2 - (1 - self.G*self.M/r/(v**2))**2
                 # *(1.-mf/self.design.mf0)\
                 # + ((gamma/np.pi*2)**2 < 0.01)*((1 - self.G*self.M/r/v**2)**2 < 0.01)*100
        # if ((gamma/np.pi*2)**2 < 0.01)*((1 - self.G*self.M/r/v**2)**2 < 0.01):
        #     wait = 1
        return new_state, reward

    # TODO: animation?
    def plot(self, soln):
        fig, ax = plt.subplots(nrows=1, ncols=soln.shape[1], figsize=(12, 4))
        for i, n in enumerate(ax.flatten()):
            n.plot(np.linspace(1, soln.shape[0], soln.shape[0]), soln[:, i])
        # ax.flatten()[-1].plot(t, soln[:, 2]-self.R)

        fig1 = plt.figure(figsize=(10,10))
        ax1 = plt.subplot(111, polar=True)
        ax1.plot(soln[:,4], soln[:,2], linewidth=2)
        ax1.plot(np.linspace(0,2*np.pi, 10000),self.R*np.ones(10000), linewidth=3)
        ax1.fill_betweenx(self.R*np.ones(10000), np.linspace(0,2*np.pi, 10000), color='g')
        ax1.set_ylim(1e4,1e6)

        circle1 = plt.Circle((0,0),self.R,color='y')

        x = np.multiply(soln[:,2], np.cos(soln[:, 4]))
        y = np.multiply(soln[:,2], np.sin(soln[:, 4]))

        fig2 = plt.figure(figsize=(10,10))
        ax2 = plt.subplot(111, polar=False)
        ax2.plot(x, y)
        # fig2.xlim(0e5,2e5)
        # fig2.ylim(-7.5e5, -5.5e5)
        fig2 = plt.gcf()
        fig2.set_size_inches(8, 8)
        fig2.gca().add_artist(circle1)
        plt.show()

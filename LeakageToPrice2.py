#Heston model simulation using the continuous Euler–Maruyama approximation
import incidents.csv
import numpy as np
import matplotlib.pyplot as plt

def OIL_SPILT(day):
    if day == 20:
        return True
    else:
        return False

def generate_heston_paths(S, T, r, kappa, theta, v_0, rho, xi, 
                          days, Npaths, return_vol=False):
    Spill_Day = 9999999999999

    dt = T/days
    size = (Npaths, days)
    prices = np.zeros(size)
    sigs = np.zeros(size)
    S_t = S
    v_t = v_0
    for t in range(days):
        WT = np.random.multivariate_normal(np.array([0,0]), 
                                           cov = np.array([[1,rho],
                                                          [rho,1]]), 
                                           size=Npaths) * np.sqrt(dt) 
        S_t = S_t*(np.exp( (r- 0.5*v_t)*dt+ np.sqrt(v_t) *WT[:,0] ) ) 
        v_t = np.abs(v_t + kappa*(theta-v_t)*dt + xi*np.sqrt(v_t)*WT[:,1])

        if OIL_SPILT(t) == True:
            print(t)
            Spill_Day = t
            theta *= 1.5
        
        if Spill_Day < t and theta > 0.15:
            theta /= 0.8

        prices[:, t] = S_t
        sigs[:, t] = v_t
    
    if return_vol:
        return prices, sigs
    
    return prices

S0 = 56  #Start Price
T = 2/12
r = 1
kappa = 1.2  #Calibrate [0.1 to 2]
theta = 0.15  #Calibrate [0.05 to 0.3]
v_0 = 0.5
Rho = 0.25  #Correlations between stock price and volatility [-0.9 to 0.9]
xi = 0.1  #Variance of volatility [0.1 to 1]
Days = 60
NPaths = 1

data = generate_heston_paths(S0, T, r, kappa, theta, v_0, Rho, xi, Days, NPaths)
print(data)
plt.plot(data[0])
plt.show()
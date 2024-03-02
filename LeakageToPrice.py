# Oil Price FLuctuation Model
import math
import numpy as np
import random

def Wiener(N):
    return np.random.normal(scale=N)

def OIL_SPILT(day):
    if day == 20:
        return True
    else:
        return False

#Configure General Values
Average_Oil_Price = 79.97  #Mu
Stand_Dev = 1e-9#Sigma
Reversion_Rate = 0.00625 #Beta
Longrun_Var = 25e-10 #Theta
Spill_Day = 0
Multiplier = 1
Decrementer = 0

#Configure Stochastic Walk Values
TIME_FRAME = 60  #In Days
DELTA_T = 1  #Necessary for random walk
Oil_Price = []
PricePerDay = Average_Oil_Price
Volatility = Stand_Dev

for day in range (TIME_FRAME):
    print(Volatility)
    PricePerDay = PricePerDay * (1 + Average_Oil_Price*DELTA_T + random.randint(0,1)*math.sqrt(abs(Volatility))*Wiener(day))
    Volatility = Volatility + Reversion_Rate*(Longrun_Var-Volatility)*TIME_FRAME + Stand_Dev*math.sqrt(abs(Volatility))*Wiener(day)# - Decrementer*(day-Spill_Day)
    

    """if OIL_SPILT(day) == True:
        Spill_Day = day
        Volatility *= Multiplier
        PricePerDay = PricePerDay * (1 + Average_Oil_Price*DELTA_T + math.sqrt(Volatility)*Wiener(TIME_FRAME))
        #Decrementer = 0.5"""

    Oil_Price.append(PricePerDay)

print(Oil_Price)
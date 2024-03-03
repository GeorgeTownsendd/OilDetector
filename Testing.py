import pandas as pd
import matplotlib.pyplot as plt
import LeakageToPrice2
import TrainParams

df_incidents = pd.read_csv('incidents.csv')

df_incidents['open_date'] = pd.to_datetime(df_incidents.open_date)
df = pd.read_csv('prices.csv')
df['Date'] = pd.to_datetime(df.Date)

S0 = df.iloc[0]['Value']  #Start Price
T = 1/12
r = 1
Days = 60
NPaths = 1
#kappa = 1.2  #Calibrate [0.1 to 2]
#theta = 0.15  #Calibrate [0.05 to 0.3]
#v_0 = 0.5
#Rho = 0.25  #Correlations between stock price and volatility [-0.9 to 0.9]
#xi = 0.1  #Variance of volatility [0.1 to 1]
observed_data = pd.read_csv('prices.csv')
observed_data['Date'] = pd.to_datetime(observed_data.Date)
observed_data = observed_data[0:30]

optimal_kappa, optimal_theta, optimal_v_0, optimal_Rho, optimal_xi = TrainParams.main(S0, T, r, Days, NPaths, observed_data)

SimulatedData = LeakageToPrice2.generate_heston_paths(df.iloc[30]["Value"], T, r, optimal_kappa, optimal_theta, optimal_v_0, optimal_Rho, optimal_xi, Days//2, NPaths)

index = 30
date = "2012-05-11"
plt.plot(df.iloc[index-30:index+1,:]['Date'],df.iloc[index-30:index+1,:]['Value'])
plt.scatter(df.iloc[index:index+1,:]['Date'], df.iloc[index:index+1,:]['Value'], color='red')
plt.plot(df.iloc[index:index+30,:]['Date'],SimulatedData[0])
plt.show()
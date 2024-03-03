import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import LeakageToPrice
import CalibrateParams

def GenerateData(date):
    date = pd.to_datetime('2012-05-11')
    index = 30

    #df_incidents = pd.read_csv('incidents.csv')
    #df_incidents['open_date'] = pd.to_datetime(df_incidents.open_date)
    df = pd.read_csv('FinancialData/prices.csv')
    df['Date'] = pd.to_datetime(df.Date)
    observed_data = pd.read_csv('FinancialData/prices.csv')
    observed_data['Date'] = pd.to_datetime(observed_data['Date'])
    ovserved_data = observed_data.sort_values(by='Date', ascending=True)

    idx = observed_data.index[observed_data['Date'] == date].tolist()[0]
    start = max(0, idx - 30)
    end = idx + 31
    filtered_data = observed_data.iloc[start:end]

    #filtered_data = observed_data[(observed_data['Date'] > (date - pd.DateOffset(days=30))) & (observed_data['Date'] < date + pd.DateOffset(days=30))]
    observed_data = filtered_data.head(60)

    IncidentPointDate = observed_data[observed_data['Date'] == date]['Date']
    IncidentPointValue = observed_data[observed_data['Date'] == date]['Value']

    train_data = observed_data.head(30)
    test_data = observed_data.tail(30)

    S0 = observed_data.iloc[0]['Value']  #Start Price
    T = 1/12
    r = 1
    Days = 60
    NPaths = 1

    optimal_kappa, optimal_theta, optimal_v_0, optimal_Rho, optimal_xi = CalibrateParams.main(S0, T, r, Days, NPaths, train_data)

    SimulatedData = LeakageToPrice.generate_heston_paths(IncidentPointValue, T, r, optimal_kappa, optimal_theta, optimal_v_0, optimal_Rho, optimal_xi, Days//2, NPaths)

    plt.plot(observed_data.iloc[0:index+1,:]['Date'],observed_data.iloc[0:index+1,:]['Value'])
    plt.scatter(IncidentPointDate, IncidentPointValue, color='red')
    plt.plot(observed_data.iloc[index:]['Date'],SimulatedData[0])
    plt.show()

    SimulatedData = SimulatedData.flatten()
    IndexOfMaxVal = np.argmax(SimulatedData) + 30
    return observed_data.iloc[IndexOfMaxVal]['Date']

print(GenerateData('2012-05-11'))
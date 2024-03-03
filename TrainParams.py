#Levenberg-Marquardt Algorithm to train the parameters of the Heston model
import numpy as np
import pandas as pd
import LeakageToPrice2
from scipy.optimize import least_squares

def calculate_residuals(simulated_data, observed_data):
    # Ensure that simulated_data and observed_data are numpy arrays
    simulated_data = np.array(simulated_data).flatten()
    observed_data = np.array(observed_data).flatten()
    residuals = simulated_data - observed_data
    return residuals

# Define a function that takes in parameters and returns the residuals
def residuals(params, S0, T, r, Days, NPaths, observed_data):
    kappa, theta, v_0, Rho, xi = params
    Days //= 2

    simulated_data = LeakageToPrice2.generate_heston_paths(S0, T, r, kappa, theta, v_0, Rho, xi, Days, NPaths)
    simulated_data = np.array(simulated_data[0]).flatten()
    observed_data = observed_data['Value']
    # Calculate the residuals between the simulated data and the observed data
    # This will depend on the structure of your data and the specific problem you're solving
    residuals = calculate_residuals(simulated_data, observed_data)
    return residuals


def main(S0, T, r, Days, NPaths, observed_data):
    initial_guesses = np.array([1.2, 0.15, 0.5, 0.25, 0.1])
    additional_args = (S0, T, r, Days, NPaths, observed_data)

    # Find the parameters that minimize the sum of the squares of the residuals
    result = least_squares(residuals, initial_guesses, args=additional_args)

    #optimal_kappa, optimal_theta, optimal_v_0, optimal_Rho, optimal_xi = result.x
    return result.x

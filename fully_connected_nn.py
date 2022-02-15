# -*- coding: utf-8 -*-
"""
Created on Thu Apr 29 20:08:01 2021

@author: laptop
"""

import numpy as np

def sigmoid(Z):
    return 1/(1+np.exp(-Z))

def relu(Z):
    return np.maximum(0,Z)

def sigmoid_backward(dA, Z):
    sig = sigmoid(Z)
    return dA * sig * (1 - sig)

def relu_backward(dA, Z):
    dZ = np.array(dA, copy = True)
    dZ[Z <= 0] = 0
    return dZ

def init_layers(nn_architecture, seed = 99):
    np.random.seed(seed)
    number_of_layers = len(nn_architecture)
    params_values = {}
    
    for idx, layer in enumerate(nn_architecture):
        layer_idx = idx + 1
        
        layer_input_size = layer["input_dim"]
        layer_output_size = layer["output_dim"]
        
        params_values['W' + str(layer_idx)] = np.random.randn(
            layer_output_size, layer_input_size) * 0.1
        params_values['b' + str(layer_idx)] = np.random.randn(
            layer_output_size, 1) * 0.1
        
    return params_values


def single_layer_forward_propagation(A_prev, W_curr, b_curr, activation="relu"):
    Z_curr = np.dot(W_curr, A_prev) + b_curr
    
    if activation == "relu":
        activation_func = relu
    elif activation == "sigmoid":
        activation_func = sigmoid
    else:
        raise Exception('Non-supported activation function')
        
    return activation_func(Z_curr), Z_curr


def full_forward_propagation(X, params_values, nn_architecture):
    memory = {}
    A_curr = X
    
    for idx, layer in enumerate(nn_architecture):
        layer_idx = idx + 1
        A_prev = A_curr
        
        activ_function_curr = layer["activation"]
        W_curr = params_values["W" + str(layer_idx)]
        b_curr = params_values["b" + str(layer_idx)]
        A_curr, Z_curr = single_layer_forward_propagation(A_prev, W_curr, b_curr, activ_function_curr)
        
        memory["A" + str(idx)] = A_prev
        memory["Z" + str(layer_idx)] = Z_curr
       
    return  A_curr, memory, W_curr



def get_cost_value(Y_hat, Y, eps = 0.001):
    # number of examples
    m = Y_hat.shape[1]
    cost = -1 / m * (np.dot(Y, np.log(Y_hat + eps).T) + np.dot(1 - Y, np.log(1 - Y_hat  + eps).T))
    return np.squeeze(cost)

def compute_cost_with_regularization(Y_hat, Y, W_curr, W_tre, lambd,  eps= 0.001):  
    cros_cost = get_cost_value(Y_hat, Y, eps)
    Weight_elim = np.sum((np.square(W_curr) / np.square(W_tre)) / (1 + np.square(W_curr) / np.square(W_tre))) * (lambd)
    cost_r = cros_cost + Weight_elim
    cost_r = np.squeeze(cost_r)
    return cost_r


def convert_prob_into_class(probs):
    probs_ = np.copy(probs)
    probs_[probs_ > 0.5] = 1
    probs_[probs_ <= 0.5] = 0
    return probs_


def get_accuracy_value(Y_hat, Y):
    Y_hat_ = convert_prob_into_class(Y_hat)
    return (Y_hat_ == Y).all(axis=0).mean()


def get_performance_value(Y_hat, Y):
    Y_hat_ = convert_prob_into_class(Y_hat)
    TP = ((Y_hat_ == 1) & (Y == 1)).sum()
    FP = ((Y_hat_ == 1) & (Y == 0)).sum()
    #TN = ((Y_hat_ == 0) & (Y == 0)).sum()
    FN = ((Y_hat_ == 0) & (Y == 1)).sum()
    precision = TP / (TP + FP)
    recall = TP / (TP + FN)
    F1 = 2 * ((recall * precision) / (recall + precision) )
    return precision, recall, F1  

def single_layer_backward_propagation(dA_curr, W_curr, b_curr, Z_curr, A_prev, activation="relu"):
    m = A_prev.shape[1]
    
    if activation == "relu":
        backward_activation_func = relu_backward
    elif activation == "sigmoid":
        backward_activation_func = sigmoid_backward
    else:
        raise Exception('Non-supported activation function')
    
    dZ_curr = backward_activation_func(dA_curr, Z_curr)
    dW_curr = np.dot(dZ_curr, A_prev.T) / m
    db_curr = np.sum(dZ_curr, axis=1, keepdims=True) / m
    dA_prev = np.dot(W_curr.T, dZ_curr)

    return dA_prev, dW_curr, db_curr


def full_backward_propagation(Y_hat, Y, memory, params_values, nn_architecture, eps = 0.000000000001):
    grads_values = {}
    m = Y.shape[1]
    Y = Y.reshape(Y_hat.shape)
    
    dA_prev = - (np.divide(Y, Y_hat + eps) - np.divide(1 - Y, 1 - Y_hat + eps))
    
    for layer_idx_prev, layer in reversed(list(enumerate(nn_architecture))):
        layer_idx_curr = layer_idx_prev + 1
        activ_function_curr = layer["activation"]
        
        dA_curr = dA_prev
        
        A_prev = memory["A" + str(layer_idx_prev)]
        Z_curr = memory["Z" + str(layer_idx_curr)]
        
        W_curr = params_values["W" + str(layer_idx_curr)]
        b_curr = params_values["b" + str(layer_idx_curr)]
        
        dA_prev, dW_curr, db_curr = single_layer_backward_propagation(
            dA_curr, W_curr, b_curr, Z_curr, A_prev, activ_function_curr)
        
        grads_values["dW" + str(layer_idx_curr)] = dW_curr
        grads_values["db" + str(layer_idx_curr)] = db_curr
         
    return grads_values, dW_curr 

def advsry(X, epsi, grad_v):
     pertubated_data = X + epsi * np.sign(grad_v[:, None])
     pertubated_data = np.clip(pertubated_data, 0, 1)
     return pertubated_data

def update(params_values, grads_values, nn_architecture, learning_rate):

    for layer_idx, layer in enumerate(nn_architecture, 1):
        params_values["W" + str(layer_idx)] -= learning_rate * grads_values["dW" + str(layer_idx)]        
        params_values["b" + str(layer_idx)] -= learning_rate * grads_values["db" + str(layer_idx)]

    return params_values


def train(X, Y, nn_architecture, epochs, learning_rate, batch_size, verbose=False, callback=None):
    params_values = init_layers(nn_architecture, 2)
    cost_history = []
    accuracy_history = []
    
    examples_size = X.shape[1]
    batch_number = examples_size // batch_size
    
    for i in range(epochs):
        batch_idx = epochs % batch_number
        # Mini-Batch
        X_batch = X[:, batch_idx * batch_size : (batch_idx +1) * batch_size]
        Y_batch = Y[:, batch_idx * batch_size : (batch_idx +1) * batch_size]
        
        Y_hat, cashe, _ = full_forward_propagation(X_batch, params_values, nn_architecture)
        cost = get_cost_value(Y_hat, Y_batch)
        cost_history.append(cost)
        accuracy = get_accuracy_value(Y_hat, Y_batch)
        accuracy_history.append(accuracy)
        grads_values, grad_a = full_backward_propagation(Y_hat, Y_batch, cashe, params_values, nn_architecture)
        params_values = update(params_values, grads_values, nn_architecture, learning_rate)
        if(i % 50 == 0):
            if(verbose):
                print("Iteration: {:05} - cost: {:.5f} - accuracy: {:.5f}".format(i, cost, accuracy))
            if(callback is not None):
                callback(i, params_values)
            
    return params_values, cost_history, accuracy_history, grad_a














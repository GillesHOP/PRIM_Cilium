import json
import time

import math

import numpy as np
import pandas as pd
import keras
from tensorflow.keras.models import load_model
from keras.losses import BinaryFocalCrossentropy


# Load the saved model, but only for inferences
model_as_a_layer = keras.layers.TFSMLayer("./model", call_endpoint='serving_default')

threshold = 0.35

# Load the English words from file
with open('./english_words.txt', 'r') as f:
    english_words = set(f.read().splitlines())


# Calculate the length of the request (excluding the TLD)
def calculate_len(request):
    parts = request.split('.')
    tld_length = len(parts[-1]) + len(parts[-2])
    return len(request) - tld_length - 2  # exclude the 2 dots

# Calculate number of subdomains
def calculate_subdomains(request):
    return request.count('.') - 1

# Count the number of English words in the request
def calculate_w_count(request):
    delimiters = ['.', '-', '_']
    words = request
    for delimiter in delimiters:
        words = words.replace(delimiter, ' ')
    words = words.split()
    #print(words)

    count = 0
    for word in words:
        if word.lower() in english_words:
            count += 1
            #print(word)
    return count


# Calculate the length of the longest English word in the request
def calculate_longest_word_length(request):
    delimiters = ['.', '-', '_']
    words = request
    for delimiter in delimiters:
        words = words.replace(delimiter, ' ')
    words = words.split()

    longest_length = 0
    for word in words:
        if word.lower() in english_words:
            if len(word) > longest_length:
                longest_length = len(word)

    return longest_length


# Calculate the percentage of digits in the request
def count_digits(text):
    return sum(char.isdigit() for char in text)


# Calculate the entropy of the request
def calculate_entropy(request):
    probability = [float(request.count(c)) / len(request) for c in dict.fromkeys(list(request))]
    entropy = - sum([p * math.log(p) / math.log(2.0) for p in probability])
    return entropy

# Function to calculate entropy of a string
def calculate_entropy(text):
    if len(text) == 0:
        return 0.0

    # Calculate frequency of each character
    freq = {}
    for char in text:
        if char in freq:
            freq[char] += 1
        else:
            freq[char] = 1

    # Calculate entropy
    entropy = 0.0
    text_length = len(text)
    for count in freq.values():
        probability = count / text_length
        entropy -= probability * math.log2(probability)

    return entropy


def preprocessing(query):
    len_query = calculate_len(query)
    subdomains_count = calculate_subdomains(query)
    w_count = calculate_w_count(query)
    w_count_ratio = w_count / len_query if len_query != 0 else 0
    w_max = calculate_longest_word_length(query)
    w_max_ratio = w_max / len_query if len_query != 0 else 0
    digit_count = count_digits(query)
    digit_ratio = digit_count / len_query
    entropy = calculate_entropy(query)
    return np.array([len_query, subdomains_count, w_count, w_count_ratio, w_max, w_max_ratio, digit_ratio, entropy])


def predict(query):
    input = preprocessing(query)
    input = input.reshape(1, -1)  # Reshape to add batch dimension
    
    pred = model_as_a_layer(input)
    #print(pred)

    return pred['dense_2'].numpy()[0, 0]


def read_and_process_logs(file_path):
    # Keep track of the last position read
    last_position = 0
    dns_counter = 0
    while True:
        with open(file_path, 'r') as file:
            # Move the cursor to the last read position
            file.seek(last_position)
            
            for line in file:
                try:
                    log = json.loads(line)
                    if 'flow' in log and 'l7' in log['flow'] and 'dns' in log['flow']['l7']:
                        flow = log['flow']
                        dns = flow['l7']['dns']
                        source_ip = flow['IP']['source']
                        destination_ip = flow['IP']['destination']
                        query = dns.get('query', '')
                        qtype = dns.get('qtypes', [''])[0]

                        prediction = predict(query)
                        attack = prediction > threshold
                        
                        dns_counter+=1
                        if attack :
                            print(f'DNS log ({dns_counter}),EXFILTRATION DETECTED! (pred={prediction}), query=\"{query}\", qtype=\"{qtype}\", from=\"{source_ip}\", to=\"{destination_ip}\"')
                        else :
                            print(f'DNS log ({dns_counter}), pred={prediction}, query=\"{query}\", qtype=\"{qtype}\", from=\"{source_ip}\", to=\"{destination_ip}\"')
                except json.JSONDecodeError:
                    continue
            
            # Update the last position
            last_position = file.tell()

        # Sleep for a while before checking for new logs
        time.sleep(5)


if __name__ == "__main__":
    log_file_path = "fetched_events.log"
    read_and_process_logs(log_file_path)

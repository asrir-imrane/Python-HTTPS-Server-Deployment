
# Python HTTPS Server Deployment with Ansible

## Overview
This document provides a step-by-step explanation of deploying a Python HTTPS server using Ansible, ensuring it runs as a non-root user, automatically starts on reboot, and verifying its functionality.

## 1. Python Script

The following Python script sets up a basic HTTPS server that responds with `"Server is up!"` to all incoming requests.

### `server.py`

```python
import http.server
import ssl

class SimpleHTTPSHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"Server is up!")

if __name__ == "__main__":
    server_address = ('', 8443)
    httpd = http.server.HTTPServer(server_address, SimpleHTTPSHandler)
    httpd.socket = ssl.wrap_socket(httpd.socket, keyfile="key.pem", certfile="cert.pem", server_side=True)
    print("Serving on port 8443...")
    httpd.serve_forever()
```

## 2. Ansible Playbook

The following Ansible playbook automates the deployment of the Python HTTPS server, ensuring it runs under a non-root user and starts on reboot via a `cron` job. 

### `DeployServer.yml`

```yaml

- name: Deploy Python HTTPS Server as Non-Root User # Define the playbook name for clarity
  hosts: all  # Target all hosts in the inventory file
  become: false  # Default to non-root privileges for tasks unless specified
  vars:
    user_name: imrane  # Define the non-root user to run the server as

  tasks:
    # Ensure Python3 is installed on the target machine (requires root access)
    - name: Ensure Python3 is installed (requires root)
      become: true  # Run this task with root privileges
      package:
        name: python3  # Specify the package name as Python3
        state: present  # Ensure Python3 is installed (present)

    # Ensure pip for Python3 is installed on the target machine (requires root access)
    - name: Ensure pip for Python3 is installed (requires root)
      become: true  # Run this task with root privileges
      package:
        name: python3-pip  # Specify the package name for Python3 pip
        state: present  # Ensure pip is installed (present)

    # Create a directory for the server files under the specified non-root user
    - name: Create directories for server files under non-root user
      file:
        path: "/home/{{ user_name }}/python_server"  # Path to create for server files
        state: directory  # Ensure a directory is created
        owner: "{{ user_name }}"  # Set ownership to the non-root user
        group: "{{ user_name }}"  # Set group ownership to the non-root user
        mode: '0755'  # Set permissions to allow the owner full access, others read/execute

    # Copy the Python server script to the specified directory on the target machine
    - name: Copy the Python server script to the target machine
      copy:
        src: ./server.py  # Local path to the server script
        dest: "/home/{{ user_name }}/python_server/server.py"  # Destination path on target machine
        owner: "{{ user_name }}"  # Set ownership to the non-root user
        group: "{{ user_name }}"  # Set group ownership to the non-root user
        mode: '0755'  # Set permissions to allow the owner full access, others read/execute

    # Copy the SSL key file to the target machine under secure permissions
    - name: Copy SSL key file
      copy:
        src: ./key.pem  # Local path to the SSL key file
        dest: "/home/{{ user_name }}/python_server/key.pem"  # Destination path on target machine
        owner: "{{ user_name }}"  # Set ownership to the non-root user
        group: "{{ user_name }}"  # Set group ownership to the non-root user
        mode: '0600'  # Secure permissions (only owner can read/write)

    # Copy the SSL certificate file to the target machine under secure permissions
    - name: Copy SSL certificate file
      copy:
        src: ./cert.pem  # Local path to the SSL certificate file
        dest: "/home/{{ user_name }}/python_server/cert.pem"  # Destination path on target machine
        owner: "{{ user_name }}"  # Set ownership to the non-root user
        group: "{{ user_name }}"  # Set group ownership to the non-root user
        mode: '0600'  # Secure permissions (only owner can read/write)

    # Start the Python server using nohup to keep it running in the background
    - name: Start Python server using nohup as non-root user
      shell: "nohup python3 /home/{{ user_name }}/python_server/server.py > /home/{{ user_name }}/python_server/server.log 2>&1 &"  # Command to start server in background
      args:
        chdir: "/home/{{ user_name }}/python_server"  # Change to server directory before running
      become: false  # Run as non-root user to keep permissions as the user

    # Set up a cron job to automatically start the Python server on system reboot
    - name: Create cron job to start Python server on reboot
      cron:
        name: "Start Python HTTPS Server on reboot"  # Description for cron job
        user: "{{ user_name }}"  # Run the cron job as the non-root user
        special_time: reboot  # Run this cron job at every system reboot
        job: "nohup python3 /home/{{ user_name }}/python_server/server.py > /home/{{ user_name }}/python_server/server.log 2>&1"  # Command to start server on reboot

    # Test if the Python HTTPS server is running by making a request to the server's URL
    - name: Test if the server is running
      uri:
        url: https://localhost:8443/  # URL to test server (localhost on HTTPS port 8443)
        validate_certs: no  # Ignore SSL certificate validation (for self-signed certificates)
        return_content: yes  # Retrieve content of the response
      register: result  # Register the response in a variable named 'result'
      retries: 5  # Retry up to 5 times if server is not running yet
      delay: 3  # Wait 3 seconds between retries
      until: result.status == 200  # Stop retrying when HTTP status 200 is received

    # Display the server response content in the console for confirmation
    - name: Display server status
      debug:
        var: result.content  # Output the server response content for review
```

## 3. Step-by-Step Approach

1. **Preparation**:
   - Created a Python script (`server.py`) for an HTTPS server responding to GET requests.
   - Generated SSL certificates (`key.pem` and `cert.pem`) using OpenSSL.

2. **Ansible Playbook**:
   - Configured Ansible to:
     - Install Python and pip as needed.
     - Copy the `server.py` script and SSL files to the target machine, setting the correct permissions for a non-root user.
     - Start the Python server using `nohup` to keep it running in the background.
     - Create a `cron` job that ensures the server starts on reboot.

3. **Verification**:
   - Used the `uri` module to test if the server is running and responding at `https://localhost:8443`.

## 4. Challenges Faced and Solutions

- **Challenge 1**: Running the server as a non-root user with automated startup on reboot.
  - **Solution**: Used `nohup` to run the server in the background and added a `cron` job to restart it on reboot.

- **Challenge 2**: Avoiding `systemd` due to its unavailability in certain environments.
  - **Solution**: Implemented `nohup` and `cron` to replace `systemd` for starting and restarting the service.

- **Challenge 3**: Self-signed certificates causing browser security warnings.
  - **Solution**: Used the `-k` option in `curl` to bypass SSL verification during server testing.

## 5. Time Spent on Each Step

1. **Preparation and Writing the Python Script**: 15 minutes
2. **Developing and Testing the Ansible Playbook**: 30 minutes
3. **Troubleshooting and Documentation**: 15 minutes

Total time spent: **60 minutes**

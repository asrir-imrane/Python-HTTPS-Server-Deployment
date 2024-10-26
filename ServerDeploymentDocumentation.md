
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
- name: Deploy Python HTTPS Server as Non-Root User
  hosts: all
  become: false
  vars:
    user_name: imrane  # Replace with the actual non-root user name
  tasks:
    - name: Ensure Python3 is installed (requires root)
      become: true
      package:
        name: python3
        state: present

    - name: Ensure pip for Python3 is installed (requires root)
      become: true
      package:
        name: python3-pip
        state: present

    - name: Create directories for server files under non-root user
      file:
        path: "/home/{{ user_name }}/python_server"
        state: directory
        owner: "{{ user_name }}"
        group: "{{ user_name }}"
        mode: '0755'

    - name: Copy the Python server script to the target machine
      copy:
        src: ./server.py
        dest: "/home/{{ user_name }}/python_server/server.py"
        owner: "{{ user_name }}"
        group: "{{ user_name }}"
        mode: '0755'

    - name: Copy SSL key file
      copy:
        src: ./key.pem
        dest: "/home/{{ user_name }}/python_server/key.pem"
        owner: "{{ user_name }}"
        group: "{{ user_name }}"
        mode: '0600'

    - name: Copy SSL certificate file
      copy:
        src: ./cert.pem
        dest: "/home/{{ user_name }}/python_server/cert.pem"
        owner: "{{ user_name }}"
        group: "{{ user_name }}"
        mode: '0600'

    - name: Start Python server using nohup as non-root user
      shell: "nohup python3 /home/{{ user_name }}/python_server/server.py > /home/{{ user_name }}/python_server/server.log 2>&1 &"
      args:
        chdir: "/home/{{ user_name }}/python_server"
      become: false

    - name: Create cron job to start Python server on reboot
      cron:
        name: "Start Python HTTPS Server on reboot"
        user: "{{ user_name }}"
        special_time: reboot
        job: "nohup python3 /home/{{ user_name }}/python_server/server.py > /home/{{ user_name }}/python_server/server.log 2>&1"

    - name: Test if the server is running
      uri:
        url: https://localhost:8443/
        validate_certs: no
        return_content: yes
      register: result
      retries: 5
      delay: 3
      until: result.status == 200

    - name: Display server status
      debug:
        var: result.content
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

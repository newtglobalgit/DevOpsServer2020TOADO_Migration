import json
import argparse
import os
import subprocess
import sys


def create_temp_configuration(template_path, temp_path, args):
    """Create a temporary configuration file based on the template."""
    if not os.path.isfile(template_path):
        print(f"Template configuration file not found at {template_path}. Exiting.")
        sys.exit(1)
    
    # Load the template configuration file
    with open(template_path, 'r') as file:
        config = json.load(file)

    # Replace placeholders in the configuration with argument values
    config['sourceAccountUrl'] = args.source_account_url
    config['sourceAccountToken'] = args.source_account_token
    config['targetAccountUrl'] = args.target_account_url
    config['targetAccountToken'] = args.target_account_token
    config['sourceProcessName'] = args.source_process_name

    # Save to a temporary configuration file
    with open(temp_path, 'w') as file:
        json.dump(config, file, indent=4)
    print(f"Temporary configuration file created at: {temp_path}")


def find_process_migrator():
    """Manually specify the full path of process-migrator and log debug info."""
    process_migrator_path = r'C:\Users\romy\AppData\Roaming\npm\process-migrator.cmd'

    print(f"Looking for process-migrator at: {process_migrator_path}")
    
    if os.path.isfile(process_migrator_path):
        print(f"process-migrator found at: {process_migrator_path}")
        return process_migrator_path
    else:
        print(f"process-migrator not found at the specified path: {process_migrator_path}")
        return None


def run_process_migrator(temp_path):
    """Run process-migrator with the temporary configuration."""
    process_migrator_path = find_process_migrator()
    if process_migrator_path:
        # Log the current working directory
        print(f"Current working directory: {os.getcwd()}")

        # Construct the command with the full path to the executable
        command = f'"{process_migrator_path}" --mode=migrate --config="{temp_path}"'
        print(f"Executing: {command}")

        try:
            # Run the process with explicit shell execution and capture output
            result = subprocess.run(
                command,
                shell=True,
                cwd=os.getcwd(),  # Ensure the tool runs in the correct directory
                capture_output=True,
                text=True
            )

            # Log stdout and stderr
            print("process-migrator output:", result.stdout)
            if result.returncode != 0:
                print("process-migrator error:", result.stderr)
                sys.exit(result.returncode)
        except Exception as e:
            print(f"An error occurred while running process-migrator: {e}")
            sys.exit(1)
    else:
        print("process-migrator not found. Exiting.")
        sys.exit(1)



def main():
    parser = argparse.ArgumentParser(description="Update configuration.json and run process-migrator tool.")
    
    # Add arguments for required parameters
    parser.add_argument('--source-account-url', required=True, help="Source account URL")
    parser.add_argument('--source-account-token', required=True, help="Source account PAT")
    parser.add_argument('--target-account-url', required=True, help="Target account URL")
    parser.add_argument('--target-account-token', required=True, help="Target account PAT")
    parser.add_argument('--source-process-name', required=True, help="Process name for export")
    
    args = parser.parse_args()

    # Paths for template and temporary configuration files
    template_path = os.path.join('process-migrator', 'configuration.json')  # Original config template
    temp_path = os.path.join('process-migrator', 'temp_configuration.json')  # Temporary config file

    # Create temporary configuration file
    create_temp_configuration(template_path, temp_path, args)

    try:
        # Run process-migrator with the temporary configuration file
        run_process_migrator(temp_path)
    finally:
        # Delete the temporary configuration file
        if os.path.isfile(temp_path):
            os.remove(temp_path)
            print(f"Temporary configuration file {temp_path} deleted.")


if __name__ == "__main__":
    main()

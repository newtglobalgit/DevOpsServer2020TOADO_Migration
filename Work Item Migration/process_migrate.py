import os
import json
import subprocess
import sys
import shutil


def ensure_process_migrator():
    npm_path = shutil.which("npm") or r"C:\Program Files\nodejs\npm.cmd"
    try:
        npm_version = subprocess.check_output([npm_path, "-v"], text=True).strip()
        print(f"npm found. Version: {npm_version}")
        process_migrator_path = shutil.which("process-migrator")
        if process_migrator_path:
            print(f"process-migrator found at: {process_migrator_path}")
            return process_migrator_path
        print("Checking global npm installation path...")
        npm_global_root = subprocess.check_output([npm_path, "root", "-g"], text=True).strip()
        npm_bin_path = os.path.dirname(npm_global_root)  
        possible_paths = [
            os.path.join(npm_bin_path, "process-migrator.cmd"),  
            os.path.join(npm_bin_path, "process-migrator")       
        ]
        for path in possible_paths:
            if os.path.isfile(path):
                print(f"process-migrator found at: {path}")
                return path
        print("process-migrator not found. Installing globally using npm...")
        subprocess.run([npm_path, "install", "-g", "process-migrator"], check=True)
        process_migrator_path = shutil.which("process-migrator")
        if process_migrator_path:
            print(f"process-migrator installed and found at: {process_migrator_path}")
            return process_migrator_path
        for path in possible_paths:
            if os.path.isfile(path):
                print(f"process-migrator installed and found at: {path}")
                return path
        print("process-migrator installation failed or not found. Please check your npm setup.")
        sys.exit(1)
    except FileNotFoundError:
        print("npm is not accessible. Please ensure Node.js and npm are installed and in PATH.")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"Error installing process-migrator: {e}")
        sys.exit(1)



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


def run_process_migrator(temp_path):
    """Run process-migrator with the temporary configuration."""
    process_migrator_path = ensure_process_migrator()
    if process_migrator_path:
        # Log the current working directory
        print(f"Current working directory: {os.getcwd()}")

        # Construct the command with the full path to the executable
        command = f'"{process_migrator_path}" --mode=migrate --config="{temp_path}"'
        print(f"Executing: {command}")

        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=os.getcwd(),  
                capture_output=True,
                text=True
            )
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
    import argparse
    parser = argparse.ArgumentParser(description="Update configuration.json and run process-migrator tool.")
    
    # Add arguments for required parameters
    parser.add_argument('--source-account-url', required=True, help="Source account URL")
    parser.add_argument('--source-account-token', required=True, help="Source account PAT")
    parser.add_argument('--target-account-url', required=True, help="Target account URL")
    parser.add_argument('--target-account-token', required=True, help="Target account PAT")
    parser.add_argument('--source-process-name', required=True, help="Process name for export")

    args = parser.parse_args()

    # Paths for template and temporary configuration files
    template_path = os.path.join('process-migrator', 'configuration.json')  
    temp_path = os.path.join('process-migrator', 'temp_configuration.json')  
    create_temp_configuration(template_path, temp_path, args)

    try:
        run_process_migrator(temp_path)
    finally:
        if os.path.isfile(temp_path):
            os.remove(temp_path)
            print(f"Temporary configuration file {temp_path} deleted.")


if __name__ == "__main__":
    main()

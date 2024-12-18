import yaml

class LinuxFileHandler:
    def __init__(self, config_path):
        self.config = self._load_config(config_path)

    def _load_config(self, config_path):
        try:
            with open(config_path, 'r') as file:
                return yaml.safe_load(file)
        except FileNotFoundError:
            print(f"Error: Config file not found at {config_path}")
            raise
        except yaml.YAMLError as e:
            print(f"Error parsing YAML file: {e}")
            raise

    def save_file_to_linux(self, file_content, file_name):
        output_directory = self.config['linux']['output_directory']
        output_path = f"{output_directory}/{file_name}"
        try:
            with open(output_path, 'w') as file:
                file.write(file_content)
            print(f"File saved successfully at {output_path}")
        except Exception as e:
            print(f"Error saving file: {e}")



if __name__ == "__main__":
    config_path = "src/configuration/config.yml" 
    file_handler = LinuxFileHandler(config_path=config_path)

# shell-copilot
able to help you navigate via shell

how to run

### prerequisites
- create a virtual environment, run the following commands
```
conda create -n shell-copilot
conda activate shell-copilot
conda install python=3.10
pip install -r requirements.txt
```
- after activating the environment ensure you have an `env.sh` with the following variables set
```
export TEMPORAL_CONNECTION="local"
export GOOGLE_API_KEY="your_google_api_key" # used for gemini api
```

### run project
- run `source run_project.sh`

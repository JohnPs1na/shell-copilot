# shell-copilot
able to help you navigate via shell

how to run (only mac instructions for now)

### prerequisites
- create a virtual environment, run the following commands
- install temporal with brew `brew install temporal`
- install rabbitmq with brew `brew install rabbitmq`
- `brew services start rabbitmq`
  
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
- in another terminal train the model using this (the default dataset is already provided in the repo)
```
cd classifier
python train_bert.py
```
### run project
- run `source run_project.sh`

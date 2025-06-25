import subprocess

# Run the retrieve script
subprocess.run(["python", "retrieve_tasas.py"], check=True)

# Run the ingest/clean script
subprocess.run(["python", "clean_tasas.py"], check=True)

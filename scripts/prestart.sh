#!/bin/sh -e

# Create initial data in DB
python /app/initial_data.py

python /app/set_data_fake.py

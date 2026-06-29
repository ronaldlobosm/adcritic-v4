#!/bin/bash
python seed_news.py
gunicorn run:app

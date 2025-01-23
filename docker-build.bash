#!/bin/bash
#
# Linux/Mac BASH script to build docker container
#
docker rmi finalproject
docker build -t finalproject .

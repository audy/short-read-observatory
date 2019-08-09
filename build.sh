#!/bin/bash

image=$(cat IMAGE)

docker build --tag ${image} .

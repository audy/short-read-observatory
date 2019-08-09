#!/bin/bash

image=$(cat IMAGE)

docker run \
  --volume $(pwd):/app/ \
  --entrypoint /bin/bash \
  -ti \
  --rm \
  ${image}

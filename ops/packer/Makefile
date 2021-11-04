.PHONY: all version docker

all: docker

version:
	mkdir -p output
	python gen_packer_cfg.py ./iris.yaml | tail -n +2 > ./output/iris.json

docker: version
	packer build -only=docker ./output/iris.json

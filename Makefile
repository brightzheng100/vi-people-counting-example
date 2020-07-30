#
# Top level makefile to orchestrate the tasks
#

build-local:
	@echo "Building all Docker images for local architecture only..."
	$(MAKE) -C detector-app build
	$(MAKE) -C detector-cam build
	$(MAKE) -C detector-monitor build
	$(MAKE) -C detector-mqtt build
	$(MAKE) -C detector-service build

push-local:
	@echo "Docker-pushing Docker images for local architecture only..."
	$(MAKE) -C detector-app push
	$(MAKE) -C detector-cam push
	$(MAKE) -C detector-monitor push
	$(MAKE) -C detector-mqtt push
	$(MAKE) -C detector-service push

clean:
	@echo "Delete Docker container and remove Docker images from local machine"
	$(MAKE) -C detector-app clean
	$(MAKE) -C detector-cam clean
	$(MAKE) -C detector-monitor clean
	$(MAKE) -C detector-mqtt clean
	$(MAKE) -C detector-service clean

ANAX_CONTAINER:=$(word 1, $(shell sh -c "docker ps | grep 'openhorizon/amd64_anax'"))
EXTRA:=$(if $(ANAX_CONTAINER), | grep -v $(ANAX_CONTAINER), )
stop:
	@echo "Stopping and removing Docker containers."
	-docker rm -f `docker ps -aq ${EXTRA}` 2>/dev/null || :

ANAX_IMAGE:=$(word 3, $(shell sh -c "docker images | grep 'openhorizon/amd64_anax'"))
foo:
deep-clean: clean stop
	@echo "Removing Docker container images."
	-docker rmi -f `docker images -aq | grep -v "${ANAX_IMAGE}"` 2>/dev/null || :
	@echo "Removing the Docker network used for testing."
	-docker network rm detector-network 2>/dev/null || :

#
# Targets for publishing this service to an Open-Horizon Exhange and for registering edge devices with Open-Horizon
#
# NOTE: You must install the Open-Horizon CLI in order to use these targets!
#
publish-local-services:
	@echo "Publishing the local services for this architecture only..."
	$(MAKE) -C restyolocpu publish-service
	$(MAKE) -C yolocpu publish-service
	@echo "  NOTE: the shared services must also be published (restcam, mqtt, monitor)."
	@echo "  NOTE: after this, also please publish a pattern or policies."

publish-all-services:
	@echo "Building, pushing, and publishing the local services for all architectures..."
	$(MAKE) -C restyolocpu publish-all-services
	$(MAKE) -C yolocpu publish-all-services
	@echo "  NOTE: the shared services must also be published (restcam, mqtt, monitor)."
	@echo "  NOTE: after this, also please publish a pattern or policies."

publish-all-patterns: validate-org
	@echo "Publishing all supported deployment patterns for this example..."
	hzn exchange pattern publish -f deployment/pattern-yolocpu.json

publish-all-policies: validate-org
	@echo "Publishing business/deployment policies for this example..."
	hzn exchange business addpolicy -f ./deployment/business-policy.json

register-pattern: check-cam-url
	@if [ -n "${CAM_URL}" ]; \
          then hzn register --pattern "${HZN_ORG_ID}/pattern-yolocpu" --input-file ./deployment/input-file.json --policy=./deployment/privileged.json; \
          else echo "ERROR: 'CAM_URL' must be set for this pattern."; \
	fi

register-policy:
	hzn register --policy ./deployment/example-node-policy.json

#
# Sanity check targets
#

validate-org:
	@if [ -z "${HZN_ORG_ID}" ]; \
	  then { echo "***** ERROR: \"HZN_ORG_ID\" is not set!"; exit 1; }; \
	  else echo "  NOTE: Using Exchange Org ID: \"${HZN_ORG_ID}\""; \
	fi
	@sleep 1

check-cam-url:
	@if [ -z "${CAM_URL}" ]; \
	  then echo "  Warning: \"CAM_URL\" is not set! Using default."; \
	  else echo "  NOTE: Using camera URL: ${CAM_URL}"; \
	fi
	@sleep 1

.PHONY: test clean deep-clean publish-all-services publish-all-patterns publish-all-policies register-pattern register-policy validate-org check-cam-url


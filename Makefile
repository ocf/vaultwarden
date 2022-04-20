DOCKER_REVISION ?= vaultwarden-testing-$(USER)
DOCKER_TAG = docker-push.ocf.berkeley.edu/vaultwarden:$(DOCKER_REVISION)

vaultwarden_VERSION := 1.24.0

.PHONY: cook-image
cook-image:
	docker build --build-arg vaultwarden_version=$(vaultwarden_VERSION) --pull -t $(DOCKER_TAG) .

.PHONY: push-image
push-image:
	docker push $(DOCKER_TAG)

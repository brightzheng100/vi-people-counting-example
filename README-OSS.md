# Trying Edge Computing By OSS Open Horizon

[Open Horizon](https://www.lfedge.org/projects/openhorizon/) is a platform for managing the service software lifecycle of containerized workloads and related machine learning assets. It enables autonomous management of applications deployed to distributed webscale fleets of edge computing nodes and devices without requiring on-premise administrators.

Formerly known as “Blue Horizon”, Open Horizon is contributed to LF Edge by IBM.
Open Horizon joins LF Edge in April 2020 as a Stage 1 “At-Large” project.

## Assumptions

Let's assume that there is already an Ubuntu Bionic VM (deployed in VirtualBox for example).

We can setup the OSS Open Horizon all in one VM for testing / evaluating purposes.

By the way, if you're running VirtualBox in your MacBook, there is a permission issue which will cause the VM crash once the app tries to connect the Facetime HD Camera.
My current workaround is to start VirtualBox as root: `sudo virtualbox`.
Check out the forum post I raised here for the follow-up: https://forums.virtualbox.org/viewtopic.php?f=8&t=99299&p=481734#p481734

## Install OSS Open Horizon

There is a great helper script which can help us setup OSS Open Horizon, in minutes:

```sh
$ curl -sSL https://raw.githubusercontent.com/open-horizon/devops/master/mgmt-hub/deploy-mgmt-hub.sh | sudo bash
```

Take note of some important info from the output logs generated:

```
...
----------- Summary of what was done:
1. Started Horizon management hub services: agbot, exchange, postgres DB, CSS, mongo DB
2. Created exchange resources: system org (IBM) admin user, user org (myorg) and admin user, and agbot
    - Exchange root user generated password: POsrcFvZPCVmKLFZb7RSbIxA3j0po5
    - System org admin user generated password: pwCMXjkUTcpj7ec3YBS5ng4NQ6QJ9n
    - Agbot generated token: YzoLxKtkpBVOCOvtEoL9rNwzkkZI0R
    - User org admin user generated password: IXtvnafMfvBiuMTw9UQDcnTX91mWgs
    - Node generated token: jkgtRtzIpCRyqnfmXTQ06185m3fAd1
    Important: save these generated passwords/tokens in a safe place. You will not be able to query them from Horizon.
3. Installed the Horizon agent and CLI (hzn)
4. Created a Horizon developer key pair
5. Installed the Horizon examples
6. Created and registered an edge node to run the helloworld example edge service
```

## Check out the environment

### Containers

```sh
$ sudo usermod -aG docker $(whoami) # remember to log out and in again to use `docker` instead of `sudo docker`

$ docker ps
CONTAINER ID        IMAGE                                         COMMAND                  CREATED             STATUS                    PORTS                      NAMES
3b9e7bad6674        openhorizon/ibm.helloworld_amd64              "/bin/sh -c /service…"   10 minutes ago      Up 10 minutes                                        a48e3f55f38053fc118777ce6476c024e6d47e75b171ebb6c1bf2efc76cdcb8c-ibm.helloworld
868ff55dbb51        openhorizon/amd64_agbot:latest                "/bin/sh -c /usr/hor…"   15 minutes ago      Up 10 minutes (healthy)   127.0.0.1:3091->3091/tcp   agbot
455f32170bd9        openhorizon/amd64_cloud-sync-service:latest   "/usr/edge-sync-serv…"   15 minutes ago      Up 15 minutes (healthy)   127.0.0.1:9443->9443/tcp   css-api
d12f635657e5        openhorizon/amd64_exchange-api:latest         "/bin/sh -c '/usr/bi…"   15 minutes ago      Up 15 minutes (healthy)   127.0.0.1:3090->8080/tcp   exchange-api
98927d16159a        mongo:latest                                  "docker-entrypoint.s…"   15 minutes ago      Up 15 minutes (healthy)   27017/tcp                  mongo
37edcfb5d6c4        postgres:latest                               "docker-entrypoint.s…"   15 minutes ago      Up 15 minutes (healthy)   5432/tcp                   postgres
```

### Edge Node

```sh
$ hzn version
Horizon CLI version: 2.26.12
Horizon Agent version: 2.26.12

$ hzn node list
{
  "id": "node1",
  "organization": "myorg",
  "pattern": "",
  "name": "node1",
  "nodeType": "device",
  "token_last_valid_time": "2020-08-12 14:21:14 +0000 UTC",
  "token_valid": true,
  "ha": false,
  "configstate": {
    "state": "configured",
    "last_update_time": "2020-08-12 14:21:14 +0000 UTC"
  },
  "configuration": {
    "exchange_api": "http://127.0.0.1:3090/v1/",
    "exchange_version": "2.38.0",
    "required_minimum_exchange_version": "2.23.0",
    "preferred_exchange_version": "2.23.0",
    "mms_api": "http://127.0.0.1:9443",
    "architecture": "amd64",
    "horizon_version": "2.26.12"
  }
}
```

### Hub Exchange

```sh
# from: User org admin user generated password: IXtvnafMfvBiuMTw9UQDcnTX91mWgs
$ export HZN_ORG_ID=myorg \
  export HZN_EXCHANGE_USER_AUTH="admin:IXtvnafMfvBiuMTw9UQDcnTX91mWgs"

$ hzn exchange status
{
  "dbSchemaVersion": 36,
  "msg": "Exchange server operating normally",
  "numberOfAgbotAgreements": 1,
  "numberOfAgbotMsgs": 0,
  "numberOfAgbots": 1,
  "numberOfNodeAgreements": 1,
  "numberOfNodeMsgs": 0,
  "numberOfNodes": 1,
  "numberOfUsers": 3
}

$ hzn exchange node list
[
  "myorg/node1"
]
```

## Try out the People Counting VI App

### Attach Facetime HD Camera to VM

In our laptop:

```sh
# List webcams
$ vboxmanage list webcams
Video Input Devices: 1
.1 "FaceTime HD Camera (Built-in)"
0x8020000005ac8514

# Attach the default Facetime webcam to the VM
$ EDGE_NODE_NAME="ubuntu-edge-allinone-oss"
$ sudo vboxmanage controlvm "${EDGE_NODE_NAME}" webcam attach .1
```

### Clone the repo

SSH into the VM:

```sh
# Clone the repo
$ git clone https://github.com/brightzheng100/vi-people-counting-example.git
$ cd vi-people-counting-example
```

### Set variables

In the VM:

```sh
# Set the necessary variables
# from: User org admin user generated password: IXtvnafMfvBiuMTw9UQDcnTX91mWgs
$ export HZN_ORG_ID=myorg \
  export HZN_EXCHANGE_USER_AUTH="admin:IXtvnafMfvBiuMTw9UQDcnTX91mWgs" \
  export DOCKERHUB_ID="quay.io/brightzheng100"
```

### Update the Node Policy

In the VM:

```sh
$ hzn exchange node updatepolicy -f horizon/node.policy.json node1
```

### Publish Service

In the VM:

```sh
# Publish the service with camera service
$ cat horizon/service.definition.json | \
  sed "s|__DOCKERHUB_ID__|${DOCKERHUB_ID}|g" | \
  hzn exchange service publish -f- -P -O
```

### Add Deploy Policy

In the VM:

```sh
# Deploy policy
$ eval $(hzn util configconv -f horizon/hzn.json) && \
  hzn exchange deployment addpolicy -f horizon/deployment.policy.json ${HZN_ORG_ID}/policy-${SERVICE_NAME}_${SERVICE_VERSION}
```

### What we get?

In the VM:

```sh
# We can check whether the policy just created is compatiple with current node
$ hzn deploycheck all --deployment-pol-id policy-${SERVICE_NAME}_${SERVICE_VERSION} -n "node1"
{
  "compatible": true,
  "reason": {
    "myorg/people-counting-bundle-service_1.0.0_amd64": "Compatible"
  }
}

# We can see that other than OSS Open Horizon containers, there are our app's Docker containers too
$ docker ps
CONTAINER ID        IMAGE                                           COMMAND                  CREATED             STATUS                 PORTS                      NAMES
c723f989e31a        quay.io/brightzheng100/detector-app_amd64       "python app.py"          8 seconds ago       Up 7 seconds                                      91dd89d302ae59343e7ffae9defcb486a67f0db95454e3afcd2233b0aa4dfa46-detector-app
9575f5267168        quay.io/brightzheng100/detector-service_amd64   "python darknet.py y…"   9 seconds ago       Up 8 seconds           0.0.0.0:5252->80/tcp       91dd89d302ae59343e7ffae9defcb486a67f0db95454e3afcd2233b0aa4dfa46-detector-service
88c655c62215        quay.io/brightzheng100/detector-mqtt_amd64      "mosquitto -c /etc/m…"   10 seconds ago      Up 8 seconds           0.0.0.0:1883->1883/tcp     91dd89d302ae59343e7ffae9defcb486a67f0db95454e3afcd2233b0aa4dfa46-detector-mqtt
9f477850db35        quay.io/brightzheng100/detector-monitor_amd64   "python app.py"          11 seconds ago      Up 9 seconds           0.0.0.0:5200->5200/tcp     91dd89d302ae59343e7ffae9defcb486a67f0db95454e3afcd2233b0aa4dfa46-detector-monitor
0826625e415c        quay.io/brightzheng100/detector-cam_amd64       "./start.sh"             11 seconds ago      Up 10 seconds          0.0.0.0:8888->80/tcp       91dd89d302ae59343e7ffae9defcb486a67f0db95454e3afcd2233b0aa4dfa46-detector-cam
868ff55dbb51        openhorizon/amd64_agbot:latest                  "/bin/sh -c /usr/hor…"   5 hours ago         Up 4 hours (healthy)   127.0.0.1:3091->3091/tcp   agbot
455f32170bd9        openhorizon/amd64_cloud-sync-service:latest     "/usr/edge-sync-serv…"   5 hours ago         Up 5 hours (healthy)   127.0.0.1:9443->9443/tcp   css-api
d12f635657e5        openhorizon/amd64_exchange-api:latest           "/bin/sh -c '/usr/bi…"   5 hours ago         Up 5 hours (healthy)   127.0.0.1:3090->8080/tcp   exchange-api
98927d16159a        mongo:latest                                    "docker-entrypoint.s…"   5 hours ago         Up 5 hours (healthy)   27017/tcp                  mongo
37edcfb5d6c4        postgres:latest                                 "docker-entrypoint.s…"   5 hours ago         Up 5 hours (healthy)   5432/tcp                   postgres
```

And then we can access monitor UI by `192.168.56.101:5200`, where `192.168.56.101` is my VM's IP address.


## Clean Up

### Remove the services deployed in Edge Node(s) by removing the deployment policy

To remove the deloyment policy, which tells OSS Open Horizon to remove the services from our Edge Node accordingly:

```sh
hzn exchange deployment removepolicy ${HZN_ORG_ID}/policy-${SERVICE_NAME}_${SERVICE_VERSION} -f
```

### Remove the services

To remove the services involved:

```sh
hzn exchange service remove "${HZN_ORG_ID}/${SERVICE_NAME}_${SERVICE_VERSION}_amd64" -f
```

### Detach the webcam

To detach the webcam from the VM, run this in our laptop (instead of in the VM):

```sh
sudo vboxmanage controlvm "${EDGE_NODE_NAME}" webcam detach .1
```

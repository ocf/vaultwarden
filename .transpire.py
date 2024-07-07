from transpire.resources import ConfigMap, Deployment, Ingress, PersistentVolumeClaim, Secret, Service

name = "vaultwarden"

def objects():
    yield {
        "apiVersion": "acid.zalan.do/v1",
        "kind": "postgresql",
        "metadata": {"name": "ocf-vaultwarden"},
        "spec": {
            "teamId": "ocf",
            "volume": {
                "size": "8Gi",
                "storageClass": "rbd-nvme",
            },
            "numberOfInstances": 1,
            "users": {"vfaultwarden": ["superuser", "createdb"]},
            "databases": {"vaultwarden": "vaultwarden"},
            "postgresql": {"version": "15"},
        },
    }

    pvc = PersistentVolumeClaim(
        name="vaultwarden-data",
        storage="10Gi",
        access_modes="ReadWriteOnce",
    )
    yield pvc.build()

    secret = Secret(
        "vaultwarden",
        string_data={
            "ADMIN_TOKEN": "",
            "DATABASE_URL": "",
            "DOMAIN": "",
            "SIGNUPS_ALLOWED": "",
        },
    )
    yield secret.build()

    dep = Deployment(
        name="vaultwarden",
        image="vaultwarden/server:1.29.1",
        ports=[80],
    )

    dep.obj.spec.template.spec.volumes = [
        {
            "name": "vaultwarden-data",
            "persistentVolumeClaim": {"claimName": "vaultwarden-data"},
        },
    ]

    dep.obj.spec.template.spec.containers[0].volume_mounts = [
        {
            "name": "vaultwarden-data",
            "mountPath": "/data",
        }
    ]

    env = {
        "DOMAIN": "https://vaultwarden.ocf.berkeley.edu",
        "SIGNUPS_ALLOWED": "false",
    }

    dep.obj.spec.template.spec.containers[0].env = [
        {
            "name": "ADMIN_TOKEN",
            "valueFrom": {
                "secretKeyRef": {
                    "name": "vaultwarden",
                    "key": "ADMIN_TOKEN",
                }
            },
        },
        *[{"name": k, "value": v} for k, v in env.items()],
    ]

    yield dep.build()

    svc = Service(
        name="vaultwarden",
        selector=dep.get_selector(),
        port_on_pod=80,
        port_on_svc=80,
    )
    yield svc.build()

    ing = Ingress.from_svc(
        svc=svc,
        host="vaultwarden.ocf.berkeley.edu",
        path_prefix="/",
    )
    yield ing.build()

from transpire.resources import ConfigMap, Ingress, PersistentVolumeClaim, Secret, Service, StatefulSet

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
            "users": {"vaultwarden": ["superuser", "createdb"]},
            "databases": {"vaultwarden": "vaultwarden"},
            "postgresql": {"version": "15"},
        },
    }

    pvc = PersistentVolumeClaim(
        name="vaultwarden-data",
        storage="10Gi",
        access_modes=["ReadWriteOnce"],
    )
    yield pvc.build()

    secret = Secret(
        "vaultwarden",
        string_data={
            "ADMIN_TOKEN": "",
        },
    )
    yield secret.build()

    dep = StatefulSet(
        name="vaultwarden",
        image="vaultwarden/server:1.29.1",
        ports=[80],
        service_name="vaultwarden"
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
        "DATABASE_URL": "postgres://$(_DB_USER):$(_DB_PASS)@ocf-vaultwarden:5432/vaultwarden",
        "DOMAIN": "https://vaultwarden.ocf.berkeley.edu",
        "SIGNUPS_ALLOWED": "false",
    }

    dep.obj.spec.template.spec.containers[0].env = [
        {
            "name": "_DB_USER",
            "valueFrom": {
                "secretKeyRef": {
                    "name": "vaultwarden.ocf-vaultwarden.credentials.postgresql.acid.zalan.do",
                    "key": "username",
                }
            },
        },
        {
            "name": "_DB_PASS",
            "valueFrom": {
                "secretKeyRef": {
                    "name": "vaultwarden.ocf-vaultwarden.credentials.postgresql.acid.zalan.do",
                    "key": "password",
                }
            },
        },
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

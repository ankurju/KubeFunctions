# your_app/tasks.py

from celery import shared_task
from kubernetes import client, config
import time

@shared_task
def execute_function(function_name,job_name):
    try:
        # Initialize Kubernetes client
        config.load_kube_config()  # Loads kubeconfig from default location
        batch_api = client.BatchV1Api()
        core_api = client.CoreV1Api()

        # Create Job definition
        job_manifest = {
            "apiVersion": "batch/v1",
            "kind": "Job",
            "metadata": {
                "name": f"function-executor-job-{job_name}",
            },
            "spec": {
                "ttlSecondsAfterFinished": 0,  # Delete Pod immediately after completion
                "template": {
                    "spec": {
                        "containers": [
                            {
                                "name": f"function-container-{job_name}",
                                "image": f'karjank7/{function_name}:latest',  # Use the function's Docker image
                            }
                        ],
                        "restartPolicy": "Never",  # Ensures Pods stop after function execution
                    }
                },
                "backoffLimit": 0,  # Ensures the Job does not retry
            }
        }

        # Execute command within container
        
        batch_api.create_namespaced_job(body=job_manifest, namespace="default")
        while True:
            pod_list = core_api.list_namespaced_pod(namespace="default", label_selector=f"job-name=function-executor-job-{job_name}")
            if pod_list.items:
                pod = pod_list.items[0]

                # Check if the Pod has completed
                if pod.status.phase == "Succeeded":
                    # Retrieve function output from the Pod
                    response = core_api.read_namespaced_pod_log(name=pod.metadata.name, namespace="default")
                    return response
                # Wait for 1 second before checking again
                time.sleep(1)
        
    except Exception as e:
        return f"Failed to execute function: {str(e)}"

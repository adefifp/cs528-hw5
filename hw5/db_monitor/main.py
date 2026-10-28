import functions_framework
from googleapiclient import discovery
from google.auth import default

PROJECT_ID = "adefifp22909"
INSTANCE_NAME = "hw5-db-instance"

@functions_framework.http
def check_and_stop_sql(request):
    credentials, _ = default()
    service = discovery.build('sqladmin', 'v1', credentials=credentials)

    try:
        instance = service.instances().get(project=PROJECT_ID, instance=INSTANCE_NAME).execute()
        current_policy = instance.get('settings', {}).get('activationPolicy', 'UNKNOWN')
        
        print(f"Current activation policy for {INSTANCE_NAME}: {current_policy}")

        # If running, stop the instance
        if current_policy == "ALWAYS":
            patch_body = {
                "settings": {
                    "activationPolicy": "NEVER"
                }
            }
            request_patch = service.instances().patch(
                project=PROJECT_ID,
                instance=INSTANCE_NAME,
                body=patch_body
            )
            response = request_patch.execute()
            msg = f"Cloud SQL instance {INSTANCE_NAME} was running. Stop command initiated."
            print(msg)
            return {"status": "success", "message": msg}, 200
        else:
            msg = f"Cloud SQL instance {INSTANCE_NAME} is already stopped (policy: {current_policy})."
            print(msg)
            return {"status": "noop", "message": msg}, 200

    except Exception as e:
        error_msg = f"Error managing SQL instance: {str(e)}"
        print(error_msg)
        return {"status": "error", "message": error_msg}, 500

Initally secrets manager should be populated with these values.  


### Naming Convention for Secrets:
<dev or prod>/<shortRepoName>/Component/SubComponent/<version>
ie:
/dev/audioClientServer/Orchestrator/v2



| **Key**                    | **Value**                                                                                  |
|----------------------------|--------------------------------------------------------------------------------------------|
| `task_queue_url`            | `UPDATE_THIS_FIELD_WITH_THE_TASK_QUEUE_URL`                                                |
| `status_update_queue_url`   | `UPDATE_THIS_FIELD_WITH_THE_STATUS_UPDATE_QUEUE_URL`                                       |
| `db_host`                   | `UPDATE_THIS_FIELD_WITH_THE_DB_HOST.cny2uiqswlls.us-east-2.rds.amazonaws.com`              |
| `db_name`                   | `UPDATE_WITH_my_rds_db`                                                                    |
| `db_user`                   | `UPDATE_WITH_db_admin`                                                                     |
| `db_password`               | `UPDATE_WITH_A_SECURE_PASSWORD`                                                            |

This version has no duplicates and represents the final set of key-value pairs for Secrets Manager.

### Next Step:
Shall I proceed with writing the Terraform script now?

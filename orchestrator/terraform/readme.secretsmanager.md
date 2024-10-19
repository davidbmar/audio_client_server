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

After you have run: terraform init, terraform plan, terraform apply you should have something like the above in secrets manager.


### Next Steps: How to Update Secrets in AWS Secrets Manager

This guide explains how to update the stub values in AWS Secrets Manager after the secret has been created using Terraform. Follow these steps to modify the secret values as needed.  You will need to do this, because initally, Secrets Manager will be populated with secrets as above.


### **Step-by-Step Instructions**

#### 1. **Access AWS Management Console**
   - Open your web browser and navigate to the [AWS Management Console](https://aws.amazon.com/console/).
   - Log in with your AWS credentials.

#### 2. **Navigate to Secrets Manager**
   - In the **AWS Management Console**, search for `Secrets Manager` in the search bar at the top.
   - Select **Secrets Manager** from the dropdown menu.

#### 3. **Find the Secret**
   - Once in the Secrets Manager dashboard, locate the search bar.
   - Type in the name of the secret you created:  
     `/dev/audioClientServer/Orchestrator/v2`
   - Click on the secret name when it appears in the search results.

#### 4. **Review the Secret**
   - After selecting the secret, you will be taken to the secret’s overview page.
   - Click the **"Retrieve secret value"** button to display the current values, which will show the stubs you created with Terraform.

#### 5. **Edit the Secret**
   - To modify the secret values:
     - Click the **"Edit"** button at the top of the secret's page.
     - Under the **Secret key/value** section, you will see the current stub values that need to be updated.

#### 6. **Update the Secret Key-Value Pairs**
   - Update each key with the appropriate real values as follows:

   | **Key**                    | **Updated Value**                                                                   |
   |----------------------------|-------------------------------------------------------------------------------------|
   | `task_queue_url`            | Enter the actual task queue URL for your orchestrator                               |
   | `status_update_queue_url`   | Enter the actual status update queue URL                                             |
   | `db_host`                   | Enter the actual RDS database host (e.g., `your-db-host.cny2uiqswlls.us-east-2.rds.amazonaws.com`) |
   | `db_name`                   | Enter the actual database name (e.g., `my_rds_db`)                                  |
   | `db_user`                   | Enter the actual database username (e.g., `db_admin`)                               |
   | `db_password`               | Enter the actual database password (ensure it's secure)                             |

#### 7. **Save Changes**
   - After updating all the values, scroll to the bottom and click the **"Save"** button to store your changes.

#### 8. **Verify Changes**
   - You can verify that the values were updated correctly by clicking the **"Retrieve secret value"** button again after saving the changes.

---

### **Important Notes**
- **Security**: Ensure that sensitive information such as `db_password` is stored securely. Avoid sharing this data in plaintext.
- **Access Control**: Make sure only authorized users or services have access to these secrets. You can manage permissions through IAM roles or policies.
- **Rotating Secrets**: Consider enabling automatic secret rotation if required, particularly for sensitive information like passwords.

---

### File Name: `update_secrets_in_secrets_manager.md`

You can save this documentation as `update_secrets_in_secrets_manager.md` for future reference.

Would you like any additional information or changes to the documentation?

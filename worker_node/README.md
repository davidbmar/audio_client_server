This directory contains two worker_node types, runpod workers which transcribe using runpod.
And AWS worker nodes which use ec2 g4dn.xlarge nodes with GPUs.  These should run faster_whisper
to transcribe audio files.  They both should be pulling data from the job scheduler.:

1.runpod_worker

2.ec2_g4dn.xlarge  

Initially, you will want to setup an AWS Access Key and Secret Key.  This will be in the same account where the worker is and potentially not be in the same account as the other components.

So you would need to setup a Trust Role and permissions for a specific EC2 instance. This instance then could be configured so that the instance profile can read Secrets Manager secrets for the worker, but couldn't write or delete them.   


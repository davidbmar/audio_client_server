This directory contains two worker_node types, runpod workers which transcribe using runpod.
And AWS worker nodes which use ec2 g4dn.xlarge nodes with GPUs.  These should run faster_whisper
to transcribe audio files.  They both should be pulling data from the job scheduler.:

1.runpod_worker

2.ec2_g4dn.xlarge  


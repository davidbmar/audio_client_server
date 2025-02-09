
So for the IAM permission, this is the permission.  
1. Create the below IAM permission:  You want to create this permission which basically has read access for the input bucket and has write access to the output bucket.  The reason this is separate, is because this is outside of AWS and on runpod.io.  Then if the creds are hacked then this limits the blast radius.  For security you might think about using the non-aws account administration "Access for non AWS workloads" - https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_common-scenarios_non-aws.html or think about presigned URLs.  At this time i haven't thought about which is best.
2. Attach this permission to a group.  This is better than attaching to a user.
3. Then add a user to the group. 

, then create a group
and 
';''
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "ComprehensiveInputBucketAccess",
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:ListBucket",
                "s3:GetObjectVersion",
                "s3:GetObjectAttributes",
                "s3:GetObjectTagging",
                "s3:HeadBucket",
                "s3:HeadObject"
            ],
            "Resource": [
                "arn:aws:s3:::2024-09-23-audiotranscribe-input-bucket",
                "arn:aws:s3:::2024-09-23-audiotranscribe-input-bucket/*"
            ]
        },
        {
            "Sid": "ComprehensiveOutputBucketAccess",
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:ListBucket",
                "s3:PutObjectTagging",
                "s3:DeleteObject",
                "s3:HeadBucket",
                "s3:HeadObject"
            ],
            "Resource": [
                "arn:aws:s3:::2024-09-23-audiotranscribe-my-output-bucket",
                "arn:aws:s3:::2024-09-23-audiotranscribe-my-output-bucket/*"
            ]
        }
    ]

}

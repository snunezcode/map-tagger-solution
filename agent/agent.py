import boto3
from os import environ
from datetime import datetime, timezone
import botocore
import pymysql.cursors
import json



class classTagger():
    
    # constructor
    def __init__(self, params):
        self.process_id = params["process_id"]
        self.account = ""
        self.aws_access_key_id = ""
        self.aws_secret_access_key = ""
        self.aws_session_token = ""
        self.tag_key = params["tag_key"]
        self.tag_value = params["tag_value"]
        self.start_date = params["start_date"]
        self.filters = [{'Name': f'tag:{self.tag_key}', 'Values': [self.tag_value]}]
        self.connection = pymysql.connect(db='db', user='root', passwd='pwd', unix_socket="/var/lib/mysql/mysql.sock")
        self.cursor = self.connection.cursor()  
        self.configuration = self.load_configuration()

    def load_configuration(self):
        file = open('../server/configuration.json')
        configuration = json.load(file)
        file.close()
        print(configuration)
        return configuration
        
    def authentication(self,account):
        self.account = account
        sts_client = boto3.client('sts',region_name="us-east-1")
        assumed_role_object = sts_client.assume_role(
            RoleArn=f"arn:aws:iam::{account}:role/MAPTaggingProcessRole",
            RoleSessionName="CrossAccountSession"
        )
        credentials = assumed_role_object['Credentials']
        self.aws_access_key_id = credentials['AccessKeyId']
        self.aws_secret_access_key = credentials['SecretAccessKey']
        self.aws_session_token = credentials['SessionToken']
        
        

    def logging(self,record):
        for resource in record["resources"]:
            sql = "INSERT INTO `tbTaggerRecords` (`process_id`, `account_id`,`region`,`service`,`type`,`resource_name`,`tag_key`,`tag_value`,`creation_date`,`tag_list`,`timestamp`) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
            self.cursor.execute(sql, (self.process_id, self.account, record["region"], record["service"],record["type"],resource['name'],self.tag_key,self.tag_value, resource['created'],resource['tags'],datetime.now().strftime("%Y-%m-%d %H:%M:%S") ))
        self.connection.commit()
    


    # Function to tag EC2 instances
    def tag_ec2_instances(self):
        
        for account in self.configuration['Accounts']:
            self.authentication(account['id'])
        
            for region in account['regions']:
                ec2_client = boto3.client('ec2',
                                        aws_access_key_id=self.aws_access_key_id,
                                        aws_secret_access_key=self.aws_secret_access_key,
                                        aws_session_token=self.aws_session_token,
                                        region_name=region)
                paginator = ec2_client.get_paginator('describe_instances')
            
                instances_with_tag = []
                instances_without_tag = []
                instances_skipped_tag = []
            
                # Iterate through pages of results
                for page in paginator.paginate(Filters=self.filters):
                    for reservation in page.get('Reservations', []):
                        for instance in reservation.get('Instances', []):
                            create_time = instance.get("LaunchTime")
                            tags = instance.get("Tags") if "Tags" in instance else [],
                            if create_time and create_time >= self.start_date:
                                ec2instance = instance.get("InstanceId")
                                instances_with_tag.append({ "name" : ec2instance, "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(tags) })
            
                # Now, use the same paginator to retrieve all instances (without filtering by tag)
                for page in paginator.paginate():
                    for reservation in page.get('Reservations', []):
                        for instance in reservation.get('Instances', []):
                            create_time = instance.get("LaunchTime")
                            ec2instance = instance.get("InstanceId")
                            tags = instance.get("Tags")  if "Tags" in instance else [],
                            if create_time and create_time >= self.start_date:
                                if not any(d['name'] == ec2instance for d in instances_with_tag):
                                    instances_without_tag.append({ "name" : ec2instance, "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(tags) })
                                    ec2_client.create_tags(
                                        Resources=[ec2instance],
                                        Tags=[
                                            {'Key': self.tag_key, 'Value': self.tag_value}
                                        ]
                                    )
                            else:
                                instances_skipped_tag.append({ "name" : ec2instance, "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(tags) })
            
                #Logging Tagging Resources
                self.logging({ "region" : region, "service" : "ec2", "type" : "1", "resources" : instances_with_tag })
                self.logging({ "region" : region, "service" : "ec2", "type" : "2", "resources" : instances_without_tag })
                self.logging({ "region" : region, "service" : "ec2", "type" : "3", "resources" : instances_skipped_tag })



    # Function to tag EBS volumes
    def tag_ebs_volumes(self):
        
        for account in self.configuration['Accounts']:
            self.authentication(account['id'])
        
            for region in account['regions']:
                ec2_client = boto3.client('ec2',
                                            aws_access_key_id=self.aws_access_key_id,
                                            aws_secret_access_key=self.aws_secret_access_key,
                                            aws_session_token=self.aws_session_token,
                                            region_name=region)
                paginator = ec2_client.get_paginator('describe_volumes')
            
                volumes_with_tag = []
                volumes_added_tag = []
                volumes_skipped_tag = []
            
                # Iterate through pages of results
                for page in paginator.paginate(Filters=self.filters):
                    for volume in page.get('Volumes', []):
                        create_time = volume.get("CreateTime")
                        tags = volume.get("Tags")  if "Tags" in volume else [],
                        if create_time and create_time >= self.start_date:
                            volumes_with_tag.append({ "name" : volume['VolumeId'], "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(tags)  })
            
                # Now, use the same paginator to retrieve all volumes (without filtering by tag)
                for page in paginator.paginate():
                    for volume in page.get('Volumes', []):
                        create_time = volume.get("CreateTime")
                        volume_id = volume['VolumeId']
                        tags = volume.get("Tags")  if "Tags" in volume else [],
                        if create_time and create_time >= self.start_date:
                            #if volume_id not in volumes_with_tag:
                            if not any(d['name'] == volume_id for d in volumes_with_tag):
                                volumes_added_tag.append({ "name" : volume_id, "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(tags) })
                                ec2_client.create_tags(
                                    Resources=[volume_id],
                                    Tags=[
                                        {'Key': self.tag_key, 'Value': self.tag_value}
                                    ]
                                )
                                print("Tagged volume:", volume_id)
                        else:
                            volumes_skipped_tag.append({ "name" : volume_id, "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(tags) })
                
                #Logging Tagging Resources
                self.logging({ "region" : region, "service" : "ebs", "type" : "1", "resources" : volumes_with_tag })
                self.logging({ "region" : region, "service" : "ebs", "type" : "2", "resources" : volumes_added_tag })
                self.logging({ "region" : region, "service" : "ebs", "type" : "3", "resources" : volumes_skipped_tag })


    # Function to tag EBS Snapshots
    def tag_ebs_snapshots(self):
        
        for account in self.configuration['Accounts']:
            self.authentication(account['id'])
        
            for region in account['regions']:
                ec2_client = boto3.client('ec2',
                                            aws_access_key_id=self.aws_access_key_id,
                                            aws_secret_access_key=self.aws_secret_access_key,
                                            aws_session_token=self.aws_session_token,
                                            region_name=region)
                snapshots_with_tag = []
                snapshots_added_tag = []
                snapshots_skipped_tag = []
            
                # Create a paginator for EBS snapshots
                paginator = ec2_client.get_paginator('describe_snapshots')
                page_iterator = paginator.paginate(OwnerIds=['self'])
            
                for page in page_iterator:
                    snapshots = page.get('Snapshots', [])
                    for snapshot in snapshots:
                        create_time = snapshot.get("StartTime")
                        tags = snapshot.get("Tags")  if "Tags" in snapshot else []
                        if create_time and create_time >= self.start_date:
                            # Check if the snapshot has the 'map-migrated' tag
                            has_map_migrated_tag = any(tag['Key'] == self.tag_key and tag['Value'] == self.tag_value for tag in tags)
                            if has_map_migrated_tag:
                                snapshots_with_tag.append({ "name" : snapshot['SnapshotId'], "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(tags) })
                            else:
                                snapshots_added_tag.append({ "name" : snapshot['SnapshotId'], "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(tags) })
                                # Add the 'map-migrated' tag to snapshots without it
                                ec2_client.create_tags(Resources=[snapshot['SnapshotId']], Tags=[{'Key': self.tag_key, 'Value': self.tag_value}])
                        else:
                            snapshots_skipped_tag.append({ "name" : snapshot['SnapshotId'], "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(tags) })
                            
                    #Logging Tagging Resources
                    self.logging({ "region" : region, "service" : "snapshot", "type" : "1", "resources" : snapshots_with_tag })
                    self.logging({ "region" : region, "service" : "snapshot", "type" : "2", "resources" : snapshots_added_tag })
                    self.logging({ "region" : region, "service" : "snapshot", "type" : "3", "resources" : snapshots_skipped_tag })

    # Function to tag RDS instances
    def tag_rds_instances(self):
        
        for account in self.configuration['Accounts']:
            self.authentication(account['id'])
        
            for region in account['regions']:
                # Create an RDS client
                rds_client = boto3.client('rds',
                                            aws_access_key_id=self.aws_access_key_id,
                                            aws_secret_access_key=self.aws_secret_access_key,
                                            aws_session_token=self.aws_session_token,
                                            region_name=region)
            
                rds_instances_with_tag = []
                rds_instances_added_tag = []
                rds_instances_skipped_tag = []
                # Create a paginator for RDS instances
                paginator = rds_client.get_paginator('describe_db_instances')
                page_iterator = paginator.paginate()
            
                for page in page_iterator:
                    db_instances = page['DBInstances']
            
                    for rds_instance in db_instances:
                        create_time = rds_instance.get("InstanceCreateTime")
                        rds_tags = rds_client.list_tags_for_resource(ResourceName=rds_instance['DBInstanceArn'])['TagList']
                        print(rds_tags)
                        if create_time and create_time >= self.start_date:
                            # Check if the instance already has the specified tag
                            has_map_migrated_tag = any(tag['Key'] == self.tag_key and tag['Value'] == self.tag_value for tag in rds_tags)
                            if has_map_migrated_tag:
                                rds_instances_with_tag.append({ "name" : rds_instance['DBInstanceIdentifier'], "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(rds_tags) })
                            else:
                                rds_instances_added_tag.append({ "name" : rds_instance['DBInstanceIdentifier'], "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(rds_tags) })
                                # Add the specified tag to the instance
                                rds_client.add_tags_to_resource(
                                    ResourceName=rds_instance['DBInstanceArn'],
                                    Tags=[{'Key': self.tag_key, 'Value': self.tag_value}]
                                )
                        else:
                            rds_instances_skipped_tag.append({ "name" : rds_instance['DBInstanceIdentifier'], "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(rds_tags) })
                                
                #Logging Tagging Resources
                self.logging({ "region" : region, "service" : "rds", "type" : "1", "resources" : rds_instances_with_tag })
                self.logging({ "region" : region, "service" : "rds", "type" : "2", "resources" : rds_instances_added_tag })
                self.logging({ "region" : region, "service" : "rds", "type" : "3", "resources" : rds_instances_skipped_tag })                
            
            

# Function to tag Elastic Load Balancers
def tag_elbs(tag_key, tag_value, start_date):
    # Describe all ELBs
    client_elbv2 = boto3.client('elbv2')

    load_balancers_with_tag = []
    load_balancers_added_tag = []

    # Create a paginator for ELBv2 load balancers
    paginator = client_elbv2.get_paginator('describe_load_balancers')
    page_iterator = paginator.paginate()

    for page in page_iterator:
        load_balancers = page.get('LoadBalancers', [])
        for load_balancer in load_balancers:
            create_time = load_balancer.get("CreatedTime")
            if create_time and create_time >= start_date:
                load_balancer_arn = load_balancer['LoadBalancerArn']
                
                # Describe tags for the ELB
                elb_tags = client_elbv2.describe_tags(ResourceArns=[load_balancer_arn])['TagDescriptions'][0]['Tags']
                
                # Check if the ELB has the 'map-migrated' tag
                has_map_migrated_tag = any(tag['Key'] == tag_key and tag['Value'] == tag_value for tag in elb_tags)
                
                if has_map_migrated_tag:
                    load_balancers_with_tag.append(load_balancer_arn)
                else:
                    load_balancers_added_tag.append(load_balancer_arn)
                    # Add the 'map-migrated' tag to ELBs without it
                    client_elbv2.add_tags(ResourceArns=[load_balancer_arn], Tags=[{'Key': tag_key, 'Value': tag_value}])

    print("\n\033[1m*** Elastic Load Balancers ***\033[0m")
    print("\nELBs found already tagged:", load_balancers_with_tag)
    print("\nELBs tagged:", load_balancers_added_tag)
    print(f"\n{len(load_balancers_with_tag)} ELBs found already tagged.")
    print(f"{len(load_balancers_added_tag)} ELBs found without proper tags and were tagged with {tag_key}/{tag_value}.\n")



# Function to tag RDS snapshots
def tag_rds_snapshots(tag_key, tag_value, start_date):
    # Create an RDS client
    rds_client = boto3.client('rds')

    rds_snapshots_with_tag = []
    rds_snapshots_added_tag = []

    # Create a paginator for RDS snapshots
    paginator = rds_client.get_paginator('describe_db_snapshots')
    page_iterator = paginator.paginate()

    for page in page_iterator:
        db_snapshots = page['DBSnapshots']

        for snapshot in db_snapshots:
            snapshot_time = snapshot.get("SnapshotCreateTime")
            if snapshot_time and snapshot_time >= start_date:
                # Check if the snapshot already has the specified tag
                rds_tags = rds_client.list_tags_for_resource(ResourceName=snapshot['DBSnapshotArn'])['TagList']
                has_map_migrated_tag = any(tag['Key'] == tag_key and tag['Value'] == tag_value for tag in rds_tags)
                if has_map_migrated_tag:
                    rds_snapshots_with_tag.append(snapshot['DBSnapshotIdentifier'])
                else:
                    rds_snapshots_added_tag.append(snapshot['DBSnapshotIdentifier'])
                    
                    # Add the specified tag to the snapshot
                    rds_client.add_tags_to_resource(
                        ResourceName=snapshot['DBSnapshotArn'],
                        Tags=[{'Key': tag_key, 'Value': tag_value}]
                    )

    print("\n\033[1m*** RDS Snapshots ***\033[0m")
    print("\nRDS Snapshots found already tagged:", rds_snapshots_with_tag)
    print("\nRDS Snapshots tagged:", rds_snapshots_added_tag)
    print(f"\n{len(rds_snapshots_with_tag)} RDS Snapshots found already tagged.")
    print(f"{len(rds_snapshots_added_tag)} RDS Snapshots found without proper tags and were tagged with {tag_key}/{tag_value}.\n")


# Function to tag EFS file systems
def tag_efs(tag_key, tag_value, start_date):
    # Create an EFS client
    efs_client = boto3.client('efs')

    efs_file_systems_with_tag = []
    efs_file_systems_added_tag = []

    # Create a paginator for EFS file systems
    paginator = efs_client.get_paginator('describe_file_systems')
    page_iterator = paginator.paginate()

    for page in page_iterator:
        efs_file_systems = page['FileSystems']

        for efs_file_system in efs_file_systems:
            create_time = efs_file_system.get("CreationTime")
            if create_time and create_time >= start_date:
                # Check if the file system already has the specified tag
                efs_tags = efs_client.describe_tags(FileSystemId=efs_file_system['FileSystemId'])['Tags']
                has_map_migrated_tag = any(tag['Key'] == tag_key and tag['Value'] == tag_value for tag in efs_tags)
                if has_map_migrated_tag:
                    efs_file_systems_with_tag.append(efs_file_system['FileSystemId'])
                else:
                    efs_file_systems_added_tag.append(efs_file_system['FileSystemId'])
                    
                    # Add the specified tag to the file system
                    efs_client.create_tags(
                        FileSystemId=efs_file_system['FileSystemId'],
                        Tags=[{'Key': tag_key, 'Value': tag_value}]
                    )

    print("\n\033[1m*** EFS file systems ***\033[0m")
    print("\nEFS file systems found already tagged:", efs_file_systems_with_tag)
    print("\nEFS file systems tagged:", efs_file_systems_added_tag)
    print(f"\n{len(efs_file_systems_with_tag)} EFS file systems found already tagged.")
    print(f"{len(efs_file_systems_added_tag)} EFS file systems found without proper tags and were tagged with {tag_key}/{tag_value}.\n")


# Function to tag Amazon FSx file systems
def tag_fsx(tag_key, tag_value, start_date):
    # Create an FSx client
    fsx_client = boto3.client('fsx')

    fsx_file_systems_with_tag = []
    fsx_file_systems_added_tag = []

    # Create a paginator for FSx file systems
    paginator = fsx_client.get_paginator('describe_file_systems')
    page_iterator = paginator.paginate()

    for page in page_iterator:
        fsx_file_systems = page['FileSystems']

        for fsx_file_system in fsx_file_systems:
            create_time = fsx_file_system.get("CreationTime")
            if create_time and create_time >= start_date:
                # Check if the file system already has the specified tag
                fsx_tags = fsx_client.list_tags_for_resource(ResourceARN=fsx_file_system['ResourceARN'])['Tags']
                has_map_migrated_tag = any(tag['Key'] == tag_key and tag['Value'] == tag_value for tag in fsx_tags)
                if has_map_migrated_tag:
                    fsx_file_systems_with_tag.append(fsx_file_system['FileSystemId'])
                else:
                    fsx_file_systems_added_tag.append(fsx_file_system['FileSystemId'])
                    
                    # Add the specified tag to the file system
                    fsx_client.tag_resource(
                        ResourceARN=fsx_file_system['ResourceARN'],
                        Tags=[{'Key': tag_key, 'Value': tag_value}]
                    )

    print("\n\033[1m*** FSx file systems ***\033[0m")
    print("\nFSx file systems found already tagged:", fsx_file_systems_with_tag)
    print("\nFSx file systems tagged:", fsx_file_systems_added_tag)
    print(f"\n{len(fsx_file_systems_with_tag)} FSx file systems found already tagged.")
    print(f"{len(fsx_file_systems_added_tag)} FSx file systems found without proper tags and were tagged with {tag_key}/{tag_value}.\n")


# Function to tag DynamoDB tables
def tag_dynamodb_tables(tag_key, tag_value, start_date):
    # Create a DynamoDB client
    dynamodb_client = boto3.client('dynamodb')

    dynamodb_tables_with_tag = []
    dynamodb_tables_added_tag = []

    # List all DynamoDB tables
    paginator = dynamodb_client.get_paginator('list_tables')
    page_iterator = paginator.paginate()

    for page in page_iterator:
        table_names = page['TableNames']

        for table_name in table_names:
            # Get the table creation timestamp
            table_arn = dynamodb_client.describe_table(TableName=table_name)['Table']['TableArn']
            table_description = dynamodb_client.describe_table(TableName=table_name)['Table']
            create_time_str = table_description['CreationDateTime']

            # Use the create_time_str directly (no need to convert)
            if start_date is None or create_time_str >= start_date:
                # Check if the table already has the specified tag
                table_tags = dynamodb_client.list_tags_of_resource(ResourceArn=table_arn)['Tags']

                has_tag = any(tag['Key'] == tag_key and tag['Value'] == tag_value for tag in table_tags)
                if has_tag:
                    dynamodb_tables_with_tag.append(table_name)
                else:
                    dynamodb_tables_added_tag.append(table_name)
                    
                    # Add the specified tag to the table
                    dynamodb_client.tag_resource(
                        ResourceArn=table_arn,
                        Tags=[{'Key': tag_key, 'Value': tag_value}]
                    )

    print("\n\033[1m*** DynamoDB Tables ***\033[0m")
    print("\nDynamoDB Tables found already tagged:", dynamodb_tables_with_tag)
    print("\nDynamoDB Tables tagged:", dynamodb_tables_added_tag)
    print(f"\n{len(dynamodb_tables_with_tag)} DynamoDB Tables found already tagged.")
    print(f"{len(dynamodb_tables_added_tag)} DynamoDB Tables found without proper tags and were tagged with {tag_key}/{tag_value}.\n")


# Function to tag Lambda functions
def tag_lambda_functions(tag_key, tag_value, start_date):
    # Describe all Lambda functions
    
    client = boto3.client('lambda')

    # List all Lambda functions
    functions = client.list_functions()['Functions']

    functions_with_tag = []
    functions_added_tag = []

    for function in functions:
        function_name = function['FunctionName']
        function_arn = function['FunctionArn']

        last_modified_str = function.get("LastModified")
        if last_modified_str:
            # Extract the timestamp part and convert to a datetime object
            last_modified_str = last_modified_str.split(".")[0]  # Remove milliseconds and timezone offset
            last_modified = datetime.strptime(last_modified_str, "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
            
            if last_modified >= start_date:
                tags_dict = client.list_tags(Resource=function_arn)['Tags']
                
                # Check if the Lambda function has the specified tag
                has_map_migrated_tag = tags_dict.get(tag_key) == tag_value
                
                if has_map_migrated_tag:
                    functions_with_tag.append(function_name)
                else:
                    functions_added_tag.append(function_name)
                    # Add or update the 'map-migrated' tag for functions without it or with a different value
                    client.tag_resource(Resource=function_arn, Tags={tag_key: tag_value})

    print("Lambda Functions with 'map-migrated' tag:", functions_with_tag)
    print("Lambda Functions tagged with 'map-migrated':", functions_added_tag)


# Function to tag S3 buckets with pagination
def tag_s3_buckets(tag_key, tag_value, start_date):
    # Tag S3 buckets
    s3_client = boto3.client('s3')

    buckets_already_tagged = []
    buckets_added_tag = []

    # Initialize marker for pagination
    marker = None

    while True:
        try:
            # List S3 buckets with pagination
            list_buckets_params = {}
            if marker:
                list_buckets_params['Marker'] = marker

            response = s3_client.list_buckets(**list_buckets_params)

            # Get the next marker for pagination
            marker = response.get('NextMarker')

            buckets = response['Buckets']

            for bucket in buckets:
                create_time = bucket.get("CreationDate")
                if create_time and create_time >= start_date:
                    try:
                        # Check if the bucket already has existing tags
                        existing_tags = s3_client.get_bucket_tagging(Bucket=bucket['Name']).get('TagSet', [])
                        
                        # Find the tag with the specified key, if it exists
                        existing_tag = next((tag for tag in existing_tags if tag['Key'] == tag_key), None)
                        
                        if existing_tag:
                            # Check if the existing tag has a different value
                            if existing_tag['Value'] != tag_value:
                                # Update the existing tag with the new value
                                existing_tag['Value'] = tag_value
                                s3_client.put_bucket_tagging(
                                    Bucket=bucket['Name'],
                                    Tagging={'TagSet': existing_tags}
                                )
                                buckets_added_tag.append(bucket['Name'])
                            else:
                                buckets_already_tagged.append(bucket['Name'])
                        else:
                            # If the tag does not exist, add it with the new value
                            existing_tags.append({'Key': tag_key, 'Value': tag_value})
                            s3_client.put_bucket_tagging(
                                Bucket=bucket['Name'],
                                Tagging={'TagSet': existing_tags}
                            )
                            buckets_added_tag.append(bucket['Name'])
                    except botocore.exceptions.ClientError as e:
                        # Check if the error code indicates the absence of the tag set
                        if e.response['Error']['Code'] == 'NoSuchTagSet':
                            # If there are no existing tags, add the 'tag_key' with 'tag_value'
                            s3_client.put_bucket_tagging(
                                Bucket=bucket['Name'],
                                Tagging={'TagSet': [{'Key': tag_key, 'Value': tag_value}]}
                            )
                            buckets_added_tag.append(bucket['Name'])
                        else:
                            # Handle other exceptions
                            print(f"An error occurred for bucket {bucket['Name']}: {str(e)}")

            # Check if there are more buckets to list, if not, exit the loop
            if not marker:
                break

        except botocore.exceptions.ClientError as e:
            print(f"An error occurred while listing buckets: {str(e)}")

    print("\n\033[1m*** S3 buckets ***\033[0m")
    print("\nS3 buckets found already tagged:", buckets_already_tagged)
    print("\nS3 buckets tagged:", buckets_added_tag)
    print(f"\n{len(buckets_already_tagged)} S3 buckets found already tagged.")
    print(f"{len(buckets_added_tag)} S3 buckets found without proper tags and were tagged with {tag_key}/{tag_value}.\n")


# Function to tag AWS Backup vaults
def tag_backup_vaults(tag_key, tag_value, start_date):
    # Create an AWS Backup client
    backup_client = boto3.client('backup')

    backup_vaults_with_tag = []
    backup_vaults_added_tag = []

    # Create a paginator for AWS Backup vaults
    paginator = backup_client.get_paginator('list_backup_vaults')
    page_iterator = paginator.paginate()

    for page in page_iterator:
        backup_vaults = page['BackupVaultList']

        for vault in backup_vaults:
            # Get the creation date of the vault
            creation_date = vault['CreationDate']

            # Check if the vault was created after the specified start date
            if creation_date >= start_date:
                # Get the tags associated with the vault
                response = backup_client.list_tags(ResourceArn=vault['BackupVaultArn'])

                # Extract tags from the response
                if 'Tags' in response:
                    if isinstance(response['Tags'], list):
                        backup_tags = response['Tags']
                    elif isinstance(response['Tags'], dict):
                        backup_tags = [{'Key': k, 'Value': v} for k, v in response['Tags'].items()]
                    else:
                        backup_tags = []
                else:
                    backup_tags = []

                # Check if the vault already has the specified tag
                has_correct_tag = any(tag['Key'] == tag_key and tag['Value'] == tag_value for tag in backup_tags)

                if has_correct_tag:
                    backup_vaults_with_tag.append(vault['BackupVaultName'])
                else:
                    # Add the specified tag to the vault
                    backup_client.tag_resource(
                        ResourceArn=vault['BackupVaultArn'],
                        Tags={tag_key: tag_value}
                    )
                    backup_vaults_added_tag.append(vault['BackupVaultName'])

    print("\n\033[1m*** AWS Backup Vaults ***\033[0m")
    print("\nAWS Backup Vaults found already tagged:", backup_vaults_with_tag)
    print("\nAWS Backup Vaults found without proper tags and were tagged with {}/{}.".format(tag_key, tag_value))
    print("\n{} AWS Backup Vaults found already tagged.".format(len(backup_vaults_with_tag)))
    print("{} AWS Backup Vaults found without proper tags and were tagged with {}/{}.\n".format(len(backup_vaults_added_tag), tag_key, tag_value))


# Function to tag AWS Backup plans
def tag_backup_plans(tag_key, tag_value, start_date):
    # Create an AWS Backup client
    backup_client = boto3.client('backup')

    backup_plans_with_tag = []
    backup_plans_added_tag = []

    # Create a paginator for AWS Backup plans
    paginator = backup_client.get_paginator('list_backup_plans')
    page_iterator = paginator.paginate()

    for page in page_iterator:
        backup_plans = page['BackupPlansList']

        for plan in backup_plans:
            # Get the creation date of the plan
            creation_date = plan['CreationDate']

            # Check if the plan was created after the specified start date
            if creation_date >= start_date:
                # Get the tags associated with the plan
                response = backup_client.list_tags(ResourceArn=plan['BackupPlanArn'])

                # Extract tags from the response
                if 'Tags' in response:
                    if isinstance(response['Tags'], list):
                        backup_tags = response['Tags']
                    elif isinstance(response['Tags'], dict):
                        backup_tags = [{'Key': k, 'Value': v} for k, v in response['Tags'].items()]
                    else:
                        backup_tags = []
                else:
                    backup_tags = []

                # Check if the plan already has the specified tag
                has_correct_tag = any(tag['Key'] == tag_key and tag['Value'] == tag_value for tag in backup_tags)

                if has_correct_tag:
                    backup_plans_with_tag.append(plan['BackupPlanName'])
                else:
                    # Add the specified tag to the plan
                    backup_client.tag_resource(
                        ResourceArn=plan['BackupPlanArn'],
                        Tags={tag_key: tag_value}
                    )
                    backup_plans_added_tag.append(plan['BackupPlanName'])

    print("\n\033[1m*** AWS Backup Plans ***\033[0m")
    print("\nAWS Backup Plans found already tagged:", backup_plans_with_tag)
    print("\nAWS Backup Plans found without proper tags and were tagged with {}/{}.".format(tag_key, tag_value))
    print("\n{} AWS Backup Plans found already tagged.".format(len(backup_plans_with_tag)))
    print("{} AWS Backup Plans found without proper tags and were tagged with {}/{}.\n".format(len(backup_plans_added_tag), tag_key, tag_value))


# Function to tag Amazon FSx snapshots
def tag_fsx_snapshots(tag_key, tag_value, start_date):
    # Create an FSx client
    fsx_client = boto3.client('fsx')

    fsx_snapshots_with_tag = []
    fsx_snapshots_added_tag = []

    # Create a paginator for FSx snapshots
    paginator = fsx_client.get_paginator('describe_backups')
    page_iterator = paginator.paginate()

    for page in page_iterator:
        fsx_snapshots = page['Backups']

        for fsx_snapshot in fsx_snapshots:
            create_time = fsx_snapshot.get("CreationTime")
            if create_time and create_time >= start_date:
                # Check if the snapshot already has the specified tag
                fsx_tags = fsx_client.list_tags_for_resource(ResourceARN=fsx_snapshot['ResourceARN'])['Tags']
                has_map_migrated_tag = any(tag['Key'] == tag_key and tag['Value'] == tag_value for tag in fsx_tags)
                if has_map_migrated_tag:
                    fsx_snapshots_with_tag.append(fsx_snapshot['BackupId'])
                else:
                    fsx_snapshots_added_tag.append(fsx_snapshot['BackupId'])
                    
                    # Add the specified tag to the snapshot
                    fsx_client.tag_resource(
                        ResourceARN=fsx_snapshot['ResourceARN'],
                        Tags=[{'Key': tag_key, 'Value': tag_value}]
                    )

    print("\n\033[1m*** FSx Snapshots ***\033[0m")
    print("\nFSx Snapshots found already tagged:", fsx_snapshots_with_tag)
    print("\nFSx Snapshots tagged:", fsx_snapshots_added_tag)
    print(f"\n{len(fsx_snapshots_with_tag)} FSx Snapshots found already tagged.")
    print(f"{len(fsx_snapshots_added_tag)} FSx Snapshots found without proper tags and were tagged with {tag_key}/{tag_value}.\n")


# Function to tag Amazon ECR repositories
def tag_ecr_repositories(tag_key, tag_value, start_date):
    # Create an ECR client
    ecr_client = boto3.client('ecr')

    ecr_repositories_with_tag = []
    ecr_repositories_added_tag = []

    # Create a paginator for ECR repositories
    paginator = ecr_client.get_paginator('describe_repositories')
    page_iterator = paginator.paginate()

    for page in page_iterator:
        ecr_repositories = page['repositories']

        for ecr_repo in ecr_repositories:
            create_time = ecr_repo.get("createdAt")
            if create_time and create_time >= start_date:
                # Check if the repository already has the specified tag
                ecr_tags = ecr_client.list_tags_for_resource(resourceArn=ecr_repo['repositoryArn'])['tags']
                has_map_migrated_tag = any(tag['Key'] == tag_key and tag['Value'] == tag_value for tag in ecr_tags)
                if has_map_migrated_tag:
                    ecr_repositories_with_tag.append(ecr_repo['repositoryName'])
                else:
                    ecr_repositories_added_tag.append(ecr_repo['repositoryName'])
                    
                    # Add the specified tag to the repository
                    ecr_client.tag_resource(
                        resourceArn=ecr_repo['repositoryArn'],
                        tags=[{'Key': tag_key, 'Value': tag_value}]
                    )

    print("\n\033[1m*** Amazon ECR Repositories ***\033[0m")
    print("\nAmazon ECR Repositories found already tagged:", ecr_repositories_with_tag)
    print("\nAmazon ECR Repositories tagged:", ecr_repositories_added_tag)
    print(f"\n{len(ecr_repositories_with_tag)} Amazon ECR Repositories found already tagged.")
    print(f"{len(ecr_repositories_added_tag)} Amazon ECR Repositories found without proper tags and were tagged with {tag_key}/{tag_value}.\n")


# Function to tag Amazon EKS clusters
def tag_eks_clusters(tag_key, tag_value, start_date):
    # Create an EKS client
    eks_client = boto3.client('eks')

    eks_clusters_with_tag = []
    eks_clusters_added_tag = []

    # Create a paginator for EKS clusters
    paginator = eks_client.get_paginator('list_clusters')
    page_iterator = paginator.paginate()

    for page in page_iterator:
        eks_clusters = page['clusters']

        for eks_cluster in eks_clusters:
            create_time = eks_cluster.get("createdAt")
            if create_time and create_time >= start_date:
                # Check if the cluster already has the specified tag
                eks_tags = eks_client.list_tags_for_resource(resourceArn=eks_cluster)['tags']
                has_map_migrated_tag = any(tag['key'] == tag_key and tag['value'] == tag_value for tag in eks_tags)
                if has_map_migrated_tag:
                    eks_clusters_with_tag.append(eks_cluster)
                else:
                    eks_clusters_added_tag.append(eks_cluster)
                    
                    # Add the specified tag to the cluster
                    eks_client.tag_resource(
                        resourceArn=eks_cluster,
                        tags=[{'key': tag_key, 'value': tag_value}]
                    )

    print("\n\033[1m*** Amazon EKS Clusters ***\033[0m")
    print("\nAmazon EKS Clusters found already tagged:", eks_clusters_with_tag)
    print("\nAmazon EKS Clusters tagged:", eks_clusters_added_tag)
    print(f"\n{len(eks_clusters_with_tag)} Amazon EKS Clusters found already tagged.")
    print(f"{len(eks_clusters_added_tag)} Amazon EKS Clusters found without proper tags and were tagged with {tag_key}/{tag_value}.\n")


# Function to tag Amazon ECS clusters
def tag_ecs_clusters(tag_key, tag_value, start_date):
    # Create an ECS client
    ecs_client = boto3.client('ecs')

    ecs_clusters_with_tag = []
    ecs_clusters_added_tag = []

    # Create a paginator for ECS clusters
    paginator = ecs_client.get_paginator('list_clusters')
    page_iterator = paginator.paginate()

    for page in page_iterator:
        ecs_clusters = page['clusterArns']

        for ecs_cluster_arn in ecs_clusters:
            # Extract cluster name from ARN
            ecs_cluster_name = ecs_cluster_arn.split("/")[-1]

            # Describe the cluster to get create time
            ecs_cluster = ecs_client.describe_clusters(clusters=[ecs_cluster_name])['clusters'][0]

            create_time = ecs_cluster.get("createdAt")
            if create_time and create_time >= start_date:
                # Check if the cluster already has the specified tag
                ecs_tags = ecs_client.list_tags_for_resource(resourceArn=ecs_cluster_arn)['tags']
                has_map_migrated_tag = any(tag['key'] == tag_key and tag['value'] == tag_value for tag in ecs_tags)
                if has_map_migrated_tag:
                    ecs_clusters_with_tag.append(ecs_cluster_name)
                else:
                    ecs_clusters_added_tag.append(ecs_cluster_name)
                    
                    # Add the specified tag to the cluster
                    ecs_client.tag_resource(
                        resourceArn=ecs_cluster_arn,
                        tags=[{'key': tag_key, 'value': tag_value}]
                    )

    print("\n\033[1m*** Amazon ECS Clusters ***\033[0m")
    print("\nAmazon ECS Clusters found already tagged:", ecs_clusters_with_tag)
    print("\nAmazon ECS Clusters tagged:", ecs_clusters_added_tag)
    print(f"\n{len(ecs_clusters_with_tag)} Amazon ECS Clusters found already tagged.")
    print(f"{len(ecs_clusters_added_tag)} Amazon ECS Clusters found without proper tags and were tagged with {tag_key}/{tag_value}.\n")


# Function to tag Amazon EMR clusters
def tag_emr_clusters(tag_key, tag_value, start_date):
    # Create an EMR client
    emr_client = boto3.client('emr')

    emr_clusters_with_tag = []
    emr_clusters_added_tag = []

    # Create a paginator for EMR clusters
    paginator = emr_client.get_paginator('list_clusters')
    page_iterator = paginator.paginate()

    for page in page_iterator:
        emr_clusters = page['Clusters']

        for emr_cluster in emr_clusters:
            create_time = emr_cluster['Status']['Timeline']['CreationDateTime']
            if create_time >= start_date:
                # Get detailed information about the cluster
                response = emr_client.describe_cluster(ClusterId=emr_cluster['Id'])

                # Extract tags from the response
                emr_tags = response['Cluster']['Tags']

                # Check if the cluster already has the specified tag
                has_correct_tag = any(tag['Key'] == tag_key and tag['Value'] == tag_value for tag in emr_tags)

                if has_correct_tag:
                    emr_clusters_with_tag.append(emr_cluster['Name'])
                else:
                    emr_clusters_added_tag.append(emr_cluster['Name'])

                    # Add the specified tag to the cluster
                    emr_client.add_tags(
                        ResourceId=emr_cluster['Id'],
                        Tags=[{'Key': tag_key, 'Value': tag_value}]
                    )

    print("\n\033[1m*** Amazon EMR Clusters ***\033[0m")
    print("\nAmazon EMR Clusters found already tagged:", emr_clusters_with_tag)
    print("\nAmazon EMR Clusters tagged:", emr_clusters_added_tag)
    print(f"\n{len(emr_clusters_with_tag)} Amazon EMR Clusters found already tagged.")
    print(f"{len(emr_clusters_added_tag)} Amazon EMR Clusters found without proper tags and were tagged with {tag_key}/{tag_value}.\n")


# Function to tag AWS Transit Gateways
def tag_transit_gateways(tag_key, tag_value, start_date):
    # Create an EC2 Transit Gateway client
    ec2_client = boto3.client('ec2')

    transit_gateways_with_tag = []
    transit_gateways_added_tag = []

    # Create a paginator for Transit Gateways
    paginator = ec2_client.get_paginator('describe_transit_gateways')
    page_iterator = paginator.paginate()

    for page in page_iterator:
        transit_gateways = page['TransitGateways']

        for transit_gateway in transit_gateways:
            create_time = transit_gateway.get("CreationTime")
            if create_time and create_time >= start_date:
                # Check if the Transit Gateway already has the specified tag
                transit_gateway_id = transit_gateway['TransitGatewayId']
                transit_gateway_tags = ec2_client.describe_tags(Filters=[{'Name': 'resource-id', 'Values': [transit_gateway_id]}])['Tags']
                has_map_migrated_tag = any(tag['Key'] == tag_key and tag['Value'] == tag_value for tag in transit_gateway_tags)
                if has_map_migrated_tag:
                    transit_gateways_with_tag.append(transit_gateway_id)
                else:
                    transit_gateways_added_tag.append(transit_gateway_id)
                    
                    # Add the specified tag to the Transit Gateway
                    ec2_client.create_tags(Resources=[transit_gateway_id], Tags=[{'Key': tag_key, 'Value': tag_value}])

    print("\n\033[1m*** AWS Transit Gateways ***\033[0m")
    print("\nAWS Transit Gateways found already tagged:", transit_gateways_with_tag)
    print("\nAWS Transit Gateways tagged:", transit_gateways_added_tag)
    print(f"\n{len(transit_gateways_with_tag)} AWS Transit Gateways found already tagged.")
    print(f"{len(transit_gateways_added_tag)} AWS Transit Gateways found without proper tags and were tagged with {tag_key}/{tag_value}.\n")


# Function to tag AWS Transit Gateway Attachments
def tag_transit_gateway_attachments(tag_key, tag_value, start_date):
    # Create an EC2 Transit Gateway client
    ec2_client = boto3.client('ec2')

    transit_gateway_attachments_with_tag = []
    transit_gateway_attachments_added_tag = []

    # Create a paginator for Transit Gateway Attachments
    paginator = ec2_client.get_paginator('describe_transit_gateway_attachments')
    page_iterator = paginator.paginate()

    for page in page_iterator:
        transit_gateway_attachments = page['TransitGatewayAttachments']

        for attachment in transit_gateway_attachments:
            create_time = attachment.get("CreationTime")
            if create_time and create_time >= start_date:
                # Check if the Transit Gateway Attachment already has the specified tag
                attachment_id = attachment['TransitGatewayAttachmentId']
                attachment_tags = ec2_client.describe_tags(Filters=[{'Name': 'resource-id', 'Values': [attachment_id]}])['Tags']
                has_map_migrated_tag = any(tag['Key'] == tag_key and tag['Value'] == tag_value for tag in attachment_tags)
                if has_map_migrated_tag:
                    transit_gateway_attachments_with_tag.append(attachment_id)
                else:
                    transit_gateway_attachments_added_tag.append(attachment_id)
                    
                    # Add the specified tag to the Transit Gateway Attachment
                    ec2_client.create_tags(Resources=[attachment_id], Tags=[{'Key': tag_key, 'Value': tag_value}])

    print("\n\033[1m*** AWS Transit Gateway Attachments ***\033[0m")
    print("\nAWS Transit Gateway Attachments found already tagged:", transit_gateway_attachments_with_tag)
    print("\nAWS Transit Gateway Attachments tagged:", transit_gateway_attachments_added_tag)
    print(f"\n{len(transit_gateway_attachments_with_tag)} AWS Transit Gateway Attachments found already tagged.")
    print(f"{len(transit_gateway_attachments_added_tag)} AWS Transit Gateway Attachments found without proper tags and were tagged with {tag_key}/{tag_value}.\n")




# Function to tag ALL AWS Transfer Family servers
def tag_transfer_family_servers(tag_key, tag_value):
    # Create an AWS Transfer client
    transfer_client = boto3.client('transfer')

    transfer_servers_with_tag = []
    transfer_servers_added_tag = []

    # Create a paginator for Transfer Family servers
    paginator = transfer_client.get_paginator('list_servers')
    page_iterator = paginator.paginate()

    for page in page_iterator:
        transfer_servers = page['Servers']

        for transfer_server in transfer_servers:
            # Check if the Transfer Family server already has the specified tag
            server_id = transfer_server['ServerId']
            server_tags = transfer_client.list_tags_for_resource(Arn=transfer_server['Arn'])['Tags']

            has_map_migrated_tag = any(tag['Key'] == tag_key and tag['Value'] == tag_value for tag in server_tags)

            if has_map_migrated_tag:
                transfer_servers_with_tag.append(server_id)
            else:
                # Use tag_resource to add or update tags
                transfer_client.tag_resource(Arn=transfer_server['Arn'], Tags=[{'Key': tag_key, 'Value': tag_value}])
                transfer_servers_added_tag.append(server_id)

    print("\n\033[1m*** AWS Transfer Family Servers ***\033[0m")
    print("\nAWS Transfer Family Servers found already tagged:", transfer_servers_with_tag)
    print("\nAWS Transfer Family Servers tagged:", transfer_servers_added_tag)
    print(f"\n{len(transfer_servers_with_tag)} AWS Transfer Family Servers found already tagged.")
    print(f"{len(transfer_servers_added_tag)} AWS Transfer Family Servers found without proper tags and were tagged with {tag_key}/{tag_value}.\n")


# Function to tag WorkSpaces
def tag_workspaces(tag_key, tag_value, start_date):
    workspaces_client = boto3.client('workspaces')
    paginator = workspaces_client.get_paginator('describe_workspaces')

    workspaces_with_tag = []
    workspaces_without_tag = []

    # Iterate through pages of results
    for page in paginator.paginate():
        for workspace in page.get('Workspaces', []):
            create_time = workspace.get("WorkspaceProperties", {}).get("LastKnownUserConnectionTimestamp")
            if create_time and create_time >= start_date:
                workspace_id = workspace.get("WorkspaceId")
                workspaces_with_tag.append(workspace_id)

    # Now, use the same paginator to retrieve all WorkSpaces (without filtering by tag)
    for page in paginator.paginate():
        for workspace in page.get('Workspaces', []):
            create_time = workspace.get("WorkspaceProperties", {}).get("LastKnownUserConnectionTimestamp")
            if create_time and create_time >= start_date:
                workspace_id = workspace.get("WorkspaceId")
                if workspace_id not in workspaces_with_tag:
                    workspaces_without_tag.append(workspace_id)
                    workspaces_client.create_tags(
                        ResourceId=workspace_id,
                        Tags=[
                            {'Key': tag_key, 'Value': tag_value}
                        ]
                    )

    print("\n\033[1m*** WorkSpaces Desktops ***\033[0m")
    print("\nWorkSpaces Desktops found already tagged:", workspaces_with_tag)
    print("\nWorkSpaces Desktops tagged:", workspaces_without_tag)
    print(f"\n{len(workspaces_with_tag)} WorkSpaces Desktops found already tagged.")
    print(f"{len(workspaces_without_tag)} WorkSpaces Desktops found without proper tags and were tagged with {tag_key}/{tag_value}.\n")


# Function to tag REST API Gateways
def tag_rest_api_gateways(tag_key, tag_value, start_date, region):
    apigateway_client = boto3.client('apigateway')
    
    api_gateways_with_tag = []
    api_gateways_without_tag = []

    paginator = apigateway_client.get_paginator('get_rest_apis')

    # Calculate the timestamp for start_date
    start_date_timestamp = start_date.timestamp()

    # Iterate through pages of REST APIs
    for page in paginator.paginate():
        for api in page.get('items', []):
            api_id = api['id']
            api_name = api['name']
            create_time = api['createdDate']

            # Check if the API Gateway is already tagged and created after start_date
            if create_time.timestamp() >= start_date_timestamp:
                tags = apigateway_client.get_tags(resourceArn=f"arn:aws:apigateway:{region}::/restapis/{api_id}")
                if tag_key in tags.get('tags', {}):
                    existing_value = tags['tags'][tag_key]
                    if existing_value != tag_value:
                        # Modify the tag value
                        apigateway_client.untag_resource(
                            resourceArn=f"arn:aws:apigateway:{region}::/restapis/{api_id}",
                            tagKeys=[tag_key]
                        )
                        apigateway_client.tag_resource(
                            resourceArn=f"arn:aws:apigateway:{region}::/restapis/{api_id}",
                            tags={
                                tag_key: tag_value
                            }
                        )
                        api_gateways_without_tag.append(api_name)  # Moved to api_gateways_without_tag
                    else:
                        api_gateways_with_tag.append(api_name)
                else:
                    api_gateways_without_tag.append(api_name)

            else:
                # Tag the API Gateway if it was created before the start_date
                apigateway_client.tag_resource(
                    resourceArn=f"arn:aws:apigateway:{region}::/restapis/{api_id}",
                    tags={
                        tag_key: tag_value
                    }
                )

    print("\n\033[1m*** API Gateways (REST) ***\033[0m")
    print("\nREST API Gateways found already tagged:", api_gateways_with_tag)
    print("\nREST API Gateways tagged:", api_gateways_without_tag)
    print(f"\n{len(api_gateways_with_tag)} REST API Gateways found already tagged.")
    print(f"{len(api_gateways_without_tag)} REST API Gateways found without proper tags and were tagged with {tag_key}/{tag_value}.\n")


# Function to tag HTTP and WebSocket API Gateways
def tag_http_websocket_api_gateways(tag_key, tag_value, start_date, region):
    apigatewayv2_client = boto3.client('apigatewayv2')

    api_gateways_with_tag = []
    api_gateways_without_tag = []

    # Iterate through HTTP and WebSocket APIs
    for api_type in ['HTTP', 'WEBSOCKET']:
        api_paginator = apigatewayv2_client.get_paginator('get_apis')
        for page in api_paginator.paginate():
            for api in page.get('Items', []):
                api_id = api['ApiId']
                api_name = api['Name']
                create_time = api['CreatedDate']

                # Check if the API Gateway is of the specified type and created after start_date
                if api['ProtocolType'] == api_type and create_time >= start_date:
                    tags = apigatewayv2_client.get_tags(ResourceArn=f"arn:aws:apigateway:{region}::/apis/{api_id}")
                    existing_tags = tags.get('Tags', {})

                    # Check if the specified tag and value are not present, and then tag the API Gateway
                    if tag_key not in existing_tags or existing_tags[tag_key] != tag_value:
                        apigatewayv2_client.tag_resource(
                            ResourceArn=f"arn:aws:apigateway:{region}::/apis/{api_id}",
                            Tags={
                                tag_key: tag_value
                            }
                        )
                        api_gateways_without_tag.append(api_name)
                    else:
                        api_gateways_with_tag.append(api_name)

    print("\n\033[1m*** API Gateways (HTTP and WebSocket) ***\033[0m")
    print("\nHTTP and WebSocket API Gateways found already tagged:", api_gateways_with_tag)
    print("\nHTTP and WebSocket API Gateways tagged:", api_gateways_without_tag)
    print(f"\n{len(api_gateways_with_tag)} HTTP and WebSocket API Gateways found already tagged.")
    print(f"{len(api_gateways_without_tag)} HTTP and WebSocket API Gateways found without proper tags and were tagged with {tag_key}/{tag_value}.\n")




# Main functions to tag AWS resources
def main():
    
    process_id = datetime.now().strftime("%Y%m%d%H%M%S")
    account_id = "12345678"
    regions = ["us-east-1","us-west-2"]
    aws_access_key_id = ""
    aws_secret_access_key = ""
    aws_session_token = ""
    tag_key = 'map-migrated'
    tag_value = 'map-2023-11-10'
    start_date_str = '2023-11-10'
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)

    
    # Tag EC2 instances
    
    tagger = classTagger({ "process_id" : process_id, "account_id" : account_id, "regions": regions, "tag_key" : tag_key, "tag_value" : tag_value, "start_date" : start_date })
    tagger.tag_ec2_instances()
    tagger.tag_ebs_volumes()
    tagger.tag_ebs_snapshots()
    tagger.tag_rds_instances()
    
        
    
    '''
    tag_ec2_instances(process_id, account_id, region, aws_access_key_id, aws_secret_access_key, aws_session_token, tag_key, tag_value, start_date, filters)
    
    # Tag EBS volumes
    tag_ebs_volumes(tag_key, tag_value, start_date, filters)

    # Tag EBS snapshots
    tag_ebs_snapshots(tag_key, tag_value, start_date)

    # Tag Elastic Load Balancers
    tag_elbs(tag_key, tag_value, start_date)

    # Tag RDS instances
    tag_rds_instances(tag_key, tag_value, start_date)

    # Tag RDS snapshots
    tag_rds_snapshots(tag_key, tag_value, start_date)

    # Tag Elastic File System (EFS)
    tag_efs(tag_key, tag_value, start_date)

    # Tag Elastic File System (FSx)
    tag_fsx(tag_key, tag_value, start_date)

    # Tag DynamoDB tables
    tag_dynamodb_tables(tag_key, tag_value, start_date)

    # Tag Lambda functions
    tag_lambda_functions(tag_key, tag_value, start_date)

    # Tag S3 buckets
    tag_s3_buckets(tag_key, tag_value, start_date)

    # Tag AWS Backup resources (Backup Vaults)
    tag_backup_vaults(tag_key, tag_value, start_date)

    # Tag AWS Backup resources (Backup Plans)
    tag_backup_plans(tag_key, tag_value, start_date)

    # Tag Amazon FSx snapshots
    tag_fsx_snapshots(tag_key, tag_value, start_date)

    # Tag Amazon ECR repositories
    tag_ecr_repositories(tag_key, tag_value, start_date)

    # Tag Transit Gateways
    tag_transit_gateways(tag_key, tag_value, start_date)

    # Tag AWS Transit Gateway Attachments
    tag_transit_gateway_attachments(tag_key, tag_value, start_date)

    # Tag AWS Transfer Family servers
    tag_transfer_family_servers(tag_key, tag_value)

    # Tag API Gateways
    tag_rest_api_gateways(tag_key, tag_value, start_date, region)
    tag_http_websocket_api_gateways(tag_key, tag_value, start_date, region)

    # Tag WorkSpaces - NOT TESTED PROPERLY
    # tag_workspaces(tag_key, tag_value, start_date)

    # Tag Amazon EKS clusters - NOT TESTED PROPERLY
    # tag_eks_clusters(tag_key, tag_value, start_date)

    # Tag Amazon ECS clusters - NOT TESTED PROPERLY
    # tag_ecs_clusters(tag_key, tag_value, start_date)

    # Tag Amazon EMR - NOT TESTED PROPERLY
    # tag_emr_clusters(tag_key, tag_value, start_date)
    '''

if __name__ == "__main__":
    main()

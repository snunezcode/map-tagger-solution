import boto3
from os import environ
from datetime import datetime, timezone
import botocore
import pymysql.cursors
import json
import logging

class classTagger():
    
    
    ####----| Object Constructor
    def __init__(self, params):
        self.process_id = ""
        self.account = ""
        self.aws_access_key_id = ""
        self.aws_secret_access_key = ""
        self.aws_session_token = ""
        self.tag_key = ""
        self.tag_value = ""
        self.start_date = ""
        self.filters = []
        self.credentials = self.load_credentials()
        self.connection = pymysql.connect(db='db', host="localhost", port=3306, user=self.credentials['user'], passwd=self.credentials['key'])
        self.cursor = self.connection.cursor()  
        self.configuration = {}
        self.initialize()

        
    
    ####----| Object Initialization
    def initialize(self):
        
        try:
            self.process_id = datetime.now().strftime("%Y%m%d%H%M%S")
            formatter = logging.Formatter(fmt='%(asctime)s - %(levelname)s - %(message)s', datefmt="%Y-%m-%d %H:%M:%S")
            logging.basicConfig(filename=f'{self.process_id}.log',format='%(asctime)s %(levelname)s : %(message)s', level=logging.INFO)
            console = logging.StreamHandler()
            console.setFormatter(formatter)
            logging.getLogger().addHandler(console)
            logging.info(f'Initialization...')
            
            file = open('../server/configuration.json')
            self.configuration = json.load(file)
            file.close()
            self.tag_key = self.configuration["TagKey"]
            self.tag_value = self.configuration["TagValue"]
            self.start_date = datetime.strptime(self.configuration["MapDate"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
            self.filters = [{'Name': f'tag:{self.tag_key}', 'Values': [self.tag_value]}]
        except Exception as err:
            logging.error(f'Error : {err}')
        
        
    
        
    ####----| Authentication
    def authentication(self,account):
        try:
            logging.info(f'Account Authentication : {account}...')
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
        except Exception as err:
            logging.error(f'Error : {err}')
        
    
    
    def load_credentials(self):
        try:
            file = open('../server/credentials.json')
            credentials = json.load(file)
            file.close()
            return credentials
        except Exception as err:
            logging.error(f'Error : {err}')
        
    
    ####----| Database Looging 
    def logging(self,record):
        try:
            for resource in record["resources"]:
                sql = "INSERT INTO `tbTaggerRecords` (`process_id`, `account_id`,`region`,`service`,`type`,`resource_name`,`tag_key`,`tag_value`,`creation_date`,`tag_list`,`timestamp`) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                self.cursor.execute(sql, (self.process_id, self.account, record["region"], record["service"],record["type"],resource['name'],self.tag_key,self.tag_value, resource['created'],resource['tags'],datetime.now().strftime("%Y-%m-%d %H:%M:%S") ))
            self.connection.commit()
        except Exception as err:
            logging.error(f'Error : logging : {err}')
    
    
    
    
    ####----| Start Process
    def start_process(self):
        try:
            logging.info(f'Starting Process...')
            for account in self.configuration['Accounts']:
                logging.info(f'Processing Account : {account}')
                self.authentication(account['id'])
                for region in account['regions']:
                    
                    # Tag EC2 instances
                    self.tag_ec2_instances(region)
                
                    # Tag EBS volumes
                    self.tag_ebs_volumes(region)
                
                    # Tag EBS snapshots
                    self.tag_ebs_snapshots(region)
                
                    # Tag Elastic Load Balancers
                    self.tag_elbs(region)
                
                    # Tag RDS instances
                    self.tag_rds_instances(region)
                
                    # Tag RDS snapshots
                    self.tag_rds_snapshots(region)
                
                    # Tag Elastic File System (EFS)
                    self.tag_efs(region)
                
                    # Tag Elastic File System (FSx)
                    self.tag_fsx(region)
                
                    # Tag DynamoDB tables
                    self.tag_dynamodb_tables(region)
                
                    # Tag Lambda functions
                    self.tag_lambda_functions(region)
                
                    # Tag S3 buckets
                    self.tag_s3_buckets(region)
                
                    # Tag AWS Backup resources (Backup Vaults)
                    self.tag_backup_vaults(region)
                
                    # Tag AWS Backup resources (Backup Plans)
                    self.tag_backup_plans(region)
                
                    # Tag Amazon FSx snapshots
                    self.tag_fsx_snapshots(region)
                
                    # Tag Amazon ECR repositories
                    self.tag_ecr_repositories(region)
                
                    # Tag Transit Gateways
                    self.tag_transit_gateways(region)
                
                    # Tag AWS Transit Gateway Attachments
                    self.tag_transit_gateway_attachments(region)
                
                    # Tag AWS Transfer Family servers
                    self.tag_transfer_family_servers(region)
                
                    # Tag API Gateways
                    self.tag_rest_api_gateways(region)
                    self.tag_http_websocket_api_gateways(region)
                
                    # Tag WorkSpaces - NOT TESTED PROPERLY
                    # self.tag_workspaces(region)
                
                    # Tag Amazon EKS clusters - NOT TESTED PROPERLY
                    # self.tag_eks_clusters(region)
                
                    # Tag Amazon ECS clusters - NOT TESTED PROPERLY
                    # self.tag_ecs_clusters(region)
                
                    # Tag Amazon EMR - NOT TESTED PROPERLY
                    # self.tag_emr_clusters(region)
                    
                    
            logging.info(f'Process Completed.')
            
        except Exception as err:
            logging.error(f'Error : start_process :  {err}')
        
        

    ####----| Function to tag EC2 instances
    def tag_ec2_instances(self,region):
        try:
        
            logging.info(f'Region : {region}, Service : {"EC2"}')
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
        
        except Exception as err:
            logging.error(f'Region : {err}')





    ####----| Function to tag EBS volumes
    def tag_ebs_volumes(self,region):
        try:
            logging.info(f'Region : {region}, Service : {"EBS"}')
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
        except Exception as err:
            logging.error(f'Region : {err}')





    ####----| Function to tag EBS Snapshots
    def tag_ebs_snapshots(self,region):
        try:
            logging.info(f'Region : {region}, Service : {"EBS-SNAPSHOT"}')
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
                self.logging({ "region" : region, "service" : "ebs-snapshot", "type" : "1", "resources" : snapshots_with_tag })
                self.logging({ "region" : region, "service" : "ebs-snapshot", "type" : "2", "resources" : snapshots_added_tag })
                self.logging({ "region" : region, "service" : "ebs-snapshot", "type" : "3", "resources" : snapshots_skipped_tag })
        except Exception as err:
            logging.error(f'Region : {err}')
            
            
         
            

    ####----| Function to tag RDS instances
    def tag_rds_instances(self,region):
        try:
            logging.info(f'Region : {region}, Service : {"RDS"}')
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
            
        except Exception as err:
            logging.error(f'Region : {err}')
    
            
            
    
       
            
    ####----| Function to tag Elastic Load Balancers
    def tag_elbs(self,region):
        
        try:
            
            logging.info(f'Region : {region}, Service : {"ELB"}')
            client_elbv2 = boto3.client('elbv2',
                                        aws_access_key_id=self.aws_access_key_id,
                                        aws_secret_access_key=self.aws_secret_access_key,
                                        aws_session_token=self.aws_session_token,
                                        region_name=region)
        
            load_balancers_with_tag = []
            load_balancers_added_tag = []
            load_balancers_skipped_tag = []
        
            # Create a paginator for ELBv2 load balancers
            paginator = client_elbv2.get_paginator('describe_load_balancers')
            page_iterator = paginator.paginate()
        
            for page in page_iterator:
                load_balancers = page.get('LoadBalancers', [])
                for load_balancer in load_balancers:
                    create_time = load_balancer.get("CreatedTime")
                    load_balancer_arn = load_balancer['LoadBalancerArn']
                    elb_tags = client_elbv2.describe_tags(ResourceArns=[load_balancer_arn])['TagDescriptions'][0]['Tags']
                    if create_time and create_time >= self.start_date:
                        
                        # Check if the ELB has the 'map-migrated' tag
                        has_map_migrated_tag = any(tag['Key'] == self.tag_key and tag['Value'] == self.tag_value for tag in elb_tags)
                        
                        if has_map_migrated_tag:
                            load_balancers_with_tag.append({ "name" : load_balancer_arn, "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(elb_tags) })
                        else:
                            load_balancers_added_tag.append({ "name" : load_balancer_arn, "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(elb_tags) })
                            # Add the 'map-migrated' tag to ELBs without it
                            client_elbv2.add_tags(ResourceArns=[load_balancer_arn], Tags=[{'Key': self.tag_key, 'Value': self.tag_value}])
                    else:
                        load_balancers_skipped_tag.append({ "name" : load_balancer_arn, "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(elb_tags) })
                            
                            
            #Logging Tagging Resources
            self.logging({ "region" : region, "service" : "elb", "type" : "1", "resources" : load_balancers_with_tag })
            self.logging({ "region" : region, "service" : "elb", "type" : "2", "resources" : load_balancers_added_tag })
            self.logging({ "region" : region, "service" : "elb", "type" : "3", "resources" : load_balancers_skipped_tag })    
            
        except Exception as err:
            logging.error(f'Region : {err}')
        
            



    ####----| Function to tag RDS snapshots
    def tag_rds_snapshots(self,region):
        try:
            logging.info(f'Region : {region}, Service : {"RDS-SNAPSHOTS"}')
            # Create an RDS client
            rds_client = boto3.client('rds',
                                            aws_access_key_id=self.aws_access_key_id,
                                            aws_secret_access_key=self.aws_secret_access_key,
                                            aws_session_token=self.aws_session_token,
                                            region_name=region)
        
            rds_snapshots_with_tag = []
            rds_snapshots_added_tag = []
            rds_snapshots_skipped_tag = []
        
            # Create a paginator for RDS snapshots
            paginator = rds_client.get_paginator('describe_db_snapshots')
            page_iterator = paginator.paginate()
        
            for page in page_iterator:
                db_snapshots = page['DBSnapshots']
        
                for snapshot in db_snapshots:
                    snapshot_time = snapshot.get("SnapshotCreateTime")
                    rds_tags = rds_client.list_tags_for_resource(ResourceName=snapshot['DBSnapshotArn'])['TagList']
                    
                    if snapshot_time and snapshot_time >= self.start_date:
                        # Check if the snapshot already has the specified tag
                        
                        has_map_migrated_tag = any(tag['Key'] == self.tag_key and tag['Value'] == self.tag_value for tag in rds_tags)
                        if has_map_migrated_tag:
                            rds_snapshots_with_tag.append({ "name" : snapshot['DBSnapshotIdentifier'], "created" : snapshot_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(rds_tags) })
                            
                        else:
                            rds_snapshots_added_tag.append({ "name" : snapshot['DBSnapshotIdentifier'], "created" : snapshot_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(rds_tags) })
                            
                            # Add the specified tag to the snapshot
                            rds_client.add_tags_to_resource(
                                ResourceName=snapshot['DBSnapshotArn'],
                                Tags=[{'Key': self.tag_key, 'Value': self.tag_value}]
                            )
                    else:
                        rds_snapshots_skipped_tag.append({ "name" : snapshot['DBSnapshotIdentifier'], "created" : snapshot_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(rds_tags) })
                            
            #Logging Tagging Resources
            self.logging({ "region" : region, "service" : "rds-snapshot", "type" : "1", "resources" : rds_snapshots_with_tag })
            self.logging({ "region" : region, "service" : "rds-snapshot", "type" : "2", "resources" : rds_snapshots_added_tag })
            self.logging({ "region" : region, "service" : "rds-snapshot", "type" : "3", "resources" : rds_snapshots_skipped_tag }) 
            
        except Exception as err:
            logging.error(f'Region : {err}')
    




    ####----| Function to tag EFS file systems
    def tag_efs(self,region):
        
        try:
            logging.info(f'Region : {region}, Service : {"EFS"}')
            efs_client = boto3.client('efs',
                                            aws_access_key_id=self.aws_access_key_id,
                                            aws_secret_access_key=self.aws_secret_access_key,
                                            aws_session_token=self.aws_session_token,
                                            region_name=region)
        
            efs_file_systems_with_tag = []
            efs_file_systems_added_tag = []
            efs_file_systems_skipped_tag = []
        
            # Create a paginator for EFS file systems
            paginator = efs_client.get_paginator('describe_file_systems')
            page_iterator = paginator.paginate()
        
            for page in page_iterator:
                efs_file_systems = page['FileSystems']
        
                for efs_file_system in efs_file_systems:
                    create_time = efs_file_system.get("CreationTime")
                    efs_tags = efs_client.describe_tags(FileSystemId=efs_file_system['FileSystemId'])['Tags']
                    if create_time and create_time >= self.start_date:
                        # Check if the file system already has the specified tag
                        
                        has_map_migrated_tag = any(tag['Key'] == self.tag_key and tag['Value'] == self.tag_value for tag in efs_tags)
                        if has_map_migrated_tag:
                            efs_file_systems_with_tag.append({ "name" : efs_file_system['FileSystemId'], "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(efs_tags) })
                            
                        else:
                            efs_file_systems_added_tag.append({ "name" : efs_file_system['FileSystemId'], "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(efs_tags) })
                            
                            # Add the specified tag to the file system
                            efs_client.create_tags(
                                FileSystemId=efs_file_system['FileSystemId'],
                                Tags=[{'Key': self.tag_key, 'Value': self.tag_value}]
                            )
                    else:
                        efs_file_systems_skipped_tag.append({ "name" : efs_file_system['FileSystemId'], "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(efs_tags) })
                            
    
            #Logging Tagging Resources
            self.logging({ "region" : region, "service" : "efs", "type" : "1", "resources" : efs_file_systems_with_tag })
            self.logging({ "region" : region, "service" : "efs", "type" : "2", "resources" : efs_file_systems_added_tag })
            self.logging({ "region" : region, "service" : "efs", "type" : "3", "resources" : efs_file_systems_skipped_tag }) 
            
        except Exception as err:
            logging.error(f'Region : {err}')





    ####----| Function to tag Amazon FSx file systems
    def tag_fsx(self,region):
        try:
            logging.info(f'Region : {region}, Service : {"FSX"}')
            fsx_client = boto3.client('fsx',
                                                aws_access_key_id=self.aws_access_key_id,
                                                aws_secret_access_key=self.aws_secret_access_key,
                                                aws_session_token=self.aws_session_token,
                                                region_name=region)
        
            fsx_file_systems_with_tag = []
            fsx_file_systems_added_tag = []
            fsx_file_systems_skipped_tag = []
        
            # Create a paginator for FSx file systems
            paginator = fsx_client.get_paginator('describe_file_systems')
            page_iterator = paginator.paginate()
        
            for page in page_iterator:
                fsx_file_systems = page['FileSystems']
        
                for fsx_file_system in fsx_file_systems:
                    create_time = fsx_file_system.get("CreationTime")
                    fsx_tags = fsx_client.list_tags_for_resource(ResourceARN=fsx_file_system['ResourceARN'])['Tags']
                    if create_time and create_time >= self.start_date:
                        # Check if the file system already has the specified tag
                        has_map_migrated_tag = any(tag['Key'] == self.tag_key and tag['Value'] == self.tag_value for tag in fsx_tags)
                        if has_map_migrated_tag:
                            fsx_file_systems_with_tag.append({ "name" : fsx_file_system['FileSystemId'], "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(fsx_tags) })
                            
                        else:
                            fsx_file_systems_added_tag.append({ "name" : fsx_file_system['FileSystemId'], "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(fsx_tags) })
                            
                            # Add the specified tag to the file system
                            fsx_client.tag_resource(
                                ResourceARN=fsx_file_system['ResourceARN'],
                                Tags=[{'Key': self.tag_key, 'Value': self.tag_value}]
                            )
                    else:
                        fsx_file_systems_skipped_tag.append({ "name" : fsx_file_system['FileSystemId'], "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(fsx_tags) })
                                
            #Logging Tagging Resources
            self.logging({ "region" : region, "service" : "fsx", "type" : "1", "resources" : fsx_file_systems_with_tag })
            self.logging({ "region" : region, "service" : "fsx", "type" : "2", "resources" : fsx_file_systems_added_tag })
            self.logging({ "region" : region, "service" : "fsx", "type" : "3", "resources" : fsx_file_systems_skipped_tag }) 
            
        except Exception as err:
            logging.error(f'Region : {err}')
        




    ####----| Function to tag DynamoDB tables
    def tag_dynamodb_tables(self,region):
        
        try:
            logging.info(f'Region : {region}, Service : {"DYNAMODB"}')
            dynamodb_client = boto3.client('dynamodb',
                                                aws_access_key_id=self.aws_access_key_id,
                                                aws_secret_access_key=self.aws_secret_access_key,
                                                aws_session_token=self.aws_session_token,
                                                region_name=region)
        
            dynamodb_tables_with_tag = []
            dynamodb_tables_added_tag = []
            dynamodb_tables_skipped_tag = []
        
            # List all DynamoDB tables
            paginator = dynamodb_client.get_paginator('list_tables')
            page_iterator = paginator.paginate()
        
            for page in page_iterator:
                table_names = page['TableNames']
        
                for table_name in table_names:
                    # Get the table creation timestamp
                    table_arn = dynamodb_client.describe_table(TableName=table_name)['Table']['TableArn']
                    table_description = dynamodb_client.describe_table(TableName=table_name)['Table']
                    create_time = table_description['CreationDateTime']
                    table_tags = dynamodb_client.list_tags_of_resource(ResourceArn=table_arn)['Tags']
        
                    # Use the create_time_str directly (no need to convert)
                    if create_time is None or create_time >= self.start_date:
                        # Check if the table already has the specified tag
                        
                        has_tag = any(tag['Key'] == self.tag_key and tag['Value'] == self.tag_value for tag in table_tags)
                        if has_tag:
                            dynamodb_tables_with_tag.append({ "name" : table_name, "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(table_tags) })
                            
                        else:
                            dynamodb_tables_added_tag.append({ "name" : table_name, "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(table_tags) })
              
                            # Add the specified tag to the table
                            dynamodb_client.tag_resource(
                                ResourceArn=table_arn,
                                Tags=[{'Key': self.tag_key, 'Value': self.tag_value}]
                            )
                    else:
                        dynamodb_tables_skipped_tag.append({ "name" : table_name, "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(table_tags) })
                            
        
            #Logging Tagging Resources
            self.logging({ "region" : region, "service" : "dynamodb", "type" : "1", "resources" : dynamodb_tables_with_tag })
            self.logging({ "region" : region, "service" : "dynamodb", "type" : "2", "resources" : dynamodb_tables_added_tag })
            self.logging({ "region" : region, "service" : "dynamodb", "type" : "3", "resources" : dynamodb_tables_skipped_tag }) 
        
        except Exception as err:
            logging.error(f'Region : {err}')

  
  
  
  
  
  
    ####----| Function to tag Lambda functions
    def tag_lambda_functions(self,region):
        try:
            logging.info(f'Region : {region}, Service : {"LAMBDA"}')
            client = boto3.client('lambda',
                                                aws_access_key_id=self.aws_access_key_id,
                                                aws_secret_access_key=self.aws_secret_access_key,
                                                aws_session_token=self.aws_session_token,
                                                region_name=region)
        
        
            # List all Lambda functions
            functions = client.list_functions()['Functions']
        
            functions_with_tag = []
            functions_added_tag = []
            functions_skipped_tag = []
        
            for function in functions:
                function_name = function['FunctionName']
                function_arn = function['FunctionArn']
        
                last_modified_str = function.get("LastModified")
                if last_modified_str:
                    # Extract the timestamp part and convert to a datetime object
                    last_modified_str = last_modified_str.split(".")[0]  # Remove milliseconds and timezone offset
                    last_modified = datetime.strptime(last_modified_str, "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
                    tags_dict = client.list_tags(Resource=function_arn)['Tags']
                        
                    if last_modified >= self.start_date:
                        
                        # Check if the Lambda function has the specified tag
                        has_map_migrated_tag = tags_dict.get(self.tag_key) == self.tag_value
                        
                        if has_map_migrated_tag:
                            functions_with_tag.append({ "name" : function_name, "created" : last_modified.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(tags_dict) })
                            
                        else:
                            functions_added_tag.append({ "name" : function_name, "created" : last_modified.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(tags_dict) })
                            
                            # Add or update the 'map-migrated' tag for functions without it or with a different value
                            client.tag_resource(Resource=function_arn, Tags={self.tag_key: self.tag_value})
                    else:
                        functions_skipped_tag.append({ "name" : function_name, "created" : last_modified.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(tags_dict) })
                            
        
            #Logging Tagging Resources
            self.logging({ "region" : region, "service" : "lambda", "type" : "1", "resources" : functions_with_tag })
            self.logging({ "region" : region, "service" : "lambda", "type" : "2", "resources" : functions_added_tag })
            self.logging({ "region" : region, "service" : "lambda", "type" : "3", "resources" : functions_skipped_tag }) 
        
        except Exception as err:
            logging.error(f'Region : {err}')
        





    ####----| Function to tag S3 buckets with pagination
    def tag_s3_buckets(self,region):
        
        
        try:
            logging.info(f'Region : {region}, Service : {"S3"}')
            s3_client = boto3.client('s3',
                                        aws_access_key_id=self.aws_access_key_id,
                                        aws_secret_access_key=self.aws_secret_access_key,
                                        aws_session_token=self.aws_session_token,
                                        region_name=region)
        
            buckets_already_tagged = []
            buckets_added_tag = []
            buckets_skipped_tag = []
        
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
                        try:
                            existing_tags = s3_client.get_bucket_tagging(Bucket=bucket['Name']).get('TagSet', [])
                        except botocore.exceptions.ClientError as e:
                            existing_tags = []
                            logging.error(f'Error on {bucket["Name"]}: {e}')
                                
                        if create_time and create_time >= self.start_date:
                            try:
                                # Check if the bucket already has existing tags
                                
                                # Find the tag with the specified key, if it exists
                                existing_tag = next((tag for tag in existing_tags if tag['Key'] == self.tag_key), None)
                                
                                if existing_tag:
                                    # Check if the existing tag has a different value
                                    if existing_tag['Value'] != self.tag_value:
                                        # Update the existing tag with the new value
                                        existing_tag['Value'] = self.tag_value
                                        s3_client.put_bucket_tagging(
                                            Bucket=bucket['Name'],
                                            Tagging={'TagSet': existing_tags}
                                        )
                                        
                                        buckets_added_tag.append({ "name" : bucket['Name'], "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(existing_tags) })
                            
                                    else:
                                        buckets_already_tagged.append({ "name" : bucket['Name'], "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(existing_tags) })
                            
                                else:
                                    # If the tag does not exist, add it with the new value
                                    existing_tags.append({'Key': self.tag_key, 'Value': self.tag_value})
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
                                        Tagging={'TagSet': [{'Key': self.tag_key, 'Value': self.tag_value}]}
                                    )
                                    buckets_added_tag.append({ "name" : bucket['Name'], "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(existing_tags) })
                            
                                else:
                                    # Handle other exceptions
                                    print(f"An error occurred for bucket {bucket['Name']}: {str(e)}")
                        else:
                            buckets_skipped_tag.append({ "name" : bucket['Name'], "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(existing_tags) })
                            
        
                    # Check if there are more buckets to list, if not, exit the loop
                    if not marker:
                        break
        
                except botocore.exceptions.ClientError as e:
                    print(f"An error occurred while listing buckets: {str(e)}")
            
            #Logging Tagging Resources
            self.logging({ "region" : region, "service" : "s3", "type" : "1", "resources" : buckets_already_tagged })
            self.logging({ "region" : region, "service" : "s3", "type" : "2", "resources" : buckets_added_tag })
            self.logging({ "region" : region, "service" : "s3", "type" : "3", "resources" : buckets_skipped_tag }) 
        
        except Exception as err:
            logging.error(f'Error : {err}')
        
       




    ####----| Function to tag AWS Backup vaults
    def tag_backup_vaults(self,region):
        try:
            logging.info(f'Region : {region}, Service : {"BACKUP-VAULT"}')
            # Create an AWS Backup client
            backup_client = boto3.client('backup',
                                        aws_access_key_id=self.aws_access_key_id,
                                        aws_secret_access_key=self.aws_secret_access_key,
                                        aws_session_token=self.aws_session_token,
                                        region_name=region)
        
            backup_vaults_with_tag = []
            backup_vaults_added_tag = []
            backup_vaults_skipped_tag = []
        
            # Create a paginator for AWS Backup vaults
            paginator = backup_client.get_paginator('list_backup_vaults')
            page_iterator = paginator.paginate()
        
            for page in page_iterator:
                backup_vaults = page['BackupVaultList']
        
                for vault in backup_vaults:
                    # Get the creation date of the vault
                    creation_date = vault['CreationDate']
                    
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
        
                    # Check if the vault was created after the specified start date
                    if creation_date >= self.start_date:
                        
                        # Check if the vault already has the specified tag
                        has_correct_tag = any(tag['Key'] == self.tag_key and tag['Value'] == self.tag_value for tag in backup_tags)
        
                        if has_correct_tag:
                            backup_vaults_with_tag.append({ "name" : vault['BackupVaultName'], "created" : creation_date.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(backup_tags) })
                            
                        else:
                            # Add the specified tag to the vault
                            backup_client.tag_resource(
                                ResourceArn=vault['BackupVaultArn'],
                                Tags={self.tag_key: self.tag_value}
                            )
                            backup_vaults_added_tag.append({ "name" : vault['BackupVaultName'], "created" : creation_date.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(backup_tags) })
                    else:
                        backup_vaults_skipped_tag.append({ "name" : vault['BackupVaultName'], "created" : creation_date.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(backup_tags) })
                            
            
            #Logging Tagging Resources
            self.logging({ "region" : region, "service" : "backup-vault", "type" : "1", "resources" : backup_vaults_with_tag })
            self.logging({ "region" : region, "service" : "backup-vault", "type" : "2", "resources" : backup_vaults_added_tag })
            self.logging({ "region" : region, "service" : "backup-vault", "type" : "3", "resources" : backup_vaults_skipped_tag }) 
        
        except Exception as err:
            logging.error(f'Region : {err}')
     





    ####----| Function to tag AWS Backup plans
    def tag_backup_plans(self,region):
        try:
            logging.info(f'Region : {region}, Service : {"BACKUP-PLAN"}')
            backup_client = boto3.client('backup',
                                        aws_access_key_id=self.aws_access_key_id,
                                        aws_secret_access_key=self.aws_secret_access_key,
                                        aws_session_token=self.aws_session_token,
                                        region_name=region)
        
            backup_plans_with_tag = []
            backup_plans_added_tag = []
            backup_plans_skipped_tag = []
        
            # Create a paginator for AWS Backup plans
            paginator = backup_client.get_paginator('list_backup_plans')
            page_iterator = paginator.paginate()
        
            for page in page_iterator:
                backup_plans = page['BackupPlansList']
        
                for plan in backup_plans:
                    # Get the creation date of the plan
                    creation_date = plan['CreationDate']
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
                        
                    # Check if the plan was created after the specified start date
                    if creation_date >= self.start_date:
        
                        # Check if the plan already has the specified tag
                        has_correct_tag = any(tag['Key'] == self.tag_key and tag['Value'] == self.tag_value for tag in backup_tags)
        
                        if has_correct_tag:
                            backup_plans_with_tag.append({ "name" : plan['BackupPlanName'], "created" : creation_date.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(backup_tags) })
                            
                        else:
                            # Add the specified tag to the plan
                            backup_client.tag_resource(
                                ResourceArn=plan['BackupPlanArn'],
                                Tags={self.tag_key: self.tag_value}
                            )
                            backup_plans_added_tag.append({ "name" : plan['BackupPlanName'], "created" : creation_date.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(backup_tags) })
                    else:
                            backup_plans_skipped_tag.append({ "name" : plan['BackupPlanName'], "created" : creation_date.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(backup_tags) })
                            
        
            #Logging Tagging Resources
            self.logging({ "region" : region, "service" : "backup-plans", "type" : "1", "resources" : backup_plans_with_tag })
            self.logging({ "region" : region, "service" : "backup-plans", "type" : "2", "resources" : backup_plans_added_tag })
            self.logging({ "region" : region, "service" : "backup-plans", "type" : "3", "resources" : backup_plans_skipped_tag }) 
        
        except Exception as err:
            logging.error(f'Region : {err}')
     

    
        
        
        

    ####----| Function to tag Amazon FSx snapshots
    def tag_fsx_snapshots(self,region):
        
        try:
            logging.info(f'Region : {region}, Service : {"FSX-SNAPSHOT"}')
            # Create an FSx client
            fsx_client = boto3.client('fsx',
                                        aws_access_key_id=self.aws_access_key_id,
                                        aws_secret_access_key=self.aws_secret_access_key,
                                        aws_session_token=self.aws_session_token,
                                        region_name=region)
        
            fsx_snapshots_with_tag = []
            fsx_snapshots_added_tag = []
            fsx_snapshots_skipped_tag = []
        
            # Create a paginator for FSx snapshots
            paginator = fsx_client.get_paginator('describe_backups')
            page_iterator = paginator.paginate()
        
            for page in page_iterator:
                fsx_snapshots = page['Backups']
        
                for fsx_snapshot in fsx_snapshots:
                    create_time = fsx_snapshot.get("CreationTime")
                    fsx_tags = fsx_client.list_tags_for_resource(ResourceARN=fsx_snapshot['ResourceARN'])['Tags']
                    if create_time and create_time >= self.start_date:
                        # Check if the snapshot already has the specified tag
                        has_map_migrated_tag = any(tag['Key'] == self.tag_key and tag['Value'] == self.tag_value for tag in fsx_tags)
                        if has_map_migrated_tag:
                            fsx_snapshots_with_tag.append({ "name" : fsx_snapshot['BackupId'], "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(fsx_tags) })
                            
                        else:
                            fsx_snapshots_added_tag.append({ "name" : fsx_snapshot['BackupId'], "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(fsx_tags) })
                            
                            
                            # Add the specified tag to the snapshot
                            fsx_client.tag_resource(
                                ResourceARN=fsx_snapshot['ResourceARN'],
                                Tags=[{'Key': self.tag_key, 'Value': self.tag_value}]
                            )
                    else:
                        fsx_snapshots_skipped_tag.append({ "name" : fsx_snapshot['BackupId'], "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(fsx_tags) })
                            
        
            #Logging Tagging Resources
            self.logging({ "region" : region, "service" : "fsx-snapshot", "type" : "1", "resources" : fsx_snapshots_with_tag })
            self.logging({ "region" : region, "service" : "fsx-snapshot", "type" : "2", "resources" : fsx_snapshots_added_tag })
            self.logging({ "region" : region, "service" : "fsx-snapshot", "type" : "3", "resources" : fsx_snapshots_skipped_tag }) 
        
        except Exception as err:
            logging.error(f'Error : {err}')
     

        
        
        
        
    
        
    ####----| Function to tag Amazon ECR repositories
    def tag_ecr_repositories(self,region):
        try:
            logging.info(f'Region : {region}, Service : {"ECR"}')
            # Create an ECR client
            ecr_client = boto3.client('ecr',
                                        aws_access_key_id=self.aws_access_key_id,
                                        aws_secret_access_key=self.aws_secret_access_key,
                                        aws_session_token=self.aws_session_token,
                                        region_name=region)
        
            ecr_repositories_with_tag = []
            ecr_repositories_added_tag = []
            ecr_repositories_skipped_tag = []
        
            # Create a paginator for ECR repositories
            paginator = ecr_client.get_paginator('describe_repositories')
            page_iterator = paginator.paginate()
        
            for page in page_iterator:
                ecr_repositories = page['repositories']
        
                for ecr_repo in ecr_repositories:
                    create_time = ecr_repo.get("createdAt")
                    ecr_tags = ecr_client.list_tags_for_resource(resourceArn=ecr_repo['repositoryArn'])['tags']
                    if create_time and create_time >= self.start_date:
                        # Check if the repository already has the specified tag
                        has_map_migrated_tag = any(tag['Key'] == self.tag_key and tag['Value'] == self.tag_value for tag in ecr_tags)
                        if has_map_migrated_tag:
                            ecr_repositories_with_tag.append({ "name" : ecr_repo['repositoryName'], "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(ecr_tags) })
                            
                        else:
                            ecr_repositories_added_tag.append({ "name" : ecr_repo['repositoryName'], "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(ecr_tags) })
                            
                            # Add the specified tag to the repository
                            ecr_client.tag_resource(
                                resourceArn=ecr_repo['repositoryArn'],
                                tags=[{'Key': self.tag_key, 'Value': self.tag_value}]
                            )
                    else:
                        ecr_repositories_skipped_tag.append({ "name" : ecr_repo['repositoryName'], "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(ecr_tags) })
                            
        
            #Logging Tagging Resources
            self.logging({ "region" : region, "service" : "ecr", "type" : "1", "resources" : ecr_repositories_with_tag })
            self.logging({ "region" : region, "service" : "ecr", "type" : "2", "resources" : ecr_repositories_added_tag })
            self.logging({ "region" : region, "service" : "ecr", "type" : "3", "resources" : ecr_repositories_skipped_tag }) 
        
        except Exception as err:
            logging.error(f'Error : {err}')
     
     
     
     
     

    ####----| Function to tag Amazon EKS clusters
    def tag_eks_clusters(self,region):
        try:
            logging.info(f'Region : {region}, Service : {"EKS"}')
            # Create an EKS clien
            eks_client = boto3.client('eks',
                                            aws_access_key_id=self.aws_access_key_id,
                                            aws_secret_access_key=self.aws_secret_access_key,
                                            aws_session_token=self.aws_session_token,
                                            region_name=region)
        
            eks_clusters_with_tag = []
            eks_clusters_added_tag = []
            eks_clusters_skipped_tag = []
            
            # Create a paginator for EKS clusters
            paginator = eks_client.get_paginator('list_clusters')
            page_iterator = paginator.paginate()
        
            for page in page_iterator:
                eks_clusters = page['clusters']
        
                for eks_cluster in eks_clusters:
                    create_time = eks_cluster.get("createdAt")
                    eks_tags = eks_client.list_tags_for_resource(resourceArn=eks_cluster)['tags']
                    if create_time and create_time >= self.start_date:
                        # Check if the cluster already has the specified tag
                        has_map_migrated_tag = any(tag['key'] == self.tag_key and tag['value'] == self.tag_value for tag in eks_tags)
                        if has_map_migrated_tag:
                            eks_clusters_with_tag.append({ "name" : eks_cluster, "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(eks_tags) })
                            
                        else:
                            eks_clusters_added_tag.append({ "name" : eks_cluster, "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(eks_tags) })
                           
                            
                            # Add the specified tag to the cluster
                            eks_client.tag_resource(
                                resourceArn=eks_cluster,
                                tags=[{'key': self.tag_key, 'value': self.tag_value}]
                            )
                    else:
                        eks_clusters_skipped_tag.append({ "name" : eks_cluster, "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(eks_tags) })
                           
        
            #Logging Tagging Resources
            self.logging({ "region" : region, "service" : "eks", "type" : "1", "resources" : eks_clusters_with_tag })
            self.logging({ "region" : region, "service" : "eks", "type" : "2", "resources" : eks_clusters_added_tag })
            self.logging({ "region" : region, "service" : "eks", "type" : "3", "resources" : eks_clusters_skipped_tag }) 
        
        except Exception as err:
            logging.error(f'Error : {err}')







    ####----| Function to tag Amazon ECS clusters
    def tag_ecs_clusters(self,region):
        try:
            logging.info(f'Region : {region}, Service : {"ECS"}')
            # Create an ECS client
            ecs_client = boto3.client('ecs',
                                            aws_access_key_id=self.aws_access_key_id,
                                            aws_secret_access_key=self.aws_secret_access_key,
                                            aws_session_token=self.aws_session_token,
                                            region_name=region)
        
            ecs_clusters_with_tag = []
            ecs_clusters_added_tag = []
            ecs_clusters_skipped_tag = []
        
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
                    ecs_tags = ecs_client.list_tags_for_resource(resourceArn=ecs_cluster_arn)['tags']
                        
                    if create_time and create_time >= self.start_date:
                        # Check if the cluster already has the specified tag
                        has_map_migrated_tag = any(tag['key'] == self.tag_key and tag['value'] == self.tag_value for tag in ecs_tags)
                        if has_map_migrated_tag:
                            ecs_clusters_with_tag.append({ "name" : ecs_cluster_name, "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(ecs_tags) })
                            
                        else:
                            ecs_clusters_added_tag.append({ "name" : ecs_cluster_name, "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(ecs_tags) })
                            
                            
                            # Add the specified tag to the cluster
                            ecs_client.tag_resource(
                                resourceArn=ecs_cluster_arn,
                                tags=[{'key': self.tag_key, 'value': self.tag_value}]
                            )
                    else:
                        ecs_clusters_skipped_tag.append({ "name" : ecs_cluster_name, "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(ecs_tags) })
                            
            #Logging Tagging Resources
            self.logging({ "region" : region, "service" : "ecs", "type" : "1", "resources" : ecs_clusters_with_tag })
            self.logging({ "region" : region, "service" : "ecs", "type" : "2", "resources" : ecs_clusters_added_tag })
            self.logging({ "region" : region, "service" : "ecs", "type" : "3", "resources" : ecs_clusters_skipped_tag }) 
        
        except Exception as err:
            logging.error(f'Error : {err}')
    
        




    ####----| Function to tag Amazon EMR clusters
    def tag_emr_clusters(self,region):
        try:
            logging.info(f'Region : {region}, Service : {"EMR"}')
            # Create an EMR client
            emr_client = boto3.client('emr',
                                            aws_access_key_id=self.aws_access_key_id,
                                            aws_secret_access_key=self.aws_secret_access_key,
                                            aws_session_token=self.aws_session_token,
                                            region_name=region)
        
            emr_clusters_with_tag = []
            emr_clusters_added_tag = []
            emr_clusters_skipped_tag = []
        
            # Create a paginator for EMR clusters
            paginator = emr_client.get_paginator('list_clusters')
            page_iterator = paginator.paginate()
        
            for page in page_iterator:
                emr_clusters = page['Clusters']
        
                for emr_cluster in emr_clusters:
                    create_time = emr_cluster['Status']['Timeline']['CreationDateTime']
                    # Extract tags from the response
                    emr_tags = response['Cluster']['Tags']
        
                    if create_time >= self.start_date:
                        # Get detailed information about the cluster
                        response = emr_client.describe_cluster(ClusterId=emr_cluster['Id'])
        
                        # Check if the cluster already has the specified tag
                        has_correct_tag = any(tag['Key'] == self.tag_key and tag['Value'] == self.tag_value for tag in emr_tags)
        
                        if has_correct_tag:
                            emr_clusters_with_tag.append({ "name" : emr_cluster['Name'], "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(emr_tags) })
                            
                        else:
                            emr_clusters_added_tag.append({ "name" : emr_cluster['Name'], "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(emr_tags) })
                            
        
                            # Add the specified tag to the cluster
                            emr_client.add_tags(
                                ResourceId=emr_cluster['Id'],
                                Tags=[{'Key': self.tag_key, 'Value': self.tag_value}]
                            )
                    else:
                        emr_clusters_skipped_tag.append({ "name" : emr_cluster['Name'], "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(emr_tags) })
                            
        
            #Logging Tagging Resources
            self.logging({ "region" : region, "service" : "emr", "type" : "1", "resources" : emr_clusters_with_tag })
            self.logging({ "region" : region, "service" : "emr", "type" : "2", "resources" : emr_clusters_added_tag })
            self.logging({ "region" : region, "service" : "emr", "type" : "3", "resources" : emr_clusters_skipped_tag }) 
        
        except Exception as err:
            logging.error(f'Error : {err}')
    
    
     
     
     


    ####----| Function to tag AWS Transit Gateways
    def tag_transit_gateways(self,region):
        
        try:
            logging.info(f'Region : {region}, Service : {"TRANSIT-GATEWAY"}')
            # Create an EC2 Transit Gateway client
            ec2_client = boto3.client('ec2',
                                            aws_access_key_id=self.aws_access_key_id,
                                            aws_secret_access_key=self.aws_secret_access_key,
                                            aws_session_token=self.aws_session_token,
                                            region_name=region)
        
            transit_gateways_with_tag = []
            transit_gateways_added_tag = []
            transit_gateways_skipped_tag = []
        
            # Create a paginator for Transit Gateways
            paginator = ec2_client.get_paginator('describe_transit_gateways')
            page_iterator = paginator.paginate()
        
            for page in page_iterator:
                transit_gateways = page['TransitGateways']
        
                for transit_gateway in transit_gateways:
                    create_time = transit_gateway.get("CreationTime")
                    transit_gateway_id = transit_gateway['TransitGatewayId']
                    transit_gateway_tags = ec2_client.describe_tags(Filters=[{'Name': 'resource-id', 'Values': [transit_gateway_id]}])['Tags']
                    if create_time and create_time >= self.start_date:
                        # Check if the Transit Gateway already has the specified tag
                        has_map_migrated_tag = any(tag['Key'] == self.tag_key and tag['Value'] == self.tag_value for tag in transit_gateway_tags)
                        if has_map_migrated_tag:
                            transit_gateways_with_tag.append({ "name" : transit_gateway_id, "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(transit_gateway_tags) })
                            
                        else:
                            transit_gateways_added_tag.append({ "name" : transit_gateway_id, "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(transit_gateway_tags) })
                            
                            
                            # Add the specified tag to the Transit Gateway
                            ec2_client.create_tags(Resources=[transit_gateway_id], Tags=[{'Key': self.tag_key, 'Value': self.tag_value}])
                    else:
                        transit_gateways_skipped_tag.append({ "name" : transit_gateway_id, "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(transit_gateway_tags) })
                            
        
            #Logging Tagging Resources
            self.logging({ "region" : region, "service" : "tgtw", "type" : "1", "resources" : transit_gateways_with_tag })
            self.logging({ "region" : region, "service" : "tgtw", "type" : "2", "resources" : transit_gateways_added_tag })
            self.logging({ "region" : region, "service" : "tgtw", "type" : "3", "resources" : transit_gateways_skipped_tag }) 
        
        except Exception as err:
            logging.error(f'Error : {err}')






    ####----| Function to tag AWS Transit Gateway Attachments
    def tag_transit_gateway_attachments(self,region):
        try:
            logging.info(f'Region : {region}, Service : {"TRANSIT-GATEWAY-ATTACHEMENT"}')
            # Create an EC2 Transit Gateway client
            ec2_client = boto3.client('ec2',
                                            aws_access_key_id=self.aws_access_key_id,
                                            aws_secret_access_key=self.aws_secret_access_key,
                                            aws_session_token=self.aws_session_token,
                                            region_name=region)
        
            transit_gateway_attachments_with_tag = []
            transit_gateway_attachments_added_tag = []
            transit_gateway_attachments_skipped_tag = []
        
            # Create a paginator for Transit Gateway Attachments
            paginator = ec2_client.get_paginator('describe_transit_gateway_attachments')
            page_iterator = paginator.paginate()
        
            for page in page_iterator:
                transit_gateway_attachments = page['TransitGatewayAttachments']
        
                for attachment in transit_gateway_attachments:
                    create_time = attachment.get("CreationTime")
                    attachment_id = attachment['TransitGatewayAttachmentId']
                    attachment_tags = ec2_client.describe_tags(Filters=[{'Name': 'resource-id', 'Values': [attachment_id]}])['Tags']
                    if create_time and create_time >= self.start_date:
                        # Check if the Transit Gateway Attachment already has the specified tag
                        has_map_migrated_tag = any(tag['Key'] == self.tag_key and tag['Value'] == self.tag_value for tag in attachment_tags)
                        if has_map_migrated_tag:
                            transit_gateway_attachments_with_tag.append({ "name" : attachment_id, "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(attachment_tags) })
                            
                        else:
                            transit_gateway_attachments_added_tag.append({ "name" : attachment_id, "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(attachment_tags) })
                            
                            
                            # Add the specified tag to the Transit Gateway Attachment
                            ec2_client.create_tags(Resources=[attachment_id], Tags=[{'Key': self.tag_key, 'Value': self.tag_value}])
                            
                    else:
                        transit_gateway_attachments_skipped_tag.append({ "name" : attachment_id, "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(attachment_tags) })
                            
        

            #Logging Tagging Resources
            self.logging({ "region" : region, "service" : "tgtw-attc", "type" : "1", "resources" : transit_gateway_attachments_with_tag })
            self.logging({ "region" : region, "service" : "tgtw-attc", "type" : "2", "resources" : transit_gateway_attachments_added_tag })
            self.logging({ "region" : region, "service" : "tgtw-attc", "type" : "3", "resources" : transit_gateway_attachments_skipped_tag }) 
        
        except Exception as err:
            logging.error(f'Error : {err}')






    ####----| Function to tag ALL AWS Transfer Family servers
    def tag_transfer_family_servers(self,region):
        try:
            logging.info(f'Region : {region}, Service : {"TRANSFER-FAMILY"}')
            # Create an AWS Transfer client
            transfer_client = boto3.client('transfer',
                                            aws_access_key_id=self.aws_access_key_id,
                                            aws_secret_access_key=self.aws_secret_access_key,
                                            aws_session_token=self.aws_session_token,
                                            region_name=region)
        
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
        
                    has_map_migrated_tag = any(tag['Key'] == self.tag_key and tag['Value'] == self.tag_value for tag in server_tags)
        
                    if has_map_migrated_tag:
                        transfer_servers_with_tag.append({ "name" : server_id, "created" : "", "tags" : json.dumps(server_tags) })
                            
                    else:
                        # Use tag_resource to add or update tags
                        transfer_client.tag_resource(Arn=transfer_server['Arn'], Tags=[{'Key': self.tag_key, 'Value': self.tag_value}])
                        transfer_servers_added_tag.append({ "name" : server_id, "created" : "", "tags" : json.dumps(server_tags) })
                        
        
    
            #Logging Tagging Resources
            self.logging({ "region" : region, "service" : "transfer", "type" : "1", "resources" : transfer_servers_with_tag })
            self.logging({ "region" : region, "service" : "transfer", "type" : "2", "resources" : transfer_servers_added_tag })
            
        except Exception as err:
            logging.error(f'Error : {err}')





    ####----| Function to tag WorkSpaces
    def tag_workspaces(self,region):
        try:
            logging.info(f'Region : {region}, Service : {"WORKSPACES"}')
            workspaces_client = boto3.client('workspaces',
                                            aws_access_key_id=self.aws_access_key_id,
                                            aws_secret_access_key=self.aws_secret_access_key,
                                            aws_session_token=self.aws_session_token,
                                            region_name=region)
                                            
            paginator = workspaces_client.get_paginator('describe_workspaces')
        
            workspaces_with_tag = []
            workspaces_without_tag = []
            
            # Iterate through pages of results
            for page in paginator.paginate():
                for workspace in page.get('Workspaces', []):
                    create_time = workspace.get("WorkspaceProperties", {}).get("LastKnownUserConnectionTimestamp")
                    if create_time and create_time >= self.start_date:
                        workspace_id = workspace.get("WorkspaceId")
                        workspaces_with_tag.append({ "name" : workspace_id, "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps([]) })
                            
        
            # Now, use the same paginator to retrieve all WorkSpaces (without filtering by tag)
            for page in paginator.paginate():
                for workspace in page.get('Workspaces', []):
                    create_time = workspace.get("WorkspaceProperties", {}).get("LastKnownUserConnectionTimestamp")
                    if create_time and create_time >= self.start_date:
                        workspace_id = workspace.get("WorkspaceId")
                        if workspace_id not in workspaces_with_tag:
                            workspaces_without_tag.append({ "name" : workspace_id, "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps([]) })
                        
                            workspaces_client.create_tags(
                                ResourceId=workspace_id,
                                Tags=[
                                    {'Key': self.tag_key, 'Value': self.tag_value}
                                ]
                            )
        
            #Logging Tagging Resources
            self.logging({ "region" : region, "service" : "workspaces", "type" : "1", "resources" : workspaces_with_tag })
            self.logging({ "region" : region, "service" : "workspaces", "type" : "2", "resources" : workspaces_without_tag })
            
        except Exception as err:
            logging.error(f'Error : {err}')

        
        
        

    ####----| Function to tag REST API Gateways
    def tag_rest_api_gateways(self,region):
        try:
            logging.info(f'Region : {region}, Service : {"APIGATEWAY"}')
            apigateway_client = boto3.client('apigateway',
                                            aws_access_key_id=self.aws_access_key_id,
                                            aws_secret_access_key=self.aws_secret_access_key,
                                            aws_session_token=self.aws_session_token,
                                            region_name=region)
            
            api_gateways_with_tag = []
            api_gateways_without_tag = []
            api_gateways_skipped_tag = []
        
            paginator = apigateway_client.get_paginator('get_rest_apis')
        
            # Calculate the timestamp for start_date
            start_date_timestamp = self.start_date.timestamp()
        
            # Iterate through pages of REST APIs
            for page in paginator.paginate():
                for api in page.get('items', []):
                    api_id = api['id']
                    api_name = api['name']
                    create_time = api['createdDate']
                    tags = apigateway_client.get_tags(resourceArn=f"arn:aws:apigateway:{region}::/restapis/{api_id}")
                    # Check if the API Gateway is already tagged and created after start_date
                    if create_time >= self.start_date:
                        
                        if self.tag_key in tags.get('tags', {}):
                            existing_value = tags['tags'][self.tag_key]
                            if existing_value != self.tag_value:
                                # Modify the tag value
                                apigateway_client.untag_resource(
                                    resourceArn=f"arn:aws:apigateway:{region}::/restapis/{api_id}",
                                    tagKeys=[self.tag_key]
                                )
                                apigateway_client.tag_resource(
                                    resourceArn=f"arn:aws:apigateway:{region}::/restapis/{api_id}",
                                    tags={
                                        self.tag_key: self.tag_value
                                    }
                                )
                                
                                api_gateways_without_tag.append({ "name" : api_name, "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(tags) })
                            
                            else:
                                api_gateways_with_tag.append({ "name" : api_name, "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(tags) })
                        else:
                            api_gateways_without_tag.append({ "name" : api_name, "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(tags) })
        
                    else:
                        # Tag the API Gateway if it was created before the start_date
                        apigateway_client.tag_resource(
                            resourceArn=f"arn:aws:apigateway:{region}::/restapis/{api_id}",
                            tags={
                                self.tag_key: self.tag_value
                            }
                        )
                        api_gateways_skipped_tag.append({ "name" : api_name, "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(tags) })

            #Logging Tagging Resources
            self.logging({ "region" : region, "service" : "apigateway", "type" : "1", "resources" : api_gateways_with_tag })
            self.logging({ "region" : region, "service" : "apigateway", "type" : "2", "resources" : api_gateways_without_tag })
            self.logging({ "region" : region, "service" : "apigateway", "type" : "3", "resources" : api_gateways_skipped_tag }) 
        
        except Exception as err:
            logging.error(f'Error : {err}')


        
    

    ####----| Function to tag HTTP and WebSocket API Gateways
    def tag_http_websocket_api_gateways(self, region):
        
        try:
            logging.info(f'Region : {region}, Service : {"APIGATEWAY-V2"}')
            apigatewayv2_client = boto3.client('apigatewayv2',
                                            aws_access_key_id=self.aws_access_key_id,
                                            aws_secret_access_key=self.aws_secret_access_key,
                                            aws_session_token=self.aws_session_token,
                                            region_name=region)
        
            api_gateways_with_tag = []
            api_gateways_without_tag = []
            api_gateways_skipped_tag = []
        
            # Iterate through HTTP and WebSocket APIs
            for api_type in ['HTTP', 'WEBSOCKET']:
                api_paginator = apigatewayv2_client.get_paginator('get_apis')
                for page in api_paginator.paginate():
                    for api in page.get('Items', []):
                        api_id = api['ApiId']
                        api_name = api['Name']
                        create_time = api['CreatedDate']
                        tags = apigatewayv2_client.get_tags(ResourceArn=f"arn:aws:apigateway:{region}::/apis/{api_id}")
                        # Check if the API Gateway is of the specified type and created after start_date
                        if api['ProtocolType'] == api_type:
                            
                            if create_time >= self.start_date:
                                existing_tags = tags.get('Tags', {})
                                # Check if the specified tag and value are not present, and then tag the API Gateway
                                if self.tag_key not in existing_tags or existing_tags[self.tag_key] != self.tag_value:
                                    apigatewayv2_client.tag_resource(
                                        ResourceArn=f"arn:aws:apigateway:{region}::/apis/{api_id}",
                                        Tags={
                                            self.tag_key: self.tag_value
                                        }
                                    )
                                    api_gateways_without_tag.append({ "name" : api_name, "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(tags) })
                                else:
                                    api_gateways_with_tag.append({ "name" : api_name, "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(tags) })
                            else:
                                api_gateways_skipped_tag.append({ "name" : api_name, "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(tags) })
        
            #Logging Tagging Resources
            self.logging({ "region" : region, "service" : "apigatewayv2", "type" : "1", "resources" : api_gateways_with_tag })
            self.logging({ "region" : region, "service" : "apigatewayv2", "type" : "2", "resources" : api_gateways_without_tag })
            self.logging({ "region" : region, "service" : "apigatewayv2", "type" : "3", "resources" : api_gateways_skipped_tag }) 
        
        except Exception as err:
            logging.error(f'Error : {err}')
        



####----| Main Function
def main():
    # Start Tagging Process
    tagger = classTagger({})
    tagger.start_process()
    
    
    
####----| Call Main Function
if __name__ == "__main__":
    main()

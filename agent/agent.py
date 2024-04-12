import boto3
from os import environ
from datetime import datetime, timezone
import botocore
import pymysql.cursors
import json

class classTagger():
    
    # constructor
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
        self.connection = pymysql.connect(db='db',user='root', unix_socket="/var/lib/mysql/mysql.sock")
        self.cursor = self.connection.cursor()  
        self.configuration = {}
        self.initialize()

    def initialize(self):
        file = open('../server/configuration.json')
        self.configuration = json.load(file)
        file.close()
        self.tag_key = self.configuration["TagKey"]
        self.tag_value = self.configuration["TagValue"]
        self.start_date = datetime.strptime(self.configuration["MapDate"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
        self.filters = [{'Name': f'tag:{self.tag_key}', 'Values': [self.tag_value]}]
        self.process_id = datetime.now().strftime("%Y%m%d%H%M%S")
        
        
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
    
    
    # Processing Tags
    def tag_processing(self,pages,object_type_field,object_id_field,launch_time_field):
        
        for account in self.configuration['Accounts']:
            self.authentication(account['id'])
        
            for region in account['regions']:
                ec2_client = boto3.client('ec2',
                                            aws_access_key_id=self.aws_access_key_id,
                                            aws_secret_access_key=self.aws_secret_access_key,
                                            aws_session_token=self.aws_session_token,
                                            region_name=region)
                item_with_tag = []
                item_added_tag = []
                item_skipped_tag = []
            
                # Create a paginator for EBS snapshots
                paginator = ec2_client.get_paginator('describe_snapshots')
                page_iterator = paginator.paginate(OwnerIds=['self'])
            
                item_with_tag = []
                item_added_tag = []
                item_skipped_tag = []
            
                for page in pages:
                    objects = page.get(object_type_field, [])
                    for item in objects:
                        create_time = item.get(launch_time_field)
                        tags = item.get("Tags")  if "Tags" in item else []
                        if create_time and create_time >= self.start_date:
                            # Check if the snapshot has the 'map-migrated' tag
                            has_map_migrated_tag = any(tag['Key'] == self.tag_key and tag['Value'] == self.tag_value for tag in tags)
                            if has_map_migrated_tag:
                                item_with_tag.append({ "name" : item[object_id_field], "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(tags) })
                            else:
                                item_added_tag.append({ "name" : item[object_id_field], "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(tags) })
                                # Add the 'map-migrated' tag to snapshots without it
                                ec2_client.create_tags(Resources=[item[object_id_field]], Tags=[{'Key': self.tag_key, 'Value': self.tag_value}])
                        else:
                            item_skipped_tag.append({ "name" : item[object_id_field], "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(tags) })
                            
                    #Logging Tagging Resources
                    self.logging({ "region" : region, "service" : "snapshot", "type" : "1", "resources" : item_with_tag })
                    self.logging({ "region" : region, "service" : "snapshot", "type" : "2", "resources" : item_added_tag })
                    self.logging({ "region" : region, "service" : "snapshot", "type" : "3", "resources" : item_skipped_tag })

        
        

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
            
            


# Main Function
def main():
    
    # Start Tagging Process
    tagger = classTagger({})
    tagger.tag_ec2_instances()
    tagger.tag_ebs_volumes()
    tagger.tag_ebs_snapshots()
    tagger.tag_rds_instances()
    
if __name__ == "__main__":
    main()

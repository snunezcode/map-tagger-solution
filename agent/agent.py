import boto3
from os import environ
from datetime import datetime, timezone
import botocore
import pymysql.cursors
import json
import logging
import sys
import time



####----|
####----| className : classAWSObject
####----|

class classLogging():

    ####----| Object Constructor
    def __init__(self,object):
        self.object = object
    
    ####----| Object Init
    def initialize(self,process_id):
        formatter = logging.Formatter(fmt='%(asctime)s - %(levelname)s - %(message)s', datefmt="%Y-%m-%d %H:%M:%S")
        logging.basicConfig(filename=f'{process_id}.log',format='%(asctime)s %(levelname)s : %(message)s', level=logging.INFO)
        console = logging.StreamHandler()
        console.setFormatter(formatter)
        logging.getLogger().addHandler(console)
        
    ####----| Write Info 
    def info(self,message):
        try:
            logging.info(message)
        except Exception as err:
            logging.error(f'Object : {self.object}, Error : {err}')
            
    
    ####----| Write Error 
    def error(self,message):
        try:
            logging.error(f'Object : {self.object}, Error : {message}')
        except Exception as err:
            logging.error(f'Object : {self.object}, Error : {err}')
            
            


    

####----|
####----| className : classDatabase
####----|

class classDatabase():
    
    
    ####----| Object Constructor
    def __init__(self):
        self.logging = classLogging("classDatabase")
        self.credentials = self.load_credentials()
        self.connection = pymysql.connect(db='db', host="localhost", port=3306, user=self.credentials['user'], passwd=self.credentials['key'])
        self.cursor = self.connection.cursor()  
        
    
    
    ####----| Load database credentials        
    def load_credentials(self):
        try:
            file = open('../server/credentials.json')
            credentials = json.load(file)
            file.close()
            return credentials
        except Exception as err:
            self.logging.error(f'Error : {err}')
            
    
    ####----| Create master inventory process 
    def create_master_inventory_process(self,record):
        try:
            
            sql = "INSERT INTO `tbTaggingProcess` (`process_id`, `inventory_status`, `inventory_start_date`,`inventory_items_total`, `inventory_items_completed`, `tagging_items_total`, `tagging_items_completed`, `configuration`) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
            self.cursor.execute(sql, (record['process_id'], "Started", datetime.now().strftime("%Y-%m-%d %H:%M:%S"),record["items_total"], 0,record["items_total"], 0, record["configuration"] ))
            self.connection.commit()
        except Exception as err:
            self.logging.error(f'Error : create_master_inventory_process : {err}')
               
    
    ####----| Update master inventory process 
    def update_master_inventory_process(self,record):
        try:
            
            sql = "UPDATE `tbTaggingProcess` SET `inventory_status` = %s, `inventory_message` = %s, `inventory_items_completed` = %s, `inventory_end_date` = %s WHERE `process_id` = %s "
            self.cursor.execute(sql, (record['status'], record['message'], record['items_completed'], datetime.now().strftime("%Y-%m-%d %H:%M:%S"), record["process_id"] ))
            self.connection.commit()
        except Exception as err:
            self.logging.error(f'Error : update_master_inventory_process : {err}')
    
    
    ####----| Create master tagging process 
    def create_master_tagging_process(self,record):
        try:
            
            sql = "UPDATE `tbTaggingProcess` SET `tagging_status` = %s, `tagging_start_date` = %s WHERE `process_id` = %s "
            self.cursor.execute(sql, ("Started", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), record['process_id'] ))
            self.connection.commit()
        except Exception as err:
            self.logging.error(f'Error : create_master_tagging_process : {err}')
               
    
    ####----| Update master tagging process 
    def update_master_tagging_process(self,record):
        try:
            
            sql = "UPDATE `tbTaggingProcess` SET `tagging_status` = %s, `tagging_message` = %s, `tagging_items_completed` = %s, `tagging_end_date` = %s WHERE `process_id` = %s "
            self.cursor.execute(sql, (record['status'], record['message'], record['items_completed'], datetime.now().strftime("%Y-%m-%d %H:%M:%S"), record["process_id"] ))
            self.connection.commit()
        except Exception as err:
            self.logging.error(f'Error : update_master_tagging_process : {err}')
    
    
    ####----| Register tagging resorces 
    def register_inventory_resources(self,resources):
        try:
            for resource in resources:
                sql = "INSERT INTO `tbTaggingRecords` (`process_id`, `account_id`,`region`,`service`,`type`,`identifier`, `resource_name`,`arn`,`tag_key`,`tag_value`,`creation_date`,`tag_list`,`timestamp`) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                self.cursor.execute(sql, (resource['process_id'], resource['account'], resource["region"], resource["service"],resource["type"],resource['identifier'],resource['resource_name'],resource['arn'],resource['tag_key'],resource['tag_value'], resource['created'],resource['tags'],datetime.now().strftime("%Y-%m-%d %H:%M:%S") ))
            self.connection.commit()
        except Exception as err:
            self.logging.error(f'Error : register_inventory_resources : {err}')
    
    
          
    ####----| Get tagging resorces 
    def get_tagging_resources(self,process_id,account,region,service):
        try:
            
            sql = "SELECT * FROM tbTaggingRecords WHERE process_id = %s AND account_id = %s AND region = %s AND service = %s AND ( type = 2 OR type = 4 )"
            #AND type = '2'
            self.cursor.execute(sql, (process_id,account,region,service))
            columns = self.cursor.description 
            result = [{columns[index][0]:column for index, column in enumerate(value)} for value in self.cursor.fetchall()]
            return result
        except Exception as err:
            self.logging.error(f'Error : get_tagging_resources : {err}')
            return []
            
            


    

####----|
####----| className : classAWSObject
####----|

class classAWSConnector():

    ####----| Object Constructor
    def __init__(self):
        self.account = ""
        self.aws_access_key_id = ""
        self.aws_secret_access_key = ""
        self.aws_session_token = ""
        self.logging = classLogging('classAWSConnector')
    
        
    
    
    ####----| Authentication
    def authentication(self,account):
        try:
            self.account = account
            self.aws_access_key_id = ""
            self.aws_secret_access_key = ""
            self.aws_session_token = ""
            sts_client = boto3.client('sts',region_name="us-east-1")
            assumed_role_object = sts_client.assume_role(
                RoleArn=f"arn:aws:iam::{account}:role/MAPTaggingProcessRole",
                RoleSessionName="CrossAccountSession"
            )
            credentials = assumed_role_object['Credentials']
            self.aws_access_key_id = credentials['AccessKeyId']
            self.aws_secret_access_key = credentials['SecretAccessKey']
            self.aws_session_token = credentials['SessionToken']
            return True
        except Exception as err:
            self.logging.error(f'authentication : {err}')
            return False
            
            
    ####----| Get AWS Client
    def get_aws_client(self,region,service):
        try:
            client = boto3.client(service,
                                    aws_access_key_id=self.aws_access_key_id,
                                    aws_secret_access_key=self.aws_secret_access_key,
                                    aws_session_token=self.aws_session_token,
                                    region_name=region)
            return client
            
        except Exception as err:
            self.logging.error(f'get_aws_client : {err}')
            return None


    ####----| Create tag by service
    def manage_tag_by_service(self,account,region,service,sub_service,resources,tags):
        try:
            self.authentication(account)
            self.logging.info(f'Tagging  # Account : {account}, Region : {region}, Service : {sub_service}')
            client = boto3.client(service,
                                    aws_access_key_id=self.aws_access_key_id,
                                    aws_secret_access_key=self.aws_secret_access_key,
                                    aws_session_token=self.aws_session_token,
                                    region_name=region)
            
            for resource in resources:
                
                
                if sub_service == 'ec2' or sub_service == 'ebs_volume' or sub_service == 'ebs_snapshot' or sub_service == 'tgw' or sub_service == 'tgw_att':
                    if resource['action'] == '2':
                        client.create_tags(
                                        Resources=[resource['identifier']],
                                        Tags=tags
                        )
                    elif resource['action'] == '4':
                        client.delete_tags(
                                        Resources=[resource['identifier']],
                                        Tags=tags
                        )
                
                
                elif sub_service == 'rds' or sub_service == 'rds_snapshot':
                    if resource['action'] == '2':
                        client.add_tags_to_resource(
                                    ResourceName=resource['arn'],
                                    Tags=tags
                        )
                    elif resource['action'] == '4':
                        client.remove_tags_from_resource(
                                    ResourceName=resource['arn'],
                                    TagKeys=[tags[0]['Key']]
                        )
                        
                
                elif sub_service == 'elbv2' :
                    if resource['action'] == '2':
                        client.add_tags(
                                    ResourceArns=[resource['arn']],
                                    Tags=tags
                        )
                        
                    elif resource['action'] == '4':
                        client.remove_tags(
                                    ResourceArns=[resource['arn']],
                                    TagKeys=[tags[0]['Key']]
                        )
                        
                elif sub_service == 'efs' :
                    if resource['action'] == '2':
                        client.create_tags(
                                    FileSystemId=resource['identifier'],
                                    Tags=tags
                        )
                        
                    elif resource['action'] == '4':
                        client.delete_tags(
                                    FileSystemId=resource['identifier'],
                                    TagKeys=[tags[0]['Key']]
                        )
        
        
                elif sub_service == 'fsx' or sub_service == 'fsx_snapshot':
                    if resource['action'] == '2':
                        client.tag_resource(
                                    ResourceARN=resource['arn'],
                                    Tags=tags
                        )
                        
                    elif resource['action'] == '4':
                        client.untag_resource(
                                    ResourceARN=resource['arn'],
                                    TagKeys=[tags[0]['Key']]
                        )


                elif sub_service == 'dynamodb':
                    if resource['action'] == '2':
                        client.tag_resource(
                                    ResourceArn=resource['arn'],
                                    Tags=tags
                        )
                        
                    elif resource['action'] == '4':
                        client.untag_resource(
                                    ResourceArn=resource['arn'],
                                    TagKeys=[tags[0]['Key']]
                        )
                        
                        
                elif sub_service == 'lambda':
                    print(tags)
                    if resource['action'] == '2':
                        client.tag_resource(
                                    Resource=resource['arn'],
                                    Tags={ tags[0]['Key'] :  tags[0]['Value'] }
                        )
                        
                    elif resource['action'] == '4':
                        client.untag_resource(
                                    Resource=resource['arn'],
                                    TagKeys=[tags[0]['Key']]
                        )
                
                
                elif sub_service == 's3':
                    if resource['action'] == '2':
                        client.put_bucket_tagging(
                                            Bucket=resource['identifier'],
                                            Tagging={'TagSet': json.loads(resource['tags']) }
                                        )
                        
                    elif resource['action'] == '4':
                        tags = json.loads(resource['tags'])
                        tags = [d for d in tags if d["Key"] != resource['tag_key']]
                        client.put_bucket_tagging(
                                            Bucket=resource['identifier'],
                                            Tagging={'TagSet': tags  }
                                        )
                
                
                elif sub_service == 'backup_vault' or sub_service == 'backup_plan':
                    if resource['action'] == '2':
                        client.tag_resource(
                                    ResourceArn=resource['arn'],
                                    Tags={ tags[0]['Key'] :  tags[0]['Value'] }
                        )
                    elif resource['action'] == '4':
                        client.untag_resource(
                                    ResourceArn=resource['arn'],
                                    TagKeyList=[tags[0]['Key']]
                        )
                        
                
                elif sub_service == 'ecr':
                    if resource['action'] == '2':
                        client.tag_resource(
                                    resourceArn=resource['arn'],
                                    tags=tags
                        )
                        
                    elif resource['action'] == '4':
                        client.untag_resource(
                                    resourceArn=resource['arn'],
                                    tagKeys=[tags[0]['Key']]
                        )
                        
                
                elif sub_service == 'eks':
                    if resource['action'] == '2':
                        client.tag_resource(
                                    resourceArn=resource['arn'],
                                    tags={ tags[0]['Key'] :  tags[0]['Value'] }
                        )
                        
                    elif resource['action'] == '4':
                        client.untag_resource(
                                    resourceArn=resource['arn'],
                                    tagKeys=[tags[0]['Key']]
                        )
                        
                
                elif sub_service == 'ecs':
                    if resource['action'] == '2':
                        client.tag_resource(
                                    resourceArn=resource['arn'],
                                    tags=[{ 'key' : tags[0]['Key'], 'value' : tags[0]['Value']  }]
                        )
                        
                    elif resource['action'] == '4':
                        client.untag_resource(
                                    resourceArn=resource['arn'],
                                    tagKeys=[tags[0]['Key']]
                        )
                        
                
                elif sub_service == 'emr':
                    if resource['action'] == '2':
                        client.add_tags(
                                ResourceId=resource['identifier'],
                                Tags=tags
                            )
                        
                    elif resource['action'] == '4':
                        client.remove_tags(
                                    ResourceId=resource['identifier'],
                                    TagKeys=[tags[0]['Key']]
                        )
                        
                        
                elif sub_service == 'tfs':
                    if resource['action'] == '2':
                        client.tag_resource(
                                    Arn=resource['arn'],
                                    Tags=tags
                        )
                        
                    elif resource['action'] == '4':
                        client.untag_resource(
                                    Arn=resource['arn'],
                                    TagKeys=[tags[0]['Key']]
                        )
                        
                        
                elif sub_service == 'api_gtw':
                    if resource['action'] == '2':
                        client.tag_resource(
                                    resourceArn=resource['arn'],
                                    tags={ tags[0]['Key'] :  tags[0]['Value'] }
                        )
                        
                    elif resource['action'] == '4':
                        client.untag_resource(
                                    resourceArn=resource['arn'],
                                    tagKeys=[tags[0]['Key']]
                        )
                        
                
                
                elif sub_service == 'api_gtw_ws':
                    if resource['action'] == '2':
                        client.tag_resource(
                                    ResourceArn=resource['arn'],
                                    Tags={ tags[0]['Key'] :  tags[0]['Value'] }
                        )
                        
                    elif resource['action'] == '4':
                        client.untag_resource(
                                    ResourceArn=resource['arn'],
                                    TagKeys=[tags[0]['Key']]
                        )
                
                
                elif sub_service == 'workspaces':
                    if resource['action'] == '2':
                        client.create_tags(
                                    ResourceId=resource['identifier'],
                                    Tags=tags
                        )
                        
                    elif resource['action'] == '4':
                        client.delete_tags(
                                    ResourceId=resource['arn'],
                                    TagKeys=[tags[0]['Key']]
                        )
                
        except Exception as err:
            self.logging.error(f'manage_tag_by_service :  {err}')
            return[]
    
            
    
    ####----| Get Active Sessions
    def get_active_regions(self):
        try:
            # Create an EC2 client
            client = boto3.client('ec2',
                                        aws_access_key_id=self.aws_access_key_id,
                                        aws_secret_access_key=self.aws_secret_access_key,
                                        aws_session_token=self.aws_session_token,
                                        region_name="us-east-1")
                                        
            # Get all available regions
            regions = client.describe_regions()['Regions']
            
            # Filter out the opt-in regions
            active_regions = [region['RegionName'] for region in regions if region['OptInStatus'] in ['opt-in-not-required', 'opted-in'] ]
        
            return active_regions
            
        except Exception as err:
            self.logging.error(f'get_active_regions :  {err}')
            return[]

   


####----|
####----| className : classTagger
####----|

class classTagger():
    
    
    ####----| Object Constructor
    def __init__(self,process_id):
        #self.process_id = datetime.now().strftime("%Y%m%d%H%M%S")
        self.process_id = process_id
        self.account = ""
        self.aws_access_key_id = ""
        self.aws_secret_access_key = ""
        self.aws_session_token = ""
        self.tag_key = ""
        self.tag_value = ""
        self.start_date = ""
        self.filters = []
        self.configuration = {}
        self.logging = classLogging('classTagger')
        self.logging.initialize(self.process_id)
        self.database = classDatabase()
        self.aws = classAWSConnector()
        self.initialize()

        
    
    ####----| Object Initialization
    def initialize(self):
        
        try:
            self.logging.info(f'Initialization...')
            file = open('../server/configuration.json')
            self.configuration = json.load(file)
            file.close()
            self.tag_key = self.configuration["TagKey"]
            self.tag_value = self.configuration["TagValue"]
            self.start_date = datetime.strptime(self.configuration["MapDate"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
            self.filters = [{'Name': f'tag:{self.tag_key}', 'Values': [self.tag_value]}]
        except Exception as err:
            self.logging.error(f'initialize : {err}')
    
    
    ###----| Get active regions
    def get_active_regions(self):
        
        try:
            self.logging.info(f'Getting active regions')
            client = self.aws.get_aws_client(region,"ec2")
            
            regions = client.describe_regions()['Regions']
            
            active_regions = [region['RegionName'] for region in regions if region['OptInStatus'] in ['opt-in-not-required', 'opted-in'] ]
        
            return active_regions
            
        except Exception as err:
            self.logging.error(f'get_active_regions :  {err}')
            return[]
            
        
    
        
    ####----| Start Inventory Process
    def start_inventory_process(self):
        items_completed = 0
        try:
            
            # Create master inventory process
            self.logging.info(f'Starting Inventory Process...')
            self.database.create_master_inventory_process({ "process_id" : self.process_id, "configuration" : json.dumps(self.configuration) , "items_total" : len(self.configuration['Accounts']) })
            
            for account in self.configuration['Accounts']:
                self.logging.info(f'Processing Account : {account}')
                if (self.aws.authentication(account['id'])):
                    active_regions = self.aws.get_active_regions()
                    self.logging.info(f'Active regions : {active_regions}')
                    for region in account['regions']:
                        if region in active_regions:
                            
                            ## EC2 Resources
                            self.get_inventory_ec2(account['id'],region)
                            
                            ## EBS Volumes Resources
                            self.get_inventory_ebs_volumes(account['id'],region)
                            
                            ## EBS Snapshots Resources
                            self.get_inventory_ebs_snapshots(account['id'],region)
                            
                            ## RDS Resources
                            self.get_inventory_rds(account['id'],region)
                            
                            ## RDS Snapshots Resources
                            self.get_inventory_rds_snapshots(account['id'],region)
                            
                            ## ELB Resources
                            self.get_inventory_elbs(account['id'],region)
                            
                            ## EFS Resources
                            self.get_inventory_efs(account['id'],region)
                            
                            ## FSX Resources
                            self.get_inventory_fsx(account['id'],region)
                            
                            ## FSX Snapshots Resources
                            self.get_inventory_fsx_snapshots(account['id'],region)
                            
                            ## DynamoDB Resources
                            self.get_inventory_dynamodb(account['id'],region)
                            
                            ## Lambda Resources
                            self.get_inventory_lambda(account['id'],region)
                            
                            ## S3 Resources
                            self.get_inventory_s3(account['id'],region)
                            
                            ## Backup Vault Resources
                            self.get_inventory_backup_vaults(account['id'],region)
                            
                            ## Backup Plans Resources
                            self.get_inventory_backup_plans(account['id'],region)
                            
                            ## Backup Plans Resources
                            self.get_inventory_ecr(account['id'],region)
                            
                            ## EKS Resources
                            self.get_inventory_eks_clusters(account['id'],region)
                            
                            ## ECS Resources
                            self.get_inventory_ecs_clusters(account['id'],region)
                            
                            ## EMR Resources
                            self.get_inventory_emr_clusters(account['id'],region)
                            
                            ## Transit Gateways Resources
                            self.get_inventory_transit_gateways(account['id'],region)
                            
                            ## Transit Gateways Attachment Resources
                            self.get_inventory_transit_gateway_attachments(account['id'],region)
                            
                            ## Transfer Family Resources
                            self.get_inventory_transfer_family_servers(account['id'],region)
                            
                            ## Transfer Family Resources
                            self.get_inventory_api_gateways(account['id'],region)
                            
                            ## Transfer Family Resources
                            self.get_inventory_api_gateway_websockets(account['id'],region)
                            
                            ## Workspaces Resources
                            self.get_inventory_workspaces(account['id'],region)
                            
                        else:
                            self.logging.info(f'The region : {region} is not active')
                        
                        
                ## Update Progress
                items_completed = items_completed + 1
                self.database.update_master_inventory_process({ "process_id" : self.process_id, "status" : "In-Progress", "message" : f'Account {account["id"]} processed.', "items_completed" :  items_completed })
            
            self.database.update_master_inventory_process({ "process_id" : self.process_id, "status" : "Completed", "message" : f'{items_completed} accounts processed.', "items_completed" :  items_completed })
            self.logging.info(f'Discovery # Process Completed.')
            
        except Exception as err:
            self.logging.error(f'start_inventory_process :  {err}')
        




    ####----| Start Tagging Process
    def start_tagging_process(self,process_id):
        
        try:
            
            self.process_id = process_id
            self.logging.info(f'Starting Tagging Process...')
            tags = [{'Key': self.tag_key, 'Value': self.tag_value}]
            items_completed = 0    
            
            # List of services
            services = [
                        { "primary" : "ec2", "secondary" : "ec2" },
                        { "primary" : "ec2", "secondary" : "ebs_volume" },
                        { "primary" : "ec2", "secondary" : "ebs_snapshot" },
                        { "primary" : "rds", "secondary" : "rds" },
                        { "primary" : "rds", "secondary" : "rds_snapshot" },
                        { "primary" : "elbv2", "secondary" : "elbv2" },
                        { "primary" : "efs", "secondary" : "efs" },
                        { "primary" : "fsx", "secondary" : "fsx" },
                        { "primary" : "fsx", "secondary" : "fsx_snapshot" },
                        { "primary" : "dynamodb", "secondary" : "dynamodb" },
                        { "primary" : "lambda", "secondary" : "lambda" },
                        { "primary" : "s3", "secondary" : "s3" },
                        { "primary" : "backup", "secondary" : "backup_vault" },
                        { "primary" : "backup", "secondary" : "backup_plan" },
                        { "primary" : "ecr", "secondary" : "ecr" },
                        { "primary" : "eks", "secondary" : "eks" },
                        { "primary" : "ecs", "secondary" : "ecs" },
                        { "primary" : "emr", "secondary" : "emr" },
                        { "primary" : "ec2", "secondary" : "tgw" },
                        { "primary" : "ec2", "secondary" : "tgw_att" },
                        { "primary" : "transfer", "secondary" : "tfs" },
                        { "primary" : "apigateway", "secondary" : "api_gtw" },
                        { "primary" : "apigatewayv2", "secondary" : "api_gtw_ws" },
                        { "primary" : "workspaces", "secondary" : "workspaces" },
                ]
            
            # Create master tagging process
            self.database.create_master_tagging_process({ "process_id" : self.process_id })
            
            for account in self.configuration['Accounts']:
                self.logging.info(f'Processing Account : {account}')
                if (self.aws.authentication(account['id'])):
                    active_regions = self.aws.get_active_regions()
                    self.logging.info(f'Active regions : {active_regions}')
                    for region in account['regions']:
                        
                        ### List of services
                        for service in services:
                            resources = []
                            recordset = self.database.get_tagging_resources(self.process_id, account['id'], region, service['secondary'])
                            for record in recordset:
                                resources.append({ "identifier" : record['identifier'], "action" : record['type'], "arn" : record['arn'], "tags" : record['tag_list'], "tag_key" : record['tag_key'] })
                            self.aws.manage_tag_by_service(account['id'], region, service['primary'], service['secondary'], resources, tags)
                        
                else:
                    self.logging.error(f'start_tagging_process : authentication account error')
                    
                ## Update Progress
                items_completed = items_completed + 1
                self.database.update_master_tagging_process({ "process_id" : self.process_id, "status" : "In-Progress", "message" : f'Account {account["id"]} processed.', "items_completed" :  items_completed })
                
            
            self.database.update_master_tagging_process({ "process_id" : self.process_id, "status" : "Completed", "message" : f'{items_completed} accounts processed.', "items_completed" :  items_completed })
            self.logging.info(f'Tagging # Process Completed.')
            
        except Exception as err:
            self.logging.error(f'start_tagging_process :  {err}')
        
    

           
           
    
    
    ###----| Function to validate tag exists
    def tag_exists(self,tags):
        result = any(tag['Key'] == self.tag_key and tag['Value'] == self.tag_value for tag in tags)
        return result      
    
    
    ###----| Function to validate tag key exists
    def tag_key_exists(self,tags):
        result = any(tag['Key'] == self.tag_key for tag in tags)
        return result      
    
    
    
    ###----| Function to get resource name
    def get_resource_name(self,tags):
        name = ""
        for tag in tags:
            if tag["Key"] == 'Name' or tag["Key"] == 'name':
                name = tag["Value"]
        return name
    
    
    ###----| Function to validate tag key exists
    def tag_exists_dict(self,tags):
        if tags.get(self.tag_key) == self.tag_value:
            return True
        else:
            return False
        
        
    ###----| Function to get resource name
    def get_resource_name_dict(self,tags):
        return (tags.get("Name") if "Name" in tags else "")
        
        
        
    ###----| Function to convert tag keys
    def tag_key_convertion(self,tags,key,value):
        tag_convertion = []
        for tag in tags:
            tag_convertion.append({ 'Key' : tag[key], 'Value' : tag[value] })
        return tag_convertion



    ###----| Function to convert tags dict to list
    def tags_dict_to_list(self,tags):
        tag_convertion = []
        for key, value in tags.items():
            tag_convertion.append({ 'Key' : key, 'Value' : value })
        return tag_convertion






    ####----| Function to get inventory for EC2 instances
    def get_inventory_ec2(self,account,region):
        try:
        
            self.logging.info(f'Discovery # Account : {account}, Region : {region}, Service : {"ec2"}')
            client = self.aws.get_aws_client(region,"ec2")
        
            paginator = client.get_paginator('describe_instances')
            resources = []
            
            for page in paginator.paginate():
                for reservation in page.get('Reservations', []):
                    for instance in reservation.get('Instances', []):
                        create_time = instance.get("LaunchTime")
                        identifier = instance.get("InstanceId")
                        arn = f'arn:aws:ec2:{region}:{account}:instance/{instance.get("InstanceId")}' 
                        tags = instance.get("Tags")  if "Tags" in instance else []
                        resource_name = self.get_resource_name(tags)
                        if create_time and create_time >= self.start_date:
                            if not self.tag_exists(tags):
                                resources.append({ "process_id" : self.process_id, "account" : account, "region" : region, "service" : "ec2", "type" : "2", "identifier" : identifier, "resource_name" : resource_name, "arn" : arn, "tag_key" : self.tag_key , "tag_value" : self.tag_value, "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(tags) })
                            else:
                                resources.append({ "process_id" : self.process_id, "account" : account, "region" : region, "service" : "ec2", "type" : "1", "identifier" : identifier, "resource_name" : resource_name, "arn" : arn, "tag_key" : self.tag_key , "tag_value" : self.tag_value, "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(tags) })
                        else:
                            resources.append({ "process_id" : self.process_id, "account" : account, "region" : region, "service" : "ec2", "type" : "3", "identifier" : identifier, "resource_name" : resource_name, "arn" : arn, "tag_key" : self.tag_key , "tag_value" : self.tag_value, "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(tags) })
        
            #Recording resources
            self.database.register_inventory_resources(resources)
            
        
        except Exception as err:
            self.logging.error(f'get_inventory_ec2 : {err}')
            
    
    
    
    ####----| Function to get inventory for EBS volumen
    def get_inventory_ebs_volumes(self,account,region):
        try:
        
            self.logging.info(f'Discovery # Account : {account}, Region : {region}, Service : {"ebs_volumes"}')
            client = self.aws.get_aws_client(region,"ec2")
        
            paginator = client.get_paginator('describe_volumes')
            resources = []
            
            for page in paginator.paginate():
                for resource in page.get('Volumes', []):
                    create_time = resource.get("CreateTime")
                    identifier = resource.get("VolumeId")
                    arn = f'arn:aws:ec2:{region}:{account}:volume/{resource.get("VolumeId")}' 
                    tags = resource.get("Tags")  if "Tags" in resource else []
                    resource_name = self.get_resource_name(tags)
                    if create_time and create_time >= self.start_date:
                        if not self.tag_exists(tags):
                            resources.append({ "process_id" : self.process_id, "account" : account, "region" : region, "service" : "ebs_volume", "type" : "2", "identifier" : identifier, "resource_name" : resource_name, "arn" : arn, "tag_key" : self.tag_key , "tag_value" : self.tag_value, "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(tags) })
                        else:
                            resources.append({ "process_id" : self.process_id, "account" : account, "region" : region, "service" : "ebs_volume", "type" : "1", "identifier" : identifier, "resource_name" : resource_name, "arn" : arn, "tag_key" : self.tag_key , "tag_value" : self.tag_value, "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(tags) })
                    else:
                        resources.append({ "process_id" : self.process_id, "account" : account, "region" : region, "service" : "ebs_volume", "type" : "3", "identifier" : identifier, "resource_name" : resource_name, "arn" : arn, "tag_key" : self.tag_key , "tag_value" : self.tag_value, "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(tags) })
    
            #Recording resources
            self.database.register_inventory_resources(resources)
            
        
        except Exception as err:
            self.logging.error(f'get_inventory_ebs_volumes : {err}')
            
    
    ####----| Function to get inventory for EBS Snapshot
    def get_inventory_ebs_snapshots(self,account,region):
        try:
        
            self.logging.info(f'Discovery # Account : {account}, Region : {region}, Service : {"ebs_snapshots"}')
            client = self.aws.get_aws_client(region,"ec2")
        
            paginator = client.get_paginator('describe_snapshots')
            resources = []
            
            for page in paginator.paginate(OwnerIds=['self']):
                for resource in page.get('Snapshots', []):
                    create_time = resource.get("StartTime")
                    identifier = resource.get("SnapshotId")
                    arn = f'arn:aws:ec2:{region}:{account}:snapshot/{resource.get("SnapshotId")}' 
                    tags = resource.get("Tags")  if "Tags" in resource else []
                    resource_name = self.get_resource_name(tags)
                    if create_time and create_time >= self.start_date:
                        if not self.tag_exists(tags):
                            resources.append({ "process_id" : self.process_id, "account" : account, "region" : region, "service" : "ebs_snapshot", "type" : "2", "identifier" : identifier, "resource_name" : resource_name, "arn" : arn, "tag_key" : self.tag_key , "tag_value" : self.tag_value, "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(tags) })
                        else:
                            resources.append({ "process_id" : self.process_id, "account" : account, "region" : region, "service" : "ebs_snapshot", "type" : "1", "identifier" : identifier, "resource_name" : resource_name, "arn" : arn, "tag_key" : self.tag_key , "tag_value" : self.tag_value, "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(tags) })
                    else:
                        resources.append({ "process_id" : self.process_id, "account" : account, "region" : region, "service" : "ebs_snapshot", "type" : "3", "identifier" : identifier, "resource_name" : resource_name, "arn" : arn, "tag_key" : self.tag_key , "tag_value" : self.tag_value, "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(tags) })
    
            #Recording resources
            self.database.register_inventory_resources(resources)
            
        except Exception as err:
            self.logging.error(f'get_inventory_ebs_snapshots : {err}')
            
   
   
     ####----| Function to get inventory for RDS Instances
    def get_inventory_rds(self,account,region):
        try:
        
            self.logging.info(f'Discovery # Account : {account}, Region : {region}, Service : {"rds"}')
            client = self.aws.get_aws_client(region,"rds")
        
            paginator = client.get_paginator('describe_db_instances')
            resources = []
            
            for page in paginator.paginate():
                instances = page['DBInstances']
                for resource in instances:
                        create_time = resource.get("InstanceCreateTime")
                        identifier = resource.get("DBInstanceIdentifier")
                        arn = resource['DBInstanceArn']
                        tags = client.list_tags_for_resource(ResourceName=resource['DBInstanceArn'])['TagList']
                        resource_name = self.get_resource_name(tags)
                        if create_time and create_time >= self.start_date:
                            if not self.tag_exists(tags):
                                resources.append({ "process_id" : self.process_id, "account" : account, "region" : region, "service" : "rds", "type" : "2", "identifier" : identifier, "resource_name" : resource_name, "arn" : arn, "tag_key" : self.tag_key , "tag_value" : self.tag_value, "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(tags) })
                            else:
                                resources.append({ "process_id" : self.process_id, "account" : account, "region" : region, "service" : "rds", "type" : "1", "identifier" : identifier, "resource_name" : resource_name, "arn" : arn, "tag_key" : self.tag_key , "tag_value" : self.tag_value, "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(tags) })
                        else:
                            resources.append({ "process_id" : self.process_id, "account" : account, "region" : region, "service" : "rds", "type" : "3", "identifier" : identifier, "resource_name" : resource_name, "arn" : arn, "tag_key" : self.tag_key , "tag_value" : self.tag_value, "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(tags) })
        
            #Recording resources
            self.database.register_inventory_resources(resources)
            
        
        except Exception as err:
            self.logging.error(f'get_inventory_rds : {err}')
            
    
    
    
    
    
    ####----| Function to get inventory for RDS Snapshots
    def get_inventory_rds_snapshots(self,account,region):
        try:
        
            self.logging.info(f'Discovery # Account : {account}, Region : {region}, Service : {"rds_snapshots"}')
            client = self.aws.get_aws_client(region,"rds")
        
            paginator = client.get_paginator('describe_db_snapshots')
            resources = []
            
            for page in paginator.paginate():
                snapshots = page['DBSnapshots']
                for resource in snapshots:
                        create_time = resource.get("SnapshotCreateTime")
                        identifier = resource.get("DBSnapshotIdentifier")
                        arn = resource['DBSnapshotArn']
                        tags = client.list_tags_for_resource(ResourceName=resource['DBSnapshotArn'])['TagList']
                        resource_name = self.get_resource_name(tags)
                        if create_time and create_time >= self.start_date:
                            if not self.tag_exists(tags):
                                resources.append({ "process_id" : self.process_id, "account" : account, "region" : region, "service" : "rds_snapshot", "type" : "2", "identifier" : identifier, "resource_name" : resource_name, "arn" : arn, "tag_key" : self.tag_key , "tag_value" : self.tag_value, "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(tags) })
                            else:
                                resources.append({ "process_id" : self.process_id, "account" : account, "region" : region, "service" : "rds_snapshot", "type" : "1", "identifier" : identifier, "resource_name" : resource_name, "arn" : arn, "tag_key" : self.tag_key , "tag_value" : self.tag_value, "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(tags) })
                        else:
                            resources.append({ "process_id" : self.process_id, "account" : account, "region" : region, "service" : "rds_snapshot", "type" : "3", "identifier" : identifier, "resource_name" : resource_name, "arn" : arn, "tag_key" : self.tag_key , "tag_value" : self.tag_value, "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(tags) })
        
            #Recording resources
            self.database.register_inventory_resources(resources)
            
        
        except Exception as err:
            self.logging.error(f'get_inventory_rds_snapshots : {err}')
            
    
    
            
            
    ####----| Function to get inventory for ELB
    def get_inventory_elbs(self,account,region):
        try:
        
            self.logging.info(f'Discovery # Account : {account}, Region : {region}, Service : {"elbv2"}')
            client = self.aws.get_aws_client(region,"elbv2")
        
            paginator = client.get_paginator('describe_load_balancers')
            resources = []

            for page in paginator.paginate():
                resource_list = page.get('LoadBalancers', [])
                for resource in resource_list:
                        create_time = resource['CreatedTime']
                        identifier = resource['LoadBalancerName']
                        arn = resource['LoadBalancerArn']
                        tags = client.describe_tags(ResourceArns=[arn])['TagDescriptions'][0]['Tags']
                        resource_name = self.get_resource_name(tags)
                        if create_time and create_time >= self.start_date:
                            if not self.tag_exists(tags):
                                resources.append({ "process_id" : self.process_id, "account" : account, "region" : region, "service" : "elbv2", "type" : "2", "identifier" : identifier, "resource_name" : resource_name, "arn" : arn, "tag_key" : self.tag_key , "tag_value" : self.tag_value, "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(tags) })
                            else:
                                resources.append({ "process_id" : self.process_id, "account" : account, "region" : region, "service" : "elbv2", "type" : "1", "identifier" : identifier, "resource_name" : resource_name, "arn" : arn, "tag_key" : self.tag_key , "tag_value" : self.tag_value, "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(tags) })
                        else:
                            resources.append({ "process_id" : self.process_id, "account" : account, "region" : region, "service" : "elbv2", "type" : "3", "identifier" : identifier, "resource_name" : resource_name, "arn" : arn, "tag_key" : self.tag_key , "tag_value" : self.tag_value, "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(tags) })
                        
            #Recording resources
            self.database.register_inventory_resources(resources)
            
        
        except Exception as err:
            self.logging.error(f'get_inventory_elbs : {err}')
    
    
    
    
            
    
    ####----| Function to get inventory for EFS
    def get_inventory_efs(self,account,region):
        try:
        
            self.logging.info(f'Discovery # Account : {account}, Region : {region}, Service : {"efs"}')
            client = self.aws.get_aws_client(region,"efs")
        
            paginator = client.get_paginator('describe_file_systems')
            resources = []

            for page in paginator.paginate():
                resource_list = page.get('FileSystems', [])
                for resource in resource_list:
                        create_time = resource['CreationTime']
                        identifier = resource['FileSystemId']
                        arn = resource['FileSystemArn']
                        tags = client.describe_tags(FileSystemId=identifier)['Tags']
                        resource_name = self.get_resource_name(tags)
                        if create_time and create_time >= self.start_date:
                            if not self.tag_exists(tags):
                                resources.append({ "process_id" : self.process_id, "account" : account, "region" : region, "service" : "efs", "type" : "2", "identifier" : identifier, "resource_name" : resource_name, "arn" : arn, "tag_key" : self.tag_key , "tag_value" : self.tag_value, "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(tags) })
                            else:
                                resources.append({ "process_id" : self.process_id, "account" : account, "region" : region, "service" : "efs", "type" : "1", "identifier" : identifier, "resource_name" : resource_name, "arn" : arn, "tag_key" : self.tag_key , "tag_value" : self.tag_value, "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(tags) })
                        else:
                            resources.append({ "process_id" : self.process_id, "account" : account, "region" : region, "service" : "efs", "type" : "3", "identifier" : identifier, "resource_name" : resource_name, "arn" : arn, "tag_key" : self.tag_key , "tag_value" : self.tag_value, "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(tags) })
                        
            #Recording resources
            self.database.register_inventory_resources(resources)
            
        
        except Exception as err:
            self.logging.error(f'get_inventory_efs : {err}')
            
            
            
    
    ####----| Function to get inventory for FSX
    def get_inventory_fsx(self,account,region):
        try:
        
            self.logging.info(f'Discovery # Account : {account}, Region : {region}, Service : {"fsx"}')
            client = self.aws.get_aws_client(region,"fsx")
        
            paginator = client.get_paginator('describe_file_systems')
            resources = []

            for page in paginator.paginate():
                resource_list = page.get('FileSystems', [])
                for resource in resource_list:
                        create_time = resource['CreationTime']
                        identifier = resource['FileSystemId']
                        arn = resource['ResourceARN']
                        tags = client.list_tags_for_resource(ResourceARN=arn)['Tags']
                        resource_name = self.get_resource_name(tags)
                        if create_time and create_time >= self.start_date:
                            if not self.tag_exists(tags):
                                resources.append({ "process_id" : self.process_id, "account" : account, "region" : region, "service" : "fsx", "type" : "2", "identifier" : identifier, "resource_name" : resource_name, "arn" : arn, "tag_key" : self.tag_key , "tag_value" : self.tag_value, "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(tags) })
                            else:
                                resources.append({ "process_id" : self.process_id, "account" : account, "region" : region, "service" : "fsx", "type" : "1", "identifier" : identifier, "resource_name" : resource_name, "arn" : arn, "tag_key" : self.tag_key , "tag_value" : self.tag_value, "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(tags) })
                        else:
                            resources.append({ "process_id" : self.process_id, "account" : account, "region" : region, "service" : "fsx", "type" : "3", "identifier" : identifier, "resource_name" : resource_name, "arn" : arn, "tag_key" : self.tag_key , "tag_value" : self.tag_value, "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(tags) })
                        
            #Recording resources
            self.database.register_inventory_resources(resources)
            
        
        except Exception as err:
            self.logging.error(f'get_inventory_fsx : {err}')
    
    
    
    ####----| Function to get inventory for FSX Snapshots
    def get_inventory_fsx_snapshots(self,account,region):
        try:
        
            self.logging.info(f'Discovery # Account : {account}, Region : {region}, Service : {"fsx_snapshot"}')
            client = self.aws.get_aws_client(region,"fsx")
        
            paginator = client.get_paginator('describe_backups')
            resources = []

            for page in paginator.paginate():
                resource_list = page.get('Backups', [])
                for resource in resource_list:
                        create_time = resource['CreationTime']
                        identifier = resource['BackupId']
                        arn = resource['ResourceARN']
                        tags = client.list_tags_for_resource(ResourceARN=arn)['Tags']
                        resource_name = self.get_resource_name(tags)
                        if create_time and create_time >= self.start_date:
                            if not self.tag_exists(tags):
                                resources.append({ "process_id" : self.process_id, "account" : account, "region" : region, "service" : "fsx_backup", "type" : "2", "identifier" : identifier, "resource_name" : resource_name, "arn" : arn, "tag_key" : self.tag_key , "tag_value" : self.tag_value, "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(tags) })
                            else:
                                resources.append({ "process_id" : self.process_id, "account" : account, "region" : region, "service" : "fsx_backup", "type" : "1", "identifier" : identifier, "resource_name" : resource_name, "arn" : arn, "tag_key" : self.tag_key , "tag_value" : self.tag_value, "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(tags) })
                        else:
                            resources.append({ "process_id" : self.process_id, "account" : account, "region" : region, "service" : "fsx_backup", "type" : "3", "identifier" : identifier, "resource_name" : resource_name, "arn" : arn, "tag_key" : self.tag_key , "tag_value" : self.tag_value, "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(tags) })
                        
            #Recording resources
            self.database.register_inventory_resources(resources)
            
        
        except Exception as err:
            self.logging.error(f'get_inventory_fsx_snapshots : {err}')
    
    
    
    
    
    
    
    ####----| Function to get inventory for DynamoDB
    def get_inventory_dynamodb(self,account,region):
        try:
        
            self.logging.info(f'Discovery # Account : {account}, Region : {region}, Service : {"dynamodb"}')
            client = self.aws.get_aws_client(region,"dynamodb")
        
            paginator = client.get_paginator('list_tables')
            resources = []

            for page in paginator.paginate():
                resource_list = page.get('TableNames', [])
                for resource in resource_list:
                        table_info = client.describe_table(TableName=resource)['Table']
                        create_time = table_info['CreationDateTime']
                        identifier = resource
                        arn = table_info['TableArn']
                        tags = client.list_tags_of_resource(ResourceArn=arn)['Tags']
                        resource_name = self.get_resource_name(tags)
                        if create_time and create_time >= self.start_date:
                            if not self.tag_exists(tags):
                                resources.append({ "process_id" : self.process_id, "account" : account, "region" : region, "service" : "dynamodb", "type" : "2", "identifier" : identifier, "resource_name" : resource_name, "arn" : arn, "tag_key" : self.tag_key , "tag_value" : self.tag_value, "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(tags) })
                            else:
                                resources.append({ "process_id" : self.process_id, "account" : account, "region" : region, "service" : "dynamodb", "type" : "1", "identifier" : identifier, "resource_name" : resource_name, "arn" : arn, "tag_key" : self.tag_key , "tag_value" : self.tag_value, "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(tags) })
                        else:
                            resources.append({ "process_id" : self.process_id, "account" : account, "region" : region, "service" : "dynamodb", "type" : "3", "identifier" : identifier, "resource_name" : resource_name, "arn" : arn, "tag_key" : self.tag_key , "tag_value" : self.tag_value, "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(tags) })
                        
            #Recording resources
            self.database.register_inventory_resources(resources)
            
        
        except Exception as err:
            self.logging.error(f'get_inventory_dynamodb : {err}')






    ####----| Function to get inventory for Lambda
    def get_inventory_lambda(self,account,region):
        try:
        
            self.logging.info(f'Discovery # Account : {account}, Region : {region}, Service : {"lambda"}')
            client = self.aws.get_aws_client(region,"lambda")
        
            resource_list = client.list_functions()['Functions']
            resources = []

            for resource in resource_list:
                    last_modified_str = resource['LastModified']
                    last_modified_str = last_modified_str.split(".")[0]  # Remove milliseconds and timezone offset
                    create_time = datetime.strptime(last_modified_str, "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
                    identifier = resource['FunctionName']
                    arn = resource['FunctionArn']
                    tags = client.list_tags(Resource=arn)['Tags']
                    resource_name = resource['FunctionName']
                    if create_time and create_time >= self.start_date:
                        if not self.tag_exists_dict(tags):
                            resources.append({ "process_id" : self.process_id, "account" : account, "region" : region, "service" : "lambda", "type" : "2", "identifier" : identifier, "resource_name" : resource_name, "arn" : arn, "tag_key" : self.tag_key , "tag_value" : self.tag_value, "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(tags) })
                        else:
                            resources.append({ "process_id" : self.process_id, "account" : account, "region" : region, "service" : "lambda", "type" : "1", "identifier" : identifier, "resource_name" : resource_name, "arn" : arn, "tag_key" : self.tag_key , "tag_value" : self.tag_value, "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(tags) })
                    else:
                        resources.append({ "process_id" : self.process_id, "account" : account, "region" : region, "service" : "lambda", "type" : "3", "identifier" : identifier, "resource_name" : resource_name, "arn" : arn, "tag_key" : self.tag_key , "tag_value" : self.tag_value, "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(tags) })
                    
            #Recording resources
            self.database.register_inventory_resources(resources)
            
        
        except Exception as err:
            self.logging.error(f'get_inventory_lambda : {err}')




    ####----| Function to get inventory for S3
    def get_inventory_s3(self,account,region):
        try:
        
            self.logging.info(f'Discovery # Account : {account}, Region : {region}, Service : {"s3"}')
            client = self.aws.get_aws_client(region,"s3")
        
            marker = None
            resources = []
            
            while True:
                    list_buckets_params = {}
                    if marker:
                        list_buckets_params['Marker'] = marker
            
                    response = client.list_buckets(**list_buckets_params)
                    marker = response.get('NextMarker')
                    buckets = response['Buckets']
                    try:
                        for bucket in buckets:
                            
                            identifier = bucket['Name']
                            resource_name = identifier
                            arn = f'arn:aws:s3:::{identifier}'
                            bucket_location = client.get_bucket_location(Bucket=identifier)
                            bucket_region = bucket_location['LocationConstraint']
                            if bucket_region is None:
                                bucket_region = 'us-east-1'
                            if bucket_region==region:
                                try:
                                    tags = client.get_bucket_tagging(Bucket=identifier).get('TagSet', [])
                                except botocore.exceptions.ClientError as e:
                                    tags = []
                                
                                create_time = bucket.get("CreationDate")
                                
                                if create_time and create_time >= self.start_date:
                                    if not self.tag_key_exists(tags):
                                        tags.append({'Key': self.tag_key, 'Value': self.tag_value})
                                        resources.append({ "process_id" : self.process_id, "account" : account, "region" : region, "service" : "s3", "type" : "2", "identifier" : identifier, "resource_name" : resource_name, "arn" : arn, "tag_key" : self.tag_key , "tag_value" : self.tag_value, "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(tags) })
                                    else:
                                        if not self.tag_exists(tags):
                                            # Remove tag
                                            tags = [d for d in tags if d["Key"] != self.tag_key]
                                            tags.append({'Key': self.tag_key, 'Value': self.tag_value})
                                            resources.append({ "process_id" : self.process_id, "account" : account, "region" : region, "service" : "s3", "type" : "2", "identifier" : identifier, "resource_name" : resource_name, "arn" : arn, "tag_key" : self.tag_key , "tag_value" : self.tag_value, "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(tags) })
                                        else:
                                            resources.append({ "process_id" : self.process_id, "account" : account, "region" : region, "service" : "s3", "type" : "1", "identifier" : identifier, "resource_name" : resource_name, "arn" : arn, "tag_key" : self.tag_key , "tag_value" : self.tag_value, "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(tags) })
                                else:
                                    resources.append({ "process_id" : self.process_id, "account" : account, "region" : region, "service" : "s3", "type" : "3", "identifier" : identifier, "resource_name" : resource_name, "arn" : arn, "tag_key" : self.tag_key , "tag_value" : self.tag_value, "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(tags) })
                                                        
                    except Exception as err:
                        self.logging.error(f'get_inventory_s3 : {err}')
                    
                    # Check if there are more buckets to list, if not, exit the loop
                    if not marker:
                        break
                    
            #Recording resources
            self.database.register_inventory_resources(resources)
            
        
        except Exception as err:
            self.logging.error(f'get_inventory_s3 : {err}')



    ####----| Function to get inventory for Backup Vaults
    def get_inventory_backup_vaults(self,account,region):
        try:
        
            self.logging.info(f'Discovery # Account : {account}, Region : {region}, Service : {"backup_vault"}')
            client = self.aws.get_aws_client(region,"backup")
        
            paginator = client.get_paginator('list_backup_vaults')
            resources = []

            for page in paginator.paginate():
                resource_list = page.get('BackupVaultList', [])
                for resource in resource_list:
                        create_time = resource['CreationDate']
                        identifier = resource['BackupVaultName']
                        arn = resource['BackupVaultArn']
                        tags = self.tags_dict_to_list(client.list_tags(ResourceArn=arn)['Tags'])
                        resource_name = identifier
                        if create_time and create_time >= self.start_date:
                            if not self.tag_exists(tags):
                                resources.append({ "process_id" : self.process_id, "account" : account, "region" : region, "service" : "backup_vault", "type" : "2", "identifier" : identifier, "resource_name" : resource_name, "arn" : arn, "tag_key" : self.tag_key , "tag_value" : self.tag_value, "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(tags) })
                            else:
                                resources.append({ "process_id" : self.process_id, "account" : account, "region" : region, "service" : "backup_vault", "type" : "1", "identifier" : identifier, "resource_name" : resource_name, "arn" : arn, "tag_key" : self.tag_key , "tag_value" : self.tag_value, "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(tags) })
                        else:
                            resources.append({ "process_id" : self.process_id, "account" : account, "region" : region, "service" : "backup_vault", "type" : "3", "identifier" : identifier, "resource_name" : resource_name, "arn" : arn, "tag_key" : self.tag_key , "tag_value" : self.tag_value, "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(tags) })
                    
            #Recording resources
            self.database.register_inventory_resources(resources)
            
        
        except Exception as err:
            self.logging.error(f'get_inventory_backup_vaults : {err}')
    
    
    
    
    
    ####----| Function to get inventory for Backup Plans
    def get_inventory_backup_plans(self,account,region):
        try:
        
            self.logging.info(f'Discovery # Account : {account}, Region : {region}, Service : {"backup_plans"}')
            client = self.aws.get_aws_client(region,"backup")
        
            paginator = client.get_paginator('list_backup_plans')
            resources = []

            for page in paginator.paginate():
                resource_list = page.get('BackupPlansList', [])
                for resource in resource_list:
                        create_time = resource['CreationDate']
                        identifier = resource['BackupPlanName']
                        arn = resource['BackupPlanArn']
                        tags = self.tags_dict_to_list(client.list_tags(ResourceArn=arn)['Tags'])
                        resource_name = identifier
                        if create_time and create_time >= self.start_date:
                            if not self.tag_exists(tags):
                                resources.append({ "process_id" : self.process_id, "account" : account, "region" : region, "service" : "backup_plan", "type" : "2", "identifier" : identifier, "resource_name" : resource_name, "arn" : arn, "tag_key" : self.tag_key , "tag_value" : self.tag_value, "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(tags) })
                            else:
                                resources.append({ "process_id" : self.process_id, "account" : account, "region" : region, "service" : "backup_plan", "type" : "1", "identifier" : identifier, "resource_name" : resource_name, "arn" : arn, "tag_key" : self.tag_key , "tag_value" : self.tag_value, "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(tags) })
                        else:
                            resources.append({ "process_id" : self.process_id, "account" : account, "region" : region, "service" : "backup_plan", "type" : "3", "identifier" : identifier, "resource_name" : resource_name, "arn" : arn, "tag_key" : self.tag_key , "tag_value" : self.tag_value, "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(tags) })
                    
            #Recording resources
            self.database.register_inventory_resources(resources)
            
        
        except Exception as err:
            self.logging.error(f'get_inventory_backup_plans : {err}')
    
    
    
    
    ####----| Function to get ECR Repositories
    def get_inventory_ecr(self,account,region):
        try:
        
            self.logging.info(f'Discovery # Account : {account}, Region : {region}, Service : {"ecr"}')
            client = self.aws.get_aws_client(region,"ecr")
        
            paginator = client.get_paginator('describe_repositories')
            resources = []
            for page in paginator.paginate():
                resource_list = page.get('repositories', [])
                for resource in resource_list:
                        create_time = resource['createdAt']
                        identifier = resource['repositoryName']
                        arn = resource['repositoryArn']
                        tags = client.list_tags_for_resource(resourceArn=arn)['tags']
                        resource_name = self.get_resource_name(tags)
                        if create_time and create_time >= self.start_date:
                            if not self.tag_exists(tags):
                                resources.append({ "process_id" : self.process_id, "account" : account, "region" : region, "service" : "ecr", "type" : "2", "identifier" : identifier, "resource_name" : resource_name, "arn" : arn, "tag_key" : self.tag_key , "tag_value" : self.tag_value, "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(tags) })
                            else:
                                resources.append({ "process_id" : self.process_id, "account" : account, "region" : region, "service" : "ecr", "type" : "1", "identifier" : identifier, "resource_name" : resource_name, "arn" : arn, "tag_key" : self.tag_key , "tag_value" : self.tag_value, "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(tags) })
                        else:
                            resources.append({ "process_id" : self.process_id, "account" : account, "region" : region, "service" : "ecr", "type" : "3", "identifier" : identifier, "resource_name" : resource_name, "arn" : arn, "tag_key" : self.tag_key , "tag_value" : self.tag_value, "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(tags) })
                        
            #Recording resources
            self.database.register_inventory_resources(resources)
            
        
        except Exception as err:
            self.logging.error(f'get_inventory_ecr : {err}')
    
    
    
    ####----| Function to get EKS Clusters
    def get_inventory_eks_clusters(self,account,region):
        try:
        
            self.logging.info(f'Discovery # Account : {account}, Region : {region}, Service : {"eks"}')
            client = self.aws.get_aws_client(region,"eks")
        
            paginator = client.get_paginator('list_clusters')
            resources = []
            for page in paginator.paginate():
                resource_list = page.get('clusters', [])
                for resource in resource_list:
                        cluster_info = client.describe_cluster(name=resource)['cluster']
                        create_time = cluster_info['createdAt']
                        identifier = resource
                        arn = cluster_info['arn']
                        tags = self.tags_dict_to_list(client.list_tags_for_resource(resourceArn=arn)['tags'])
                        resource_name = self.get_resource_name(tags)
                        if create_time and create_time >= self.start_date:
                            if not self.tag_exists(tags):
                                resources.append({ "process_id" : self.process_id, "account" : account, "region" : region, "service" : "eks", "type" : "2", "identifier" : identifier, "resource_name" : resource_name, "arn" : arn, "tag_key" : self.tag_key , "tag_value" : self.tag_value, "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(tags) })
                            else:
                                resources.append({ "process_id" : self.process_id, "account" : account, "region" : region, "service" : "eks", "type" : "1", "identifier" : identifier, "resource_name" : resource_name, "arn" : arn, "tag_key" : self.tag_key , "tag_value" : self.tag_value, "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(tags) })
                        else:
                            resources.append({ "process_id" : self.process_id, "account" : account, "region" : region, "service" : "eks", "type" : "3", "identifier" : identifier, "resource_name" : resource_name, "arn" : arn, "tag_key" : self.tag_key , "tag_value" : self.tag_value, "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(tags) })
                    
                        
            #Recording resources
            self.database.register_inventory_resources(resources)
            
        
        except Exception as err:
            self.logging.error(f'get_inventory_eks_clusters : {err}')
    
    
    
    
    ####----| Function to get ECS Clusters
    def get_inventory_ecs_clusters(self,account,region):
        try:
        
            self.logging.info(f'Discovery # Account : {account}, Region : {region}, Service : {"ecs"}')
            client = self.aws.get_aws_client(region,"ecs")
        
            paginator = client.get_paginator('list_clusters')
            resources = []
            for page in paginator.paginate():
                resource_list = page.get('clusterArns', [])
                for resource in resource_list:
                        cluster_info = client.describe_clusters(clusters=[resource])['clusters'][0]
                        create_time = ""
                        identifier = cluster_info['clusterName']
                        arn = cluster_info['clusterArn']
                        tags = client.list_tags_for_resource(resourceArn=arn)['tags']
                        tags = self.tag_key_convertion(tags,'key','value')
                        resource_name = self.get_resource_name(tags)
                        if not self.tag_exists(tags):
                            resources.append({ "process_id" : self.process_id, "account" : account, "region" : region, "service" : "ecs", "type" : "2", "identifier" : identifier, "resource_name" : resource_name, "arn" : arn, "tag_key" : self.tag_key , "tag_value" : self.tag_value, "created" : create_time, "tags" : json.dumps(tags) })
                        else:
                            resources.append({ "process_id" : self.process_id, "account" : account, "region" : region, "service" : "ecs", "type" : "1", "identifier" : identifier, "resource_name" : resource_name, "arn" : arn, "tag_key" : self.tag_key , "tag_value" : self.tag_value, "created" : create_time, "tags" : json.dumps(tags) })
                        
            #Recording resources
            self.database.register_inventory_resources(resources)
            
        
        except Exception as err:
            self.logging.error(f'get_inventory_ecs_clusters : {err}')
    
    
    
    ####----| Function to get EMR Clusters
    def get_inventory_emr_clusters(self,account,region):
        try:
        
            self.logging.info(f'Discovery # Account : {account}, Region : {region}, Service : {"emr"}')
            client = self.aws.get_aws_client(region,"emr")
        
            paginator = client.get_paginator('list_clusters')
            resources = []
            for page in paginator.paginate():
                resource_list = page.get('Clusters', [])
                for resource in resource_list:
                        status = resource['Status']['State']
                        if status == 'STARTING' or status ==  'BOOTSTRAPPING' or status == 'RUNNING' or status == 'WAITING':
                            create_time = resource['Status']['Timeline']['CreationDateTime']
                            identifier = resource['Id']
                            arn = resource['ClusterArn']
                            resource_name = resource['Name']
                            cluster_info = client.describe_cluster(ClusterId=identifier)['Cluster']
                            tags = cluster_info['Tags']
                            if not self.tag_exists(tags):
                                resources.append({ "process_id" : self.process_id, "account" : account, "region" : region, "service" : "emr", "type" : "2", "identifier" : identifier, "resource_name" : resource_name, "arn" : arn, "tag_key" : self.tag_key , "tag_value" : self.tag_value, "created" : create_time, "tags" : json.dumps(tags) })
                            else:
                                resources.append({ "process_id" : self.process_id, "account" : account, "region" : region, "service" : "emr", "type" : "1", "identifier" : identifier, "resource_name" : resource_name, "arn" : arn, "tag_key" : self.tag_key , "tag_value" : self.tag_value, "created" : create_time, "tags" : json.dumps(tags) })
                            
            #Recording resources
            self.database.register_inventory_resources(resources)
            
        
        except Exception as err:
            self.logging.error(f'get_inventory_emr_clusters : {err}')
    
    
    
    
    ####----| Function to get Transit Gateways Clusters
    def get_inventory_transit_gateways(self,account,region):
        try:
        
            self.logging.info(f'Discovery # Account : {account}, Region : {region}, Service : {"tgw"}')
            client = self.aws.get_aws_client(region,"ec2")
        
            paginator = client.get_paginator('describe_transit_gateways')
            resources = []
            for page in paginator.paginate():
                resource_list = page.get('TransitGateways', [])
                for resource in resource_list:
                        create_time = resource['CreationTime']
                        identifier = resource['TransitGatewayId']
                        arn = resource['TransitGatewayArn']
                        tags = resource.get("Tags")  if "Tags" in resource else []
                        resource_name = self.get_resource_name(tags)
                        if create_time and create_time >= self.start_date:
                            if not self.tag_exists(tags):
                                resources.append({ "process_id" : self.process_id, "account" : account, "region" : region, "service" : "tgw", "type" : "2", "identifier" : identifier, "resource_name" : resource_name, "arn" : arn, "tag_key" : self.tag_key , "tag_value" : self.tag_value, "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(tags) })
                            else:
                                resources.append({ "process_id" : self.process_id, "account" : account, "region" : region, "service" : "tgw", "type" : "1", "identifier" : identifier, "resource_name" : resource_name, "arn" : arn, "tag_key" : self.tag_key , "tag_value" : self.tag_value, "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(tags) })
                        else:
                            resources.append({ "process_id" : self.process_id, "account" : account, "region" : region, "service" : "tgw", "type" : "3", "identifier" : identifier, "resource_name" : resource_name, "arn" : arn, "tag_key" : self.tag_key , "tag_value" : self.tag_value, "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(tags) })
                        
            #Recording resources
            self.database.register_inventory_resources(resources)
            
        
        except Exception as err:
            self.logging.error(f'get_inventory_transit_gateways : {err}')
    
    
    
    
    ####----| Function to get Transit Gateways Clusters
    def get_inventory_transit_gateway_attachments(self,account,region):
        try:
        
            self.logging.info(f'Discovery # Account : {account}, Region : {region}, Service : {"tgw_att"}')
            client = self.aws.get_aws_client(region,"ec2")
        
            paginator = client.get_paginator('describe_transit_gateway_attachments')
            resources = []
            for page in paginator.paginate():
                resource_list = page.get('TransitGatewayAttachments', [])
                for resource in resource_list:
                        create_time = resource['CreationTime']
                        identifier = resource['TransitGatewayAttachmentId']
                        arn = resource['ResourceId']
                        tags = resource.get("Tags")  if "Tags" in resource else []
                        resource_name = self.get_resource_name(tags)
                        if create_time and create_time >= self.start_date:
                            if not self.tag_exists(tags):
                                resources.append({ "process_id" : self.process_id, "account" : account, "region" : region, "service" : "tgw_att", "type" : "2", "identifier" : identifier, "resource_name" : resource_name, "arn" : arn, "tag_key" : self.tag_key , "tag_value" : self.tag_value, "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(tags) })
                            else:
                                resources.append({ "process_id" : self.process_id, "account" : account, "region" : region, "service" : "tgw_att", "type" : "1", "identifier" : identifier, "resource_name" : resource_name, "arn" : arn, "tag_key" : self.tag_key , "tag_value" : self.tag_value, "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(tags) })
                        else:
                            resources.append({ "process_id" : self.process_id, "account" : account, "region" : region, "service" : "tgw_att", "type" : "3", "identifier" : identifier, "resource_name" : resource_name, "arn" : arn, "tag_key" : self.tag_key , "tag_value" : self.tag_value, "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(tags) })
                        
            #Recording resources
            self.database.register_inventory_resources(resources)
            
        
        except Exception as err:
            self.logging.error(f'get_inventory_transit_gateway_attachments : {err}')
            
            
            
            
    
    ####----| Function to get Transfer Family 
    def get_inventory_transfer_family_servers(self,account,region):
        try:
        
            self.logging.info(f'Discovery # Account : {account}, Region : {region}, Service : {"tfs"}')
            client = self.aws.get_aws_client(region,"transfer")
        
            paginator = client.get_paginator('list_servers')
            resources = []
            for page in paginator.paginate():
                resource_list = page.get('Servers', [])
                for resource in resource_list:
                        create_time = ""
                        identifier = resource['ServerId']
                        arn = resource['Arn']
                        server_info = client.describe_server(ServerId=identifier)['Server']
                        tags = server_info.get("Tags")  if "Tags" in server_info else []
                        resource_name = self.get_resource_name(tags)
                        if not self.tag_exists(tags):
                            resources.append({ "process_id" : self.process_id, "account" : account, "region" : region, "service" : "tfs", "type" : "2", "identifier" : identifier, "resource_name" : resource_name, "arn" : arn, "tag_key" : self.tag_key , "tag_value" : self.tag_value, "created" : create_time, "tags" : json.dumps(tags) })
                        else:
                            resources.append({ "process_id" : self.process_id, "account" : account, "region" : region, "service" : "tfs", "type" : "1", "identifier" : identifier, "resource_name" : resource_name, "arn" : arn, "tag_key" : self.tag_key , "tag_value" : self.tag_value, "created" : create_time, "tags" : json.dumps(tags) })
                    
            #Recording resources
            self.database.register_inventory_resources(resources)
            
        
        except Exception as err:
            self.logging.error(f'get_inventory_transfer_family_servers : {err}')
            
            
            
            
    
    
    ####----| Function to get API Gateways
    def get_inventory_api_gateways(self,account,region):
        try:
        
            self.logging.info(f'Discovery # Account : {account}, Region : {region}, Service : {"api_gtw"}')
            client = self.aws.get_aws_client(region,"apigateway")
        
            paginator = client.get_paginator('get_rest_apis')
            resources = []
            for page in paginator.paginate():
                resource_list = page.get('items', [])
                for resource in resource_list:
                        create_time = resource['createdDate']
                        identifier = resource['id']
                        arn = f"arn:aws:apigateway:{region}::/restapis/{identifier}"
                        tags = resource.get("tags")  if "tags" in resource else {}
                        resource_name = self.get_resource_name_dict(tags)
                        if create_time and create_time >= self.start_date:
                            if not self.tag_exists_dict(tags):
                                resources.append({ "process_id" : self.process_id, "account" : account, "region" : region, "service" : "api_gtw", "type" : "2", "identifier" : identifier, "resource_name" : resource_name, "arn" : arn, "tag_key" : self.tag_key , "tag_value" : self.tag_value, "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(tags) })
                            else:
                                resources.append({ "process_id" : self.process_id, "account" : account, "region" : region, "service" : "api_gtw", "type" : "1", "identifier" : identifier, "resource_name" : resource_name, "arn" : arn, "tag_key" : self.tag_key , "tag_value" : self.tag_value, "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(tags) })
                        else:
                            resources.append({ "process_id" : self.process_id, "account" : account, "region" : region, "service" : "api_gtw", "type" : "3", "identifier" : identifier, "resource_name" : resource_name, "arn" : arn, "tag_key" : self.tag_key , "tag_value" : self.tag_value, "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(tags) })
                        
            #Recording resources
            self.database.register_inventory_resources(resources)
            
        
        except Exception as err:
            self.logging.error(f'get_inventory_api_gateways : {err}')
            
            
            
            
    
    
    ####----| Function to get API Gateways Websocket
    def get_inventory_api_gateway_websockets(self,account,region):
        try:
        
            self.logging.info(f'Discovery # Account : {account}, Region : {region}, Service : {"api_gtw_ws"}')
            client = self.aws.get_aws_client(region,"apigatewayv2")
        
            paginator = client.get_paginator('get_apis')
            resources = []
            for page in paginator.paginate():
                resource_list = page.get('Items', [])
                for resource in resource_list:
                        create_time = resource['CreatedDate']
                        identifier = resource['ApiId']
                        arn = f"arn:aws:apigateway:{region}::/apis/{identifier}"
                        tags = resource.get("Tags")  if "Tags" in resource else {}
                        resource_name = self.get_resource_name_dict(tags)
                        if create_time and create_time >= self.start_date:
                            if not self.tag_exists_dict(tags):
                                resources.append({ "process_id" : self.process_id, "account" : account, "region" : region, "service" : "api_gtw_ws", "type" : "2", "identifier" : identifier, "resource_name" : resource_name, "arn" : arn, "tag_key" : self.tag_key , "tag_value" : self.tag_value, "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(tags) })
                            else:
                                resources.append({ "process_id" : self.process_id, "account" : account, "region" : region, "service" : "api_gtw_ws", "type" : "1", "identifier" : identifier, "resource_name" : resource_name, "arn" : arn, "tag_key" : self.tag_key , "tag_value" : self.tag_value, "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(tags) })
                        else:
                            resources.append({ "process_id" : self.process_id, "account" : account, "region" : region, "service" : "api_gtw_ws", "type" : "3", "identifier" : identifier, "resource_name" : resource_name, "arn" : arn, "tag_key" : self.tag_key , "tag_value" : self.tag_value, "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(tags) })
                        
            #Recording resources
            self.database.register_inventory_resources(resources)
            
        
        except Exception as err:
            self.logging.error(f'get_inventory_api_gateway_websockets : {err}')
            
            
    
    
    
    
    ####----| Function to get Workspaces
    def get_inventory_workspaces(self,account,region):
        try:
        
            self.logging.info(f'Discovery # Account : {account}, Region : {region}, Service : {"workspaces"}')
            client = self.aws.get_aws_client(region,"workspaces")
        
            paginator = client.get_paginator('describe_workspaces')
            resources = []
            for page in paginator.paginate():
                resource_list = page.get('Workspaces', [])
                for resource in resource_list:
                        create_time = ""
                        identifier = resource['WorkspaceId']
                        arn = resource['WorkspaceId']
                        tags = client.describe_tags(ResourceId=identifier)['TagList']
                        resource_name = self.get_resource_name(tags)
                        if not self.tag_exists(tags):
                            resources.append({ "process_id" : self.process_id, "account" : account, "region" : region, "service" : "workspaces", "type" : "2", "identifier" : identifier, "resource_name" : resource_name, "arn" : arn, "tag_key" : self.tag_key , "tag_value" : self.tag_value, "created" : create_time, "tags" : json.dumps(tags) })
                        else:
                            resources.append({ "process_id" : self.process_id, "account" : account, "region" : region, "service" : "workspaces", "type" : "1", "identifier" : identifier, "resource_name" : resource_name, "arn" : arn, "tag_key" : self.tag_key , "tag_value" : self.tag_value, "created" : create_time, "tags" : json.dumps(tags) })
                    
            #Recording resources
            self.database.register_inventory_resources(resources)
            
        
        except Exception as err:
            self.logging.error(f'get_inventory_workspaces : {err}')
            

####----| Main Function
def main():
    
    # Start Tagging Process
    process_type = sys.argv[1]
    process_id = sys.argv[2]
    tagger = classTagger(process_id)
    
    print(sys.argv)
    
    if process_type == "inventory":
        tagger.start_inventory_process()
    
    if process_type == "tagging":
        tagger.start_tagging_process(tagger.process_id)
    
    
    
####----| Call Main Function
if __name__ == "__main__":
    main()

import boto3
from os import environ
from datetime import datetime, timezone
import botocore
import pymysql.cursors
import json
import logging
import sys
import time
import os
import importlib


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
                            
                            ## Modules
                            for file in os.listdir('plugins'):
                                if file[:3] == 'srv':
                                    module = importlib.import_module(f'plugins.{file[:-3]}')
                                    module.discovery(self,account['id'],region)
                            
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
                  
            # Create master tagging process
            self.database.create_master_tagging_process({ "process_id" : self.process_id })
            
            for account in self.configuration['Accounts']:
                self.logging.info(f'Processing Account : {account}')
                if (self.aws.authentication(account['id'])):
                    active_regions = self.aws.get_active_regions()
                    self.logging.info(f'Active regions : {active_regions}')
                    for region in account['regions']:
                        
                        ## Modules
                        for file in os.listdir('plugins'):
                            if file[:3] == 'srv':
                                module = importlib.import_module(f'plugins.{file[:-3]}')
                                info = json.loads(module.info())
                                
                                resources = []
                                recordset = self.database.get_tagging_resources(self.process_id, account['id'], region, info['sub_service'])
                                for record in recordset:
                                    resources.append({ "identifier" : record['identifier'], "action" : record['type'], "arn" : record['arn'], "tags" : record['tag_list'], "tag_key" : record['tag_key'] })
                                
                                module.tagging(self, account['id'], region, resources, tags)
                        
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

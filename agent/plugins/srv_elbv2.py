import json

####----| Info method
def info():
    return (json.dumps({ "id" : "m013", "service" : "elbv2", "sub_service" : "elbv2", "description" : "AWS Service EC2", "version" : "1.0.0", "date" : "2024-09-10" }))


####----| Init method
def init():
    pass


####----| Release method
def release():
    pass


####----| Discovery method
def discovery(tagger,account,region):
    try:
        service_info = json.loads(info())
        tagger.logging.info(f'Discovery # Account : {account}, Region : {region}, Service : {service_info["sub_service"]}')
        client = tagger.aws.get_aws_client(region,service_info["service"])
        paginator = client.get_paginator('describe_load_balancers')
        resources = []
        
        for page in paginator.paginate():
            resource_list = page.get('LoadBalancers', [])
            for resource in resource_list:
                    create_time = resource['CreatedTime']
                    identifier = resource['LoadBalancerName']
                    arn = resource['LoadBalancerArn']
                    tags = client.describe_tags(ResourceArns=[arn])['TagDescriptions'][0]['Tags']
                    resource_name = tagger.get_resource_name(tags)
                    action = ""
                    if create_time and create_time >= tagger.start_date:
                        if not tagger.tag_exists(tags):
                            action = "2"
                        else:
                            action = "1"
                    else:
                        action = "3"                        
                        
                    resources.append({ "process_id" : tagger.process_id, "account" : account, "region" : region, "service" : service_info["sub_service"], "type" : action, "identifier" : identifier, "resource_name" : resource_name, "arn" : arn, "tag_key" : tagger.tag_key , "tag_value" : tagger.tag_value, "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(tags) })
    
        #Recording resources
        tagger.database.register_inventory_resources(resources)

    except Exception as err:
        tagger.logging.error(f'discovery : {err}')
        
        

####----| Tagging method
def tagging(tagger,account,region,resources,tags):
    try:
        service_info = json.loads(info())
        tagger.logging.info(f'Tagging # Account : {account}, Region : {region}, Service : {service_info["sub_service"]}')
        client = tagger.aws.get_aws_client(region,service_info["service"])
        for resource in resources:
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
                        
    except Exception as err:
        tagger.logging.error(f'tagging : {err}')

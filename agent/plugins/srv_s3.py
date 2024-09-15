import json

####----| Info method
def info():
    return (json.dumps({ "id" : "m020", "service" : "s3", "sub_service" : "s3", "description" : "AWS Service S3", "version" : "1.0.0", "date" : "2024-09-10" }))


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
                        except:
                            tags = []
                        
                        create_time = bucket.get("CreationDate")
                        action = ""
                        if create_time and create_time >= tagger.start_date:
                            if not tagger.tag_key_exists(tags):
                                tags.append({'Key': tagger.tag_key, 'Value': tagger.tag_value})
                                action = "2"
                            else:
                                if not tagger.tag_exists(tags):
                                    # Remove tag
                                    tags = [d for d in tags if d["Key"] != tagger.tag_key]
                                    tags.append({'Key': tagger.tag_key, 'Value': tagger.tag_value})
                                    action = "2"
                                else:
                                    action = "1"
                        else:
                            action = "3"
                        resources.append({ "process_id" : tagger.process_id, "account" : account, "region" : region, "service" : service_info["sub_service"], "type" : action, "identifier" : identifier, "resource_name" : resource_name, "arn" : arn, "tag_key" : tagger.tag_key , "tag_value" : tagger.tag_value, "created" : create_time.strftime("%Y-%m-%d %H:%M:%S"), "tags" : json.dumps(tags) })
                        
            except Exception as err:
                tagger.logging.error(f'discovery : {err}')
            
            # Check if there are more buckets to list, if not, exit the loop
            if not marker:
                break
    
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
                        
    except Exception as err:
        tagger.logging.error(f'tagging : {err}')

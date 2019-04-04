import boto3, argparse, os, redis, json



AWS_CREDENTIALS = {
    'access_key': None,
    'secret_key': None,
    'role'      : None,
    'region'    : None,
    'profile'   : None
}

r53 = boto3.client('route53')

def _get_credentials():
    creds = AWS_CREDENTIALS.copy()
    profile = args.profile or os.environ.get('AWS_PROFILE') or None
    if profile:
        creds.update(dict(profile=profile))
    else:
        access_key = args.access_key or os.environ.get('AWS_ACCESS_KEY') or os.environ.get('AWS_ACCESS_KEY_ID') or None
        secret_key = args.secret_key or os.environ.get('AWS_SECRET_KEY') or os.environ.get('AWS_SECRET_ACCESS_KEY') or None
        role = args.role or None
        region = args.region or os.environ.get('AWS_DEFAULT_REGION') or None
        creds.update(dict(access_key=access_key, secret_key=secret_key, role=role, region=region))

    return creds

def get_connection():
    credentials = _get_credentials()
    if credentials['profile']:
        conn = boto3.Session(profile_name=credentials['profile'])
    else:
        if credentials['role']:
            sts_conn = boto3.client('sts',
                aws_access_key_id=credentials['access_key'],
                aws_secret_access_key=credentials['secret_key']
            )
            assumed = sts_conn.assume_role(RoleArn=credentials['role'],RoleSessionName='route53-search')
            c = assumed.get('Credentials')
            temp_creds = {
                'access_key': c.get('AccessKeyId'),
                'secret_key': c.get('SecretAccessKey'),
                'session_token': c.get('SessionToken')
            }
        else:
            temp_creds = credentials.copy()
        conn = boto3.Session(
        aws_access_key_id=temp_creds.get('access_key'),
        aws_secret_access_key=temp_creds.get('secret_key'),
        aws_session_token=temp_creds.get('session_token',None)
        )
    return conn

def get_hosted_zones():
    if use_redis:
        result = redis_client.get('zones')
        if result:
            return json.loads(result)
    result = r53.list_hosted_zones()
    zones = result.get('HostedZones')
    while(result.get('IsTruncated')):
        result = r53.list_hosted_zones(Marker=result.get('NextMarker'))
        zones+=result.get('HostedZones')
    if use_redis:
        redis_client.set('zones',json.dumps(zones),1200)
    return zones


def get_record_for_zone(zone_id):
    if use_redis:
        result = redis_client.get('records-'+zone_id)
        if result:
            return json.loads(result)
    result = r53.list_resource_record_sets(
        HostedZoneId=zone_id
    )
    records = result.get('ResourceRecordSets')
    while(result.get('IsTruncated')):
        result = r53.list_resource_record_sets(
        HostedZoneId=zone_id,
        StartRecordName=result.get('NextRecordName'),
        StartRecordType=result.get('NextRecordType')
        )
        records += result.get('ResourceRecordSets')
    if use_redis:
        redis_client.set('records-'+zone_id,json.dumps(records),300)
    return records

def search_for_val(val, record_type, records):
    results = []
    print(val)
    for record in records:
        valid = True
        values = []
        if record_type:
            valid = record.get('Type') == record_type
        display = False
        if val in record.get('Name') and valid:
            display = True
        if valid:
            for rr in (record.get('ResourceRecords') or []):
                if val in rr.get('Value') or display:
                    display = True
                    values.append(rr.get('Value'))
        if display:
            results.append({'name': record.get('Name'), 'type': record.get('Type'), 'values': values})
    return sorted(results, key = lambda i: (i['name'])) 

def search(user_input):
    if(args.zone_id):
        records = get_record_for_zone(args.zone_id)
    else:
        zones = get_hosted_zones()
        records = []
        for zone in zones:
            records+=get_record_for_zone(zone.get('Id'))

    results = search_for_val(user_input,args.type,records)
    for result in results:
        print(result)


parser = argparse.ArgumentParser(description='Route53 Record Search')
parser.add_argument('--profile', type=str, help='AWS Profile to use', default=None)
parser.add_argument('--zone_id', type=str, help='Zone to search', default=None)
parser.add_argument('--access_key', type=str, help='AWS Access Key', default=None)
parser.add_argument('--secret_key', type=str, help='AWS Secret Key', default=None)
parser.add_argument('--region', type=str, help='AWS Region', default='us-east-1')
parser.add_argument('--role', type=str, help='AWS Role to assume', default=None)
parser.add_argument('--type', type=str, help='DNS record type to check', default=None)
parser.add_argument('--redis', type=str, help='Redis server to cache with', default=None)
parser.add_argument('--redis_port', type=str, help='Redis server port', default=6379)
parser.add_argument('val', type=str, help='Value to search for', default=None)
args = parser.parse_args()
conn = get_connection()
use_redis = args.redis


if use_redis:
    redis_client = redis.Redis(host=use_redis, port=args.redis_port, db=0)

r53 = conn.client('route53')
search(args.val)






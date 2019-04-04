# route53-search

# Description
I need to search for a dns record across all of my hosted zones. This utility allows you to do this. You can either specify the zone_id for single zone search or by default search all hosted zones returned to you by route 53.
# Installation
python3 -m venv PATH  
source PATH/bin/activate  
pip install -r requirements.txt  

# Usage

```
usage: search.py [-h] [--profile PROFILE] [--zone_id ZONE_ID]
                 [--access_key ACCESS_KEY] [--secret_key SECRET_KEY]
                 [--region REGION] [--role ROLE] [--type TYPE] [--redis REDIS]
                 [--redis_port REDIS_PORT]
                 val

Route53 Record Search

positional arguments:
  val                   Value to search for

optional arguments:
  -h, --help            show this help message and exit
  --profile PROFILE     AWS Profile to use
  --zone_id ZONE_ID     Zone to search
  --access_key ACCESS_KEY
                        AWS Access Key
  --secret_key SECRET_KEY
                        AWS Secret Key
  --region REGION       AWS Region
  --role ROLE           AWS Role to assume
  --type TYPE           DNS record type to check
  --redis REDIS         Redis server to cache with
  --redis_port REDIS_PORT
                        Redis server port
```

```
python search.py --role AWS_ROLE_TO_ASSUME --redis 127.0.0.1 VALUE_TO_SEARCH_FOR
```
Docker one liner if you need it:  
`docker run -d -p 6379:6379 redis:latest` 

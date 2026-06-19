import boto3


# get the corresponding `AssetValue` based on the `AssetName` key from the dynamoDB database table named `ZacharyGeorgeBaker-Assets`
def GetValueFromDb(key: str) -> str:
    value = ""
    try:
        db_resource = boto3.Session().resource('dynamodb', region_name='us-west-1')
        db_table = db_resource.Table('ZacharyGeorgeBaker-Assets')
        resp = db_table.get_item(
            Key={
                'AssetName': key
            }
        )
        if 'Item' in resp:
            value = resp['Item']['AssetValue']
        print(resp)
    finally:
        return value

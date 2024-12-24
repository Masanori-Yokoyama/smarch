import os
import boto3
from smb.SMBConnection import SMBConnection
from datetime import datetime

def lambda_handler(event, context):
    """
    AWS Lambda handler for archiving files from SMB share to S3
    """
    conn = None
    try:
        # Systems Manager Parameter Storeから認証情報を取得
        ssm = boto3.client('ssm', endpoint_url=os.getenv('SSM_ENDPOINT_URL'))
        smb_user = ssm.get_parameter(Name='/smb/username', WithDecryption=True)['Parameter']['Value']
        smb_pass = ssm.get_parameter(Name='/smb/password', WithDecryption=True)['Parameter']['Value']
        
        # SMB接続の設定
        smb_host = os.getenv('SMB_HOST', 'localhost')  # デフォルトをlocalhostに変更
        conn = SMBConnection(
            smb_user,
            smb_pass,
            'lambda_client',
            smb_host,
            use_ntlm_v2=True
        )
        
        # SMB接続
        if not conn.connect(smb_host, 445):
            return {
                'statusCode': 500,
                'body': 'Failed to connect to SMB share'
            }

        # ファイル一覧取得
        files = conn.listPath('share', '/')
        
        # S3クライアント
        s3 = boto3.client('s3', endpoint_url=os.getenv('S3_ENDPOINT_URL'))
        bucket_name = os.getenv('S3_BUCKET_NAME', 'test-bucket')
        
        processed_files = []
        for file in files:
            if file.isDirectory:
                continue
                
            # 一時ファイルにダウンロード
            temp_path = f"/tmp/{file.filename}"
            with open(temp_path, 'wb') as f:
                conn.retrieveFile('share', f"/{file.filename}", f)
            
            # S3にアップロード
            s3_key = f"archives/{datetime.now().strftime('%Y%m%d')}/{file.filename}"
            s3.upload_file(temp_path, bucket_name, s3_key)
            
            # 元ファイルを削除
            conn.deleteFiles('share', f"/{file.filename}")
            
            # 一時ファイルを削除
            os.remove(temp_path)
            
            processed_files.append(file.filename)
        
        return {
            'statusCode': 200,
            'body': f'Processed files: {processed_files}'
        }
            
    except Exception as e:
        return {
            'statusCode': 500,
            'body': f'Error: {e.__class__.__name__}: {str(e)}'
        }
    finally:
        if conn:
            conn.close()